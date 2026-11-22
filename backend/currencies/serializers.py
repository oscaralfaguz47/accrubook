from rest_framework import serializers

from currencies.models import Currency


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        # Models explicit to ensure only these fields are exposed to the client not all as ModelSerializer does
        fields = ["code", "name", "decimal_places", "is_active"]
        read_only_fields = fields