"""Homepage-carrousel (core/templates/core/home.html, static/js/carrousel.js) en de keuze vanuit Beheer.

Wat deze tests bewaken:
- alleen actieve, openbare Luxe- en Special-ontwerpen die in Beheer zijn uitgelicht, staan in de carrousel, in de volgorde van Beheer;
- bij minder dan vijf geldige uitgelichte ontwerpen blijft de bestaande homepagepresentatie (envelop in de kop) gewoon staan;
- de kaarten openen de bestaande ontwerppagina met het werkende voorbeeld en de bestelknop; er komt geen nieuwe route;
- de migratie voegt alleen twee velden toe en laat bestaande ontwerpgegevens ongemoeid;
- de vaste teksten van de eigenaar, de fonkelingen en het bestelproces blijven staan;
- Beheer: alleen voor beheerders, velden worden bewaard en een ongeschikt ontwerp wordt gemeld."""
import re

from django.conf import settings
from django.test import Client
from django.urls import reverse

from accounts.models import User
from catalog import collectie, prijzen
from catalog.models import Template

from .helpers import VaylideTestCase

SPECIAL = ["rose-royale", "zwanenhart", "aurora-nocturne", "balzaal", "strandboog"]
LUXE = ["winterlicht", "gloria"]


def lichten_uit(slugs):
    for volgorde, slug in enumerate(slugs, start=1):
        Template.objects.filter(slug=slug).update(is_active=True, homepage_uitgelicht=True, homepage_volgorde=volgorde * 10)


def home_html():
    return Client().get("/").content.decode()


def carrousel_slugs(html):
    return re.findall(r'<li class="cv__card"[^>]*data-href="/ontwerpen/([a-z0-9-]+)/', html)


class CarrouselSelectieTests(VaylideTestCase):
    def test_standaard_staat_er_niets_uitgelicht_en_blijft_de_oude_kop(self):
        self.assertFalse(Template.objects.filter(homepage_uitgelicht=True).exists())
        html = home_html()
        self.assertNotIn("data-carrousel", html)
        self.assertIn('class="card-stage"', html)
        self.assertNotIn("js/carrousel.js", html)

    def test_zeven_geldige_ontwerpen_geven_een_carrousel_in_de_volgorde_van_beheer(self):
        lichten_uit(SPECIAL + LUXE)
        Template.objects.filter(slug="gloria").update(homepage_volgorde=5)        # wordt de eerste
        html = home_html()
        self.assertIn("data-carrousel", html)
        self.assertEqual(carrousel_slugs(html), ["gloria"] + [s for s in SPECIAL + LUXE if s != "gloria"])
        self.assertIn("js/carrousel.js", html)
        self.assertNotIn('class="card-stage"', html)

    def test_alleen_luxe_en_special_basis_wordt_overgeslagen(self):
        lichten_uit(SPECIAL + LUXE)
        basis = Template.objects.filter(slug="confetti")
        self.assertEqual(prijzen.tier(basis.first()), prijzen.BASIS)
        basis.update(homepage_uitgelicht=True, homepage_volgorde=1, is_active=True)
        self.assertNotIn("confetti", carrousel_slugs(home_html()))

    def test_een_niet_zichtbaar_ontwerp_wordt_overgeslagen(self):
        lichten_uit(SPECIAL + LUXE)
        Template.objects.filter(slug="balzaal").update(is_active=False)
        slugs = carrousel_slugs(home_html())
        self.assertNotIn("balzaal", slugs)
        self.assertEqual(len(slugs), 6)

    def test_een_verborgen_filmkaart_komt_niet_in_beeld_zolang_hij_verborgen_is(self):
        lichten_uit(SPECIAL + LUXE)
        Template.objects.filter(slug="rozenboog").update(is_active=False, homepage_uitgelicht=True, homepage_volgorde=1)
        self.assertNotIn("rozenboog", carrousel_slugs(home_html()))

    def test_ontwerp_zonder_huidige_versie_wordt_overgeslagen(self):
        lichten_uit(SPECIAL + LUXE)
        Template.objects.filter(slug="strandboog").update(current_version=None)
        self.assertNotIn("strandboog", carrousel_slugs(home_html()))

    def test_minder_dan_vijf_geldige_geeft_de_vorige_presentatie(self):
        lichten_uit(SPECIAL[:4])
        html = home_html()
        self.assertNotIn("data-carrousel", html)
        self.assertIn('class="card-stage"', html)
        # vier geldige plus een ongeschikte (Basis) blijft vier
        Template.objects.filter(slug="confetti").update(homepage_uitgelicht=True, is_active=True)
        self.assertNotIn("data-carrousel", home_html())
        self.assertEqual(collectie.homepage_ontwerpen(Template), [])

    def test_precies_vijf_is_genoeg(self):
        lichten_uit(SPECIAL)
        self.assertEqual(len(carrousel_slugs(home_html())), 5)

    def test_geen_vaste_bovengrens(self):
        slugs = list(Template.objects.filter(is_active=True, current_version__isnull=False).values_list("slug", flat=True))
        luxe_special = [s for s in slugs if prijzen.INDELING.get(s) in (prijzen.LUXE, prijzen.SPECIAL)]
        lichten_uit(luxe_special)
        self.assertEqual(len(carrousel_slugs(home_html())), len(luxe_special))
        self.assertGreater(len(luxe_special), 9)


