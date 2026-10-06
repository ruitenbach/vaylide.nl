"""Kerst: de gelegenheid, een kerstgroet zonder evenement, het ontwerp Winterlicht, sneeuw en de website."""
import os
import json
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.management import call_command
from django.template.loader import render_to_string
from django.test import Client
from django.urls import reverse

from catalog.atelier import contrast
from catalog.effects import EFFECT_OPTIONS, effect_summary, effects_errors
from catalog.models import Template
from core.csp import BOOT_SCRIPT
from catalog.occasions import OCCASION_LABELS, OCCASIONS, display_title, monogram
from invitations.content import publish_issues
from invitations.demo import DESIGN_IMAGES, demo_content
from invitations.models import Invitation
from invitations.render import RenderOptions, build_view, christmas_target, new_year, program_icon
from invitations.services import create_draft, save_draft
from processing.models import OutboundEmail

from .helpers import VaylideTestCase, future_date

AMS = ZoneInfo("Europe/Amsterdam")
EVENT_KEYS = ("date", "start_time", "end_time", "venue_name", "address")


def greeting_only(content: dict) -> dict:
    """Maakt van voorbeeldinhoud een kerstgroet zonder evenement: uitdrukkelijk gekozen als wenskaart (alleen dan is het er een)."""
    content = json.loads(json.dumps(content))
    for key in EVENT_KEYS:
        content[key] = ""
    content["soort"] = "wenskaart"
    return content


class KerstOccasionTests(VaylideTestCase):
    def test_occasion_is_available_everywhere(self):
        self.assertEqual(OCCASION_LABELS["kerst"], "Kerst")
        cfg = OCCASIONS["kerst"]
        self.assertTrue(cfg["event_optional"])
        self.assertEqual([f[0] for f in cfg["name_fields"]], ["family", "members"])
        self.assertTrue(cfg["name_fields"][0][2])   # afzender verplicht
        self.assertFalse(cfg["name_fields"][1][2])  # gezinsnamen optioneel
        # Geen wijzigingen in het datamodel die nog een migratie nodig hebben.
        call_command("makemigrations", "--check", "--dry-run", verbosity=0)

    def test_title_and_seal(self):
        cases = {
            "Familie Van Dijk": "D", "Familie de Vries": "V", "Het gezin Bakker": "B", "Fam. Yilmaz": "Y",
            "Sanne & Daan": "S&D", "Sanne en Daan de Boer": "S&D", "Studio Voorbeeld": "SV",
        }
        for sender, seal in cases.items():
            content = {"names": {"family": sender, "members": ""}}
            self.assertEqual(display_title("kerst", content), sender)
            self.assertEqual(monogram("kerst", content), seal, sender)

    def test_new_year_and_christmas_countdown(self):
        now = datetime(2026, 9, 27, 12, tzinfo=AMS)
        self.assertEqual(new_year(date(2026, 12, 25), now), 2027)
        self.assertEqual(new_year(date(2027, 1, 3), now), 2027)
        self.assertEqual(new_year(None, now), 2027)
        self.assertEqual(new_year(None, datetime(2027, 2, 1, tzinfo=AMS)), 2027)
        self.assertEqual(christmas_target(AMS, now), datetime(2026, 12, 25, tzinfo=AMS))
        self.assertIsNone(christmas_target(AMS, datetime(2026, 12, 27, tzinfo=AMS)))  # kerst is voorbij
        self.assertIsNone(christmas_target(AMS, datetime(2027, 3, 1, tzinfo=AMS)))    # te ver weg

    def test_program_icons_by_keyword(self):
        expected = {"Glühwein bij de haard": "drank", "Kerstdiner": "diner", "Cadeautjes onder de boom": "cadeau",
                    "Kerstliedjes zingen": "muziek", "Kerstkransjes en koffie": "dessert", "Nachtmis": "kerk",
                    "Proosten op het nieuwe jaar": "proost", "Wandeling langs de lichtjes": "wandeling"}
        for title, icon in expected.items():
            self.assertEqual(program_icon(title, 0), icon, title)
        self.assertEqual([program_icon("Spelletjes", i) for i in range(4)], ["ster", "bel", "kaars", "kerstbal"])


