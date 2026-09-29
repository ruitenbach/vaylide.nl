"""Koppeling met de beeld-API voor eigen gezichten.

- GeminiProvider: Google Gemini (Nano Banana Pro, model instelbaar met VIERLIEF_FACES_MODEL) via de REST-API. De sleutel
  (GEMINI_API_KEY) staat alleen in de omgeving van de server, nooit in de browser, in Git of in de logs.
- TestProvider: alleen in testmodus. Maakt géén echte bewerking maar zet een duidelijke balk "Testvoorbeeld" op de
  scène, zodat de hele stroom (voortgang, goedkeuren, betalen, publiceren) te testen is zonder kosten.

Beide krijgen de scène (zaal met het standaardpaar) en de foto's van de klant, en geven één afbeelding terug.
"""
from __future__ import annotations

import base64
import io
import json
import logging
import urllib.error
import urllib.request

from django.conf import settings
from PIL import Image, ImageDraw

log = logging.getLogger(__name__)

PROMPT = (
    "Edit the first image, a wedding photo of a bride and groom in a ballroom. The groom stands on the left and wears a "
    "black tuxedo, white shirt and black bow tie; the bride stands on the right and wears a bright white western wedding "
    "dress with a structured bodice and a full skirt. {who} Keep everything else exactly the same: the pose, body shape, "
    "hands, the bright white dress (never gold, champagne or beige), the black tuxedo, the lighting, the ballroom, the "
    "framing and the composition. Make the result natural and photorealistic in the warm light of the scene. Do not add "
    "text, logos or watermarks."
)
WHO = {
    ("bride", "groom"): "Replace only the face and hair of the bride with the woman in the second image, and only the "
                        "face and hair of the groom with the man in the third image.",
    ("bride",): "Replace only the face and hair of the bride with the woman in the second image. Keep the groom unchanged.",
    ("groom",): "Replace only the face and hair of the groom with the man in the second image. Keep the bride unchanged.",
}


HAIR_EN = {"zwart": "black", "bruin": "brown", "blond": "blonde"}


def hair_sentence(hair: dict | None) -> str:
    """De gekozen haarkleuren in de opdracht (alleen kleur; lengte en stijl blijven natuurlijk)."""
    hair = hair or {}
    parts = []
    if hair.get("vrouw") in HAIR_EN:
        parts.append(f"the bride has long {HAIR_EN[hair['vrouw']]} hair in loose waves")
    if hair.get("man") in HAIR_EN:
        parts.append(f"the groom has short {HAIR_EN[hair['man']]} hair")
    return (" In the result, " + " and ".join(parts) + ".") if parts else ""


class FaceProviderError(RuntimeError):
    """Fout met een begrijpelijke melding voor de klant. retryable: later opnieuw proberen kan helpen."""

    def __init__(self, message: str, *, retryable: bool = False, detail: str = ""):
        super().__init__(message)
        self.retryable = retryable
        self.detail = detail


def _jpeg(data: bytes, max_side: int) -> bytes:
    with Image.open(io.BytesIO(data)) as img:
        img = img.convert("RGB")
        img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, "JPEG", quality=92)
        return buffer.getvalue()


def _find_image(node) -> bytes | None:
    """Zoekt de eerste afbeelding (base64) in het antwoord; tolerant voor kleine verschillen in de vorm van het antwoord."""
    if isinstance(node, dict):
        mime = node.get("mime_type") or node.get("mimeType") or ""
        data = node.get("data")
        if isinstance(data, str) and mime.startswith("image/"):
            return base64.b64decode(data)
        for key in ("inline_data", "inlineData", "output_image", "image"):
            if key in node:
                found = _find_image(node[key])
                if found:
                    return found
        for value in node.values():
            found = _find_image(value)
            if found:
                return found
    elif isinstance(node, list):
        for value in node:
            found = _find_image(value)
            if found:
                return found
    return None


