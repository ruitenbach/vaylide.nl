"""De officiële VAYLIDE-collectie: indeling in A, B en C, specials, volgorde, envelope_mode en kaartbeelden (catalog/collectie.py).

De ontwerpen zelf blijven zoals ze zijn: deze tests bewaken alleen de indeling en de bijbehorende gegevens.
"""
import json
from pathlib import Path

from django.conf import settings
from django.test import Client

from catalog import collectie
from catalog.envelop_collectie import MODI, ONTWERP_MODUS
from catalog.models import Template
from catalog.seed import design_manifests

from .helpers import VaylideTestCase

MANIFESTEN = {data["slug"]: data for _, data in design_manifests()}
STATIC_DESIGNS = Path(settings.BASE_DIR) / "static" / "img" / "designs"


class IndelingTests(VaylideTestCase):
    def test_every_design_is_in_exactly_one_group(self):
        indeling = list(collectie.A) + list(collectie.B) + list(collectie.C)
        self.assertEqual(len(indeling), len(set(indeling)), "een ontwerp staat in meer dan één groep")
        self.assertEqual(set(indeling), set(MANIFESTEN), "elk ontwerp in designs/ staat in precies één groep, en andersom")
        self.assertEqual((len(collectie.A), len(collectie.B), len(collectie.C)), (15, 26, 9))
        self.assertEqual(len(MANIFESTEN), 50)

    def test_unknown_design_defaults_to_b_and_c_is_the_only_hidden_group(self):
        self.assertEqual(collectie.groep("nieuw-ontwerp"), "B")
        self.assertTrue(collectie.zichtbaar("nieuw-ontwerp"))
        self.assertFalse(collectie.zichtbaar("kerstman"))
        self.assertTrue(collectie.zichtbaar("winterlicht"))

    def test_specials_match_the_manifests(self):
        in_manifest = {slug for slug, data in MANIFESTEN.items() if data.get("special")}
        self.assertEqual(in_manifest, set(collectie.SPECIALS))
        self.assertTrue({"midnight-emeraude", "rose-royale"} <= in_manifest)
        self.assertNotIn("winterlicht", in_manifest)          # Winterlicht blijft A, maar bewust geen special
        self.assertEqual(collectie.groep("winterlicht"), "A")
        self.assertTrue(set(collectie.SPECIALS) <= set(collectie.A))

    def test_sort_order_is_unique_and_a_comes_before_b(self):
        nummers = [data["sort_order"] for data in MANIFESTEN.values()]
        self.assertEqual(len(nummers), len(set(nummers)), "dubbele sort_order")
        a = [MANIFESTEN[s]["sort_order"] for s in collectie.A]
        b = [MANIFESTEN[s]["sort_order"] for s in collectie.B]
        self.assertLess(max(a), min(b), "alle A-ontwerpen staan vóór alle B-ontwerpen")
        for slug, nummer in collectie.SORT_ORDER.items():
            self.assertEqual(MANIFESTEN[slug]["sort_order"], nummer, slug)

    def test_envelope_mode_is_explicit_and_agrees_with_the_platform_table(self):
        for slug, data in MANIFESTEN.items():
            self.assertIn(data.get("envelope_mode"), MODI, f"{slug}: envelope_mode ontbreekt of is onbekend")
            verwacht = ONTWERP_MODUS.get(slug, "built_in")
            self.assertEqual(data["envelope_mode"], verwacht, f"{slug}: het manifest wijkt af van catalog/envelop_collectie.py")

    def test_every_design_has_a_card_image(self):
        ontbreekt = [slug for slug in MANIFESTEN if not (STATIC_DESIGNS / f"{slug}.webp").exists()]
        self.assertEqual(ontbreekt, [])
        for slug in ("midnight-emeraude", "rose-royale", "golden-noel"):
            self.assertGreater((STATIC_DESIGNS / f"{slug}.webp").stat().st_size, 10_000, slug)

    def test_no_design_was_removed(self):
        for slug in MANIFESTEN:
            map_ = Path(settings.BASE_DIR) / "designs" / slug / "v1"
            self.assertTrue((map_ / "manifest.json").exists(), slug)
            json.loads((map_ / "manifest.json").read_text(encoding="utf-8"))


