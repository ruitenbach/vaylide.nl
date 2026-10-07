"""Kerststad (special, kerst): de goedgekeurde peperkoekstad-video met de gouden V-badge als klikpunt, één keer volledig afgespeeld en daarna een levende eindloop,
met een kaart in dezelfde wereld. De kaart toont alleen wat de klant heeft ingevuld; datum, programma, locatie, aftellen en aanmelden alleen bij een kerstdiner (een datum).
Als wenskaart kost hij de bestaande speciale prijs van € 24,95 incl. btw."""
import json
import re
import struct

from django.conf import settings
from django.template.loader import render_to_string
from django.core.files.uploadedfile import SimpleUploadedFile
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
LUS_START = 16.5


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
        for naam, maximum in (("opening.mp4", 6_500_000), ("opening-desktop.mp4", 30_000_000), ("poster.webp", 200_000), ("eind.webp", 300_000), ("badge.webp", 60_000),
                              ("poster-desktop.webp", 250_000), ("eind-desktop.webp", 350_000),
                              ("dorp-kerk.webp", 150_000), ("dorp-ijs.webp", 150_000), ("dorp-brug.webp", 150_000)):
            bestand = media / naam
            self.assertTrue(bestand.exists(), naam)
            self.assertLess(bestand.stat().st_size, maximum, naam)
        self.assertGreater((settings.BASE_DIR / "static/img/designs/kerststad.webp").stat().st_size, 10_000)
        self.assertEqual(sorted(p.name for p in media.glob("*.mp4")), ["loop-desktop.mp4", "loop.mp4", "opening-desktop.mp4", "opening.mp4"],
                         "per bron een opening en een loopclip; de masters horen niet in de repository")
        for clip, groot in (("loop.mp4", 2_000_000), ("loop-desktop.mp4", 8_000_000)):
            self.assertLess((media / clip).stat().st_size, groot, clip)
            self.assertAlmostEqual(_duur_mp4(media / clip), 20.04 - LUS_START, delta=0.1, msg=f"{clip}: de laatste scène vanaf de overgang tot het einde van de film")
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
        self.assertIn(f'data-ks-lus-desktop="{LUS_START:g}"', html, "de opening gaat bij dezelfde seconde over in de loopclip van beide bronnen")
        js = (ONTWERP / "kerststad.js").read_text(encoding="utf-8")
        self.assertIn('"data-ks-lus"', js)
        self.assertIn('"data-ks-lus-desktop"', js)
        self.assertIn("lusStart", js)


