from celery import shared_task
from django.core.mail import send_mail
from api_calendar.models import CountryHolidays
from api_calendar.utils import parse_country_holidays


# Task to send email with login and password
@shared_task
def send_reg_mail(username, email, password):
    send_mail(
        'You register on site',
        f'You register on site. You can log with email or login\n'
        f'Your login: {username} \n'
        f'Your email: {email} \n'
        f'Your pass: {password}',
        'fakekrolchatka@gmail.com',
        [email],
        fail_silently=False
    )
    return f'Mail is send to {email}'


# Send email to remind about future event
@shared_task
def send_remind(**kwargs):
    send_mail(
        'Reminder',
        f'Dear {kwargs["user"]}! You have planned an event {kwargs["event"]}\n'
        f'This event begins: {kwargs["start date"]} {kwargs["start time"]} \n'
        f'Sincerely with love!',
        'fakekrolchatka@gmail.com',
        [kwargs['email']],
        fail_silently=False
    )
    return f'Send remind on email {kwargs["email"]}'


# Get holidays of new user's country when he to register on site
@shared_task
def get_country_holidays(user):
    data = CountryHolidays.objects.get(user_id=user)
    holidays = parse_country_holidays(data.country)
    data.holidays = holidays
    data.save()
    return 'Holidays is saved'


# Periodic task. Update holidays in user's country (one time in 6 month)
@shared_task
def update_country_holidays():
    all_data = CountryHolidays.objects.all()
    for data in all_data:
        holidays = parse_country_holidays(data.country)
        data.holidays = holidays
        data.save()
    return 'Holidays is updated'
