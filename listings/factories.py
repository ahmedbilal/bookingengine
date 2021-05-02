import random
from decimal import Decimal

import factory
from faker import Faker

from . import models

fake = Faker()

PRICE_CHOICES = list(map(Decimal, [50, 70, 90, 100, 150, 300]))

def fake_hotel_name():
    return f"{fake.name()} {random.randint(1, 6)}* hotel"

def fake_apartment_name():
    return f'{random.choice(["Luxurious", "Modern 2 Bed", "Traditional 3 Bed"])} Apartment'


class BookingInfoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.BookingInfo


class HotelRoomFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.HotelRoom

    room_number = factory.Iterator([101, 102, 201, 202, 301, 302])


class HotelRoomTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.HotelRoomType

    title = factory.LazyFunction(lambda: random.choice(["Single", "Double", "Triple"]) + " Room")
    hotel_rooms = factory.RelatedFactoryList(
        HotelRoomFactory,
        "hotel_room_type",
        size=lambda: random.randint(1, 3)
    )
    booking_info = factory.RelatedFactory(
        BookingInfoFactory,
        "hotel_room_type",
        price=factory.LazyFunction(lambda: random.choice(PRICE_CHOICES))
    )


class ListingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Listing

    title = factory.LazyFunction(fake_hotel_name)
    listing_type = models.Listing.HOTEL
    country = factory.Faker("country")
    city = factory.Faker("city")


    class Params:
        apartment = factory.Trait(
            listing_type = models.Listing.APARTMENT,
            booking_info = factory.RelatedFactory(
                BookingInfoFactory, "listing",
                price=factory.LazyFunction(lambda: random.choice(PRICE_CHOICES))
            ),
            hotel_room_types = None,
            title = factory.LazyFunction(fake_apartment_name)
        )

    hotel_room_types = factory.RelatedFactoryList(
        HotelRoomTypeFactory, "hotel", size=lambda: random.randint(1, 3)
    )


class BlockedDaysFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.BlockedDays
