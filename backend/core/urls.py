from django.urls import path

from core.views import health

app_name = "core"

urlpatterns = [
    path("health/", health, name="health"),
]
