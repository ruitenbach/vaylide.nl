"""De inlog van Django-admin (noodtoegang), met dezelfde bescherming tegen wachtwoord raden als Beheer."""
from __future__ import annotations

from django.contrib import admin
from django.http import HttpResponse

from . import bruteforce


def admin_login(request, extra_context=None):
    username = request.POST.get("username", "") if request.method == "POST" else ""
    if request.method == "POST" and bruteforce.is_blocked(request, username):
        response = HttpResponse(bruteforce.MESSAGE, status=429, content_type="text/plain; charset=utf-8")
        response["Retry-After"] = str(bruteforce.WINDOW)
        return response
    response = admin.site.login(request, extra_context)
    if request.method == "POST":
        # Een geslaagde inlog stuurt door (302); alles anders is een mislukking.
        if response.status_code in (301, 302):
            bruteforce.register_success(username)
        else:
            bruteforce.register_failure(request, username)
    return response
