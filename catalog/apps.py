from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "catalog"
    verbose_name = "Catalogus"

    def ready(self):
        from django.db.models.signals import post_migrate

        from .seed import ensure_catalog_on_migrate

        post_migrate.connect(ensure_catalog_on_migrate, sender=self)
        post_migrate.connect(_ensure_roles, dispatch_uid="vaylide-ensure-roles")


def _ensure_roles(sender, **kwargs):
    # Draait na elke migrate van elke app; de rechten van de app 'catalog' bestaan pas na haar eigen post_migrate (create_permissions).
    from beheer.rollen import ensure_roles

    ensure_roles()
