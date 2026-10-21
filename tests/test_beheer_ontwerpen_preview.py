"""Beheer → Ontwerpen: previewkolom, kolommen en filters (alleen kijken; niets aan de publieke site)."""
import re

from django.test import Client
from django.urls import reverse

from accounts.models import User
from catalog.models import Template

from .helpers import VaylideTestCase


class OntwerpenLijstTests(VaylideTestCase):
    def setUp(self):
        super().setUp()
        self.staff = User.objects.create_user(email="beheer@example.com", password="Een-lang-wachtwoord-2026")
        self.staff.is_staff = True
        self.staff.save()
        self.c = Client()
        self.c.force_login(self.staff)
        self.url = reverse("beheer:templates")

    def lijst(self, **params):
        r = self.c.get(self.url, params)
        self.assertEqual(r.status_code, 200)
        return r.content.decode()

    def test_kolommen_en_previewkolom(self):
        html = self.lijst()
        for kop in ("Preview", "Naam", "Gelegenheid", "Indeling", "Zichtbaar", "Uitgelicht op homepage", "Volgorde"):
            self.assertIn(f"<th>{kop}</th>", html.replace('<th class="num">', "<th>"))
        t = Template.objects.get(slug="rose-royale")
        self.assertIn(f'href="{reverse("beheer:template_edit", args=[t.pk])}" aria-label="Bewerk {t.name}"', html)
        self.assertRegex(html, r'<img src="[^"]*rose-royale[^"]*" alt="" width="60" height="96"')

    def test_zonder_afbeelding_staat_er_geen_afbeelding(self):
        Template.objects.create(slug="zonder-beeld-xyz", name="Zonder beeld", occasions=["bruiloft"])
        html = self.lijst()
        self.assertIn("geen afbeelding", html)
        self.assertNotIn("_standaard.webp", html)

    def test_filters(self):
        Template.objects.filter(slug="rose-royale").update(homepage_uitgelicht=True, is_active=True)
        Template.objects.filter(slug="confetti").update(is_active=False)
        slugs = lambda h: set(re.findall(r'<span class="small muted">([a-z0-9-]+)</span></td>', h))
        self.assertEqual(slugs(self.lijst(uitgelicht="ja")), {"rose-royale"})
        self.assertNotIn("rose-royale", slugs(self.lijst(uitgelicht="nee")))
        self.assertEqual(slugs(self.lijst(zichtbaar="nee")) & {"confetti", "rose-royale"}, {"confetti"})
        self.assertIn("rose-royale", slugs(self.lijst(indeling="special")))
        self.assertNotIn("confetti", slugs(self.lijst(indeling="special")))
        self.assertIn("Geen ontwerpen", self.lijst(uitgelicht="ja", indeling="basis"))
        self.assertEqual(self.c.get(self.url, {"indeling": "onzin", "zichtbaar": "x"}).status_code, 200)

    def test_alleen_voor_beheerders(self):
        self.assertNotEqual(Client().get(self.url).status_code, 200)
