from django.core.exceptions import ValidationError
from django.db import models


class Listing(models.Model):
    HOTEL = 'hotel'
    APARTMENT = 'apartment'
    LISTING_TYPE_CHOICES = (
        ('hotel', 'Hotel'),
        ('apartment', 'Apartment'),
    )

    listing_type = models.CharField(
        max_length=16,
        choices=LISTING_TYPE_CHOICES,
        default=APARTMENT
    )
    title = models.CharField(max_length=255,)
    country = models.CharField(max_length=255,)
    city = models.CharField(max_length=255,)

    def __str__(self):
        return self.title


class HotelRoomType(models.Model):
    hotel = models.ForeignKey(
        Listing,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='hotel_room_types'
    )
    title = models.CharField(max_length=255,)

    def __str__(self):
        return f'{self.hotel} - {self.title}'


class HotelRoom(models.Model):
    hotel_room_type = models.ForeignKey(
        HotelRoomType,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='hotel_rooms'
    )
    room_number = models.CharField(max_length=255,)

    def __str__(self):
        return f"{self.room_number} - {self.hotel_room_type}"


class BookingInfo(models.Model):
    listing = models.OneToOneField(
        Listing,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='booking_info'
    )
    hotel_room_type = models.OneToOneField(
        HotelRoomType,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='booking_info',
    )
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        if self.listing:
            obj = self.listing
        else:
            obj = self.hotel_room_type

        return f'{obj} {self.price}'


class BlockedDays(models.Model):
    booking_info = models.ForeignKey(BookingInfo, on_delete=models.CASCADE, related_name="blocked_days")
    hotel_room = models.ForeignKey(
        HotelRoom, on_delete=models.CASCADE, null=True, blank=True, related_name="blocked_days"
    )
    start_date = models.DateField(blank=False)
    end_date = models.DateField(blank=False)

    class Meta:
        verbose_name_plural = "Blocked days"

    def clean(self):
        if (
            self.booking_info.listing is not None and
            self.booking_info.listing.listing_type == Listing.APARTMENT and
            self.hotel_room is not None
        ):
            raise ValidationError({
                "hotel_room": "Hotel room shouldn't be selected if the selected booking is of apartment"
            })

        if self.end_date is None:
            raise ValidationError({"end_date": "End Date is a required field"})

        if self.booking_info.hotel_room_type:
            rooms_in_selected_hotel = self.booking_info.hotel_room_type.hotel_rooms.all()
            if self.hotel_room not in rooms_in_selected_hotel:
                raise ValidationError({"hotel_room": "Invalid Hotel room for selected booking info"})

        if BlockedDays.objects.\
            filter(
                booking_info=self.booking_info,
                hotel_room=self.hotel_room,
                end_date__gte=self.start_date,
                start_date__lte=self.end_date
            ).exclude(id=self.id).exists():
            raise ValidationError("This booking/hotel room is blocked for this period")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.hotel_room:
            return f"{self.hotel_room} | {self.start_date} - {self.end_date}"
        else:
            return f"{self.booking_info} | {self.start_date} - {self.end_date}"
