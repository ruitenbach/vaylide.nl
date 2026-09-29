"""Website: nieuwe pagina's, zoeken zonder klantgegevens en de navigatie uit de nieuwe vormgeving."""
from django.test import Client

from .helpers import VaylideTestCase


class NewPagesTests(VaylideTestCase):
    def test_inspiration_and_about_pages(self):
        inspiration = Client().get("/inspiratie/")
        self.assertContains(inspiration, "Voorbeeldteksten")
        self.assertContains(inspiration, 'id="tekst-bruiloft"')
        self.assertContains(inspiration, "/ontwerpen/?gelegenheid=babyshower")
        about = Client().get("/over-ons/")
        self.assertContains(about, "Waarom VAYLIDE?")
        self.assertContains(about, "Onze visie")
        self.assertContains(about, "Maak van jouw moment een uitnodiging om naar uit te kijken.")
        self.assertContains(about, "Voor particulieren en bedrijven")
        # Geen onbewezen duurzaamheidsclaims.
        for word in ("duurzaam", "co2", "milieuvriendelijk", "groener"):
            self.assertNotIn(word, about.content.decode().lower())
        # Geen verzonnen reviews, sterren of klantenaantallen.
        for page in (inspiration, about, Client().get("/")):
            html = page.content.decode()
            self.assertNotIn("★", html)
            self.assertNotIn("klanten gingen je voor", html.lower())

    def test_header_has_mockup_navigation(self):
        html = Client().get("/prijzen/").content.decode()
        for label in ("Home", "Collectie", "Zo werkt het", "Prijzen", "Inspiratie", "Over ons", "Start nu"):
            self.assertIn(f">{label}<", html)
        self.assertIn('aria-label="Zoeken"', html)
        self.assertIn('href="/prijzen/" aria-current="page"', html)

    def test_sitemap_lists_new_pages_but_not_search(self):
        body = Client().get("/sitemap.xml").content.decode()
        self.assertIn("/inspiratie/</loc>", body)
        self.assertIn("/over-ons/</loc>", body)
        self.assertNotIn("/zoeken/", body)

    def test_faq_items_can_be_linked(self):
        self.assertContains(Client().get("/veelgestelde-vragen/"), 'id="vraag-1"')


class SearchTests(VaylideTestCase):
    def test_finds_faq_designs_and_pages(self):
        response = Client().get("/zoeken/", {"q": "muziek"})
        self.assertContains(response, "Kan ik muziek toevoegen?")
        self.assertContains(response, "/veelgestelde-vragen/#vraag-")
        self.assertContains(Client().get("/zoeken/", {"q": "Avondgoud"}), "/ontwerpen/avondgoud/")
        self.assertContains(Client().get("/zoeken/", {"q": "prijs pakket"}), "/prijzen/")

    def test_accents_and_case_do_not_matter(self):
        self.assertContains(Client().get("/zoeken/", {"q": "PRIVE"}), "Privacy")

    def test_never_returns_customer_data(self):
        owner = self.make_customer()
        invitation = self.published(owner=owner)
        self.rsvp(Client(), invitation, name="Geheime Gast", attending="ja", party_size="1")
        for term in ("Anna", "Bram", "Kasteel Test", "Geheime Gast", owner.email, invitation.slug):
            response = Client().get("/zoeken/", {"q": term})
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Niets gevonden", msg_prefix=term)
            self.assertNotContains(response, "/u/", msg_prefix=term)

    def test_is_not_indexed_and_escapes_input(self):
        response = Client().get("/zoeken/", {"q": "<script>alert(1)</script>"})
        self.assertContains(response, 'content="noindex, follow"')
        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertContains(response, "&lt;script&gt;")

    def test_long_query_is_cut_off(self):
        response = Client().get("/zoeken/", {"q": "muziek " + "x" * 500})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["query"]), 100)

    def test_empty_query_shows_examples(self):
        response = Client().get("/zoeken/")
        self.assertContains(response, "Bijvoorbeeld:")
        self.assertEqual(response.context["results"], [])


class BrandTests(VaylideTestCase):
    """Merk Vaylide: het logo zoals aangeleverd, de iconen en nergens meer een oude naam (Vierlief, Vaylia)."""

    PAGES = ("/", "/ontwerpen/", "/zo-werkt-het/", "/prijzen/", "/inspiratie/", "/over-ons/", "/veelgestelde-vragen/",
             "/contact/", "/privacy/", "/voorwaarden/", "/inloggen/", "/maken/", "/voorbeeld/stipjes/", "/bestaat-niet/")

    def test_logo_icons_and_share_image(self):
        from django.contrib.staticfiles import finders

        html = Client().get("/").content.decode()
        self.assertIn('class="logo__img"', html)
        self.assertIn('alt="VAYLIDE"', html)
        self.assertIn('aria-label="VAYLIDE, naar de homepage"', html)
        self.assertIn("img/og-vaylide.jpg", html)
        self.assertIn('<meta property="og:site_name" content="VAYLIDE">', html)
        for path in ("img/merk/vaylide-logo.webp", "img/favicon-32.png", "img/favicon-48.png", "img/icon-192.png",
                     "img/apple-touch-icon.png", "img/og-vaylide.jpg"):
            self.assertIn(path.rsplit(".", 1)[0], html, path)
            self.assertTrue(finders.find(path), path)
        # De PNG-versie is voor de e-mails.
        self.assertTrue(finders.find("img/merk/vaylide-logo.png"))
        # Het oude merkteken is weg.
        self.assertNotIn("favicon.svg", html)
        self.assertFalse(finders.find("img/favicon.svg"))

    def test_old_name_is_gone_from_pages(self):
        for url in self.PAGES:
            response = Client().get(url)
            self.assertIn(response.status_code, (200, 404), url)
            html = response.content.decode()
            for old in ("Vierlief", "Vaylia"):
                self.assertNotIn(old, html, url)
            self.assertIn("VAYLIDE", html, url)

    def test_emails_show_logo_and_name(self):
        from processing.emails import send_login_code

        email = send_login_code("gast@example.com", "123456", "/inloggen/code/")
        self.assertIn("VAYLIDE", email.subject)
        self.assertIn('alt="VAYLIDE"', email.body_html)
        self.assertIn("https://vaylide.test/static/img/merk/vaylide-logo.png", email.body_html)
        for old in ("Vierlief", "Vaylia"):
            self.assertNotIn(old, email.body_html + email.body_text + email.subject)
