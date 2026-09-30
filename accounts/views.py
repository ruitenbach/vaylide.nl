"""Inloggen voor klanten (zonder wachtwoord) en uitloggen."""
from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from core.utils import ip_fingerprint, rate_limit
from processing.emails import send_draft_saved, send_login_code

from .forms import CodeForm, EmailForm
from .models import LoginCode, normalize_email
from .services import complete_login, safe_next, verify_code

SESSION_EMAIL = "vierlief_login_email"
SESSION_NEXT = "vierlief_login_next"
SESSION_TEST_CODE = "vierlief_test_code"


def _code_on_screen() -> bool:
    """Alleen als e-mails in de testomgeving echt niet worden verstuurd (outbox), staat de code op het scherm. Met SMTP
    komt de code in de mailbox, net als straks live; dan tonen we hem niet (ook niet aan wie het adres niet bezit)."""
    return settings.TEST_MODE and settings.EMAIL_MODE == "outbox"


def _after_login(request, user):
    from invitations.models import Invitation

    claimed = request.session.pop("vierlief_claimed", 0)
    if claimed:
        latest = Invitation.objects.filter(owner=user).order_by("-updated_at").first()
        if latest:
            send_draft_saved(latest, user)
        messages.success(request, "Je bent ingelogd en je ontwerp is bewaard in Mijn VAYLIDE.")
    else:
        messages.success(request, "Je bent ingelogd.")


@require_http_methods(["GET", "POST"])
def login_view(request):
    next_url = safe_next(request, request.GET.get("next") or request.POST.get("next", ""), reverse("portal:home"))
    if request.user.is_authenticated and not request.user.is_staff:
        return redirect(next_url)
    purpose = request.GET.get("doel") or request.POST.get("doel") or "login"
    form = EmailForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = normalize_email(form.cleaned_data["email"])
        ip = ip_fingerprint(request)
        if not rate_limit(f"login-ip:{ip}", 12, 3600) or not rate_limit(f"login-email:{email}", 5, 3600):
            form.add_error(None, "Er zijn te veel codes aangevraagd. Wacht even en probeer het dan opnieuw.")
        else:
            code_obj, code, token = LoginCode.issue(email, next_url)
            send_login_code(email, code, reverse("accounts:link", args=[token]), purpose="verify" if purpose == "bewaren" else "login")
            request.session[SESSION_EMAIL] = email
            request.session[SESSION_NEXT] = next_url
            if _code_on_screen():
                request.session[SESSION_TEST_CODE] = {"code": code, "link": reverse("accounts:link", args=[token])}
            return redirect("accounts:code")
    return render(request, "accounts/login.html", {"form": form, "next": next_url, "purpose": purpose})


@require_http_methods(["GET", "POST"])
def code_view(request):
    email = request.session.get(SESSION_EMAIL)
    if not email:
        return redirect("accounts:login")
    form = CodeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if not rate_limit(f"code-ip:{ip_fingerprint(request)}", 30, 3600):
            form.add_error(None, "Te veel pogingen. Vraag over een tijdje een nieuwe code aan.")
        elif verify_code(email, form.cleaned_data["code"]) is None:
            form.add_error("code", "Deze code klopt niet of is verlopen. Controleer de code of vraag een nieuwe aan.")
        else:
            user, error = complete_login(request, email)
            if user is None:
                form.add_error(None, error)
            else:
                next_url = request.session.pop(SESSION_NEXT, "") or reverse("portal:home")
                request.session.pop(SESSION_EMAIL, None)
                request.session.pop(SESSION_TEST_CODE, None)
                _after_login(request, user)
                return redirect(safe_next(request, next_url, reverse("portal:home")))
    test_code = request.session.get(SESSION_TEST_CODE) if _code_on_screen() else None
    return render(request, "accounts/code.html", {"form": form, "email": email, "test_code": test_code})


@require_http_methods(["GET", "POST"])
def link_view(request, token):
    # GET toont alleen een knop: zo verbruiken e-mailscanners de link niet.
    code_obj = LoginCode.find_by_token(token)
    valid = code_obj is not None and code_obj.used_at is None and code_obj.expires_at > timezone.now()
    if request.method == "POST" and valid:
        code_obj.used_at = timezone.now()
        code_obj.save(update_fields=["used_at"])
        user, error = complete_login(request, code_obj.email)
        if user is None:
            messages.error(request, error)
            return redirect("accounts:login")
        request.session.pop(SESSION_TEST_CODE, None)
        _after_login(request, user)
        return redirect(safe_next(request, code_obj.next_url, reverse("portal:home")))
    return render(request, "accounts/link.html", {"valid": valid, "email": code_obj.email if code_obj else ""}, status=200 if valid else 400)


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "Je bent uitgelogd.")
    return redirect("core:home")
