from django.contrib import admin
from api_calendar.models import Remind, Event, CountryHolidays


# Add columns in admin
class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'start_date', 'user')


class CountryHolidaysAdmin(admin.ModelAdmin):
    list_display = ('user', 'country')


admin.site.register(Remind)
admin.site.register(Event, EventAdmin)
admin.site.register(CountryHolidays, CountryHolidaysAdmin)
