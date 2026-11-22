from rest_framework.routers import SimpleRouter

from currencies.views import CurrencyViewSet

app_name = "currencies"

router = SimpleRouter()
router.register("currencies", CurrencyViewSet, basename="currency")

urlpatterns = router.urls
