"""
kai_play.py
Streams Chatterbox audio from Modal and plays it on speakers as bytes arrive.

Usage:
    python kai_play.py "Hey what's up chat, this is Kai speaking live."
    python kai_play.py "Whatever you want Kai to say."

First call: ~1.5s before audio starts (warm container)
Cold call:  ~30-60s before audio starts

Edit the CONFIG section below with your URL and tokens.
"""

import sys
import requests
import numpy as np
import sounddevice as sd

# ============================================================
# CONFIG
# ============================================================
URL = "https://agencympire--chatterbox-tts-streaming-chatterboxstreamin-6d5dad.modal.run"
KEY = "REDACTED"
SECRET = "REDACTED"
SAMPLE_RATE = 24000   # Chatterbox native sample rate
# ============================================================


def stream_and_play(text: str, exaggeration: float = 0.7, cfg_weight: float = 0.4):
    headers = {
        "Modal-Key": KEY,
        "Modal-Secret": SECRET,
        "Content-Type": "application/json",
    }
    body = {
        "text": text,
        "exaggeration": exaggeration,
        "cfg_weight": cfg_weight,
        "chunk_size": 25,
    }

    print(f"Sending: {text[:80]}{'...' if len(text) > 80 else ''}")
    print("Waiting for first chunk...")

    # Open a streaming connection
    with requests.post(URL, headers=headers, json=body, stream=True, timeout=120) as r:
        r.raise_for_status()

        # Open the audio output stream
        stream = sd.OutputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=0,           # auto
            latency="low",
        )
        stream.start()

        first_audio = True
        bytes_received = 0
        wav_header_skipped = False
        leftover = b""

        try:
            for raw in r.iter_content(chunk_size=4096):
                if not raw:
                    continue
                bytes_received += len(raw)

                # Skip the 44-byte WAV header on the first chunks
                if not wav_header_skipped:
                    if bytes_received < 44:
                        leftover += raw
                        continue
                    combined = leftover + raw
                    raw = combined[44:]
                    wav_header_skipped = True
                    leftover = b""
                    if not raw:
                        continue

                # Convert raw bytes to int16 samples and play
                # Make sure we have an even number of bytes (int16 = 2 bytes)
                if len(raw) % 2 != 0:
                    leftover = raw[-1:]
                    raw = raw[:-1]
                else:
                    if leftover:
                        raw = leftover + raw
                        leftover = b""

                samples = np.frombuffer(raw, dtype=np.int16)
                stream.write(samples)

                if first_audio:
                    print("Audio playing...")
                    first_audio = False

        finally:
            stream.stop()
            stream.close()

    print("Done.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        text = "Hey what's up chat. This is Kai speaking live from Modal. If you can hear this clearly, the streaming setup works."
    else:
        text = " ".join(sys.argv[1:])
    stream_and_play(text)
