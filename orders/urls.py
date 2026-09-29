from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("bestelling/<uuid:uid>/", views.status, name="status"),
    path("bestelling/<uuid:uid>/status.json", views.status_json, name="status_json"),
    path("bestelling/<uuid:uid>/opnieuw-betalen/", views.retry_payment, name="retry"),
    path("betalen/test/<str:ref>/", views.test_checkout, name="test_checkout"),
    path("webhooks/betaling/<str:provider>/", views.webhook, name="webhook"),
    path("herroepen/", views.withdraw, name="withdraw"),
    path("herroepen/ontvangen/<uuid:uid>/", views.withdraw_done, name="withdraw_done"),
]
