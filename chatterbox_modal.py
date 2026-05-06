"""
Chatterbox TTS deployed on Modal.

Deploy:
    modal deploy chatterbox_modal.py

Test:
    curl -X POST https://YOUR-WORKSPACE--chatterbox-tts-generate.modal.run \
      -H "Modal-Key: ak-..." -H "Modal-Secret: as-..." \
      -H "Content-Type: application/json" \
      -d '{"text": "Hello, this is Kai speaking."}' \
      --output test.wav
"""

import io
import modal

app = modal.App("chatterbox-tts")

# Container image: Python 3.10 + CUDA + Chatterbox
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

# Persistent volume so model weights (~2GB) only download once, not on every cold start
model_cache = modal.Volume.from_name("chatterbox-cache", create_if_missing=True)


@app.cls(
    image=image,
    gpu="A10G",
    volumes={"/cache": model_cache},
    scaledown_window=300,   # keep container warm for 5 mins after last request
    min_containers=0,       # 0 = scale to zero (cheapest). Set to 1 for zero cold starts.
)
@modal.concurrent(max_inputs=4)
class ChatterboxService:

    @modal.enter()
    def load(self):
        """Runs once when container starts. Loads model into VRAM."""
        import os
        os.environ["HF_HOME"] = "/cache/hf"

        from chatterbox.tts import ChatterboxTTS
        print("Loading Chatterbox model...")
        self.model = ChatterboxTTS.from_pretrained(device="cuda")
        print("Model loaded and ready.")

    @modal.fastapi_endpoint(method="POST", requires_proxy_auth=True)
    def generate(self, request: dict):
        """
        Generate speech from text, with optional voice cloning.

        POST body:
        {
            "text": "Hello world",                        // required
            "reference_audio_url": "https://...",         // optional - for voice cloning
            "exaggeration": 0.5,                          // optional - 0.0 to 1.0+
            "cfg_weight": 0.5                             // optional - prosody control
        }

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

        # Optional voice cloning via reference audio URL
        ref_url = request.get("reference_audio_url")
        if ref_url:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                urllib.request.urlretrieve(ref_url, f.name)
                kwargs["audio_prompt_path"] = f.name

        # Generate
        wav = self.model.generate(text, **kwargs)

        # Encode as WAV bytes
        buf = io.BytesIO()
        ta.save(buf, wav, self.model.sr, format="wav")
        buf.seek(0)

        return Response(content=buf.read(), media_type="audio/wav")


# Optional: simple health check endpoint
@app.function(image=image)
@modal.fastapi_endpoint(method="GET")
def health():
    return {"status": "ok", "service": "chatterbox-tts"}