class GeminiProvider:
    code = "gemini"

    def __init__(self, api_key: str | None = None, model: str | None = None, base: str | None = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.FACES_MODEL
        self.base = (base or settings.FACES_API_BASE).rstrip("/")
        if not self.api_key:
            raise FaceProviderError("De beeldbewerking is niet ingesteld.")

    def generate(self, scene: bytes, bride: bytes | None, groom: bytes | None, hair: dict | None = None) -> bytes:
        who = tuple(k for k, v in (("bride", bride), ("groom", groom)) if v)
        return self.edit(PROMPT.format(who=WHO[who] + hair_sentence(hair)), [scene] + [p for p in (bride, groom) if p])

    def edit(self, prompt: str, images: list[bytes]) -> bytes:
        """Algemene beeldbewerking: tekstopdracht plus beelden (het eerste is de scène) → één nieuwe afbeelding."""
        parts = [{"type": "text", "text": prompt}]
        for i, image in enumerate(images):
            parts.append({"type": "image", "mime_type": "image/jpeg", "data": base64.b64encode(_jpeg(image, 1672 if i == 0 else 1280)).decode()})
        body = {
            "model": self.model,
            "input": parts,
            "response_format": {"type": "image", "mime_type": "image/png", "aspect_ratio": "9:16", "image_size": "2K"},
        }
        request = urllib.request.Request(
            f"{self.base}/interactions", data=json.dumps(body).encode(), method="POST",
            headers={"x-goog-api-key": self.api_key, "Content-Type": "application/json", "User-Agent": "Vaylide/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:300]
            # Geen sleutel of klantgegevens in de log; alleen status en het begin van de foutmelding.
            log.warning("Beeld-API gaf status %s", exc.code)
            if exc.code in (429, 500, 502, 503, 504):
                raise FaceProviderError("De beeldbewerking is even druk. We proberen het zo opnieuw.", retryable=True, detail=detail) from exc
            if exc.code in (400, 403):
                raise FaceProviderError("Deze foto's konden niet worden gebruikt. Kies een andere, duidelijke foto van het gezicht.", detail=detail) from exc
            raise FaceProviderError("Het maken van het voorbeeld is mislukt. Probeer het later opnieuw.", detail=detail) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise FaceProviderError("De beeldbewerking is nu niet bereikbaar. We proberen het zo opnieuw.", retryable=True) from exc
        image = _find_image(payload)
        if not image:
            raise FaceProviderError("Er kwam geen bruikbaar voorbeeld terug. Kies eventueel andere foto's en probeer het opnieuw.")
        return image


class TestProvider:
    """Alleen in testmodus: nagebootst, zonder echte bewerking en zonder kosten."""

    code = "test"

    def __init__(self):
        if not settings.TEST_MODE:
            raise FaceProviderError("De testbewerking is alleen beschikbaar in testmodus.")

    def generate(self, scene: bytes, bride: bytes | None, groom: bytes | None, hair: dict | None = None) -> bytes:
        with Image.open(io.BytesIO(scene)) as img:
            img = img.convert("RGB")
            draw = ImageDraw.Draw(img)
            h = img.height // 18
            draw.rectangle([0, 0, img.width, h], fill=(122, 90, 46))
            draw.text((16, h // 3), "TESTVOORBEELD - gezichten nagebootst, geen echte bewerking", fill=(255, 255, 255))
            buffer = io.BytesIO()
            img.save(buffer, "PNG")
            return buffer.getvalue()


def get_provider():
    if settings.FACES_PROVIDER == "test":
        return TestProvider()
    if settings.FACES_PROVIDER == "gemini":
        return GeminiProvider()
    raise FaceProviderError("Onbekende beeldbewerking.")


def configured() -> bool:
    """Is er een werkende koppeling ingesteld (zonder de sleutel te tonen)?"""
    if settings.FACES_PROVIDER == "test":
        return settings.TEST_MODE
    return settings.FACES_PROVIDER == "gemini" and bool(settings.GEMINI_API_KEY)
