"""URL-structuur van Vaylide."""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

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
    path("beheer/", include("beheer.urls")),
    path(settings.ADMIN_URL, admin.site.urls),
]

handler404 = "core.views.not_found"
handler500 = "core.views.server_error"
