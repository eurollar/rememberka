from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from api_calendar.models import Event, CountryHolidays
from api_calendar.utils import check_dates


class AllDateSerializer(serializers.ModelSerializer):
    """Serializer show all events for current user"""

    # Show name fields not ID
    memento = serializers.CharField(source='memento.title')
    user = serializers.CharField(source='user.username')

    class Meta:
        model = Event
        fields = ['id', 'title', 'start_date', 'start_time', 'end_date', 'end_time', 'memento', 'user']


class EventSerializer(serializers.ModelSerializer):
    """Serializer show specific event for current user

        Specific event get from primary key which send in url"""
    user = serializers.CharField(read_only=True,
                                 default=serializers.CurrentUserDefault(),
                                 )

    class Meta:
        model = Event
        fields = ['id', 'title', 'start_date', 'start_time', 'end_date', 'end_time', 'memento', 'user']

    # Check correct dates
    def validate(self, instance):
        data = check_dates(instance)
        if data == 'End date error':
            raise serializers.ValidationError('End date must be more than start date')
        elif data == 'End time error':
            raise serializers.ValidationError('End time in one day must be more than start time')
        return data


class CreateDataSerializer(serializers.ModelSerializer):
    """Serializer for create user's event with protection from another users"""

    # Hide current user to protect another users send own events
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
        write_only=False
    )

    user_email = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = ['id', 'title', 'start_date', 'start_time', 'end_date', 'end_time', 'memento', 'user', 'user_email']

    # Get user's email to send remind
    def get_user_email(self, instance):
        email = self.context['request'].user.email
        return email

    # Check correct dates
    def validate(self, instance):
        data = check_dates(instance)
        if data == 'End date error':
            raise serializers.ValidationError('End date must be more than start date')
        elif data == 'End time error':
            raise serializers.ValidationError('End time in one day must be more than start time')
        return data


class OuterDataFromCreateData(serializers.ModelSerializer):
    """Output data to show what is was created"""

    class Meta:
        model = Event
        fields = ['id', 'title']


class GetDataDaySerializer(serializers.ModelSerializer):
    """Serializer to get day from user"""

    class Meta:
        model = Event
        fields = ['id', 'start_date']


class CountrySerializer(serializers.ModelSerializer):
    """Serializer for ↓ CountrySerializer ↓

        This need to add field 'Country' while user register on site"""

    class Meta:
        model = CountryHolidays
        exclude = ['user', 'holidays']


class UserSerializer(serializers.ModelSerializer):
    """Serializer to send user's data for create new user"""

    # Additional field 'Country'. It need to create new record in CountryHolidays model
    model_country = CountrySerializer(write_only=True)

    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        max_length=32,
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        min_length=8,
        write_only=True,
        style={'input_type': 'password'}  # Hide password in field
    )

    def create(self, validated_data):
        # Take data from fields to create new record in CountryHolidays model
        model_country_data = validated_data.pop('model_country')

        # Create new user
        user = User.objects.create_user(validated_data['username'],
                                        validated_data['email'],
                                        validated_data['password'])

        # Create new record in CountryHolidays model
        CountryHolidays.objects.create(
            user=user,
            country=model_country_data['country']
        )
        return user

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'model_country']


class EventGroupSerializer(serializers.ModelSerializer):
    """Serializer to get number of month from user"""
    month = serializers.IntegerField()

    class Meta:
        model = Event
        fields = ['id', 'month']

    def validate(self, instance):
        if 0 < instance['month'] < 13:
            return instance
        raise serializers.ValidationError('Month must be more than 12')


class HolidaysSerializer(serializers.ModelSerializer):
    """Serializer show user's country holidays for current user"""
    user = serializers.CharField(source='user.username')

    class Meta:
        model = CountryHolidays
        fields = ['id', 'user', 'country', 'holidays']
