from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from currencies.models import Currency
from currencies.serializers import CurrencySerializer


class CurrencyViewSet(viewsets.ReadOnlyModelViewSet):
    """ISO 4217 currencies: public reference data, read-only."""

    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [AllowAny]  # Public on purpose: overrides the IsAuthenticated default.
    lookup_field = "code"