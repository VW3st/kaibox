"""
Chatterbox TTS deployed on Modal — STREAMING version.

Streams audio chunks as they're generated. First chunk arrives in ~0.5s on warm
container, perfect for live agents (Kai, Alex) and Pipecat pipelines.

Deploy:
    modal deploy chatterbox_modal_streaming.py

Test (PowerShell):
    $headers = @{
      "Modal-Key" = "wk-..."
      "Modal-Secret" = "ws-..."
      "Content-Type" = "application/json"
    }
    $body = '{"text": "Hello, this is Kai speaking with streaming audio."}'
    Invoke-WebRequest -Uri "https://YOUR-URL.modal.run" `
      -Method POST -Headers $headers -Body $body -OutFile test.wav
"""

import struct
import modal

app = modal.App("chatterbox-tts-streaming")

# Container image — uses the chatterbox-streaming fork which adds generate_stream()
image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("git", "ffmpeg")
    .pip_install(
        "chatterbox-streaming",   # community fork with streaming support
        "torch",
        "torchaudio",
        "fastapi[standard]",
        "huggingface_hub",
        "requests",
        "numpy",
    )
)

# Persistent volume so model weights only download once
model_cache = modal.Volume.from_name("chatterbox-cache", create_if_missing=True)


def make_streaming_wav_header(sample_rate: int, num_channels: int = 1, bits_per_sample: int = 16) -> bytes:
    """
    Build a WAV header with maximum size markers (0xFFFFFFFF) so audio players
    treat it as a stream of unknown length. Lets the client start playback
    before generation finishes.
    """
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8

    header = b"RIFF"
    header += struct.pack("<I", 0xFFFFFFFF)            # Total size unknown
    header += b"WAVE"
    header += b"fmt "
    header += struct.pack("<I", 16)                    # Subchunk1Size (PCM)
    header += struct.pack("<H", 1)                     # AudioFormat = PCM
    header += struct.pack("<H", num_channels)
    header += struct.pack("<I", sample_rate)
    header += struct.pack("<I", byte_rate)
    header += struct.pack("<H", block_align)
    header += struct.pack("<H", bits_per_sample)
    header += b"data"
    header += struct.pack("<I", 0xFFFFFFFF)            # Data size unknown
    return header


@app.cls(
    image=image,
    gpu="A10G",
    volumes={"/cache": model_cache},
    scaledown_window=300,
    min_containers=0,
)
@modal.concurrent(max_inputs=4)
class ChatterboxStreamingService:

    @modal.enter()
    def load(self):
        """Runs once when container starts. Loads model into VRAM."""
        import os
        os.environ["HF_HOME"] = "/cache/hf"

        from chatterbox.tts import ChatterboxTTS
        print("Loading Chatterbox model...")
        self.model = ChatterboxTTS.from_pretrained(device="cuda")
        print(f"Model loaded. Sample rate: {self.model.sr}")

    @modal.fastapi_endpoint(method="POST", requires_proxy_auth=True)
    def generate(self, request: dict):
        """
        Generate streaming speech.

        POST body:
        {
            "text": "Hello world",                    // required
            "reference_audio_url": "https://...",     // optional - voice cloning
            "exaggeration": 0.5,                      // optional
            "cfg_weight": 0.5,                        // optional
            "chunk_size": 25                          // optional - smaller = lower latency
        }

        Returns: streaming WAV audio (audio/wav)
        """
        import tempfile
        import urllib.request
        import numpy as np
        from fastapi.responses import StreamingResponse

        text = request.get("text", "").strip()
        if not text:
            from fastapi.responses import Response
            return Response(content="'text' field is required", status_code=400)

        kwargs = {
            "exaggeration": request.get("exaggeration", 0.5),
            "cfg_weight": request.get("cfg_weight", 0.5),
            "chunk_size": request.get("chunk_size", 25),
        }

        # Optional voice cloning
        ref_url = request.get("reference_audio_url")
        if ref_url:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                urllib.request.urlretrieve(ref_url, f.name)
                kwargs["audio_prompt_path"] = f.name

        sample_rate = self.model.sr

        def audio_stream():
            # First, send the WAV header so the client knows the format
            yield make_streaming_wav_header(sample_rate)

            # Then stream each generated chunk as raw PCM
            for audio_chunk, metrics in self.model.generate_stream(text, **kwargs):
                # audio_chunk is a torch tensor; convert to int16 PCM bytes
                pcm = audio_chunk.cpu().numpy()
                # Ensure mono and proper shape
                if pcm.ndim > 1:
                    pcm = pcm.squeeze()
                # Float [-1, 1] → int16
                pcm_int16 = np.clip(pcm * 32767, -32768, 32767).astype(np.int16)
                yield pcm_int16.tobytes()

                if metrics and metrics.rtf is not None:
                    print(f"Chunk {metrics.chunk_count}, RTF: {metrics.rtf:.3f}")

        return StreamingResponse(
            audio_stream(),
            media_type="audio/wav",
            headers={"X-Sample-Rate": str(sample_rate)},
        )


# Health check
@app.function(image=image)
@modal.fastapi_endpoint(method="GET")
def health():
    return {"status": "ok", "service": "chatterbox-tts-streaming"}