class CarrouselHomepageTests(VaylideTestCase):
    def setUp(self):
        super().setUp()
        lichten_uit(SPECIAL + LUXE)
        self.html = home_html()

    def test_vaste_teksten_knoppen_en_fonkelingen_blijven(self):
        for tekst in ("Maak jouw uitnodiging", "Bekijk dit ontwerp", "Ontdek de collectie", "<em>bijzondere</em>"):
            self.assertIn(tekst, self.html)
        kop = self.html.split('id="hero-titel">', 1)[1].split("</h1>", 1)[0]
        zichtbaar = re.sub(r"<[^>]+>", "", kop).split()
        self.assertEqual(" ".join(zichtbaar), "Bijzondere momenten verdienen een bijzondere uitnodiging.")
        self.assertIn("data-hero3d", self.html)
        self.assertIn('<canvas class="hero__sparkles"></canvas>', self.html)
        self.assertIn("js/hero3d.js", self.html)
        self.assertEqual(self.html.count("<h1"), 1)

    def test_kaarten_openen_de_bestaande_ontwerppagina_met_voorbeeld_en_bestelknop(self):
        links = set(re.findall(r'data-href="(/ontwerpen/[^"]+)"', self.html))
        self.assertEqual(len(links), 7)
        for link in links:
            antwoord = Client().get(link)
            self.assertEqual(antwoord.status_code, 200, link)
            tekst = antwoord.content.decode()
            self.assertIn(reverse("studio:start"), tekst)       # bestellen blijft mogelijk

    def test_elke_kaart_heeft_naam_afbeelding_en_alt(self):
        self.assertEqual(self.html.count('class="cv__card"'), 7)
        self.assertEqual(len(re.findall(r'<img src="[^"]+designs/[^"]+" width="800" height="1000" alt="Digitale uitnodiging [^"]+"', self.html)), 7)
        self.assertIn("Special", self.html)
        self.assertIn("Luxe", self.html)

    def test_toegankelijke_opbouw(self):
        self.assertIn('role="group" aria-roledescription="carrousel"', self.html)
        self.assertIn('aria-label="Vorig ontwerp"', self.html)
        self.assertIn('aria-label="Volgend ontwerp"', self.html)
        self.assertIn('role="status" aria-live="polite"', self.html)

    def test_geen_inline_script_of_stijlblok_erbij(self):
        # de enige inline scripts zijn die al bestonden (startscript met hash); de carrousel voegt er geen toe
        voor = Client().get("/").content.decode()
        self.assertEqual(len(re.findall(r"<script(?![^>]*src=)", voor)), len(re.findall(r"<script(?![^>]*src=)", self.html)))
        self.assertNotIn("<style", self.html)

    def test_bestellen_prijzen_en_overige_routes_blijven_werken(self):
        for pad in ("/ontwerpen/", "/prijzen/", "/digitale-kerstkaarten/", "/zo-werkt-het/", "/robots.txt"):
            self.assertEqual(Client().get(pad).status_code, 200, pad)
        self.assertEqual(Client().get(reverse("studio:start")).status_code, 200)

    def test_script_en_stijl_bevatten_de_veiligheidsregels(self):
        js = (settings.BASE_DIR / "static/js/carrousel.js").read_text(encoding="utf-8")
        css = (settings.BASE_DIR / "static/css/vierlief.css").read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion: reduce", js)
        self.assertIn("IntersectionObserver", js)            # zweven pauzeert uit beeld
        self.assertIn("visibilitychange", js)
        self.assertIn("touch-action: pan-y", css)             # verticaal scrollen blijft aan de browser
        self.assertRegex(css, r"@media \(prefers-reduced-motion: reduce\) \{ \.cv__float, \.cv__float::before \{ animation: none")
        self.assertIn("html:not(.js)", css)                   # zonder JavaScript een gewone rij
        self.assertNotIn("setPointerCapture(e.pointerId); } catch", js.replace('if (e.pointerType === "mouse") { try { stage.setPointerCapture(e.pointerId); }', ""))   # aanraking krijgt geen pointer-capture
        self.assertNotIn("preventDefault()", js.split('stage.addEventListener("pointermove"')[1].split('function los')[0])   # nooit scrollen blokkeren


