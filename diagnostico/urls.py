"""URLs de la app `diagnostico`."""

from django.urls import path

from . import views

app_name = "diagnostico"

urlpatterns = [
    path("", views.index, name="index"),
    path("predecir/", views.predecir, name="predecir"),
]
