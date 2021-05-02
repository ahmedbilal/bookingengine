from django.urls import path

from . import views

urlpatterns = [
    path("units/", views.AvailableBookingView.as_view(), name="available_booking_view")
]
