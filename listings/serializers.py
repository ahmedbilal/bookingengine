from rest_framework import serializers

from . import models


class AvailableBookingSerializer(serializers.Serializer):
    max_price = serializers.FloatField(required=True)
    check_in = serializers.DateField(required=True)
    check_out = serializers.DateField(required=True)


class ListingSerializer(serializers.ModelSerializer):
    price = serializers.ReadOnlyField()
    class Meta:
        model = models.Listing
        exclude = ["id"]
