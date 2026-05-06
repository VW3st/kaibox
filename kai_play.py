"""
kai_play.py
Streams Chatterbox audio from Modal and plays it on speakers as bytes arrive.

Setup:
    pip install requests sounddevice numpy python-dotenv
    Copy .env.example to .env and fill in your tokens.

Usage:
    python kai_play.py "Hey what's up chat, this is Kai speaking live."
    python kai_play.py
"""

import os
import sys
import requests
import numpy as np
import sounddevice as sd
from dotenv import load_dotenv

load_dotenv()

URL = os.environ["MODAL_URL_STREAMING"]
KEY = os.environ["MODAL_KEY"]
SECRET = os.environ["MODAL_SECRET"]
SAMPLE_RATE = 24000


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

    with requests.post(URL, headers=headers, json=body, stream=True, timeout=120) as r:
        r.raise_for_status()

        stream = sd.OutputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=0,
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

                # Make sure we have an even number of bytes (int16 = 2 bytes)
                if len(raw) % 2 != 0:
                    leftover_byte = raw[-1:]
                    raw = raw[:-1]
                    if leftover:
                        raw = leftover + raw
                    leftover = leftover_byte
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
