# LIRelay — Agent Guide

**Repo:** https://github.com/NinhGhoster/LIRelay

macOS live translation audio bridge using Gemini Live Translate.

## Commands

```bash
# Setup
brew install portaudio
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cp .env.example .env   # fill GEMINI_API_KEY

# All scripts require PYTHONPATH=. (scripts/ is not a package)
PYTHONPATH=. python scripts/list_audio_devices.py
PYTHONPATH=. python scripts/one_way_translate.py -i "MacBook" -o "Haut-parleurs" -l en
PYTHONPATH=. python scripts/run_app.py
PYTHONPATH=. python scripts/bridge_cli.py --incoming-input "BlackHole 2ch" --incoming-output "Haut-parleurs" --incoming-target en
```

## Gemini API Quirks

- Client uses `http_options={"api_version": "v1beta"}` — required for Live Translate
- `client.aio.live.connect()` is an `AsyncGeneratorContextManager` — use `__aenter__`/`__aexit__`, never `await` directly
- `session.send_realtime_input()` is a **coroutine** — must `await`
- **Never** include `media_resolution` in `LiveConnectConfig` — causes 1011 errors on translate model
- Transient `1011 Internal error` on connect is normal — `GeminiLiveSession.connect()` has built-in 3-retry backoff
- `echo_target_language=False` by default; setting `True` causes original-language audio echo alongside translation
- Model: `models/gemini-3.5-live-translate-preview`

## Audio Quirks

- Two sample rates: 16 kHz send (mic→Gemini), 24 kHz receive (Gemini→speakers)
- Device matching is case-insensitive substring — `"MacBook"` matches `"Micro MacBook Pro"`
- `pyaudio` reads via `asyncio.to_thread()` — audio I/O runs off the event loop
- Dual BlackHole routing:
  - **BlackHole 2ch** → incoming pipeline input (capture conference app speakers)
  - **BlackHole 16ch** → outgoing pipeline output (virtual mic for conference app)
  - Conference app: speakers=BlackHole 2ch, mic=BlackHole 16ch
- AirPods appear as **two separate devices** with the same name: input-only and output-only — use `find_device(name, kind="input"/"output")` to disambiguate
- Output channels capped at `min(device.channels_out, 2)` — prevents channel-count mismatch on multi-channel devices (BlackHole 16ch has 16 output channels)
- `open_output_stream()` returns `(stream, actual_channels)` tuple — caller must unpack
- `_mono_to_stereo()` converts Gemini's mono PCM to stereo when output device uses 2 channels

## Architecture

```
src/gemini_live_session.py    — wraps Gemini Live Translate lifecycle (connect/send/receive/close)
src/translation_pipeline.py   — one-direction: capture_task + play_task in asyncio.TaskGroup
src/bridge_controller.py      — runs two TranslationPipelines in parallel (incoming + outgoing)
src/gui_app.py                — customtkinter GUI with BridgeRunner (threads → asyncio.run)
src/audio_device_manager.py   — enumerate/select CoreAudio devices
scripts/                      — CLI + GUI entry points (not a package, hence PYTHONPATH)
```

- `play_task` wraps `self._session.receive()` in a `while self._running` loop — SDK returns a per-turn generator, not a continuous stream
- `BridgeRunner` runs the bridge in a `daemon=True` thread via `asyncio.run()`
- `BridgeRunner.start()` accepts `enable_outgoing` — GUI checkbox "Receive only (no mic)" sets `False`
- Bridge uses a single `asyncio.TaskGroup` with 4-5 tasks (incoming capture/play, outgoing capture/play if enabled, plus poll_stop)
- GUI has "↻ Refresh Devices" button (pyaudio only sees devices connected at init)
- `logging.getLogger("google_genai").setLevel(logging.ERROR)` — suppresses noisy "non-text parts" SDK warning at WARNING level

## Gotchas

- `logging_utils` module exists in `src/` — used by CLI scripts
- `configs/` directory contains reference language profiles, not wired to any CLI
- No test framework, no lint config, no typecheck config
