from django.urls import path

from . import views

app_name = "studio"

urlpatterns = [
    path("", views.start, name="start"),
    path("<uuid:uid>/", views.resume, name="resume"),
    path("<uuid:uid>/voorbeeld/weergave/", views.preview_frame, name="preview_frame"),
    path("<uuid:uid>/voorbeeld/live/", views.live_frame, name="live_frame"),
    path("<uuid:uid>/voorbeeld/live/<str:step>/", views.live_update, name="live_update"),
    path("<uuid:uid>/media/<uuid:asset_uid>/<str:variant>/", views.media, name="media"),
    path("<uuid:uid>/upload/", views.upload, name="upload"),
    path("<uuid:uid>/upload/<uuid:asset_uid>/verwijderen/", views.delete_asset, name="delete_asset"),
    path("<uuid:uid>/tekstvoorstel/", views.ai_text, name="ai_text"),
    path("<uuid:uid>/publiceren/", views.publish, name="publish"),
    path("<uuid:uid>/<str:step>/", views.step, name="step"),
]
