"""Kerststad (special, kerst): de goedgekeurde peperkoekstad-video met de gouden V-badge als klikpunt, één keer volledig afgespeeld en daarna een levende eindloop,
met een kaart in dezelfde wereld. De kaart toont alleen wat de klant heeft ingevuld; datum, programma, locatie, aftellen en aanmelden alleen bij een kerstdiner (een datum).
Als wenskaart kost hij de bestaande speciale prijs van € 24,95 incl. btw."""
import json
import re
import struct

from django.conf import settings
from django.template.loader import render_to_string
from django.test import Client

from catalog import collectie, wenskaart
from catalog.atelier import contrast
from catalog.effects import effects_errors
from catalog.models import Template
from catalog.specials import special_addon
from invitations.content import card_kind
from invitations.demo import demo_content
from invitations.render import RenderOptions, build_view
from invitations.services import create_draft
from orders.pricing import compare_packages

from .helpers import VaylideTestCase

ONTWERP = settings.BASE_DIR / "designs" / "kerststad" / "v1"
DEMO = "/voorbeeld/kerststad/?gelegenheid=kerst"
LUS_START = 16.0


def _render(content=None, **view_wijzigingen):
    version = Template.objects.get(slug="kerststad").current_version
    content = content if content is not None else demo_content("kerststad", "kerst")
    view = build_view(occasion="kerst", content=content, overrides={}, template_version=version, options=RenderOptions(mode="demo"))
    view.update(view_wijzigingen)
    return render_to_string(version.template_path, {"v": view, "rsvp_form": {"client_token": "x", "form_ts": ""}})


def _duur_mp4(pad) -> float:
    """Duur uit het mvhd-blok van een mp4 (faststart: staat vooraan)."""
    kop = pad.read_bytes()[:4096]
    i = kop.index(b"mvhd")
    versie = kop[i + 4]
    assert versie == 0, "verwacht een mvhd van versie 0"
    schaal, duur = struct.unpack(">II", kop[i + 16:i + 24])
    return duur / schaal