class KerstRenderTests(VaylideTestCase):
    def view(self, content, occasion="kerst", now=None, slug="winterlicht", mode="demo"):
        template = Template.objects.get(slug=slug)
        return build_view(occasion=occasion, content=content, overrides={}, template_version=template.current_version,
                          options=RenderOptions(mode=mode, now=now, music_synth=True))

    def test_christmas_card_with_dinner(self):
        now = datetime(2026, 9, 27, 12, tzinfo=AMS)
        v = self.view(demo_content("winterlicht", "kerst"), now=now)
        self.assertEqual(v["title"], "Familie Van Dijk")
        self.assertEqual(v["kicker"], "Warme kerstgroeten")
        self.assertFalse(v["headline_custom"])
        self.assertTrue(v["tagline"].startswith("wenst je fijne feestdagen en een gelukkig 20"))
        self.assertEqual(v["subnames"], "Sanne, Daan, Lotte en Siem")
        self.assertEqual(v["monogram"], "D")
        self.assertEqual(v["page_title"], "Familie Van Dijk · kerstkaart")
        self.assertTrue(v["has_event"])
        self.assertTrue(v["show"]["rsvp"] and v["show"]["location"] and v["show"]["program"])
        self.assertEqual(v["countdown_label"], "")
        self.assertEqual(v["music_melody"], "stille-nacht")
        self.assertEqual([p["icon"] for p in v["program"]], ["drank", "diner", "cadeau", "muziek", "dessert"])

    def test_greeting_without_event(self):
        content = greeting_only(demo_content("winterlicht", "kerst"))
        v = self.view(content, now=datetime(2026, 11, 2, 9, tzinfo=AMS))
        self.assertFalse(v["has_event"])
        self.assertFalse(v["show"]["rsvp"])
        self.assertFalse(v["show"]["location"])
        self.assertIsNone(v["calendar"])
        self.assertFalse(v["is_past"])
        # Van juli tot en met kerstavond telt de afteller af naar eerste kerstdag.
        self.assertTrue(v["show"]["countdown"])
        self.assertEqual(v["countdown_label"], "kerst")
        self.assertTrue(v["countdown_iso"].startswith("2026-12-25T00:00:00"))
        self.assertEqual(v["countdown"]["days"], 52)
        self.assertEqual(v["tagline"], "wenst je fijne feestdagen en een gelukkig 2027")
        html = render_to_string("invitations/partials/countdown.html", {"v": v})
        self.assertIn("dagen tot kerst", html)
        self.assertIn("Het is kerst!", html)
        # Na kerst geen afteller meer.
        after = self.view(content, now=datetime(2026, 12, 28, 9, tzinfo=AMS))
        self.assertFalse(after["show"]["countdown"])

    def test_couple_and_other_texts_when_used_for_another_occasion(self):
        # In Beheer kan een ontwerp ook voor andere gelegenheden worden aangezet (bijv. een winterbruiloft).
        v = self.view(demo_content("winterlicht", "bruiloft"), occasion="bruiloft")
        html = render_to_string("winterlicht/v1/invitation.html", {"v": v, "rsvp_form": {}})
        self.assertIn("Sanne", html)
        self.assertIn("Daan", html)
        self.assertIn("wl-names__amp", html)
        self.assertIn("Een uitnodiging voor jou", html)
        self.assertIn("Kom je ook?", html)
        self.assertNotIn("Fijne feestdagen", html)
        self.assertNotIn("Schuif je aan?", html)
        self.assertIn("Digitale uitnodiging gemaakt met", html)

    def test_publish_rules_for_a_greeting(self):
        content = greeting_only(demo_content("winterlicht", "kerst"))
        blocking = [i for i in publish_issues(content, "kerst", first_publication=True) if i.blocking]
        self.assertEqual(blocking, [])
        # Wie kiest voor een uitnodiging en een datum invult, nodigt mensen uit: dan zijn begintijd en locatie wel nodig.
        content["soort"] = "uitnodiging"
        content["date"] = future_date(60)
        fields = {i.field for i in publish_issues(content, "kerst", first_publication=True) if i.blocking}
        self.assertEqual(fields, {"start_time", "venue_name", "deadline"})
        # Bij een uitnodiging voor een andere gelegenheid blijft een datum altijd verplicht; alleen een uitdrukkelijke wenskaart heeft er geen nodig.
        other = greeting_only(demo_content("liefde-op-papier", "bruiloft"))
        self.assertEqual([i for i in publish_issues(other, "bruiloft", first_publication=True) if i.blocking], [])
        other["soort"] = "uitnodiging"
        fields = {i.field for i in publish_issues(other, "bruiloft", first_publication=True) if i.blocking}
        self.assertTrue({"date", "start_time", "venue_name"} <= fields)


