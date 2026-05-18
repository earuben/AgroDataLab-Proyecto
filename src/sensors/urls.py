from django.urls import path

from . import views


urlpatterns = [
    path("importacion/", views.import_status, name="sensor_import"),
]
