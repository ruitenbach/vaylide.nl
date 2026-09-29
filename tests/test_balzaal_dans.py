"""Balzaal: de dans (videolaag alleen met een echte video), haarkleurscènes, de Veo-koppeling (nagebootst) en de
haarkleur bij eigen gezichten."""
import json
from datetime import timedelta
from unittest import mock

from django.conf import settings
from django.template.loader import render_to_string
from django.test import Client, override_settings
from django.utils import timezone

from catalog import paar
from catalog.models import AddOn, Template
from gezichten.models import FaceRequest
from gezichten.provider import TestProvider, hair_sentence
from gezichten.veo import VeoClient, VeoError, estimate
from invitations.demo import demo_content
from invitations.render import RenderOptions, build_view

from .helpers import VaylideTestCase
from .test_gezichten import foto


def _render(content):
    version = Template.objects.get(slug="balzaal").current_version
    view = build_view(occasion="bruiloft", content=content, overrides={}, template_version=version, options=RenderOptions(mode="demo"))
    return view, render_to_string(version.template_path, {"v": view, "rsvp_form": {"client_token": "x", "form_ts": ""}})


class DanceLayerTests(VaylideTestCase):
    def test_no_video_no_dance_and_no_fake(self):
        view, html = _render(demo_content("balzaal", "bruiloft"))
        self.assertNotIn("video", view["paar"])
        self.assertNotIn("<video", html)
        self.assertNotIn("data-bz-dans-knop", html)
        self.assertIn('data-paar="bruin-blond"', html)  # stilstaand paar als laag

    def test_with_a_video_file_the_dance_plays_with_poster_and_button(self):
        with mock.patch("catalog.paar._exists", return_value=True):
            view, html = _render(demo_content("balzaal", "bruiloft"))
        self.assertIn('<video class="bz-zaal bz-dans" muted playsinline loop preload="none"', html)
        self.assertIn("designs/balzaal/v1/video/dans-bruin-blond.mp4", html)
        self.assertIn('poster="/static/designs/balzaal/v1/img/scene-bruin-blond-600.webp"', html)
        knop = html[html.index("data-bz-dans-knop") - 120:html.index("data-bz-dans-knop") + 80]
        self.assertIn("hidden", knop)  # de knop verschijnt pas met JavaScript
        self.assertNotIn('class="bz-laag bz-laag--paar"', html)  # het paar zit in de video
        self.assertNotIn("autoplay", html)

    def test_hair_variant_uses_its_own_scene_and_video(self):
        content = demo_content("balzaal", "bruiloft")
        content["style"]["haar"] = {"man": "blond", "vrouw": "zwart"}
        with mock.patch("catalog.paar._exists", return_value=True):
            view, html = _render(content)
        self.assertIn("scene-blond-zwart-600.webp", html)
        self.assertIn("dans-blond-zwart.mp4", html)

    def test_default_scene_exists_and_eight_variants_are_missing(self):
        for name in ("scene-bruin-blond.webp", "scene-bruin-blond-600.webp"):
            self.assertTrue((settings.BASE_DIR / "designs/balzaal/v1/img" / name).is_file())
        version = Template.objects.get(slug="balzaal").current_version
        self.assertEqual(len(paar.missing(version)), 8)
        self.assertNotIn(("bruin", "blond"), paar.missing(version))

    def test_motion_rules_for_the_dance(self):
        js = (settings.BASE_DIR / "designs/balzaal/v1/balzaal.js").read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion: reduce", js)
        self.assertIn("fx-paused", js)
        self.assertIn("Dans pauzeren", js)


