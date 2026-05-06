"""
Chatterbox TURBO deployed on Modal.

Why Turbo over standard Chatterbox:
  - Native paralinguistic tags: [laugh] [chuckle] [cough] [sigh] [gasp] [breathe]
  - 350M params (vs 0.5B), 1-step decoder, sub-200ms inference
  - Built specifically for live voice agents and streamer-style content

Deploy:
    modal deploy chatterbox_turbo_modal.py

Test with the included test_voices.ps1 script.
"""

import io
import modal

app = modal.App("chatterbox-turbo")

# Container image — uses the official chatterbox-tts package (which ships Turbo)
image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("git", "ffmpeg")
    .pip_install(
        "chatterbox-tts",
        "torch",
        "torchaudio",
        "fastapi[standard]",
        "huggingface_hub",
        "requests",
    )
)

# Persistent volume so model weights only download once
model_cache = modal.Volume.from_name("chatterbox-cache", create_if_missing=True)


@app.cls(
    image=image,
    gpu="A10G",
    volumes={"/cache": model_cache},
    scaledown_window=300,
    min_containers=0,
)
@modal.concurrent(max_inputs=4)
class ChatterboxTurboService:

    @modal.enter()
    def load(self):
        """Runs once when container starts. Loads Turbo into VRAM."""
        import os
        os.environ["HF_HOME"] = "/cache/hf"

        from chatterbox.tts_turbo import ChatterboxTurboTTS
        print("Loading Chatterbox Turbo...")
        self.model = ChatterboxTurboTTS.from_pretrained(device="cuda")
        print(f"Turbo loaded. Sample rate: {self.model.sr}")

    @modal.fastapi_endpoint(method="POST", requires_proxy_auth=True)
    def generate(self, request: dict):
        """
        POST body:
        {
            "text": "Hello [laugh] this is fun!",         // required
            "reference_audio_url": "https://...",         // optional - voice clone
            "exaggeration": 0.5,                          // 0.0-2.0
            "cfg_weight": 0.5                             // 0.0-1.0
        }

        Tags supported in text:
          [laugh] [chuckle] [cough] [sigh] [gasp] [breathe]

        CAPITALIZATION shifts emphasis. Use it.

        Returns: WAV audio (audio/wav)
        """
        import tempfile
        import urllib.request
        import torchaudio as ta
        from fastapi.responses import Response

        text = request.get("text", "").strip()
        if not text:
            return Response(content="'text' field is required", status_code=400)

        kwargs = {
            "exaggeration": request.get("exaggeration", 0.5),
            "cfg_weight": request.get("cfg_weight", 0.5),
        }

        ref_url = request.get("reference_audio_url")
        if ref_url:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                urllib.request.urlretrieve(ref_url, f.name)
                kwargs["audio_prompt_path"] = f.name

        wav = self.model.generate(text, **kwargs)

        buf = io.BytesIO()
        ta.save(buf, wav, self.model.sr, format="wav")
        buf.seek(0)

        return Response(content=buf.read(), media_type="audio/wav")


@app.function(image=image)
@modal.fastapi_endpoint(method="GET")
def health():
    return {"status": "ok", "service": "chatterbox-turbo"}
