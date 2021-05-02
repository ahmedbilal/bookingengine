import random
import time

import factory
from django.test import TestCase
from faker import Faker
from rest_framework.test import APIClient, APIRequestFactory

from . import factories, models, serializers


def get_available(max_price, check_in, check_out):
    client = APIClient()
    response = client.get(
        '/api/v1/units/',
        data={
            'max_price': max_price,
            'check_in': check_in,
            'check_out': check_out,
        }
    )
    return response.json()


def block(booking_info, start_date, end_date, **kwargs):
    factories.BlockedDaysFactory.create(booking_info=booking_info, start_date=start_date, end_date=end_date, **kwargs)


class TestListingAPI(TestCase):
    def test_max_price(self):
        hotels = [
            factories.ListingFactory.create(),
            factories.ListingFactory.create(hotel_room_types__booking_info__price=800),
        ]
        apartments = [
            factories.ListingFactory.create(apartment=True)
        ]

        max_price = 500
        response = get_available(max_price, "2021-05-01", "2021-05-01")
        max_price_of_returned_listings = max(map(lambda r: r['price'], response['items']))

        assert max_price_of_returned_listings <= max_price, \
            "All listings returned should be less than the max_price user mentioned"

    def test_apartment_blocking(self):
        hotels = [
            factories.ListingFactory.create(),
            factories.ListingFactory.create(),
        ]
        apartments = [
            factories.ListingFactory.create(apartment=True)
        ]

        # Block Apartment
        block(apartments[0].booking_info, "2021-05-01", "2021-05-01")

        response = get_available(300, "2021-05-01", "2021-05-01")
        assert "appartment" not in map(lambda r: r['listing_type'], response['items']), \
            "There shouldn't be any appartment because we have blocked it for this period"

    def test_blocking_cheapest_hotel_room_type(self):
        hotels = [
            factories.ListingFactory.create(),
            factories.ListingFactory.create(),
        ]
        apartments = [
            factories.ListingFactory.create(apartment=True)
        ]
        # Block Cheapest Room Type(s) at hotel[0]
        cheapest_room_type_in_hotel0 = min(hotels[0].hotel_room_types.all(), key=lambda hrt: hrt.booking_info.price)
        cheapest_room_types_in_hotel0 = hotels[0].hotel_room_types.filter(booking_info__price=cheapest_room_type_in_hotel0.booking_info.price)

        for cheapest_room_type in cheapest_room_types_in_hotel0.all():
            for room in cheapest_room_type.hotel_rooms.all():
                block(cheapest_room_type.booking_info, start_date="2021-05-01", end_date="2021-05-01", hotel_room=room)

        response = get_available(300, "2021-05-01", "2021-05-01")
        serializer = serializers.ListingSerializer(instance=hotels[0])
        cheapest_listing = dict(serializer.data)
        cheapest_listing['price'] = float(cheapest_room_type_in_hotel0.booking_info.price)

        assert cheapest_listing not in response['items'], \
            "Cheapest Room Type shouldn't be available as we blocked it"

        response = get_available(300, "2021-05-02", "2021-05-03")
        assert cheapest_listing in response['items'], \
            "Cheapest Room Type should be available as we didn't blocked it for the mentioned period"

    def test_blocking(self):
        max_price = 100

        hotel = factories.ListingFactory.create(hotel_room_types=None)
        hotel_room_types = [
            factories.HotelRoomTypeFactory.create(
                booking_info__price=50, hotel=hotel, hotel_rooms=None
            ),
            factories.HotelRoomTypeFactory.create(
                booking_info__price=60, hotel=hotel, hotel_rooms=None,
            ),
            factories.HotelRoomTypeFactory.create(
                booking_info__price=max_price + 100, hotel=hotel
            ),
        ]
        hotel_room_types[0].hotel_rooms.add(
            factories.HotelRoomFactory.create()
        )
        hotel_room_types[1].hotel_rooms.add(
            factories.HotelRoomFactory.create(), factories.HotelRoomFactory.create(),
            factories.HotelRoomFactory.create(),
        )

        # Block all rooms for first room type
        block(
            hotel_room_types[0].booking_info, "2021-05-02", "2021-05-02",
            hotel_room=hotel_room_types[0].hotel_rooms.first()
        )

        # Block one room for second room type
        block(
            hotel_room_types[1].booking_info, "2021-05-02", "2021-05-02",
            hotel_room=hotel_room_types[1].hotel_rooms.first()
        )

        response = get_available(max_price, "2021-05-02", "2021-05-02")
        assert response['items'][0]['price'] == 60.0, (
            "The price should be 60, as we have blocked all rooms for first room type"
            " and one of the room for second room type. The third room type is out of"
            " budget for user"
        )

