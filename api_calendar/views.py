from datetime import datetime
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView, CreateAPIView, GenericAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from dj_rest_auth.views import LoginView
from api_calendar.models import Event, CountryHolidays
from api_calendar.serializers import AllDateSerializer, CreateDataSerializer, OuterDataFromCreateData, \
    EventSerializer, GetDataDaySerializer, UserSerializer, EventGroupSerializer, HolidaysSerializer

# Tasks
from api_calendar.tasks import send_reg_mail as send_reg_mail_task
from api_calendar.tasks import send_remind as send_remind_task
from api_calendar.tasks import get_country_holidays as get_country_holidays_task

# Utils
from api_calendar.utils import convert_date


class APIData(ListAPIView):
    """Get all api for current user"""
    serializer_class = AllDateSerializer

    def get_queryset(self):
        """Method determine current user"""
        return Event.objects.all().filter(user_id=self.request.user)


class AddData(CreateAPIView):
    """Add event to api planner for current user"""
    serializer_class = CreateDataSerializer

    # Override method to add event only for current user
    def perform_create(self, serializer):
        serializer.validated_data['user'] = self.request.user
        return super(AddData, self).perform_create(serializer)

    # Send info for new event
    def post(self, request):
        context = {'request': self.request}
        serializer = self.serializer_class(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        data = serializer.save()

        # Prepare time from data to calculate time to send email remind
        remind_time = convert_date(serializer.data['memento'])
        start_event = f'{serializer.data["start_date"]} {serializer.data["start_time"]}'
        remind_event = datetime.strptime(start_event, "%Y-%m-%d %H:%M:%S") - remind_time

        # Task to send email remind
        try:
            send_remind_task.apply_async(
                kwargs={'user': serializer.validated_data['user'].username,
                        'email': serializer.data['user_email'],
                        'event': serializer.data['title'],
                        'start date': serializer.data['start_date'],
                        'start time': serializer.data['start_time']
                        },
                eta=remind_event
            )
        except TimeoutError:
            print("Email is not send")

        # Return info to show what was created
        outer_serializer = OuterDataFromCreateData(data)
        return Response(outer_serializer.data, status=status.HTTP_201_CREATED)


class DataUpdateAPI(RetrieveUpdateDestroyAPIView):
    """Get, update, delete existing event

        Event gets from primary key which send in url"""
    serializer_class = EventSerializer

    def get_queryset(self):
        return Event.objects.all().filter(user_id=self.request.user)


class GetDataForDay(GenericAPIView):
    """Choose and get all events for day"""
    serializer_class = GetDataDaySerializer

    def get_queryset(self):
        return Event.objects.all().filter(user_id=self.request.user)

    # User choose a day to show all data for this day
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Filter to show all events for user's choosing day
        data = Event.objects.all().filter(start_date=request.data['start_date']).filter(user_id=self.request.user)
        outer_serializer = AllDateSerializer(data, many=True)
        return Response(outer_serializer.data, status=status.HTTP_200_OK)


class UserCreate(APIView):
    """Create a new user"""
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

    def post(self, request):  # Form for registration of new user
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            if user:  # Create token for new user
                token = Token.objects.create(user=user)
                json = serializer.data
                json['token'] = token.key

                # Send email with login and pass
                try:
                    send_reg_mail_task.delay(
                        request.data['username'],
                        request.data['email'],
                        request.data['password'],
                        json['token']
                    )
                except TimeoutError:
                    print("Email is not send")

                try:
                    #  Update field Country holiday
                    get_country_holidays_task.delay(user.id)
                except TimeoutError:
                    print("Doesn't get holidays")
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyLoginView(LoginView):
    """This class from dj-rest-auth library"""

    def login(self):
        """Override method from dj-rest-auth library to login with username or email"""
        self.user = self.serializer.validated_data['user'] or self.serializer.validated_data['email']


class EventGroupData(GenericAPIView):
    """Choose and get all events for month"""

    def get_queryset(self):
        return Event.objects.all().filter(user_id=self.request.user)

    serializer_class = EventGroupSerializer

    # User send a number of month to show all data for this month
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Filter to show all events for user's choosing month
        data = Event.objects.all().filter(user_id=self.request.user).filter(start_date__month=request.data['month'])
        outer_serializer = AllDateSerializer(data, many=True)
        return Response(outer_serializer.data, status=status.HTTP_200_OK)


class GetHolidays(ListAPIView):
    """Get all holidays of user's country"""
    serializer_class = HolidaysSerializer

    def get_queryset(self):
        return CountryHolidays.objects.all().filter(user_id=self.request.user)
