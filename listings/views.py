from datetime import date
from functools import reduce

from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView

from . import models, serializers


def one_room_per_hotel_reducer(acc, value):
    if value.hotel_room_type.hotel not in map(lambda r: r.hotel_room_type.hotel, acc):
        acc.append(value)
    return acc


class AvailableBookingView(APIView):
    def get(self, request):
        check_in = request.query_params.get("check_in")
        check_out = request.query_params.get("check_out")
        max_price = request.query_params.get("max_price")
        serializer = serializers.AvailableBookingSerializer(data=dict(request.query_params.items()))
        serializer.is_valid(raise_exception=True)

        # Queries
        apartments_q = Q(booking_info__listing__listing_type=models.Listing.APARTMENT)
        blocked_q = Q(end_date__gte=check_in, start_date__lte=check_out)

        # Apartments / Hotel Rooms under user's budget
        affordable_apartments = models.Listing.objects.filter(listing_type=models.Listing.APARTMENT).exclude(booking_info__price__gt=max_price)
        affordable_hotel_room_types = models.HotelRoomType.objects.filter(booking_info__price__lte=max_price).values_list("id", flat=True)
        affordable_hotel_rooms = models.HotelRoom.objects.filter(hotel_room_type__in=affordable_hotel_room_types)

        # Already booked apartments / hotel rooms
        blocked_apartments = models.BlockedDays.objects.filter(apartments_q & blocked_q).values_list("booking_info__listing")
        blocked_hotel_rooms = models.BlockedDays.objects.exclude(apartments_q).filter(blocked_q).values_list("hotel_room")

        # Available Apartments / Hotel Rooms
        available_apartments = affordable_apartments.exclude(id__in=blocked_apartments)
        available_hotel_rooms = affordable_hotel_rooms.exclude(id__in=blocked_hotel_rooms).order_by("hotel_room_type__booking_info__price")

        one_room_per_hotel = reduce(one_room_per_hotel_reducer, available_hotel_rooms, [])

        result = [
            {
                "listing_type": apartment.listing_type,
                "title": apartment.title,
                "country": apartment.country,
                "city": apartment.city,
                "price": apartment.booking_info.price
            }
            for apartment in available_apartments
        ]
        result += [
            {
                "listing_type": room.hotel_room_type.hotel.listing_type,
                "title": room.hotel_room_type.hotel.title,
                "country": room.hotel_room_type.hotel.country,
                "city": room.hotel_room_type.hotel.city,
                "price": room.hotel_room_type.booking_info.price
            }
            for room in one_room_per_hotel
        ]
        return Response({"items": result}, status=200)
