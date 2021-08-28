import datetime
from django.contrib.auth.models import User
from django.db import models


class Remind(models.Model):
    """Model with time to remember.

        Automatically load data from fixtures:
        'За час', 'За 2 часа', 'За 4 часа', 'За день' , 'За 3 дня' ,'За неделю'.
        Each time when server is up from docker-compose, this model will be overwrite"""
    title = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class Event(models.Model):
    """Model of user's event"""
    title = models.CharField(max_length=250, db_index=True)
    start_date = models.DateField()
    start_time = models.TimeField()
    end_date = models.DateField(blank=True)
    end_time = models.TimeField(blank=True, default=datetime.time(23, 59, 59))
    memento = models.ForeignKey(Remind, on_delete=models.CASCADE, related_name='event')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dates')

    # Override method for save end date if is None
    def save(self, *args, **kwargs):
        if self.end_date is None:
            self.end_date = self.start_date
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class CountryHolidays(models.Model):
    """Model to save user's country holidays"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='holidays')
    country = models.CharField(max_length=100)
    holidays = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.country.capitalize()

    # Override method to do country in lowercase
    def save(self, *args, **kwargs):
        self.country = self.country.lower()
        return super(CountryHolidays, self).save(*args, **kwargs)