class KerststadOntwerpTests(VaylideTestCase):
    def manifest(self):
        return json.loads((ONTWERP / "manifest.json").read_text(encoding="utf-8"))

    def test_is_een_special_voor_kerst_met_eigen_opening_zonder_aparte_envelop(self):
        template = Template.objects.get(slug="kerststad")
        self.assertTrue(template.special)
        self.assertIsNone(special_addon(template), "er is geen verzonnen meerprijs: zonder optie special-<code> geldt de pakketprijs (zie test_specials)")
        self.assertEqual(template.occasions, ["kerst"])
        self.assertEqual(self.manifest()["envelope_mode"], "built_in", "geen aparte envelop vóór deze opening")
        self.assertEqual(collectie.groep("kerststad"), "A")
        self.assertIn("kerststad", collectie.SPECIALS)

    def test_staat_onder_specials_en_niet_tussen_de_gewone_kaarten(self):
        pagina = Client().get("/ontwerpen/", {"gelegenheid": "kerst"}).content.decode()
        speciaal = pagina[pagina.index("Specials"):]
        self.assertIn("/ontwerpen/kerststad/", speciaal)
        self.assertNotIn("/ontwerpen/kerststad/", pagina[:pagina.index("Specials")])

    def test_effecten_en_tekstkleuren(self):
        data = self.manifest()
        self.assertEqual(effects_errors(data["effects"]), [])
        v = data["palettes"][0]["vars"]
        for achtergrond in (v["--ks-nacht"], v["--ks-nacht-2"], v["--ks-nacht-3"]):
            for tekst in (v["--ks-glazuur"], v["--ks-glazuur-2"], v["--ks-goud-lt"]):
                self.assertGreaterEqual(contrast(tekst, achtergrond), 7, f"{tekst} op {achtergrond}")
            self.assertGreaterEqual(contrast(v["--ks-goud"], achtergrond), 4.5, f"goud op {achtergrond}")
        for koek in (v["--ks-koek-2"], v["--ks-koek-3"]):          # de peperkoekplaten: de donkere helft van het verloop
            self.assertGreaterEqual(contrast(v["--ks-glazuur"], koek), 7, f"glazuur op {koek}")
        self.assertGreaterEqual(contrast(v["--ks-glazuur"], v["--ks-koek"]), 5.5)
        self.assertGreaterEqual(contrast(v["--ks-glazuur-2"], v["--ks-koek"]), 4.5)
        for papier in (v["--ks-glazuur"], v["--ks-glazuur-2"]):      # het aanmeldkaartje
            for tekst in (v["--ks-ink"], v["--ks-ink-2"], v["--ks-accent"]):
                self.assertGreaterEqual(contrast(tekst, papier), 4.5, f"{tekst} op {papier}")

    def test_media_is_web_klaar_en_aanwezig_en_de_video_is_onbewerkt_van_duur(self):
        media = ONTWERP / "media"
        for naam, maximum in (("opening.mp4", 6_500_000), ("opening-desktop.mp4", 9_000_000), ("poster.webp", 200_000), ("eind.webp", 300_000), ("badge.webp", 60_000),
                              ("poster-desktop.webp", 250_000), ("eind-desktop.webp", 350_000),
                              ("dorp-kerk.webp", 150_000), ("dorp-ijs.webp", 150_000), ("dorp-brug.webp", 150_000)):
            bestand = media / naam
            self.assertTrue(bestand.exists(), naam)
            self.assertLess(bestand.stat().st_size, maximum, naam)
        self.assertGreater((settings.BASE_DIR / "static/img/designs/kerststad.webp").stat().st_size, 10_000)
        self.assertEqual(sorted(p.name for p in media.glob("*.mp4")), ["opening-desktop.mp4", "opening.mp4"], "twee webvideo's (staand en liggend); de masters horen niet in de repository")
        duur = _duur_mp4(media / "opening.mp4")
        self.assertAlmostEqual(duur, 20.04, delta=0.1, msg="de staande video is de goedgekeurde video van 20,04 s, niet bijgesneden")
        self.assertLess(LUS_START, duur - 3, "de eindloop is ongeveer de laatste vier à vijf seconden")
        html = (ONTWERP / "invitation.html").read_text(encoding="utf-8")
        lus_desktop = float(re.search(r'data-ks-lus-desktop="([\d.]+)"', html).group(1))
        duur_desktop = _duur_mp4(media / "opening-desktop.mp4")
        self.assertGreater(duur_desktop, 8)
        self.assertLess(lus_desktop, duur_desktop - 2.5, "de eindloop van de liggende video begint ruim voor het einde")

    def test_loopstart_staat_op_een_plek_en_wordt_door_script_en_sjabloon_gelezen(self):
        html = (ONTWERP / "invitation.html").read_text(encoding="utf-8")
        self.assertIn(f'data-ks-lus="{LUS_START:g}"', html)
        js = (ONTWERP / "kerststad.js").read_text(encoding="utf-8")
        self.assertIn('"data-ks-lus"', js)
        self.assertIn('"data-ks-lus-desktop"', js)
        self.assertIn("lusStart", js)


