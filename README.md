# Kaibox

Self-hosted Chatterbox TTS for Kai — AI live-streaming influencer persona.

Modal-deployed Chatterbox endpoints (standard, streaming, and Turbo) plus PowerShell + Python clients for testing and live playback.

## Stack

- **Chatterbox TTS** (Resemble AI, MIT license)
- **Modal** for serverless GPU inference (A10G)
- **Python + PowerShell** clients

## Setup

```bash
# 1. Clone
git clone https://github.com/VW3st/kaibox.git
cd kaibox

# 2. Copy env template and fill in your Modal credentials
cp .env.example .env
# Edit .env with your URL + tokens from https://modal.com/settings/proxy-auth-tokens

# 3. Install Python deps
pip install requests sounddevice numpy python-dotenv modal

# 4. Authenticate Modal CLI (one time)
modal setup

# 5. Deploy the apps
modal deploy chatterbox_modal.py
modal deploy chatterbox_modal_streaming.py
modal deploy chatterbox_turbo_modal.py
```

## Usage

### Live playback through speakers
```bash
python kai_play.py "Yo what's up chat, this is Kai live."
```

### Streaming benchmark
```powershell
powershell -ExecutionPolicy Bypass -File .\test_streaming.ps1
```

### Voice variation test (Turbo, with paralinguistic tags)
```powershell
powershell -ExecutionPolicy Bypass -File .\test_voices.ps1
```

## Files

- `chatterbox_modal.py` — basic non-streaming endpoint
- `chatterbox_modal_streaming.py` — streaming endpoint (TTFB ~1.5s)
- `chatterbox_turbo_modal.py` — Turbo with `[laugh] [sigh] [chuckle]` tags
- `kai_play.py` — Python client, live audio playback
- `test_streaming.ps1` — benchmark harness with TTFB and RTF metrics
- `test_voices.ps1` — runs 8 personality variations for A/B
- `load_env.ps1` — loads `.env` for PowerShell scripts
- `KAI_SCRIPTING_GUIDE.md` — full reference for tags, parameters, and prompt craft
- `podcast.txt` — sample 2-min script for streaming tests

## Performance

On Modal A10G, warm container:
- TTFB: ~1.5s
- RTF: 0.94 (faster than realtime)
- Cost: ~$0.03/minute of audio
- Hard cap: ~40 seconds per single call (split longer text)

## Cost Estimate

Kai 5h/day on Modal A10G with `min_containers=1` during streaming hours: **~$175/month** for TTS layer.
