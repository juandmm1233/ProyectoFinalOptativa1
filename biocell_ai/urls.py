"""URLs principales del proyecto BioCell AI."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("diagnostico.urls", namespace="diagnostico")),
]
