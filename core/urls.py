from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("ontwerpen/", views.designs, name="designs"),
    path("ontwerpen/<slug:slug>/", views.design_detail, name="design_detail"),
    path("digitale-trouwkaarten/", views.wedding_cards, name="wedding_cards"),
    path("digitale-kerstkaarten/", views.christmas_cards, name="christmas_cards"),
    path("digitale-verjaardagsuitnodigingen/", views.birthday_invitations, name="birthday_invitations"),
    path("digitale-zakelijke-uitnodigingen/", views.business_invitations, name="business_invitations"),
    path("digitale-uitnodiging-maken/", views.make_invitation, name="make_invitation"),
    path("zo-werkt-het/", views.how, name="how"),
    path("prijzen/", views.pricing, name="pricing"),
    path("veelgestelde-vragen/", views.faq, name="faq"),
    path("inspiratie/", views.inspiration, name="inspiration"),
    path("over-ons/", views.about, name="about"),
    path("zoeken/", views.search, name="search"),
    path("contact/", views.contact, name="contact"),
    path("privacy/", views.privacy, name="privacy"),
    path("voorwaarden/", views.terms, name="terms"),
    path("voorwaarden/versie/<str:version>/", views.terms_version, name="terms_version"),
    path("voorwaarden/download/<str:version>/", views.terms_download, name="terms_download"),
    path("voorwaarden/pdf/<str:version>/", views.terms_pdf, name="terms_pdf"),
    path("robots.txt", views.robots_txt, name="robots"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap"),
    path("healthz", views.healthz, name="healthz"),
    path("intern/taken/", views.cron_jobs, name="cron_jobs"),
    # Alleen lokaal (DEBUG): ontwerpstudio voor de VAYLIDE Envelope Collection.
    path("lab/enveloppen/", views.envelop_lab, name="envelop_lab"),
]
