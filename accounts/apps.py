from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "Accounts"

    def ready(self):
        from django.contrib.auth.signals import user_logged_in

        from . import tweestaps

        def vergeet_tweede_stap(sender, request, user, **kwargs):
            """Elke inlog met wachtwoord begint zonder bevestigde tweede stap, ook als de sessie al eens bevestigd was."""
            if request is not None and hasattr(request, "session"):
                request.session.pop(tweestaps.SESSION_KEY, None)

        user_logged_in.connect(vergeet_tweede_stap, dispatch_uid="vaylide_vergeet_tweede_stap")