class KerststadWeergaveTests(VaylideTestCase):
    def test_demo_toont_badge_klikpunt_hint_skip_en_de_groet_uit_de_studiogegevens(self):
        html = Client().get(DEMO).content.decode()
        for fragment in ("ks-hero", "data-ks-opening", "data-ks-open", 'aria-label="Tik op de V om de kerststad te openen"', "TIK OP DE V OM TE OPENEN",
                         "data-ks-video", "data-ks-skip", "Opening overslaan", "data-ks-replay", 'role="status"', "data-ks-scroll", "data-ks-spiegel"):
            self.assertIn(fragment, html, fragment)
        self.assertIn("Familie Van Dijk", html)             # afzender uit de studiovelden
        self.assertIn("wenst je fijne feestdagen", html)    # tagline uit de studiovelden
        self.assertNotIn("data-cover", html, "geen aparte envelop vóór de opening")
        self.assertNotIn("envelop-cover", html)

    def test_video_is_stil_speelt_niet_vanzelf_en_herhaalt_niet_in_de_html(self):
        html = Client().get(DEMO).content.decode()
        video = re.search(r"<video[^>]*>", html).group(0)
        for woord in ("muted", "playsinline", 'preload="metadata"', "data-ks-bron-desktop=", "data-ks-lus-desktop="):
            self.assertIn(woord, video)
        self.assertIn('<picture class="ks-poster"', html, "het eerste beeld (staand en liggend) staat in een picture, zodat de juiste poster direct laadt")
        self.assertIn("poster-desktop.webp", html)
        for woord in ("autoplay", "loop", "controls"):
            self.assertNotRegex(video, rf"\s{woord}(?:[\s>=]|$)", woord)
        self.assertEqual(html.count("<video"), 1, "één video, hergebruikt voor de eindloop en opnieuw beleven")
        self.assertNotIn("data:video", html)

    def test_de_eindloop_is_een_sprong_naar_loopstart_en_geen_native_loop_of_autoplay_van_de_opening(self):
        js = (ONTWERP / "kerststad.js").read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
        self.assertNotRegex(code, r"\.loop\s*=|\bautoplay\b", "de lus is een eigen sprong met kruisverloop, geen native loop")
        self.assertIn('video.addEventListener("ended", einde)', code)
        self.assertIn("zoekNaar(lusStart)", code)
        # De opening begint alleen vanuit een tik (begin), de eerste keer vanaf 0 s en pas na een tik; een tweede bezoek slaat de opening over.
        self.assertIn('open.addEventListener("click", begin)', code)
        self.assertIn("zoekNaar(0)", code)
        self.assertIn("gezien()", code)
        self.assertIn("onthoud()", code)
        # Minder beweging, stilgezette beweging en de Studio: geen beweging zonder tik.
        self.assertIn("rustig()", code)
        self.assertIn("studioStil", code)

    def test_kleurenkaart_en_de_v_van_het_merk_zitten_in_de_pagina(self):
        html = Client().get(DEMO).content.decode()
        self.assertIn("designs/kerststad/v1/media/badge.webp", html)       # de ronde badge met de officiële VAYLIDE-V, uit de video zelf
        self.assertIn("designs/kerststad/v1/media/poster.webp", html)      # het eerste beeld: extreem ingezoomd op de badge
        self.assertTrue((settings.BASE_DIR / "static/img/merk/vaylide-v.png").exists())

    def test_prototypeteksten_zijn_alleen_een_terugval_als_het_studioveld_leeg_is(self):
        html = _render(content=demo_content("kerststad", "kerst"), kicker="", tagline="", names=[""])
        for fallback in ("Een warme kerst gewenst", "Fijne feestdagen", "Vol warmte, licht en bijzondere momenten."):
            self.assertIn(fallback, html)
        gevuld = _render()
        for fallback in ("Een warme kerst gewenst", "Vol warmte, licht en bijzondere momenten."):
            self.assertNotIn(fallback, gevuld, "studiovelden zijn altijd leidend")

    def test_zonder_datum_geen_kerstdiner_programma_locatie_aftellen_of_aanmelden(self):
        content = demo_content("kerststad", "kerst")
        content["date"] = ""
        html = _render(content=content)
        for weg in ('id="aanmelden"', "data-countdown", "ks-datum", "ks-programma", "ks-plaats", "ks-aftellen", "Kerstdiner"):
            self.assertNotIn(weg, html, weg)
        self.assertIn("ks-brief", html)
        self.assertIn("ks-afsluiting", html)

    def test_met_datum_komen_kerstdiner_programma_aftellen_locatie_en_aanmelden_erbij(self):
        html = Client().get(DEMO).content.decode()
        for erbij in ('id="aanmelden"', "data-countdown", "ks-datum", "ks-programma", "ks-plaats", "ks-aftellen", "Kerstdiner"):
            self.assertIn(erbij, html, erbij)

    def test_zonder_ingevulde_teksten_geen_lege_banden_en_niets_verzonnen(self):
        content = demo_content("kerststad", "kerst")
        content.update({"welcome_text": "", "story": {}, "photos": {}, "date": "", "closing_text": "", "dresscode": {"text": "", "colors": []}, "practical": [],
                        "contact": {"name": "", "phone": "", "email": "", "note": ""}})
        html = _render(content=content)
        for weg in ("ks-brief", "ks-jaar", "ks-momenten", "ks-kleding", "ks-praktisch", "ks-contact", "Ons jaar", "Momenten"):
            self.assertNotIn(weg, html, weg)

    def test_zonder_opening_start_de_kaart_in_de_levende_eindstand(self):
        html = _render(content=demo_content("kerststad", "kerst"), opening_enabled=False)
        self.assertIn('class="ks-hero ks-eind ks-klaar"', html)
        self.assertNotIn("data-ks-opening", html)
        self.assertNotIn("data-ks-open", html.replace("data-ks-opening", ""))
        self.assertNotIn("data-ks-skip", html)

    def test_reduced_motion_en_terugval_staan_in_de_opmaak(self):
        css = (ONTWERP / "style.css").read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion: reduce", css)
        self.assertIn(".ks-eindbeeld", css)
        self.assertNotIn("<style", (ONTWERP / "invitation.html").read_text(encoding="utf-8"), "CSP: geen inline stijlblokken")

    def test_geen_horizontale_overloop_door_vaste_breedtes_in_de_opmaak(self):
        css = (ONTWERP / "style.css").read_text(encoding="utf-8")
        self.assertIn("overflow-x: clip", css)
        for vast in re.findall(r"\bwidth:\s*(\d{4,})px", css):
            self.fail(f"vaste breedte van {vast}px in de opmaak")