class MigratieTests(VaylideTestCase):
    def test_migratie_voegt_alleen_twee_velden_toe(self):
        import importlib
        from django.db import migrations

        mod = importlib.import_module("catalog.migrations.0009_homepage_uitgelicht")
        ops = mod.Migration.operations
        self.assertEqual([type(o) for o in ops], [migrations.AddField, migrations.AddField])
        self.assertEqual({o.name for o in ops}, {"homepage_uitgelicht", "homepage_volgorde"})
        self.assertEqual(mod.Migration.dependencies, [("catalog", "0008_prijsbeheer_startstand")])

    def test_bestaande_ontwerpen_krijgen_de_standaardwaarden(self):
        self.assertTrue(Template.objects.exists())
        self.assertFalse(Template.objects.exclude(homepage_uitgelicht=False, homepage_volgorde=100).exists())


class BeheerHomepageTests(VaylideTestCase):
    def setUp(self):
        super().setUp()
        self.staff = User.objects.create_user(email="beheer@example.com", password="Een-lang-wachtwoord-2026")
        self.staff.is_staff = True
        self.staff.save()
        self.klant = User.objects.create_user(email="klant@example.com", password="Een-lang-wachtwoord-2026")

    def als(self, user):
        c = Client()
        c.force_login(user)
        return c

    def test_alleen_beheerders(self):
        t = Template.objects.get(slug="rose-royale")
        for pad in (reverse("beheer:templates"), reverse("beheer:template_edit", args=[t.pk])):
            self.assertNotEqual(self.als(self.klant).get(pad).status_code, 200)
            self.assertNotEqual(Client().get(pad).status_code, 200)
            self.assertEqual(self.als(self.staff).get(pad).status_code, 200)

    def test_velden_worden_bewaard_en_andere_gegevens_blijven_gelijk(self):
        t = Template.objects.get(slug="rose-royale")
        voor = {f: getattr(t, f) for f in ("name", "tagline", "description", "occasions", "is_active", "special", "sort_order", "current_version_id")}
        post = {"name": t.name, "tagline": t.tagline, "description": t.description, "style_notes": t.style_notes, "occasions": t.occasions,
                "is_active": "on", "sort_order": t.sort_order, "current_version": t.current_version_id,
                "homepage_uitgelicht": "on", "homepage_volgorde": "3"}
        if t.special:
            post["special"] = "on"
        r = self.als(self.staff).post(reverse("beheer:template_edit", args=[t.pk]), post)
        self.assertEqual(r.status_code, 302, getattr(r, "content", b"")[:300])
        t.refresh_from_db()
        self.assertTrue(t.homepage_uitgelicht)
        self.assertEqual(t.homepage_volgorde, 3)
        self.assertEqual({f: getattr(t, f) for f in voor}, voor)

    def test_lijst_en_bewerkscherm_melden_een_ongeschikt_ontwerp(self):
        Template.objects.filter(slug="confetti").update(homepage_uitgelicht=True, homepage_volgorde=7)      # Basis
        c = self.als(self.staff)
        lijst = c.get(reverse("beheer:templates")).content.decode()
        self.assertIn("wordt overgeslagen", lijst)
        self.assertIn("De carrousel staat uit", lijst)
        pk = Template.objects.get(slug="confetti").pk
        self.assertIn("Dit ontwerp is nu niet geschikt", c.get(reverse("beheer:template_edit", args=[pk])).content.decode())
        pk = Template.objects.get(slug="rose-royale").pk
        self.assertNotIn("Dit ontwerp is nu niet geschikt", c.get(reverse("beheer:template_edit", args=[pk])).content.decode())

    def test_lijst_meldt_dat_de_carrousel_aanstaat(self):
        lichten_uit(SPECIAL)
        self.assertIn("De carrousel staat aan met 5 ontwerpen", self.als(self.staff).get(reverse("beheer:templates")).content.decode())