class KerstStudioTests(VaylideTestCase):
    def test_greeting_card_needs_no_date_venue_or_deadline(self):
        c = Client()
        response = c.post("/maken/", {"occasion": "kerst", "template": "winterlicht", "soort": "wenskaart"})
        self.assertEqual(response.status_code, 302)
        uid = response["Location"].split("/")[2]
        inv = Invitation.objects.get(uid=uid)
        page = c.get(f"/maken/{uid}/gegevens/")
        self.assertContains(page, "Van wie komt de kerstkaart?")
        self.assertContains(page, "Wat voor kaart wordt het?")
        self.assertContains(page, 'name="soort" value="wenskaart" checked')  # uitdrukkelijk gekozen aan het begin
        response = c.post(f"/maken/{uid}/gegevens/", {
            "rev": inv.draft_rev, "actie": "volgende", "soort": "wenskaart", "name_family": "Familie Jansen", "name_members": "Eva, Tom en Noor",
            "timezone": "Europe/Amsterdam", "welcome_text": "Fijne feestdagen!",
        })
        self.assertRedirects(response, f"/maken/{uid}/programma/", fetch_redirect_response=False)
        inv.refresh_from_db()
        self.assertEqual(inv.title, "Familie Jansen")
        # Aanmelden staat standaard aan, maar zonder evenement is er geen deadline nodig.
        # Uitdrukkelijk een wenskaart: de stap Aanmelden valt weg.
        self.assertRedirects(c.get(f"/maken/{uid}/aanmelden/"), f"/maken/{uid}/fotos/", fetch_redirect_response=False)

    def test_partial_event_still_asks_for_time_and_venue(self):
        c = Client()
        response = c.post("/maken/", {"occasion": "kerst", "template": "winterlicht"})
        uid = response["Location"].split("/")[2]
        inv = Invitation.objects.get(uid=uid)
        response = c.post(f"/maken/{uid}/gegevens/", {
            "rev": inv.draft_rev, "actie": "volgende", "name_family": "Familie Jansen", "date": future_date(60), "timezone": "Europe/Amsterdam",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vul de begintijd in.")
        self.assertContains(response, "Vul de naam van de locatie in.")

    def test_published_greeting_card(self):
        owner = self.make_customer()
        inv = create_draft(occasion="kerst", template=Template.objects.get(slug="winterlicht"), owner=owner, soort="wenskaart")
        content = dict(inv.draft_content)
        content["names"] = {"family": "Familie Jansen", "members": "Eva, Tom en Noor"}
        content["welcome_text"] = "Lieve allemaal, fijne feestdagen!"
        inv = save_draft(inv, expected_rev=None, content=content, user=owner)
        payment = self.pay(inv, owner)
        self.assertTrue(inv.is_published)
        # De e-mails en de bestelstatus spreken van een kerstkaart "van" de afzender.
        live = OutboundEmail.objects.get(kind="invitation_live", invitation=inv)
        self.assertEqual(live.subject, "[TEST] Je kerstkaart staat online")
        self.assertIn("Goed nieuws: je kerstkaart van Familie Jansen staat online.", live.body_text)
        self.assertNotIn("uitnodiging voor", live.body_text)
        confirmation = OutboundEmail.objects.get(kind="order_confirmation", invitation=inv)
        self.assertIn("Je kerstkaart wordt automatisch gepubliceerd.", confirmation.body_text)
        status = Client()
        status.force_login(owner)
        page = status.get(reverse("orders:status", args=[payment.order.uid]))
        self.assertContains(page, "Je kerstkaart staat online")
        self.assertContains(page, "Bekijk je kerstkaart")
        self.assertContains(page, "Kerstkaart gepubliceerd")
        page = Client().get(f"/u/{inv.slug}/")
        self.assertEqual(page.status_code, 200)
        html = page.content.decode()
        self.assertIn("Familie Jansen", html)
        self.assertIn("Eva, Tom en Noor", html)
        self.assertIn("Een kerstgroet voor jou", html)
        self.assertIn("Digitale kerstkaart gemaakt met", html)
        self.assertIn("<title>Familie Jansen · kerstkaart</title>", html)
        self.assertNotIn("data-rsvp-form", html)        # geen evenement, dus geen aanmelden
        self.assertNotIn("Plan je route", html)
        self.assertNotIn("data-scratch", html)          # niets om open te krassen
        self.assertEqual("Aftellen naar kerst" in html, christmas_target(AMS, datetime.now(AMS)) is not None)
        self.assertIn('name="robots" content="noindex', html)


class WinterlichtDesignTests(VaylideTestCase):
    def manifest(self):
        return json.loads((settings.BASE_DIR / "designs" / "winterlicht" / "v1" / "manifest.json").read_text(encoding="utf-8"))

    def test_manifest_images_and_readable_colours(self):
        data = self.manifest()
        self.assertEqual(data["occasions"], ["kerst"])
        self.assertEqual(effects_errors(data["effects"]), [])
        self.assertEqual([p["key"] for p in data["palettes"]], ["kaarslicht", "hulst", "dennengroen", "winternacht"])
        pairs = [("ink", "paper"), ("ink", "paper-2"), ("muted", "paper"), ("muted", "paper-2"), ("accent", "paper"),
                 ("accent", "paper-2"), ("accent-ink", "accent"), ("env-ink", "env"), ("seal-ink", "seal"), ("gold-2", "paper")]
        for palette in data["palettes"]:
            c = {k[5:]: v for k, v in palette["vars"].items() if k.startswith("--wl-")}
            for fg, bg in pairs:
                self.assertGreaterEqual(contrast(c[fg], c[bg]), 4.5, f"{palette['key']}: {fg} op {bg}")
            for name in (f"scene-{palette['key']}.webp", f"scene-{palette['key']}-720.webp", f"huis-{palette['key']}.webp"):
                self.assertTrue(finders.find(f"designs{os.sep}winterlicht/v1/img/{name}"), name)
        for name in ("relief-boven", "relief-krans", "relief-zijkant", "relief-patroon", "goud-boven", "goud-krans", "goud-zijkant"):
            self.assertTrue(finders.find(f"designs{os.sep}winterlicht/v1/img/{name}.webp"), name)
        self.assertTrue(finders.find("img/designs/winterlicht.webp"))
        self.assertTrue(finders.find("img/site/gelegenheid-kerst.webp"))
        self.assertEqual(len(DESIGN_IMAGES["winterlicht"]), 5)
        for name in DESIGN_IMAGES["winterlicht"]:
            self.assertTrue(finders.find(f"img/demo/{name}.webp") and finders.find(f"img/demo/{name}-1000.webp"), name)

    def test_demo_page_has_the_whole_experience(self):
        for palette in ("kaarslicht", "hulst", "dennengroen", "winternacht"):
            response = Client().get("/voorbeeld/winterlicht/", {"kleur": palette})
            self.assertEqual(response.status_code, 200)
            html = response.content.decode()
            self.assertIn(f"designs/winterlicht/v1/img/scene-{palette}-720.webp", html)
            self.assertIn(f'data-palette="{palette}"', html)
        html = Client().get("/voorbeeld/winterlicht/").content.decode()
        for fragment in (
            'class="wl-seal fx-pulse" data-open data-fx-origin',   # het zegel opent de kaart
            'href="#uitnodiging"',                                # ook zonder JavaScript
            "wl-flap--boven", "wl-flap__goud",                    # kleppen en de gouden golf
            'data-fx-slot="cover"', 'data-fx-slot="hero"',          # sneeuw op de envelop en in het kerstraam
            "wl-l--flame", "wl-l--fairy",                          # levende kaarsvlammen en lichtsnoer
            "Warme kerstgroeten", "Familie Van Dijk", "Sanne, Daan, Lotte en Siem",
            "data-scratch", "data-scratch-all", "Kras en ontdek de datum",
            'class="wl-icon"', "Het programma", "Schuif je aan?", "Fijne feestdagen", "wl-bauble",
            'data-music-synth="stille-nacht"', "designs/winterlicht/v1/winterlicht.js",
            "data-tekst-op-beeld",                                  # contrast op de tekening: e2e/kerstraam.cjs
        ):
            self.assertIn(fragment, html)
        # De volledige datum staat er voor schermlezers, los van de kraskaartjes.
        self.assertRegex(html, r'<p class="visually-hidden">Vrijdag|<p class="visually-hidden">[A-Z][a-z]+dag \d+ december')
        self.assertIn('data-fx-sfeer="sneeuw"', html)
        # Geen eigen inline scripts: alleen het vaste startscript met een hash in de CSP.
        self.assertEqual(html.count("<script>"), 1)
        self.assertIn(f"<script>{BOOT_SCRIPT}</script>", html)
        self.assertNotIn("<style", html)

    def test_hero_fills_the_screen_below_the_demo_bar(self):
        # De voorbeeldbalk duwt de kop niet onder de vouw: 'Scroll verder' blijft in beeld.
        folder = settings.BASE_DIR / "designs" / "winterlicht" / "v1"
        css = (folder / "style.css").read_text(encoding="utf-8")
        script = (folder / "winterlicht.js").read_text(encoding="utf-8")
        self.assertIn("height: calc(100svh - var(--wl-bar, 0px))", css)
        self.assertIn('document.querySelector(".inv-banner")', script)
        self.assertIn('setProperty("--wl-bar"', script)
        self.assertIn("Scroll verder", Client().get("/voorbeeld/winterlicht/").content.decode())
        # De bovenste regels blijven tussen de lantaarns van het kerstraam (ook op 360 pixels breed).
        self.assertIn(".wl-hero__kicker { max-width: 56cqi; margin-inline: auto; }", css)
        self.assertIn(".wl-names { max-width: 52cqi; margin-inline: auto; }", css)

    def test_long_text_stays_above_the_church(self):
        # Veel tekst: winterlicht.js maakt de letters in het kerstraam kleiner (--wl-fit), zonder overgang, zodat
        # de meting klopt, ook bij 'minder beweging'. Zonder script blijft alles op de gewone maat.
        folder = settings.BASE_DIR / "designs" / "winterlicht" / "v1"
        css = (folder / "style.css").read_text(encoding="utf-8")
        script = (folder / "winterlicht.js").read_text(encoding="utf-8")
        for rule in ("calc(12cqi * var(--wl-fit, 1))", "calc(10cqi * var(--wl-fit, 1))", "calc(7.6cqi * var(--wl-fit, 1))",
                     "calc(4.4cqi * var(--wl-fit, 1))", "max(min(10px, 2.8cqi), calc(2.8cqi * var(--wl-fit, 1)))",
                     "max(min(10px, 3cqi), calc(3cqi * var(--wl-fit, 1)))", ".wl-hero__text, .wl-hero__text * { transition: none !important; }"):
            self.assertIn(rule, css)
        self.assertIn("var LIMIT = 0.485;", script)
        self.assertIn('text.style.setProperty("--wl-fit"', script)
        self.assertIn('document.fonts.addEventListener("loadingdone", fit)', script)

    def test_lights_rest_when_nobody_sees_them(self):
        # Onder de dichte envelop en als de kop uit beeld is, staan de lichtjes stil (minder werk voor de telefoon).
        folder = settings.BASE_DIR / "designs" / "winterlicht" / "v1"
        css = (folder / "style.css").read_text(encoding="utf-8")
        script = (folder / "winterlicht.js").read_text(encoding="utf-8")
        self.assertIn(".has-cover:not(.is-opening) .wl-l, .wl-lights--rust > .wl-l { --fx-play: paused; }", css)
        self.assertIn('lights.classList.toggle("wl-lights--rust"', script)
        # Alle doorlopende animaties van de lichtjes luisteren naar de knop Beweging (--fx-play) en staan onder .fx-motion.
        for line in css.splitlines():
            if line.startswith(".fx-motion .wl-l") and "infinite" in line:
                self.assertIn("animation-play-state: var(--fx-play, running)", line, line)
        self.assertNotRegex(css, r"(?m)^\.wl-l[^{]*\{[^}]*animation:")

    def test_envelope_loads_light(self):
        # De envelop is het eerste beeld: reliëf klein gehouden (comprimeer.py), de gouden laag pas na 'load'.
        folder = settings.BASE_DIR / "designs" / "winterlicht" / "v1"
        sizes = {p.stem: p.stat().st_size for p in (folder / "img").glob("*.webp")}
        first_view = sum(sizes[n] for n in ("relief-boven", "relief-krans", "relief-zijkant", "relief-patroon"))
        self.assertLess(first_view, 220 * 1024)
        self.assertLess(sum(sizes[n] for n in ("goud-boven", "goud-krans", "goud-zijkant")), 130 * 1024)
        css = (folder / "style.css").read_text(encoding="utf-8")
        script = (folder / "winterlicht.js").read_text(encoding="utf-8")
        self.assertNotRegex(css, r"(?m)^\.wl-flap__goud[^{]*\{[^}]*goud-")
        self.assertIn('.wl-geladen .wl-flap__goud .wl-emb--boven { background-image: url("img/goud-boven.webp"); }', css)
        self.assertIn('classList.add("wl-geladen")', script)

    def test_other_demos_keep_their_own_music(self):
        html = Client().get("/voorbeeld/liefde-op-papier/").content.decode()
        self.assertIn('data-music-synth=""', html)


class SnowEffectTests(VaylideTestCase):
    def test_snow_is_a_valid_choice(self):
        self.assertIn("sneeuw", EFFECT_OPTIONS["sfeer"])
        self.assertIn("sneeuw", EFFECT_OPTIONS["knal"])
        self.assertIn("sneeuw", EFFECT_OPTIONS["viering"])
        summary = effect_summary({"sfeer": "sneeuw", "knal": "sneeuw", "viering": "sterren", "namen": "schrijf", "onthul": "zacht", "extra": []})
        self.assertEqual(summary, "Zacht vallende sneeuw en bij het openen een wolk sneeuwvlokjes en gouden sterretjes.")
        script = (settings.BASE_DIR / "invitations" / "static" / "invitations" / "effects.js").read_text(encoding="utf-8")
        self.assertIn("sneeuw: { type: \"multi\"", script)
        self.assertIn("sneeuw: function (x, y, k)", script)


class KerstSiteTests(VaylideTestCase):
    def test_home_and_inspiration_show_the_christmas_tile(self):
        home = Client().get("/")
        # Kerst staat voorop bij de gelegenheden en heeft een eigen podium met de kerstkaarten.
        html = home.content.decode()
        self.assertContains(home, 'class="tile tile--kerst" href="/ontwerpen/?gelegenheid=kerst"')
        self.assertLess(html.index("tile--kerst"), html.index("tile--bruiloft"))
        self.assertContains(home, "Een warme digitale kerstkaart")
        self.assertContains(home, "img/site/tegel-kerst.webp")
        self.assertContains(home, 'class="kerstpodium"')
        inspiration = Client().get("/inspiratie/")
        self.assertContains(inspiration, 'id="tekst-kerst"')
        self.assertContains(inspiration, "img/site/gelegenheid-kerst.webp")
        self.assertContains(Client().get("/inspiratie/"), "Schuif je aan bij ons kerstdiner?")

    def test_collection_filter_and_search(self):
        response = Client().get("/ontwerpen/", {"gelegenheid": "kerst"})
        self.assertEqual([c["template"].slug for c in response.context["cards"]], ["gloria", "winterlicht", "aan-tafel", "middernacht"])   # A vóór B; Ho ho ho en Sneeuwpret (C) staan voorlopig niet in de collectie
        self.assertContains(response, "Ontwerpen voor kerst")
        self.assertContains(Client().get("/zoeken/", {"q": "kerst"}), "/ontwerpen/?gelegenheid=kerst")
        detail = Client().get("/ontwerpen/winterlicht/")
        self.assertContains(detail, "Zacht vallende sneeuw")
        self.assertContains(detail, "Envelop met lakzegel")
        self.assertContains(detail, "/maken/?ontwerp=winterlicht&amp;gelegenheid=kerst")