class KerststadWenskaartTests(VaylideTestCase):
    def test_als_wenskaart_een_groet_zonder_aanmelden_en_de_speciale_prijs(self):
        content = demo_content("kerststad", "kerst", soort="wenskaart")
        self.assertEqual(card_kind(content, "kerst"), "wenskaart")
        html = _render(content=content)
        for weg in ('id="aanmelden"', "data-countdown", "ks-programma", "ks-plaats", "ks-aftellen", "ks-kleding", "ks-contact"):
            self.assertNotIn(weg, html, weg)
        for blijft in ("ks-hero", "ks-brief", "ks-afsluiting", "data-ks-open"):
            self.assertIn(blijft, html, blijft)
        owner = self.make_customer()
        inv = create_draft(occasion="kerst", template=Template.objects.get(slug="kerststad"), owner=owner, soort="wenskaart")
        quote = compare_packages(inv.draft_content, template_version=inv.template_version)[0]
        self.assertEqual(quote.total_cents, 2495)
        self.assertEqual(quote.total_cents, wenskaart.PRIJS_SPECIAL_CENTS)
        self.assertEqual(quote.package.code, "wenskaart-special")

    def test_een_gewone_uitnodiging_blijft_een_uitnodiging_met_pakketprijzen(self):
        owner = self.make_customer()
        inv = create_draft(occasion="kerst", template=Template.objects.get(slug="kerststad"), owner=owner)
        self.assertEqual(card_kind(inv.draft_content, "kerst"), "uitnodiging")
        quotes = compare_packages(inv.draft_content, template_version=inv.template_version)
        self.assertGreater(len(quotes), 1)
        self.assertNotIn("wenskaart-special", [q.package.code for q in quotes])

    def test_ontwerppagina_en_prijzenpagina_tonen_de_speciale_wenskaartprijs(self):
        html = Client().get("/ontwerpen/kerststad/", {"soort": "wenskaart"}).content.decode()
        self.assertIn('data-soort="wenskaart" aria-current="true"', html)
        self.assertIn("€ 24,95 incl. btw", html)


class ManifestPastInDeDatabaseTests(VaylideTestCase):
    def test_alle_manifestvelden_passen_in_de_databasekolommen(self):
        """SQLite negeert max_length, PostgreSQL (staging en production) niet: een te lange tekst laat de registratie bij het opstarten stilzwijgend mislukken."""
        from catalog.models import Template, TemplateVersion

        grenzen = {veld: Template._meta.get_field(veld).max_length for veld in ("name", "tagline", "style_notes", "slug")}
        for pad in (settings.BASE_DIR / "designs").glob("*/v*/manifest.json"):
            data = json.loads(pad.read_text(encoding="utf-8"))
            for veld, grens in grenzen.items():
                self.assertLessEqual(len(data.get(veld, "")), grens, f"{pad.parent.parent.name}: {veld} is {len(data.get(veld, ''))} tekens (maximaal {grens})")
            renderer = f"{pad.parent.parent.name}/{pad.parent.name}"
            self.assertLessEqual(len(renderer), TemplateVersion._meta.get_field("renderer").max_length)


class KerststadBronkeuzeTests(VaylideTestCase):
    def test_bronkeuze_gebeurt_in_het_script_vooraf_en_wisselt_niet_midden_in_het_afspelen(self):
        js = (ONTWERP / "kerststad.js").read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
        self.assertIn("function kiesBron()", code)
        self.assertIn("(min-aspect-ratio: 6/5)", code)
        # Tijdens de opening of de eindloop wordt nooit van bron gewisseld.
        self.assertRegex(code, r"function kiesBron\(\) \{\s*if \(!video \|\| bezig \|\| lusAan\) return;")
        # Gekozen vóór het afspelen: bij het begin, bij een tik en bij opnieuw beleven.
        for plek in ("function start() {\n    kiesBron();", "lusLos(); kiesBron();" if False else "zetSprong(false); kiesBron();"):
            self.assertIn(plek, code)

    def test_staand_en_liggend_hebben_een_eigen_poster_eindbeeld_en_klikpuntgeometrie(self):
        html = Client().get(DEMO).content.decode()
        for naam in ("poster.webp", "poster-desktop.webp", "eind.webp", "eind-desktop.webp", "opening.mp4", "opening-desktop.mp4"):
            self.assertIn(naam, html, naam)
        css = (ONTWERP / "style.css").read_text(encoding="utf-8")
        self.assertIn('[data-ks-formaat="breed"]', css)
        self.assertIn("--ks-vr: 1.7778", css)
        self.assertIn("--ks-vr: .5625", css)

    def test_de_hero_vult_de_viewport_zonder_kolom_zijgloed_of_rand(self):
        css = (ONTWERP / "style.css").read_text(encoding="utf-8")
        scene = re.search(r"\.ks-scene \{[^}]*\}", css).group(0)
        self.assertIn("inset: 0", scene)
        self.assertNotRegex(scene, r"width:\s*min\(")
        self.assertNotIn("ks-ambient", css)
        self.assertNotRegex(css.split("/* ================================================================ de kaart")[0], r"(?<!backdrop-)filter:\s*blur\(\d{2}", "geen blur-fill naast de video (een lichte scherptediepte op de figuurtjes mag wel)")
        html = (ONTWERP / "invitation.html").read_text(encoding="utf-8")
        self.assertNotIn("ks-ambient", html)


