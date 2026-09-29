from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Algemeen"

    def ready(self):
        from . import privacyverklaring  # noqa: F401  (registreert de controle vóór livegang)
