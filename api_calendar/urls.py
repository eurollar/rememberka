from django.urls import path
from api_calendar import views


urlpatterns = [
    # Get all info about user's events - GET
    path('all-api-data/', views.APIData.as_view(), name='home'),

    # Add new event - POST
    path('add-api-data/', views.AddData.as_view(), name='add-event'),

    # Get, update or delete specific user's event - CRUD
    path('update-api-date/<int:pk>/', views.DataUpdateAPI.as_view(), name='crud-event'),

    # Get all events for one day. User choose day and get info - POST
    path('get-for-day/', views.GetDataForDay.as_view(), name='day-events'),

    # Register new user - POST
    path('register/', views.UserCreate.as_view(), name='account-create'),

    # Get all events for month. User choose month and get info - POST
    path('get-for-month/', views.EventGroupData.as_view(), name='month-events'),

    # Get all user's country holidays - GET
    path('get-holidays/', views.GetHolidays.as_view(), name='holidays'),
]
