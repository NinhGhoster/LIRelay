# LIRelay — Live Lingua Relay

[![GitHub](https://img.shields.io/badge/GitHub-NinhGhoster/LIRelay-181717?logo=github)](https://github.com/NinhGhoster/LIRelay)

macOS live translation audio bridge using Gemini Live Translate.

Two independent translation pipelines for real-time two-way conversation:

- **Incoming:** Caller speech → Gemini → translated audio to your headphones
- **Outgoing:** Your speech → Gemini → translated audio to caller via virtual mic

## Quick Start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy and fill in your API key
cp .env.example .env

# List audio devices
PYTHONPATH=. python scripts/list_audio_devices.py

# Audio passthrough test (mic → speakers, no translation)
PYTHONPATH=. python scripts/audio_passthrough.py -i "MacBook" -o "Haut-parleurs"

# One-way translation
PYTHONPATH=. python scripts/one_way_translate.py \
  -i "MacBook Microphone" \
  -o "External Headphones" \
  -l en

# Two-way bridge
PYTHONPATH=. python scripts/bridge_cli.py \
  --incoming-input "BlackHole 2ch" \
  --incoming-output "External Headphones" \
  --incoming-target en \
  --outgoing-input "MacBook Microphone" \
  --outgoing-output "Virtual Microphone" \
  --outgoing-target fr
```

Requires [BlackHole](https://github.com/ExistentialAudio/BlackHole) or [Loopback](https://rogueamoeba.com/loopback/) for virtual audio routing.

## Project Structure

```
src/                  # Core library modules
scripts/              # CLI entry points
configs/              # Language/device profiles
docs/                 # Architecture and troubleshooting
```

## Phases

1. Audio device discovery + passthrough PoC
2. One-way Gemini translation
3. Two-way bridge
4. CLI refinement + SwiftUI frontend

## Development

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run commands with `PYTHONPATH=.` prefix so Python finds the `src/` module:
```bash
PYTHONPATH=. python scripts/list_audio_devices.py
```
