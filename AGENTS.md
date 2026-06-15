# LiRelay — Agent Guide

## Project

Live Lingua Relay — macOS live translation audio bridge using Gemini Live Translate.

**Repo:** https://github.com/NinhGhoster/LIRelay

## Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Key Files

| File | Purpose |
|------|---------|
| `src/audio_device_manager.py` | Enumerate/select CoreAudio devices |
| `src/gemini_live_session.py` | Wraps Gemini Live Translate API |
| `src/translation_pipeline.py` | Input device → Gemini → output device |
| `src/bridge_controller.py` | Orchestrates two pipelines |
| `scripts/list_audio_devices.py` | CLI device scanner |
| `scripts/one_way_translate.py` | Single-direction translation |
| `scripts/bridge_cli.py` | Full duplex bridge |
| `configs/` | JSON language profiles |

## Architecture

Two independent Gemini Live Translate sessions:

- **Incoming:** Caller audio → BlackHole → Gemini(target=my_lang) → Headphones
- **Outgoing:** User mic → Gemini(target=other_lang) → Virtual mic → Call app

## Code Style

- 4 spaces, no tabs, ~100 char lines
- snake_case (funcs/vars), CamelCase (classes), ALL_CAPS (constants)
- Type hints via `typing` module
- Imports: stdlib → third-party → local
- asyncio throughout

## Key Design Decisions

- CLI-first, SwiftUI later
- Two sessions (not one dynamic session)
- BlackHole/Loopback for virtual audio
- Local-only (no backend server for MVP)
