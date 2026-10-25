"""URL-structuur van Vaylide."""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from core.admin_login import admin_login

admin.site.site_header = "VAYLIDE systeembeheer"
admin.site.site_title = "VAYLIDE"
admin.site.index_title = "Noodtoegang tot de database (gebruik bij voorkeur /beheer/)"

urlpatterns = [
    path("", include("core.urls")),
    path("", include("invitations.urls")),
    path("", include("accounts.urls")),
    path("", include("orders.urls")),
    path("maken/", include("gezichten.urls")),  # vóór de editor: /maken/<id>/gezichten/
    path("maken/", include("studio.urls")),
    path("account/", include("portal.urls")),
    path("moments/", include("moments.urls")),  # alleen de demonstratiepagina, achter de vlag (moments/flags.py)
    path("beheer/", include("beheer.urls")),
    path(f"{settings.ADMIN_URL}login/", admin_login),  # vóór admin.site.urls: dezelfde adres, mét begrenzing
    path(settings.ADMIN_URL, admin.site.urls),
]

handler404 = "core.views.not_found"
handler500 = "core.views.server_error"
