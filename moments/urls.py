from django.urls import path

from . import api, views

app_name = "moments"

urlpatterns = [
    path("demo/", views.demo_guest, name="demo_guest"),
    # Stap 3A: JSON voor gasten. Alle adressen bestaan alleen met de vlag aan.
    path("api/start/<str:code>/", api.start_session, name="start"),
    path("api/uploads/", api.uploads, name="uploads"),
    path("api/uploads/<uuid:uid>/", api.upload_status, name="upload_status"),
    path("api/uploads/<uuid:uid>/klaar/", api.upload_complete, name="upload_complete"),
    path("api/uploads/<uuid:uid>/bestand/", api.upload_file, name="upload_file"),
    path("api/test-opslag/<str:signed>/", api.test_storage_upload, name="test_opslag"),
]
