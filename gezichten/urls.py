from django.urls import path

from . import views

app_name = "gezichten"

urlpatterns = [
    path("<uuid:uid>/gezichten/", views.page, name="page"),
    path("<uuid:uid>/gezichten/status.json", views.status, name="status"),
    path("<uuid:uid>/gezichten/beeld/<str:soort>/", views.image, name="image"),
]
