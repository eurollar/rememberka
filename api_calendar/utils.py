from datetime import timedelta, time
from api_calendar.models import Remind
from ics import Calendar
import requests


# Check dates
def check_dates(instance):
    start_date = instance['start_date']
    end_date = instance['end_date'] if 'end_date' in instance else instance['start_date']
    start_time = instance['start_time']
    end_time = instance['end_time'] if 'end_time' in instance else time(23, 59, 59)

    # Check end date more than start date
    if end_date < start_date:
        return 'End date error'
    # Check end time more than start time in same day
    if (start_date == end_date) and (start_time > end_time):
        return 'End time error'
    return instance


# Convert id and title from models to time. This need to set date for remind with Celery
def convert_date(remind_id):
    raw_date = Remind.objects.get(id=remind_id)
    if raw_date.title == 'За час':
        convertable_date = timedelta(hours=1)
    elif raw_date.title == 'За 2 часа':
        convertable_date = timedelta(hours=12)
    elif raw_date.title == 'За 4 часа':
        convertable_date = timedelta(hours=4)
    elif raw_date.title == 'За день':
        convertable_date = timedelta(days=1)
    elif raw_date.title == 'За 3 дня':
        convertable_date = timedelta(days=3)
    elif raw_date.title == 'За неделю':
        convertable_date = timedelta(days=7)
    else:
        raise ValueError

    return convertable_date


# Parse to get country holidays
def parse_country_holidays(country):
    url = 'https://www.officeholidays.com/ics/ics_country.php?tbl_country='
    holidays = Calendar(requests.get(f"{url}{country}").text)
    return holidays.events
