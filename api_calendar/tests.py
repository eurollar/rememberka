import copy
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import force_authenticate
from api_calendar.models import Event, Remind, CountryHolidays
from api_calendar.serializers import AllDateSerializer, EventSerializer


class GetAllAPIDataTest(TestCase):
    """Test module for GET all events for current user"""

    def setUp(self):
        self.user1 = User.objects.create_user('test name1')
        self.token1 = Token.objects.create(user=self.user1)
        self.user2 = User.objects.create_user('test name2')
        self.token2 = Token.objects.create(user=self.user2)
        self.remind = Remind.objects.create(title='За 2 часа')
        self.event1 = Event.objects.create(
            title='test title',
            start_date='2021-08-25',
            start_time='10:00:00',
            end_date='2021-08-26',
            end_time='11:00:00',
            memento=self.remind,
            user=self.user1,
        )
        self.event2 = Event.objects.create(
            title='test title',
            start_date='2021-08-27',
            start_time='12:09:00',
            end_date='2021-08-28',
            end_time='13:00:00',
            memento=self.remind,
            user=self.user2,
        )

    def test_get_all_events(self):
        force_authenticate(self.user1, token=self.token1.key)
        url = reverse('home')
        data = Event.objects.all().filter(user_id=self.user1.id)
        serializer = AllDateSerializer(data, many=True)

        # Valid - Get data to current user
        response = self.client.get(
            url,
            HTTP_AUTHORIZATION=f'Token {self.token1}'
        )
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Invalid data - POST request
        data = {'title': 'Edit title'}
        response = self.client.post(url, data=data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Invalid data - PUT request
        response = self.client.post(url, data=data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Invalid data - DELETE request
        response = self.client.delete(url, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Invalid - Get data to unauthorized user
        self.client.logout()
        response = self.client.get(
            url
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Get data to another user - different data
        force_authenticate(self.user1, token=self.token1.key)
        response_user_1 = self.client.get(
            url,
            HTTP_AUTHORIZATION=f'Token {self.token1}'
        )
        self.assertEqual(response_user_1.status_code, status.HTTP_200_OK)
        force_authenticate(self.user2, token=self.token2.key)
        response_user_2 = self.client.get(
            url,
            HTTP_AUTHORIZATION=f'Token {self.token2}'
        )
        self.assertEqual(response_user_2.status_code, status.HTTP_200_OK)
        # Compare responses
        self.assertNotEqual(response_user_1.data, response_user_2.data)


class AddDataTest(TestCase):
    """Test to add new event"""
    def setUp(self):
        self.user1 = User.objects.create_user('test name1')
        self.token1 = Token.objects.create(user=self.user1)
        self.user2 = User.objects.create_user('test name2')
        self.token2 = Token.objects.create(user=self.user2)
        self.remind = Remind.objects.create(title='За 2 часа')

        self.data = {
            'title': 'test title',
            'start_date': '2021-08-25',
            'start_time': '10:00:00',
            'end_date': '2021-08-26',
            'end_time': '11:00:00',
            'memento': self.remind.id,
            'user': self.user1
        }

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_validated_data(self):
        force_authenticate(self.user1, token=self.token1.key)
        url = reverse('add-event')
        response = self.client.post(url, data=self.data, HTTP_AUTHORIZATION=f'Token {self.token1}')

        # Valid data
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        event = Event.objects.get(**self.data)
        self.assertEqual(response.data['id'], event.id)

        # Valid data without end data
        self.data['end_date'] = ''
        response = self.client.post(url, data=self.data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Valid data without end time
        self.data['end_time'] = ''
        response = self.client.post(url, data=self.data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Valid data without end data and time
        self.data['end_date'] = ''
        self.data['end_time'] = ''
        response = self.client.post(url, data=self.data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Invalid data where end date less than start date
        self.data['end_date'] = '2021-08-24'
        response = self.client.post(url, data=self.data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid data where end time less than start time in one day
        self.data['end_date'] = '2021-08-25'
        self.data['end_time'] = '09:00:00'
        response = self.client.post(url, data=self.data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid data where end time less than start time when end date is '' (in this case end_date == start_date)
        self.data['end_date'] = ''
        self.data['end_time'] = '09:00:00'
        response = self.client.post(url, data=self.data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid - empty title
        self.data['title'] = ''
        response = self.client.post(url, data=self.data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid - empty user
        self.data['user'] = ''
        response = self.client.post(url, data=self.data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid - empty start date
        self.data['start_date'] = ''
        response = self.client.post(url, data=self.data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid - empty start time
        self.data['start_time'] = ''
        response = self.client.post(url, data=self.data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid - empty remind
        self.data['memento'] = ''
        response = self.client.post(url, data=self.data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid - non-existent user
        self.data['user'] = "DOESN'T EXIST"
        response = self.client.post(url, data=self.data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid - incorrect date
        self.data['start_date'] = 'INCORRECT'
        response = self.client.post(url, data=self.data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid - incorrect time
        self.data['start_time'] = 'ICC-0-rRe-cT'
        response = self.client.post(url, data=self.data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid - incorrect remind
        self.data['memento'] = 'Incorrect'
        response = self.client.post(url, data=self.data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid data - non-existed ID remind
        self.data['memento'] = 54
        response = self.client.post(url, data=self.data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid - another user
        self.data['user'] = self.user2
        response = self.client.post(url, data=self.data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid data without field
        self.data.pop('end_time')
        response = self.client.post(url, data=self.data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid data with non-exist field
        self.data['non-exist'] = 'field'
        response = self.client.post(url, data=self.data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetSingleDataTest(TestCase):
    """Tests to get single event (with primary key in url)"""
    def setUp(self):
        self.user1 = User.objects.create_user('test name1')
        self.token1 = Token.objects.create(user=self.user1)
        self.user2 = User.objects.create_user('test name2')
        self.token2 = Token.objects.create(user=self.user2)
        self.remind = Remind.objects.create(title='За 2 часа')
        self.event = Event.objects.create(
            title='test title',
            start_date='2021-08-25',
            start_time='10:00:00',
            end_date='2021-08-26',
            end_time='11:00:00',
            memento=self.remind,
            user=self.user1,
        )

    def test_get_single_event(self):
        force_authenticate(self.user1, token=self.token1.key)
        url = reverse('crud-event', kwargs={'pk': self.event.pk})

        # Valid data
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Token {self.token1}')
        data = Event.objects.get(pk=self.event.pk)
        serializer = EventSerializer(data)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Invalid data, non-exist PK
        url = reverse('crud-event', kwargs={'pk': 54})
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Invalid - Get event for unauthorized user
        self.client.logout()
        url = reverse('crud-event', kwargs={'pk': self.event.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Invalid - Get event for another user
        force_authenticate(self.user2, token=self.token2.key)
        response = self.client.get(url, kwargs={'pk': self.event.pk}, HTTP_AUTHORIZATION=f'Token {self.token2}')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PutSingleDataTest(TestCase):
    """Tests to update single event (with primary key in url)"""
    def setUp(self):
        self.user1 = User.objects.create_user('test name1')
        self.token1 = Token.objects.create(user=self.user1)
        self.user2 = User.objects.create_user('test name2')
        self.token2 = Token.objects.create(user=self.user2)
        self.remind = Remind.objects.create(title='За 2 часа')
        self.event = Event.objects.create(
            title='test title',
            start_date='2021-08-25',
            start_time='10:00:00',
            end_date='2021-08-26',
            end_time='11:00:00',
            memento=self.remind,
            user=self.user1,
        )

        self.data = {
            'title': 'test title',
            'start_date': '2021-08-25',
            'start_time': '10:00:00',
            'end_date': '2021-08-26',
            'end_time': '11:00:00',
            'memento': self.remind.id,
            'user': self.user1.id
        }

    def test_put_single_event(self):
        force_authenticate(self.user1, token=self.token1.key)
        url = reverse('crud-event', kwargs={'pk': self.event.pk})

        # Valid data
        self.data['title'] = 'edit title'
        response = self.client.put(url,
                                   data=self.data,
                                   HTTP_AUTHORIZATION=f'Token {self.token1}',
                                   content_type='application/json'
                                   )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Valid start date
        self.data['start_date'] = '2021-08-26'
        response = self.client.put(url,
                                   data=self.data,
                                   HTTP_AUTHORIZATION=f'Token {self.token1}',
                                   content_type='application/json'
                                   )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Valid end date
        self.data['end_date'] = '2021-08-27'
        response = self.client.put(url,
                                   data=self.data,
                                   HTTP_AUTHORIZATION=f'Token {self.token1}',
                                   content_type='application/json'
                                   )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Valid start time
        self.data['start_time'] = '10:00:00'
        response = self.client.put(url,
                                   data=self.data,
                                   HTTP_AUTHORIZATION=f'Token {self.token1}',
                                   content_type='application/json'
                                   )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Valid end date
        self.data['end_time'] = '12:00:00'
        response = self.client.put(url,
                                   data=self.data,
                                   HTTP_AUTHORIZATION=f'Token {self.token1}',
                                   content_type='application/json'
                                   )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Valid some data
        self.data['start_time'] = '12:00:00'
        self.data['end_time'] = '13:00:00'
        response = self.client.put(url,
                                   data=self.data,
                                   HTTP_AUTHORIZATION=f'Token {self.token1}',
                                   content_type='application/json'
                                   )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Invalid data when end date less than start date
        self.data['start_date'] = '2021-08-27'
        self.data['end_date'] = '2021-08-26'
        response = self.client.put(url,
                                   data=self.data,
                                   HTTP_AUTHORIZATION=f'Token {self.token1}',
                                   content_type='application/json'
                                   )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid data when end time less than start time in one day
        self.data['start_date'] = '2021-08-27'
        self.data['end_date'] = '2021-08-27'
        self.data['start_time'] = '12:00:00'
        self.data['end_time'] = '11:00:00'
        response = self.client.put(url,
                                   data=self.data,
                                   HTTP_AUTHORIZATION=f'Token {self.token1}',
                                   content_type='application/json'
                                   )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid empty required data
        self.data['start_date'] = ''
        response = self.client.put(url,
                                   data=self.data,
                                   HTTP_AUTHORIZATION=f'Token {self.token1}',
                                   content_type='application/json'
                                   )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid empty data
        self.data['end_date'] = ''
        response = self.client.put(url,
                                   data=self.data,
                                   HTTP_AUTHORIZATION=f'Token {self.token1}',
                                   content_type='application/json'
                                   )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid data - set event to another user
        self.data['user'] = self.user2.id
        response = self.client.put(url,
                                   data=self.data,
                                   HTTP_AUTHORIZATION=f'Token {self.token1}',
                                   content_type='application/json'
                                   )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid data - unauthorized user
        self.client.logout()
        url = reverse('crud-event', kwargs={'pk': self.event.pk})
        self.data['title'] = 'edit title'
        response = self.client.put(url,
                                   data=self.data,
                                   content_type='application/json'
                                   )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Invalid data - update event through another user
        force_authenticate(self.user2, token=self.token2.key)
        url = reverse('crud-event', kwargs={'pk': self.event.pk})
        self.data['title'] = 'edit title'
        response = self.client.put(url,
                                   data=self.data,
                                   HTTP_AUTHORIZATION=f'Token {self.token2}',
                                   content_type='application/json'
                                   )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class DeleteSingleDataTest(TestCase):
    """Tests to delete single event (with primary key in url)"""
    def setUp(self):
        self.user1 = User.objects.create_user('test name1')
        self.token1 = Token.objects.create(user=self.user1)
        self.user2 = User.objects.create_user('test name2')
        self.token2 = Token.objects.create(user=self.user2)
        self.remind = Remind.objects.create(title='За 2 часа')
        self.event = Event.objects.create(
            title='test title',
            start_date='2021-08-25',
            start_time='10:00:00',
            end_date='2021-08-26',
            end_time='11:00:00',
            memento=self.remind,
            user=self.user1,
        )

    def test_delete_single_event(self):
        force_authenticate(self.user1, token=self.token1.key)
        url = reverse('crud-event', kwargs={'pk': self.event.pk})

        # Valid data
        response = self.client.delete(url, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Invalid data - delete non-exist event
        url = reverse('crud-event', kwargs={'pk': 54})
        response = self.client.delete(url, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Invalid - Delete event unauthorized user
        self.client.logout()
        url = reverse('crud-event', kwargs={'pk': self.event.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Invalid - Delete event another user
        force_authenticate(self.user2, token=self.token2.key)
        response = self.client.delete(url, kwargs={'pk': self.event.pk}, HTTP_AUTHORIZATION=f'Token {self.token2}')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GetDataForDayTest(TestCase):
    """Tests to get all event for choosing user's day"""
    def setUp(self):
        self.user1 = User.objects.create_user('test name1')
        self.token1 = Token.objects.create(user=self.user1)
        self.user2 = User.objects.create_user('test name2')
        self.token2 = Token.objects.create(user=self.user2)
        self.remind = Remind.objects.create(title='За 2 часа')
        self.event1 = Event.objects.create(
            title='test title',
            start_date='2021-08-25',
            start_time='10:00:00',
            end_date='2021-08-26',
            end_time='11:00:00',
            memento=self.remind,
            user=self.user1,
        )
        self.event2 = Event.objects.create(
            title='test title',
            start_date='2021-08-27',
            start_time='12:09:00',
            end_date='2021-08-28',
            end_time='13:00:00',
            memento=self.remind,
            user=self.user2,
        )

    def test_data_for_day(self):
        force_authenticate(self.user1, token=self.token1.key)
        url = reverse('day-events')

        # Valid data
        data = {'start_date': '2021-08-25'}
        response = self.client.post(url, data=data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Invalid data - no date format
        data = {'start_date': 'In-Va-L1dd'}
        response = self.client.post(url, data=data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid data - non-exist date
        data = {'start_date': '2021-08-54'}
        response = self.client.post(url, data=data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid data - non-exist field
        data = {'start_': '11:00:00'}
        response = self.client.post(url, data=data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid - Get event unauthorized user
        data = {'start_date': '2021-08-25'}
        self.client.logout()
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Different data for different users
        data = {'start_date': '2021-08-25'}
        force_authenticate(self.user1, token=self.token1.key)
        response_1_user = self.client.post(url, data=data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        force_authenticate(self.user2, token=self.token2.key)
        response_2_user = self.client.post(url, data=data, HTTP_AUTHORIZATION=f'Token {self.token2}')
        self.assertNotEqual(response_1_user.data, response_2_user.data)


class GetDataForMonthTest(TestCase):
    """Tests to get all event for choosing user's month"""
    def setUp(self):
        self.user1 = User.objects.create_user('test name1')
        self.token1 = Token.objects.create(user=self.user1)
        self.user2 = User.objects.create_user('test name2')
        self.token2 = Token.objects.create(user=self.user2)
        self.remind = Remind.objects.create(title='За 2 часа')
        self.event1 = Event.objects.create(
            title='test title',
            start_date='2021-08-25',
            start_time='10:00:00',
            end_date='2021-08-26',
            end_time='11:00:00',
            memento=self.remind,
            user=self.user1,
        )
        self.event2 = Event.objects.create(
            title='test title',
            start_date='2021-08-27',
            start_time='12:09:00',
            end_date='2021-08-28',
            end_time='13:00:00',
            memento=self.remind,
            user=self.user2,
        )

    def test_data_for_month(self):
        force_authenticate(self.user1, token=self.token1.key)
        url = reverse('month-events')

        # Valid data
        data = {'month': 8}
        response = self.client.post(url, data=data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Invalid data - no date format
        data = {'month': 'asd'}
        response = self.client.post(url, data=data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid data - non-exist date
        data = {'month': 15}
        response = self.client.post(url, data=data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid data - non-exist field
        data = {'month_day': 8}
        response = self.client.post(url, data=data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid - Get event unauthorized user
        data = {'month': 8}
        self.client.logout()
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Different data for different users
        data = {'month': 8}
        force_authenticate(self.user1, token=self.token1.key)
        response_1_user = self.client.post(url, data=data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response_1_user.status_code, status.HTTP_200_OK)
        force_authenticate(self.user2, token=self.token2.key)
        response_2_user = self.client.post(url, data=data, HTTP_AUTHORIZATION=f'Token {self.token2}')
        self.assertEqual(response_2_user.status_code, status.HTTP_200_OK)
        # Compare response
        self.assertNotEqual(response_1_user.data, response_2_user.data)


class GetHolidaysTest(TestCase):
    """Tests to get holidays for user's country"""
    def setUp(self):
        self.user1 = User.objects.create_user('test name1')
        self.token1 = Token.objects.create(user=self.user1)
        self.user2 = User.objects.create_user('test name2')
        self.token2 = Token.objects.create(user=self.user2)
        self.holidays1 = CountryHolidays.objects.create(
            user=self.user1,
            country='Canada',
            holidays='2021-09-15'
        )
        self.holidays2 = CountryHolidays.objects.create(
            user=self.user2,
            country='Belarus',
            holidays='2021-09-17'
        )

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_get_holidays(self):
        force_authenticate(self.user1, token=self.token1.key)
        url = reverse('holidays')

        # Valid data
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Invalid data - POST request
        data = {'country': 'Russia', 'holidays': '2021-09-20'}
        response = self.client.post(url, data=data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Invalid data - PUT request
        response = self.client.post(url, data=data, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Invalid data - DELETE request
        response = self.client.delete(url, HTTP_AUTHORIZATION=f'Token {self.token1}')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Invalid data - unauthorized user
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Get data to another user, different data
        force_authenticate(self.user1, token=self.token1.key)
        response_user_1 = self.client.get(
            url,
            HTTP_AUTHORIZATION=f'Token {self.token1}'
        )
        self.assertEqual(response_user_1.status_code, status.HTTP_200_OK)
        force_authenticate(self.user2, token=self.token2.key)
        response_user_2 = self.client.get(
            url,
            HTTP_AUTHORIZATION=f'Token {self.token2}'
        )
        self.assertEqual(response_user_2.status_code, status.HTTP_200_OK)
        # Compare responses
        self.assertNotEqual(response_user_1.data, response_user_2.data)


class RegistrationTest(TestCase):
    """Tests to register new user"""
    def setUp(self):
        self.data = {
            'username': 'test name',
            'email': 'testname@test.name',
            'password': 'testusertestuser',
            'model_country': {'country': 'Canada'}
        }

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_create_user(self):
        url = reverse('account-create')

        # Valid data
        response = self.client.post(url, data=self.data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, msg=response.data)

        # Valid - check creating token and country
        token = Token.objects.get(user=response.data['id'])
        country = CountryHolidays.objects.get(user=response.data['id'])
        self.assertTrue(token)
        self.assertTrue(country)

        # Invalid - Create exist user in db
        response = self.client.post(url, data=self.data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid - create exist email
        self.invalid_data = copy.deepcopy(self.data)
        self.invalid_data['username'] = 'test name 2'
        response = self.client.post(url, data=self.invalid_data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_data(self):
        url = reverse('account-create')

        # Invalid - empty user
        self.invalid_data = copy.deepcopy(self.data)
        self.invalid_data['username'] = ''
        response = self.client.post(url, data=self.invalid_data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid - empty email
        self.invalid_data = copy.deepcopy(self.data)
        self.invalid_data['email'] = ''
        response = self.client.post(url, data=self.invalid_data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid - empty password
        self.invalid_data = copy.deepcopy(self.data)
        self.invalid_data['password'] = ''
        response = self.client.post(url, data=self.invalid_data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid - empty country
        self.invalid_data = copy.deepcopy(self.data)
        self.invalid_data['model_country'] = ''
        response = self.client.post(url, data=self.invalid_data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid - empty user
        self.invalid_data = copy.deepcopy(self.data)
        self.invalid_data['username'] = ''
        response = self.client.post(url, data=self.invalid_data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
