from django.urls import path

from . import views

app_name = "moments"

urlpatterns = [
    path("demo/", views.demo_guest, name="demo_guest"),
]