class _Resp:
    def __init__(self, payload=None, raw=None):
        self.payload, self.raw = payload, raw

    def read(self):
        return self.raw if self.raw is not None else json.dumps(self.payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class VeoClientTests(VaylideTestCase):
    @override_settings(GEMINI_API_KEY="nagebootste-sleutel")
    def test_image_to_video_flow(self):
        calls = []

        def fake(request, timeout=0):
            calls.append(request)
            if request.full_url.endswith(":predictLongRunning"):
                return _Resp({"name": "operations/abc"})
            if request.full_url.endswith("operations/abc"):
                done = sum(1 for c in calls if c.full_url.endswith("operations/abc")) >= 2
                return _Resp({"name": "operations/abc", "done": done,
                              "response": {"generateVideoResponse": {"generatedSamples": [{"video": {"uri": "https://video.example/v.mp4"}}]}}})
            return _Resp(raw=b"MP4DATA")

        with mock.patch("gezichten.veo.urllib.request.urlopen", side_effect=fake):
            data = VeoClient(sleep=lambda s: None).generate(b"png", model="fast", resolution="720p")
        self.assertEqual(data, b"MP4DATA")
        first = json.loads(calls[0].data)
        self.assertIn("veo-3.1-fast-generate-preview", calls[0].full_url)
        self.assertEqual(first["parameters"]["aspectRatio"], "9:16")
        self.assertEqual(first["parameters"]["personGeneration"], "allow_adult")
        self.assertIn("pirouette", first["instances"][0]["prompt"])
        self.assertTrue(all(c.headers["X-goog-api-key"] == "nagebootste-sleutel" for c in calls))
        self.assertTrue(all("nagebootste-sleutel" not in c.full_url for c in calls))

    @override_settings(GEMINI_API_KEY="")
    def test_no_key(self):
        with self.assertRaises(VeoError):
            VeoClient()

    def test_cost_estimate(self):
        self.assertEqual(estimate("fast", "720p"), 0.8)
        self.assertEqual(estimate("standaard", "1080p"), 3.2)
        self.assertEqual(estimate("lite", "720p"), 0.4)


@override_settings(FACES_ENABLED=True, FACES_PROVIDER="test")
class FacesHairTests(VaylideTestCase):
    def setUp(self):
        AddOn.objects.create(code="gezichten", name="Eigen gezichten", price_cents=100, feature="gezichten")
        AddOn.objects.create(code="special-balzaal", name="Special Balzaal", price_cents=100, feature="special")
        self.customer = self.make_customer()
        self.inv = self.make_invitation(owner=self.customer, template="balzaal")
        self.client = Client()
        self.client.force_login(self.customer)
        self.url = f"/maken/{self.inv.uid}/gezichten/"

    def upload(self):
        self.client.post(self.url, {"actie": "uploaden", "toestemming": "ja", "foto_vrouw": foto(), "foto_man": foto()})

    def test_hair_choice_goes_into_the_request_and_is_saved_with_the_approved_image(self):
        self.upload()
        page = self.client.get(self.url)
        self.assertContains(page, "Demo in de afgeschermde testomgeving")  # nooit als echte bewerking gepresenteerd
        self.assertContains(page, 'name="haar_man"')
        self.assertContains(page, '<option value="blond" selected>')  # vrouw standaard blond
        real = TestProvider().generate
        with mock.patch("gezichten.provider.TestProvider.generate", side_effect=real) as gen:
            with self.captureOnCommitCallbacks(execute=True):
                self.client.post(self.url, {"actie": "maken", "haar_man": "zwart", "haar_vrouw": "bruin"})
            self.assertEqual(gen.call_args.kwargs["hair"], {"man": "zwart", "vrouw": "bruin"})
        req = FaceRequest.objects.get()
        self.assertEqual((req.hair_man, req.hair_woman), ("zwart", "bruin"))
        self.assertContains(self.client.get(self.url), "Haarkleur: man zwart, vrouw bruin")
        self.client.post(self.url, {"actie": "goedkeuren"})
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.draft_content["style"]["haar"], {"man": "zwart", "vrouw": "bruin"})
        with mock.patch("catalog.paar._exists", return_value=True):
            preview = self.client.get(f"/maken/{self.inv.uid}/voorbeeld/weergave/").content.decode()
        self.assertIn('data-paar="eigen"', preview)
        self.assertNotIn("<video", preview)  # geen dans van het voorbeeldpaar over eigen gezichten heen

    def test_invalid_hair_value_falls_back(self):
        self.upload()
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(self.url, {"actie": "maken", "haar_man": "<b>", "haar_vrouw": "groen"})
        req = FaceRequest.objects.get()
        self.assertEqual((req.hair_man, req.hair_woman), ("bruin", "blond"))

    def test_prompt_sentence(self):
        self.assertIn("long black hair", hair_sentence({"vrouw": "zwart"}))
        self.assertIn("short blonde hair", hair_sentence({"man": "blond"}))
        self.assertEqual(hair_sentence({"man": "paars"}), "")

    def test_unpaid_photos_are_removed_after_30_days(self):
        from core.privacy import apply_retention

        self.upload()
        FaceRequest.objects.update(updated_at=timezone.now() - timedelta(days=31))
        self.assertEqual(apply_retention()["opgeschoonde_gezichtfotos"], 1)
        req = FaceRequest.objects.get()
        self.assertFalse(req.photo_bride or req.photo_groom)
