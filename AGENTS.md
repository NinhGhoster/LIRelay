# LIRelay — Agent Guide

**Repo:** https://github.com/NinhGhoster/LIRelay

macOS live translation audio bridge using Gemini Live Translate.

## Commands

```bash
# Setup (portaudio brew prerequisite for pyaudio)
brew install portaudio
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cp .env.example .env   # fill GEMINI_API_KEY

# All scripts require PYTHONPATH=. (scripts/ is not a package)
PYTHONPATH=. python scripts/list_audio_devices.py
PYTHONPATH=. python scripts/audio_passthrough.py -i "MacBook" -o "Haut-parleurs"
PYTHONPATH=. python scripts/one_way_translate.py -i "MacBook" -o "Haut-parleurs" -l en

# Two-way bridge (needs BlackHole installed)
PYTHONPATH=. python scripts/bridge_cli.py \
  --incoming-input "BlackHole 2ch" --incoming-output "Haut-parleurs" --incoming-target en \
  --outgoing-input "MacBook Microphone" --outgoing-output "BlackHole 2ch" --outgoing-target fr
```

## Gemini API Quirks

- Client uses `http_options={"api_version": "v1beta"}` — required for Live Translate
- `client.aio.live.connect()` is an **async context manager** — use `__aenter__`/`__aexit__`, not direct `await`
- `session.send_realtime_input()` is a **coroutine** — must `await`
- **Do not** include `media_resolution` in `LiveConnectConfig` — causes 1011 errors on the translate model
- Transient `1011 Internal error` on connect is normal — retry with backoff (3 retries built into `GeminiLiveSession.connect()`)
- Model: `models/gemini-3.5-live-translate-preview`

## Audio Quirks

- Two sample rates: 16 kHz send (mic→Gemini), 24 kHz receive (Gemini→speakers)
- Device matching is case-insensitive substring — `"MacBook"` matches `"Micro MacBook Pro"`
- `pyaudio` reads block via `asyncio.to_thread()` — audio I/O is off the event loop
- BlackHole virtual audio: `brew install --cask blackhole-2ch` + sudo + reboot/audio restart
- Device names differ per machine — always run `list_audio_devices.py` first

## Architecture

```
src/audio_device_manager.py   — enumerate/select CoreAudio devices
src/gemini_live_session.py    — wraps Gemini Live Translate lifecycle
src/translation_pipeline.py   — one-direction: device → Gemini → device
src/bridge_controller.py      — runs two pipelines in parallel
scripts/                      — CLI entry points (not package, hence PYTHONPATH)
configs/                      — language profiles (reference only, not wired to CLI)
```

Two independent `TranslationPipeline`s in a single `asyncio.TaskGroup`. No tests, no typecheck/lint config exist.
