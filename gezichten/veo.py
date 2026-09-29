"""Koppeling met Google Veo (via de Gemini API) voor een korte dansscène uit een startbeeld (image-to-video).

Wordt alleen gebruikt door tools/balzaal/maak_dansvideo.py (door de eigenaar, bewust gestart). De sleutel
(GEMINI_API_KEY) komt uit de omgeving en gaat alleen in een header mee; niet in de URL of de logs.

Kosten (Google, september 2026, per seconde video, incl. geluid): Veo 3.1 $0,40 (720p/1080p), Fast $0,10 (720p)
of $0,12 (1080p), Lite $0,05 (720p) of $0,08 (1080p). Een scène van 8 seconden kost dus $0,40 tot $3,20 per poging.
Alleen een gelukte video wordt berekend.
"""
from __future__ import annotations

import base64
import json
import logging
import time
import urllib.error
import urllib.request

from django.conf import settings

log = logging.getLogger(__name__)

MODELS = {
    "standaard": "veo-3.1-generate-preview",
    "fast": "veo-3.1-fast-generate-preview",
    "lite": "veo-3.1-lite-generate-preview",
}
PRICE_PER_SECOND = {  # dollar, september 2026
    ("standaard", "720p"): 0.40, ("standaard", "1080p"): 0.40,
    ("fast", "720p"): 0.10, ("fast", "1080p"): 0.12,
    ("lite", "720p"): 0.05, ("lite", "1080p"): 0.08,
}

DANCE_PROMPT = (
    "Starting exactly from this image, the bride and groom dance a slow, elegant wedding waltz together in the ballroom. "
    "They hold hands and move naturally; about halfway the groom raises their joined hands and the bride makes one "
    "graceful, full pirouette under his arm, her long blonde hair and the full skirt of her bright white wedding dress "
    "flowing with the turn, then she returns into his arms. The groom in his black tuxedo moves naturally and smiles. "
    "Keep their faces, hair colours, the bright white dress, the black tuxedo, the ballroom, the warm light and the "
    "framing consistent with the image. The camera stays still. Photorealistic, smooth, no text, no logos."
)
NEGATIVE = "distorted faces, extra limbs, extra people, changing clothes, colour change of the dress, text, watermark, fast camera movement"


class VeoError(RuntimeError):
    pass


def estimate(model: str, resolution: str, seconds: int = 8) -> float:
    return round(PRICE_PER_SECOND[(model, resolution)] * seconds, 2)


class VeoClient:
    def __init__(self, api_key: str | None = None, base: str | None = None, sleep=time.sleep):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.base = (base or settings.FACES_API_BASE).rstrip("/")
        self.sleep = sleep
        if not self.api_key:
            raise VeoError("GEMINI_API_KEY ontbreekt (alleen in de omgeving zetten, nooit in Git).")

    def _call(self, url: str, body: dict | None = None) -> dict:
        request = urllib.request.Request(
            url, data=json.dumps(body).encode() if body is not None else None, method="POST" if body is not None else "GET",
            headers={"x-goog-api-key": self.api_key, "Content-Type": "application/json", "User-Agent": "Vaylide/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:300]
            raise VeoError(f"Veo gaf status {exc.code}: {detail}") from exc

    def generate(self, first_frame: bytes, *, model: str = "fast", resolution: str = "720p", seconds: int = 8,
                 prompt: str = DANCE_PROMPT, timeout: int = 900) -> bytes:
        body = {
            "instances": [{"prompt": prompt, "image": {"inlineData": {"mimeType": "image/png", "data": base64.b64encode(first_frame).decode()}}}],
            "parameters": {"aspectRatio": "9:16", "resolution": resolution, "durationSeconds": str(seconds),
                           "personGeneration": "allow_adult", "negativePrompt": NEGATIVE},
        }
        operation = self._call(f"{self.base}/models/{MODELS[model]}:predictLongRunning", body)
        name = operation.get("name")
        if not name:
            raise VeoError("Veo gaf geen taak terug.")
        waited = 0
        while not operation.get("done"):
            if waited >= timeout:
                raise VeoError("Veo was niet op tijd klaar; probeer het later opnieuw.")
            self.sleep(10)
            waited += 10
            operation = self._call(f"{self.base}/{name}")
        if operation.get("error"):
            raise VeoError(f"Veo meldde een fout: {str(operation['error'])[:300]}")
        try:
            uri = operation["response"]["generateVideoResponse"]["generatedSamples"][0]["video"]["uri"]
        except (KeyError, IndexError, TypeError) as exc:
            raise VeoError("Er kwam geen video terug (mogelijk afgewezen door de veiligheidsfilters).") from exc
        request = urllib.request.Request(uri, headers={"x-goog-api-key": self.api_key})
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.read()