class VoordelenTests(VaylideTestCase):
    def test_vijf_voordelen_in_de_juiste_volgorde(self):
        verwacht = ["Snel en eenvoudig", "Stijlvolle ontwerpen", "Eigen foto's en muziek toevoegen", "Automatisch online", "RSVP & gastenlijst"]
        for html in [Client().get("/").content.decode()]:
            lijst = html.split('class="hero__checks"', 1)[1].split("</ul>", 1)[0].replace("&#x27;", "'").replace("&amp;", "&")
            posities = [lijst.index(tekst) for tekst in verwacht]
            self.assertEqual(posities, sorted(posities))
            self.assertEqual(lijst.count('<li>'), 5)


class KopTypografieTests(VaylideTestCase):
    def test_pinyon_script_alleen_voor_het_woord_bijzondere_met_eigen_bestand(self):
        css = (settings.BASE_DIR / "static/css/vierlief.css").read_text()
        self.assertIn('url("../fonts/pinyon-script-latin-400-normal.woff2")', css)
        self.assertIn(".hero--carrousel .hero__kop h1 em { display: block; font-family: \"Pinyon Script\"", css)
        self.assertTrue((settings.BASE_DIR / "static/fonts/pinyon-script-latin-400-normal.woff2").exists())
        self.assertTrue((settings.BASE_DIR / "static/fonts/OFL-pinyon-script.txt").exists())

    def test_teller_in_plaats_van_zichtbare_bolletjes(self):
        lichten_uit(SPECIAL + LUXE)
        html = home_html()
        self.assertIn('class="cv__teller" aria-hidden="true"', html)
        css = (settings.BASE_DIR / "static/css/vierlief.css").read_text()
        self.assertIn(".hero--carrousel .cv__dots { display: none; }", css)
        js = (settings.BASE_DIR / "static/js/carrousel.js").read_text()
        self.assertIn('" / "', js)

    def test_voordelenrij_staat_op_desktop_over_de_hele_hero_gecentreerd(self):
        css = (settings.BASE_DIR / "static/css/vierlief.css").read_text()
        self.assertIn(".hero--carrousel .hero__checksrij { grid-column: 1 / -1;", css)
        self.assertIn(".hero--carrousel .hero__checks { justify-content: center;", css)

    def test_linker_kop_heeft_een_entree_die_minder_beweging_respecteert(self):
        css = (settings.BASE_DIR / "static/css/vierlief.css").read_text()
        self.assertIn("@keyframes hero-kop-in", css)
        blok = css.split("@media (prefers-reduced-motion: no-preference) {\n  .hero--carrousel .hero__kop .eyebrow")[1]
        self.assertIn("hero-kop-in", blok.split("}\n")[0] + blok.split("}\n")[1])

    def test_mobiele_bediening_heeft_vaste_volgorde_en_teller_telt_alle_kaarten(self):
        css = (settings.BASE_DIR / "static/css/vierlief.css").read_text()
        self.assertIn(".hero--carrousel .cv__acties { display: contents; }", css)
        self.assertIn(".hero--carrousel .cv__teller { grid-column: 2; grid-row: 6;", css)
        js = (settings.BASE_DIR / "static/js/carrousel.js").read_text()
        self.assertIn('" / " + (N < 10 ? "0" : "") + N', js)
