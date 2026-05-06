# Kai Scripting Guide — Chatterbox TTS

Everything you need to know about writing text that makes Kai sound natural, on-brand, and not like a flat AI.

---

## TL;DR — The Three Knobs That Matter

| Parameter | Range | What it does | Kai default |
|---|---|---|---|
| `exaggeration` | 0.0 – 2.0 | Emotional intensity / drama | **0.7** |
| `cfg_weight` | 0.0 – 1.0 | Pacing / how closely it follows the text | **0.4** |
| `chunk_size` | 10 – 50 | Streaming chunk size (lower = faster TTFB) | **25** |

Plus: text formatting (CAPS, punctuation), paralinguistic tags (`[laugh]`, etc.), and voice cloning via reference audio URL.

---

## 1. exaggeration (the drama dial)

Controls how expressive the delivery is.

| Value | What it sounds like | Use for |
|---|---|---|
| 0.3 | Flat, almost monotone | Reading instructions, neutral info |
| 0.5 | Natural conversation | Default speech, replies |
| 0.7 | Lively, engaged | **Kai default** — streamer chatting |
| 0.9 | Hyped, animated | Reactions, hype moments |
| 1.1 | Big, theatrical | Dramatic pauses, punchlines |
| 1.5+ | Unhinged, cartoonish | Comedic effect only, breaks at 2.0 |

**Pairing rule:** when you raise `exaggeration`, lower `cfg_weight` to match. High drama needs slower pacing or it sounds rushed.

---

## 2. cfg_weight (the pacing dial)

Controls how strictly the model follows the literal text and how fast it speaks.

| Value | What it sounds like | Use for |
|---|---|---|
| 0.2 | Very slow, dramatic, lots of breath | Heavy reactions, reveals, "listen up" moments |
| 0.3 | Slow, intentional | Hyped takes paired with high exaggeration |
| 0.4 | Natural conversational speed | **Kai default** |
| 0.5 | Slightly tighter, more "read" | Standard narration |
| 0.7 | Fast, clipped | Quick info dumps, urgency |
| 0.9 | Very fast, robotic | Don't use, sounds AI-y |

**Counter-intuitive but true:** lower `cfg_weight` sounds MORE human, not less. The model takes more liberty with pacing and breath, which is how real people talk.

---

## 3. CAPITALIZATION (free emphasis)

Caps shift word-level stress. Use sparingly or it loses meaning.

| Text | What you hear |
|---|---|
| `that was insane` | flat statement |
| `that was INSANE` | "insane" stressed, voice goes up |
| `THAT WAS INSANE` | shouted, whole phrase emphasized |
| `that WAS insane` | "was" stressed, almost surprised |

**Best practice:** one or two CAPS words per sentence max. Use to mark the beat of a punchline.

```
GOOD: "Yo that was the CRAZIEST play I've ever seen on stream."
BAD:  "YO THAT WAS THE CRAZIEST PLAY I'VE EVER SEEN ON STREAM."
```

---

## 4. Punctuation (controls breath and timing)

| Mark | What it does |
|---|---|
| `.` | Normal sentence end, small pause |
| `,` | Comma pause, breath in |
| `...` | Trailing off, hesitation, longer beat |
| `!` | Energy lift |
| `!!` `!!!` | More energy, but Chatterbox caps at ~2 marks |
| `?` | Rising intonation |
| `--` (em equivalent) | Mid-thought break, abrupt cut |
| `-` (single dash) | Connecting hyphen, no audio effect |

**Tricks:**
- `"Wait... what?"` gives a real pause and surprised reading
- `"I was gonna say -- never mind"` gives a self-interruption
- `"yeah yeah yeah"` actually reads as escalating, the model handles repetition well

---

## 5. Paralinguistic Tags (Turbo only)

These work on the **Chatterbox Turbo** app, not the streaming app currently deployed. To use these you'd hit the Turbo endpoint instead.

| Tag | Sound | Best paired with |
|---|---|---|
| `[laugh]` | Full laugh | Reactions, mid-sentence amusement |
| `[chuckle]` | Soft laugh, exhale | Self-deprecating jokes, dry humor |
| `[cough]` | Cough | Awkward moments, throat clears |
| `[sigh]` | Audible sigh | Frustration, resignation, deep breath |
| `[gasp]` | Sharp intake | Surprise, shock |
| `[breathe]` | Audible inhale/exhale | Thinking pauses, transitions |

### Tag placement matters

Tags work best at natural breath points: end of a clause, between sentences, after a beat.

```
GOOD: "Bro I can't believe that. [laugh] absolutely insane."
BAD:  "Bro I [laugh] can't [laugh] believe that absolutely insane."
```

### Combinations that hit

```
"[gasp] No way! [laugh] You're joking right?"
"[sigh] alright fine, you got me."
"hold on hold on [chuckle] let me think about this."
"[breathe] okay so here's what we're gonna do."
```

---

## 6. Voice Cloning (reference_audio_url)

Pass a public URL to a 5-20 second audio clip and Chatterbox clones it instantly. No training required.

```json
{
  "text": "Hello from Kai",
  "reference_audio_url": "https://yourdomain.com/kai_reference.wav",
  "exaggeration": 0.7,
  "cfg_weight": 0.4
}
```

### What makes a good reference clip

- 10-15 seconds is the sweet spot (5s minimum, 30s max useful)
- Clean audio, no background music or noise
- Single speaker, no overlap
- Natural conversational tone (matching what you want Kai to do)
- WAV or high-quality MP3
- Sample rate doesn't matter, model resamples