class CatalogusTests(VaylideTestCase):
    def test_database_follows_the_collection(self):
        self.assertEqual(Template.objects.count(), 50)
        verborgen = set(Template.objects.filter(is_active=False).values_list("slug", flat=True))
        self.assertEqual(verborgen, set(collectie.C))
        specials = set(Template.objects.filter(special=True).values_list("slug", flat=True))
        self.assertEqual(specials, set(collectie.SPECIALS))

    def test_existing_database_is_aligned_once_without_removing_anything(self):
        # Een oude database: alle ontwerpen zichtbaar, de twee nieuwe specials nog gewone kaarten, de oude volgorde.
        Template.objects.update(is_active=True)
        Template.objects.filter(slug__in=("midnight-emeraude", "rose-royale")).update(special=False)
        Template.objects.filter(slug="rose-royale").update(sort_order=8)
        Template.objects.filter(slug="aurora-nocturne").update(sort_order=8)
        Template.objects.filter(slug="golden-noel").update(sort_order=39)
        Template.objects.filter(slug="gloria").update(sort_order=39)
        voor = Template.objects.count()

        aangepast = collectie.pas_toe(Template)

        self.assertEqual(Template.objects.count(), voor)
        self.assertGreater(aangepast, 0)
        self.assertEqual(set(Template.objects.filter(is_active=False).values_list("slug", flat=True)), set(collectie.C))
        self.assertTrue(Template.objects.get(slug="midnight-emeraude").special)
        self.assertTrue(Template.objects.get(slug="rose-royale").special)
        self.assertFalse(Template.objects.get(slug="winterlicht").special)
        sorteer = list(Template.objects.values_list("sort_order", flat=True))
        self.assertEqual(len(sorteer), len(set(sorteer)))
        self.assertEqual(collectie.pas_toe(Template), 0, "tweede keer doet niets")

    def test_owner_choice_in_beheer_survives_sync(self):
        # De eigenaar zet een C-ontwerp in Beheer bewust weer aan: opnieuw inlezen van de ontwerpen zet het niet terug.
        from catalog.seed import sync_designs

        Template.objects.filter(slug="kerstman").update(is_active=True)
        sync_designs()
        self.assertTrue(Template.objects.get(slug="kerstman").is_active)


class WebsiteTests(VaylideTestCase):
    def test_collection_hides_c_designs_but_shows_a_and_b(self):
        html = Client().get("/ontwerpen/").content.decode()
        for slug in ("kerstman", "sneeuwpop", "wolkje", "stipjes", "door-de-jaren", "mijlpaal", "borrel", "congres", "lijnenspel"):
            self.assertNotIn(f"/ontwerpen/{slug}/", html, slug)
        for slug in ("liefde-op-papier", "voor-altijd", "winterlicht", "gloria", "eucalyptus", "eerste-dans"):
            self.assertIn(f"/ontwerpen/{slug}/", html, slug)

    def test_specials_page_lists_the_five_specials_in_order(self):
        html = Client().get("/ontwerpen/", {"categorie": "specials"}).content.decode()
        posities = [html.find(f"/ontwerpen/{slug}/") for slug in ("aurora-nocturne", "midnight-emeraude", "rose-royale", "balzaal")]
        self.assertTrue(all(p >= 0 for p in posities), posities)
        self.assertEqual(posities, sorted(posities))
        self.assertNotIn("/ontwerpen/winterlicht/", html)

    def test_a_hidden_design_keeps_working_for_existing_invitations(self):
        inv = self.published(template="lijnenspel", occasion="bruiloft")
        self.assertFalse(inv.template_version.template.is_active)
        self.assertEqual(Client().get(inv.public_path).status_code, 200)
        self.assertEqual(Client().get("/ontwerpen/lijnenspel/").status_code, 404)

    def test_card_images_of_the_new_specials_are_used(self):
        html = Client().get("/ontwerpen/", {"categorie": "specials"}).content.decode()
        for slug in ("midnight-emeraude", "rose-royale", "golden-noel"):
            self.assertIn(f"img/designs/{slug}.webp", html, slug)