class KerststadLaagTests(VaylideTestCase):
    """De levende laag op de liggende video: de officiële VAYLIDE-V op de gevel en geanimeerde peperkoekfiguurtjes op het plein."""

    def test_de_v_is_het_officiele_merkteken_zonder_woordmerk(self):
        html = Client().get(DEMO).content.decode()
        self.assertIn("data-ks-v", html)
        self.assertRegex(html, r'<img class="ks-v"[^>]*src="/static/img/merk/vaylide-v[^"]*\.png"')
        self.assertNotIn("vaylide-logo", html.split('data-ks-laag')[1].split("ks-open")[0], "alleen de V, geen woordmerk")
        self.assertTrue((settings.BASE_DIR / "static/img/merk/vaylide-v.png").exists())

    def test_er_staan_figuurtjes_die_lopen_zwaaien_en_een_kind(self):
        html = Client().get(DEMO).content.decode()
        gedrag = re.findall(r'data-ks-fig data-pad="[^"]*" data-snelheid="[^"]*" data-gedrag="(\w+)"', html)
        self.assertGreaterEqual(gedrag.count("loop"), 3)
        self.assertEqual(gedrag.count("zwaai"), 1)
        self.assertEqual(gedrag.count("kind"), 1)
        self.assertLessEqual(len(gedrag), 8, "geen chaotische drukte")

    def test_het_spoor_dekt_de_hele_avondscene_van_de_liggende_video(self):
        js = (ONTWERP / "kerststad-spoor.js").read_text(encoding="utf-8")
        data = json.loads(re.search(r"window\.KERSTSTAD_SPOOR = \{van: 12, stap: 2 / 24, ref: 16, gevel: (\[.*?\]\]), plein: (\[.*\]\])\};", js, re.S).expand(r"[\1,\2]"))
        for rij in data:
            self.assertEqual(len(rij), 97, "12 per seconde van 12,0 tot 20,0 s")
            self.assertTrue(all(len(r) == 6 for r in rij))
        duur = _duur_mp4(ONTWERP / "media" / "opening-desktop.mp4")
        self.assertGreaterEqual(12 + 96 * 2 / 24, duur - 0.1)

    def test_de_laag_start_pas_in_de_avond_en_draait_alleen_bij_de_liggende_bron(self):
        js = (ONTWERP / "kerststad.js").read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
        self.assertRegex(code, r"T_V = 1[23]\.\d, T_FIG = 1[3-5]\.\d")
        self.assertIn('formaat !== "breed"', code)
        self.assertIn("nu / 1000", code, "de figuurtjes lopen op hun eigen klok, zodat de beweging bij de sprong van de eindloop doorloopt")
        self.assertIn("opSpiegel", code, "tijdens het kruisverloop schuift de laag mee")
        css = (ONTWERP / "style.css").read_text(encoding="utf-8")
        self.assertIn(".ks-laag { display: none;", css)
        self.assertIn('.ks-hero[data-ks-formaat="breed"] .ks-laag { display: block; }', css)
        self.assertRegex(css, r"prefers-reduced-motion: reduce\) \{ \.ks-laag \.ks-fig__lijf[^}]*\.ks-v \{ animation: none")

    def test_de_mobiele_pagina_houdt_dezelfde_bron_en_de_laag_blijft_verborgen(self):
        css = (ONTWERP / "style.css").read_text(encoding="utf-8")
        self.assertNotRegex(css, r"(?m)^\.ks-laag \{[^}]*display: (block|flex)")