class KerststadWeergaveTests(VaylideTestCase):
    def test_demo_toont_badge_klikpunt_hint_skip_en_de_groet_uit_de_studiogegevens(self):
        html = Client().get(DEMO).content.decode()
        for fragment in ("ks-hero", "data-ks-opening", "data-ks-open", 'aria-label="Tik op de V om de kerststad te openen"', "TIK OP DE V OM TE OPENEN",
                         "data-ks-video", "data-ks-skip", "Opening overslaan", "data-ks-replay", 'role="status"', "data-ks-scroll"):
            self.assertIn(fragment, html, fragment)
        self.assertIn("Familie Van Dijk", html)             # afzender uit de studiovelden
        self.assertIn("wenst je fijne feestdagen", html)    # tagline uit de studiovelden
        self.assertNotIn("data-cover", html, "geen aparte envelop vóór de opening")
        self.assertNotIn("envelop-cover", html)

    def test_video_is_stil_speelt_niet_vanzelf_en_herhaalt_niet_in_de_html(self):
        html = Client().get(DEMO).content.decode()
        video = re.search(r"<video[^>]*>", html).group(0)
        for woord in ("muted", "playsinline", 'preload="none"', "data-ks-bron-desktop=", "data-ks-lus-desktop=", "data-ks-loop=", "data-ks-loop-desktop="):
            self.assertIn(woord, video)
        self.assertIn('<picture class="ks-poster"', html, "het eerste beeld (staand en liggend) staat in een picture, zodat de juiste poster direct laadt")
        self.assertIn("poster-desktop.webp", html)
        for woord in ("autoplay", "loop", "controls"):
            self.assertNotRegex(video, rf"\s{woord}(?:[\s>=]|$)", woord)
        self.assertEqual(html.count("<video"), 1, "één video, hergebruikt voor de eindloop en opnieuw beleven")
        self.assertNotIn("data:video", html)

    def test_de_eindloop_is_een_aparte_clip_in_twee_exemplaren_en_springt_nooit_terug_in_de_opening(self):
        js = (ONTWERP / "kerststad.js").read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
        self.assertNotRegex(code, r"\.loop\s*=\s*true|\bautoplay\b", "geen native loop en geen autoplay")
        # de oude methode (terugspringen in de grote openingsvideo met een stilstaand kruisverloopbeeld) is weg
        for weg in ("springNaarLus", "kanZoeken", "zetSprong", "ks-spiegel", "zoekNaar(lusStart)"):
            self.assertNotIn(weg, code, weg)
        # twee exemplaren van de loopclip, A/B, met een kruisverloop; het volgende exemplaar staat al klaar op zijn eerste beeld
        self.assertIn("function maakLoop()", code)
        self.assertIn("function wissel()", code)
        self.assertRegex(code, r"loopEls = \[0, 1\]\.map")
        self.assertIn("LOOP_FADE = 0.8", code)
        self.assertIn("data-ks-loop", code)
        # de opening gaat bij lusStart over in clip A (requestVideoFrameCallback, met timeupdate als vangnet) en blijft nooit terugspringen
        self.assertIn("meta.mediaTime >= lusStart", code)
        self.assertIn("function startLoop()", code)
        # de opening start alleen vanuit een tik; een tweede bezoek en overslaan laden alleen de kleine clip
        self.assertIn('open.addEventListener("click", begin)', code)
        self.assertIn("gezien()", code)
        self.assertIn("onthoud()", code)
        # minder beweging, stilgezette beweging en de Studio: geen beweging zonder tik
        self.assertIn("rustig()", code)
        self.assertIn("studioStil", code)
        css = (ONTWERP / "style.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.ks-loop \{[^}]*opacity: 0[^}]*transition: opacity \.8s")
        self.assertIn(".ks-loop.ks-boven { z-index: 1; }", css)
        self.assertIn(".ks-loop.ks-zicht { opacity: 1; }", css)

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
        for plek in ("function start() {\n    kiesBron();", "stopLoop(); kiesBron(); maakLoop();"):
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