### Where to host the reference

- GitHub raw URL (simplest, free, public)
- Cloudflare R2 / S3 bucket
- Any HTTPS-accessible WAV/MP3
- HuggingFace dataset (good for versioning)

### Cloning quality tips

- The clip's emotional tone leaks into all output. A flat reference makes Kai flat. An energetic reference makes Kai energetic.
- If you want Kai to do voices/range, use a reference clip that already has range
- Same reference file = same voice every time (deterministic)

---

## 7. Kai Voice Presets (recommended starting points)

### Default Kai (talking to chat)
```json
{ "exaggeration": 0.7, "cfg_weight": 0.4 }
```

### Hyped Kai (reaction, viral moment)
```json
{ "exaggeration": 0.95, "cfg_weight": 0.3 }
```

### Chill Kai (casual conversation, low energy chat)
```json
{ "exaggeration": 0.55, "cfg_weight": 0.45 }
```

### Storyteller Kai (recap, long-form)
```json
{ "exaggeration": 0.65, "cfg_weight": 0.5 }
```

### Dramatic Kai (reveals, hot takes)
```json
{ "exaggeration": 1.0, "cfg_weight": 0.25 }
```

### Calm Kai (educational segments, ad reads)
```json
{ "exaggeration": 0.5, "cfg_weight": 0.5 }
```

---

## 8. Writing Text That Sounds Real

This is where most AI voices fail. Even with perfect TTS, robotic text reads robotic.

### Rules for Kai's written responses

**Use contractions.** "I'm gonna" not "I am going to". "Don't" not "do not". Real people contract everything.

**Short sentences win.** Two short sentences beat one long one every time. The model also handles pacing better on short sentences.

**Filler words help.** "Yeah" "okay" "so" "I mean" "like" sound natural when scattered in moderation. Don't overdo it.

**Repeat for emphasis, not punctuation.** "no no no" sounds better than "no!!!". "wait wait wait" sounds better than "WAIT!".

**Read it out loud first.** If it doesn't sound like something a real person would say, the model can't save it.

### Example: same idea, three ways

```
ROBOTIC: "Hello viewers, I find this development to be quite interesting."

OKAY: "Yo this is actually pretty interesting."

KAI: "Yo, hold on. This is actually... kinda crazy."
```

The third one has natural breath points, contractions, and the trailing dots create a beat that gives the punchline weight.

---

## 9. What Doesn't Work

- **SSML tags** (`<break>`, `<emphasis>`, `<prosody>`) — Chatterbox isn't SSML-based. They get spoken as words.
- **HTML entities** (`&amp;`, `&quot;`) — same, spoken literally.
- **Phonetic spelling** (like "kuh-RAY-zee") — model just reads it weird, doesn't help.
- **Long single calls (>40 seconds of audio)** — gets truncated. Split into sentences.
- **Multi-speaker text** — no speaker tags. One voice per call. For dialogue, generate each speaker separately and stitch.
- **Background music or sound effects** — TTS only, no SFX support. Mix those in post.
- **Numbers in tricky formats** — "2,500" might read "two thousand five hundred" or "twenty-five hundred". Test both, or write out: "twenty five hundred".
- **Acronyms** — "AI" reads as letters ("ay-eye"), "NASA" reads as a word. If wrong, spell it: "ay eye" or "N A S A".

---

## 10. Streaming Endpoint Cheat Sheet

Your current Modal endpoints:

```
Standard (streaming, no tags):
  https://agencympire--chatterbox-tts-streaming-chatterboxstreamin-6d5dad.modal.run

Turbo (tags work, no streaming yet):
  https://agencympire--chatterbox-turbo-chatterboxturboservice-generate.modal.run
```

### Standard request body (streaming)
```json
{
  "text": "Hey what's up chat",
  "exaggeration": 0.7,
  "cfg_weight": 0.4,
  "chunk_size": 25,
  "reference_audio_url": "https://..."
}
```

### Turbo request body (with tags)
```json
{
  "text": "[laugh] yo that's actually wild",
  "exaggeration": 0.7,
  "cfg_weight": 0.4,
  "reference_audio_url": "https://..."
}
```

---

## 11. Decision Tree: Which Endpoint For What

```
Need [laugh], [sigh], [chuckle] etc?
└─ Yes → Turbo endpoint (no streaming, get full WAV back)
└─ No  → Streaming endpoint (TTFB ~1.5s, plays as it generates)

Need <40s response?
└─ Yes → Single call to either endpoint
└─ No  → Split text into sentences, queue them one by one

Need same voice every time?
└─ Yes → Always pass the same reference_audio_url
└─ No  → Omit reference for default voice (random per call)
```

---

## 12. Quick Test Snippets

Copy-paste these into `kai_play.py` to hear different vibes.

### Hype reaction
```
"YO chat did you SEE that? bro I'm losing my mind right now, that was actually insane!"
```

### Chill explainer
```
"Okay so, real quick. Here's the thing about AI voices. They've gotten really good. Like, really really good."
```

### Surprise
```
"Wait... what? No way that just happened. Did anyone else see that?"
```

### Self-deprecating
```
"Yeah I know I know, I always say that. But this time I actually mean it. Probably."
```

### Storytelling
```
"So check this out. Last week I'm sitting here, just minding my business, and out of nowhere I get a message that completely changed everything."
```

---

That's the full playbook. Bookmark it, iterate, and you'll dial Kai in fast.
