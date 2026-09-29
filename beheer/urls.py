from django.urls import path

from . import views

app_name = "beheer"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("inloggen/", views.StaffLoginView.as_view(), name="login"),
    path("bestellingen/", views.orders, name="orders"),
    path("bestellingen/<uuid:uid>/", views.order_detail, name="order"),
    path("uitnodigingen/", views.invitations, name="invitations"),
    path("uitnodigingen/<uuid:uid>/", views.invitation_detail, name="invitation"),
    path("uitnodigingen/<uuid:uid>/gasten.csv", views.invitation_guests_export, name="invitation_guests_export"),
    path("klanten/", views.customers, name="customers"),
    path("klanten/nieuwsbrief.csv", views.newsletter_export, name="newsletter_export"),
    path("klanten/<int:pk>/", views.customer_detail, name="customer"),
    path("wensen/", views.wishes, name="wishes"),
    path("wensen/<uuid:uid>/", views.wish_detail, name="wish"),
    path("wensen/<uuid:uid>/bijlage/<uuid:attachment_uid>/", views.wish_attachment, name="wish_attachment"),
    path("ontwerpen/", views.templates, name="templates"),
    path("ontwerpen/<int:pk>/", views.template_edit, name="template_edit"),
    path("prijzen/", views.pricing, name="pricing"),
    path("prijzen/pakket/nieuw/", views.package_edit, name="package_new"),
    path("prijzen/pakket/<int:pk>/", views.package_edit, name="package_edit"),
    path("prijzen/optie/nieuw/", views.addon_edit, name="addon_new"),
    path("prijzen/optie/<int:pk>/", views.addon_edit, name="addon_edit"),
    path("verwerking/", views.processing, name="processing"),
    path("verwerking/email/<int:pk>/", views.email_detail, name="email"),
    path("contact/", views.contact_messages, name="contact_messages"),
    path("instellingen/", views.site_settings, name="settings"),
]