class OntwerpMuziekTests(VaylideTestCase):
    """Een ontwerp kan in zijn manifest een eigen track aanwijzen ("music"); Kerststad is de eerste. Andere ontwerpen blijven ongewijzigd."""

    def test_kerststad_speelt_zijn_eigen_track_via_de_bestaande_muziekknop(self):
        html = Client().get(DEMO).content.decode()
        self.assertIn("data-music", html)
        audio = re.search(r"<audio[^>]*data-music-audio[^>]*>", html).group(0)
        self.assertIn("designs/kerststad/v1/media/muziek", audio)
        for woord in ("loop", 'preload="none"'):
            self.assertIn(woord, audio)
        self.assertNotRegex(audio, r"\sautoplay\b", "geen autoplay")
        self.assertIn("data-music-volume=", html)
        self.assertNotIn("data-music-synth", html, "het speeldoosje is vervangen door de echte track")
        self.assertIn("data-music-toggle", html)
        self.assertIn("Muziek afspelen", html)
        self.assertTrue((ONTWERP / "media" / "muziek.mp3").exists())
        self.assertLess((ONTWERP / "media" / "muziek.mp3").stat().st_size, 3_000_000)

    def test_het_volume_staat_rustig_en_begint_met_een_zachte_inzet(self):
        volume = float(self.manifest()["music"]["volume"])
        self.assertTrue(0.2 <= volume <= 0.6, volume)
        js = (settings.BASE_DIR / "invitations/static/invitations/invite.js").read_text(encoding="utf-8")
        self.assertIn("zachteInzet", js)
        self.assertIn("data-music-volume", js)

    def manifest(self):
        return json.loads((ONTWERP / "manifest.json").read_text(encoding="utf-8"))

    def test_andere_ontwerpen_houden_het_speeldoosje_en_krijgen_geen_track(self):
        for slug in ("kerstbol", "kerstkaart", "gouden-avond", "winterlicht", "golden-noel"):
            html = Client().get(f"/voorbeeld/{slug}/", {"gelegenheid": "bruiloft" if slug == "gouden-avond" else "kerst"}).content.decode()
            self.assertIn("data-music-synth=", html, slug)
            self.assertNotIn("<audio", html.split('data-music')[1].split("</div>")[0] if "data-music" in html else "", slug)
            self.assertNotIn("data-music-volume", html, slug)
        for pad in (settings.BASE_DIR / "designs").glob("*/v*/manifest.json"):
            if pad.parent.parent.name != "kerststad":
                self.assertNotIn("music", json.loads(pad.read_text(encoding="utf-8")), pad.parent.parent.name)

    def test_eigen_muziek_van_de_klant_gaat_voor_de_track_van_het_ontwerp(self):
        version = Template.objects.get(slug="kerststad").current_version
        content = demo_content("kerststad", "kerst")
        view = build_view(occasion="kerst", content=content, overrides={}, template_version=version, options=RenderOptions(mode="demo", music_synth=True))
        self.assertIn("kerststad/v1/media/muziek", view["music_url"])

        class Resolver:
            def meta(self, uid):
                return {"kind": "audio"}

            def url(self, uid, kind):
                return "/media/klant.mp3"

        content["music"] = {"asset": "abc", "title": "Ons liedje"}
        view = build_view(occasion="kerst", content=content, overrides={}, template_version=version, options=RenderOptions(mode="demo", music_synth=True, resolver=Resolver()))
        self.assertEqual(view["music_url"], "/media/klant.mp3")
        self.assertEqual(view["music_volume"], "")
        self.assertEqual(view["music_title"], "Ons liedje")

    def test_een_wenskaart_toont_nog_steeds_geen_muziek(self):
        html = _render(content=demo_content("kerststad", "kerst", soort="wenskaart"))
        self.assertNotIn("data-music", html)

    def test_het_registreren_werkt_alleen_de_muziek_van_een_bestaande_versie_bij(self):
        from catalog.seed import sync_designs

        version = Template.objects.get(slug="kerststad").current_version
        oud = dict(version.manifest)
        oud.pop("music")
        oud["tagline"] = "oude tagline"
        version.manifest = oud
        version.save(update_fields=["manifest"])
        andere = Template.objects.get(slug="kerstbol").current_version
        voor = dict(andere.manifest)
        sync_designs()
        version.refresh_from_db()
        andere.refresh_from_db()
        self.assertEqual(version.manifest["music"]["src"], "designs/kerststad/v1/media/muziek.mp3")
        self.assertEqual(version.manifest["tagline"], "oude tagline", "de rest van het vastgelegde manifest blijft zoals het was")
        self.assertEqual(andere.manifest, voor)

    def test_de_hotlinkblokkade_dekt_ook_de_muziek_van_een_ontwerp(self):
        client = Client()
        self.assertEqual(client.get("/static/designs/kerststad/v1/media/muziek.mp3", HTTP_REFERER="https://elders.example/").status_code, 403)

    def _live(self, content, resolver=None):
        version = Template.objects.get(slug="kerststad").current_version
        return build_view(occasion="kerst", content=content, overrides={}, template_version=version, options=RenderOptions(mode="live", resolver=resolver))

    def test_de_muziekbron_wordt_expliciet_gevolgd_in_de_echte_kaart(self):
        content = demo_content("kerststad", "kerst")
        content["sections"]["music"] = True
        content["music"] = {"asset": None, "title": "", "source": ""}
        view = self._live(content)
        self.assertEqual((view["music_url"], view["show"]["music"]), ("", False), "zonder gekozen bron speelt de track van het ontwerp niet in een echte kaart")
        content["music"]["source"] = "design"
        view = self._live(content)
        self.assertIn("kerststad/v1/media/muziek", view["music_url"])
        self.assertEqual(view["music_volume"], "0.45")
        self.assertTrue(view["show"]["music"])
        content["music"]["source"] = "none"
        view = self._live(content)
        self.assertEqual((view["music_url"], view["show"]["music"]), ("", False))

    def test_eigen_muziek_gaat_voor_en_blijft_bij_andere_keuzes_bewaard_maar_stil(self):
        class Resolver:
            def meta(self, uid):
                return {"kind": "audio"}

            def url(self, uid, kind):
                return "/media/klant.mp3"

        content = demo_content("kerststad", "kerst")
        content["sections"]["music"] = True
        content["music"] = {"asset": "abc", "title": "Ons liedje", "source": "custom"}
        view = self._live(content, Resolver())
        self.assertEqual((view["music_url"], view["music_volume"], view["music_title"]), ("/media/klant.mp3", "", "Ons liedje"))
        content["music"]["source"] = "design"
        view = self._live(content, Resolver())
        self.assertIn("kerststad/v1/media/muziek", view["music_url"], "bij design speelt de upload niet, ook al is hij bewaard")
        content["music"]["source"] = "none"
        self.assertEqual(self._live(content, Resolver())["music_url"], "")
        content["music"]["source"] = ""      # een eerdere upload zonder gekozen bron speelt zoals altijd
        self.assertEqual(self._live(content, Resolver())["music_url"], "/media/klant.mp3")

    def test_prijs_per_scenario(self):
        from invitations.content import required_features

        content = demo_content("kerststad", "kerst")
        content["sections"]["music"] = True
        for bron, asset, verwacht in (("design", None, set()), ("none", None, set()), ("custom", "abc", {"music"}), ("design", "abc", set()), ("none", "abc", set()), ("", "abc", {"music"})):
            content["music"] = {"asset": asset, "title": "", "source": bron}
            self.assertEqual(required_features(content) & {"music"}, verwacht, (bron, asset))

    def test_nieuw_concept_bij_kerststad_begint_met_de_muziek_van_het_ontwerp(self):
        owner = self.make_customer()
        inv = create_draft(occasion="kerst", template=Template.objects.get(slug="kerststad"), owner=owner)
        self.assertEqual(inv.draft_content["music"]["source"], "design")
        self.assertTrue(inv.draft_content["sections"]["music"])
        andere = create_draft(occasion="kerst", template=Template.objects.get(slug="kerstbol"), owner=owner)
        self.assertEqual(andere.draft_content["music"]["source"], "")
        self.assertFalse(andere.draft_content["sections"]["music"], "een ontwerp zonder eigen track blijft zoals het was")

    def test_studio_stap_toont_drie_keuzes_en_bewaart_de_gekozen_bron(self):
        owner = self.make_customer()
        self.client.force_login(owner)
        inv = create_draft(occasion="kerst", template=Template.objects.get(slug="kerststad"), owner=owner)
        pagina = self.client.get(f"/maken/{inv.uid}/fotos/").content.decode()
        for tekst in ("Muziek van dit ontwerp", "Geen muziek", "Eigen muziek uploaden", "Inbegrepen"):
            self.assertIn(tekst, pagina)
        self.assertRegex(pagina, r'value="design"[^>]*checked')
        for bron in ("none", "design"):
            inv.refresh_from_db()
            self.client.post(f"/maken/{inv.uid}/fotos/", {"rev": inv.draft_rev, "actie": "opslaan", "hero": "", "music_source": bron})
            inv.refresh_from_db()
            self.assertEqual(inv.draft_content["music"]["source"], bron)
            self.assertEqual(inv.draft_content["sections"]["music"], bron == "design")
        inv.refresh_from_db()
        fout = self.client.post(f"/maken/{inv.uid}/fotos/", {"rev": inv.draft_rev, "actie": "opslaan", "hero": "", "music_source": "custom"})
        self.assertContains(fout, "Upload een muziekbestand")
        inv.refresh_from_db()
        self.assertEqual(inv.draft_content["music"]["source"], "design", "een ongeldige keuze wijzigt niets")

    def test_studio_eigen_muziek_uploaden_kost_de_extra_en_de_ontwerptrack_vervalt(self):
        from invitations.content import required_features

        owner = self.make_customer()
        self.client.force_login(owner)
        inv = create_draft(occasion="kerst", template=Template.objects.get(slug="kerststad"), owner=owner)
        mp3 = SimpleUploadedFile("liedje.mp3", b"ID3\x03\x00\x00\x00\x00\x00\x00" + b"\xff\xfb\x90\x00" + b"\x00" * 600, content_type="audio/mpeg")
        r = self.client.post(f"/maken/{inv.uid}/upload/", {"muziek": mp3}, HTTP_ACCEPT="application/json")
        if r.status_code != 200 or not r.json().get("created"):
            self.skipTest(f"synthetische mp3 niet geaccepteerd door de uploadcontrole: {r.content[:120]!r}")
        uid = r.json()["created"][0]["uid"]
        self.assertIn("liedje.mp3", self.client.get(f"/maken/{inv.uid}/fotos/").content.decode())
        inv.refresh_from_db()
        self.client.post(f"/maken/{inv.uid}/fotos/", {"rev": inv.draft_rev, "actie": "opslaan", "hero": "", "music_source": "custom",
                                                      "music_asset": uid, "music_rights": "on", "music_title": "Ons liedje"})
        inv.refresh_from_db()
        self.assertEqual(inv.draft_content["music"], {"asset": uid, "title": "Ons liedje", "source": "custom"})
        self.assertIn("music", required_features(inv.draft_content))
        self.client.post(f"/maken/{inv.uid}/fotos/", {"rev": inv.draft_rev, "actie": "opslaan", "hero": "", "music_source": "design"})
        inv.refresh_from_db()
        self.assertEqual((inv.draft_content["music"]["asset"], inv.draft_content["music"]["source"]), (uid, "design"))
        self.assertNotIn("music", required_features(inv.draft_content))

    def test_een_bestaande_kerstkaart_zonder_track_houdt_de_oude_muziekstap(self):
        owner = self.make_customer()
        self.client.force_login(owner)
        inv = create_draft(occasion="kerst", template=Template.objects.get(slug="kerstbol"), owner=owner)
        pagina = self.client.get(f"/maken/{inv.uid}/fotos/").content.decode()
        self.assertNotIn("music_source", pagina)
        self.assertNotIn("Muziek van dit ontwerp", pagina)
        self.assertIn("Muziek", pagina)
        inv.refresh_from_db()
        self.client.post(f"/maken/{inv.uid}/fotos/", {"rev": inv.draft_rev, "actie": "opslaan", "hero": "", "music_asset": ""})
        inv.refresh_from_db()
        self.assertEqual(inv.draft_content["music"]["source"], "")
        self.assertFalse(inv.draft_content["sections"]["music"])

    def test_wisselen_van_ontwerp_zet_de_bron_goed(self):
        from invitations.content import muziek_bij_ontwerp

        stad = Template.objects.get(slug="kerststad").current_version.manifest
        bol = Template.objects.get(slug="kerstbol").current_version.manifest
        content = {"music": {"asset": None, "title": "", "source": ""}, "sections": {"music": False}}
        muziek_bij_ontwerp(content, stad)
        self.assertEqual((content["music"]["source"], content["sections"]["music"]), ("design", True))
        muziek_bij_ontwerp(content, bol)
        self.assertEqual((content["music"]["source"], content["sections"]["music"]), ("", False))
        eigen = {"music": {"asset": "abc", "title": "", "source": ""}, "sections": {"music": True}}
        muziek_bij_ontwerp(eigen, stad)
        self.assertEqual(eigen["music"], {"asset": "abc", "title": "", "source": ""}, "bestaande klantmuziek wordt nooit vervangen")
