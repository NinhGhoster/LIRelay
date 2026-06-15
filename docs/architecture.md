# Project Brief: macOS Gemini Live Translate Audio Bridge

## 1. Motivation

The goal of this project is to build a **macOS-based live translation audio bridge** using **Gemini 3.5 Live Translate** or a similar real-time translation model.

The user currently uses **Gemini 3.5 Live Translate through Google AI Studio**, and finds the translation quality very good. However, the current browser/AI Studio workflow is not suitable for real phone calls because of audio routing and feedback-loop problems.

The desired outcome is a system where a user can make or receive a normal call on an iPhone, route that call through a MacBook, and have the MacBook perform live two-way translation:

- The caller speaks their language.
- The Mac app captures the caller's audio.
- Gemini translates the caller's speech into the user's language.
- The user hears only, or primarily, the translated version.
- The user speaks their own language.
- The Mac app translates the user's speech into the caller's language.
- The translated voice is sent back into the call as the Mac's microphone input.

In short:

```text
Caller speech → Mac app → Gemini Live Translate → translated audio to user
User speech   → Mac app → Gemini Live Translate → translated audio to caller
```

The long-term vision is a **universal macOS translation bridge** that can work not only with iPhone calls relayed to macOS, but also with other calling or conferencing software such as FaceTime, Zoom, WhatsApp, Teams, Google Meet, or any app that can use macOS audio input/output devices.

---

## 2. Core Problem Being Solved

### 2.1 Existing Workflow Problem

The current manual setup is roughly:

```text
iPhone regular call + Google AI Studio running on computer
```

This creates several problems:

1. **Audio feedback loop**
   - The computer plays translated audio.
   - The phone microphone picks up the computer's translated audio.
   - Gemini hears that translated audio again and translates it back.
   - The result is a confusing voice-over-voice loop.

2. **No clean separation between call audio and translation audio**
   - The user hears both the original speech and translated speech.
   - The system may re-capture its own output.
   - There is no controlled routing between caller audio, user microphone, Gemini, headphones, and call input.

3. **Fixed target-language behavior**
   - In the sample setup, the target language is fixed.
   - Example: if target is English, Gemini outputs English even if the user speaks English.
   - This is not ideal for two-way translation because each direction needs a different target language.

---

## 3. Proposed Solution Overview

The proposed solution is to build a **local macOS app** that acts as an audio bridge between:

- the iPhone call audio routed through macOS,
- the user's microphone,
- Gemini Live Translate,
- the user's headphones,
- and a virtual microphone sent back into the call.

The app should manage **two independent live translation pipelines**:

### Pipeline A: Caller → User

```text
Caller's voice from iPhone/Mac call
    ↓
Virtual audio input on macOS
    ↓
Gemini Live Translate session
    ↓
Translated audio in user's language
    ↓
User's headphones
```

Example:

```text
French caller → English translation → user hears English
```

### Pipeline B: User → Caller

```text
User microphone
    ↓
Gemini Live Translate session
    ↓
Translated audio in caller's language
    ↓
Virtual microphone on macOS
    ↓
Call app / iPhone call input
```

Example:

```text
User speaks English → French translation → caller hears French
```

This two-session design is preferred over a single dynamic session because it avoids ambiguity and directly solves the fixed target-language problem.

---

## 4. Important Platform Constraints

### 4.1 iOS Native Calls Cannot Be Directly Intercepted

A native iPhone cellular call cannot generally be intercepted or processed directly by a third-party iOS app. The iPhone Phone app and the cellular audio path are sandboxed.

Therefore, building an iPhone app that directly modifies or intercepts native cellular call audio is not the preferred route.

### 4.2 VoIP Is Possible but Not the Preferred Starting Point

A full VoIP app could technically solve the problem by using:

- WebRTC,
- CallKit,
- custom audio routing,
- and Gemini translation.

However, this introduces additional complexity and potential costs:

- VoIP infrastructure,
- account management,
- call routing,
- SIP/WebRTC configuration,
- telecom compliance,
- and possibly paid calling services.

The user prefers avoiding a VoIP-first approach if possible.

### 4.3 macOS Is Better Suited for Audio Bridging

macOS allows more flexible audio routing than iOS. With virtual audio devices such as **BlackHole** or **Loopback**, it is possible to route audio between apps.

This makes a Mac bridge more practical than an iPhone-native solution.

---

## 5. Current Gemini Example Code Context

The starting code is based on Google's Gemini Live API / Live Translate Python example.

The example uses:

- `google-genai`
- `pyaudio`
- `opencv-python`
- `pillow`
- `mss`
- `asyncio`
- Gemini model: `models/gemini-3.5-live-translate-preview`

The sample code configures Gemini with:

```python
CONFIG = types.LiveConnectConfig(
    response_modalities=[
        "AUDIO",
    ],
    media_resolution="MEDIA_RESOLUTION_MEDIUM",
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=0,
        sliding_window=types.SlidingWindow(target_tokens=0),
    ),
    translation_config=types.TranslationConfig(
        target_language_code="en",
        echo_target_language=True,
    ),
)
```

The key current behavior is:

```text
Default microphone → Gemini Live Translate → default speaker/headphones
```

This is a single-pipeline demo. It is useful as a starting point, but it does not yet support a real two-way call bridge.

The official quickstart also warns that the sample uses the system default audio input and output, and that headphones are important to avoid echo or the model interrupting itself.

Relevant documentation / code reference:

- <https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started_LiveAPI.py>
- <https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started_LiveTranslate.py>

---

## 6. Limitations of the Current Example Code

The current example is not yet sufficient because:

1. It uses the **default input device** only.
2. It uses the **default output device** only.
3. It assumes a **single target language**.
4. It has only **one Gemini session**.
5. It mixes all audio into one pipeline.
6. It does not expose device selection.
7. It does not distinguish between:
   - caller audio,
   - user microphone audio,
   - translated audio for the user,
   - translated audio for the caller.
8. It includes camera/screen functionality that is probably unnecessary for this project.

---

## 7. Required System Design

The real app should be designed as an audio-routing and translation system, not merely as a front-end UI for Gemini.

### 7.1 High-Level Architecture

```text
                         ┌──────────────────────┐
                         │ iPhone call on Mac    │
                         │ FaceTime/Continuity   │
                         └──────────┬───────────┘
                                    │ call output
                                    ▼
                         ┌──────────────────────┐
                         │ Virtual Audio Device  │
                         │ BlackHole / Loopback  │
                         └──────────┬───────────┘
                                    │
                                    ▼
        ┌────────────────────────────────────────────────┐
        │             macOS Translator Bridge App         │
        │                                                │
        │  Incoming pipeline:                            │
        │  call audio → Gemini → translated audio         │
        │                         ↓                      │
        │                    headphones                  │
        │                                                │
        │  Outgoing pipeline:                            │
        │  user mic → Gemini → translated audio           │
        │                         ↓                      │
        │                    virtual mic                 │
        └────────────────────────────────────────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Call app microphone   │
                         │ selects virtual mic   │
                         └──────────────────────┘
```

---

## 8. Audio Routing Design

The app must support explicit audio device selection.

### 8.1 Required Audio Devices

The system needs four logical devices:

1. **Incoming call audio input**
   - Source: iPhone call audio routed to macOS.
   - Likely through BlackHole, Loopback, or another virtual audio driver.

2. **User microphone input**
   - Source: MacBook microphone, external microphone, headset microphone, or USB microphone.

3. **User headphone output**
   - Destination: translated caller speech that the user hears.

4. **Virtual microphone output**
   - Destination: translated user speech sent back to the call.
   - The call app should select this virtual device as its microphone.

### 8.2 Audio Separation Requirement

The following must be kept separate:

```text
Caller original audio should not be routed back into the call.
User headphone audio should not be re-captured by Gemini.
Translated outgoing audio should go only to the call's microphone input.
Translated incoming audio should go only to the user's headphones.
```

This separation is essential to avoid feedback loops.

### 8.3 Candidate Audio Routing Tools

#### BlackHole

Good for a free/open-source prototype.

Possible use:

```text
Call output → BlackHole input → translator app
Translator output → BlackHole/virtual mic → call input
```

#### Loopback by Rogue Amoeba

Paid, but easier for complex routing.

Advantages:

- GUI for virtual devices.
- Easier multi-device routing.
- Better debugging.
- Useful during development.

---

## 9. Gemini Session Design

The recommended approach is to use **two Gemini Live Translate sessions**.

### 9.1 Incoming Session

Purpose:

```text
Translate caller speech into user's language.
```

Example config:

```text
Input device: Call Audio Virtual Device
Output device: User Headphones
Target language: English
```

### 9.2 Outgoing Session

Purpose:

```text
Translate user's speech into caller's language.
```

Example config:

```text
Input device: User Microphone
Output device: Virtual Microphone
Target language: French
```

### 9.3 Why Two Sessions?

Using two sessions is cleaner because:

- each direction has a fixed and correct target language,
- it avoids the problem where Gemini always outputs one target language,
- it reduces logic complexity,
- it makes routing easier,
- it maps directly to a real conversation.

Example:

```text
Session 1: French → English
Session 2: English → French
```

---

## 10. Proposed Software Components

The sample `AudioLoop` class should be refactored into smaller components.

### 10.1 AudioDeviceManager

Responsibilities:

- List available input devices.
- List available output devices.
- Detect virtual audio devices.
- Open selected input streams.
- Open selected output streams.
- Handle device reconnects or failures.

Example CLI goal:

```bash
python list_devices.py
```

Expected output:

```text
Input devices:
[0] MacBook Microphone
[1] BlackHole 2ch
[2] USB Microphone

Output devices:
[3] MacBook Speakers
[4] External Headphones
[5] BlackHole 2ch
```

### 10.2 GeminiLiveTranslateSession

Responsibilities:

- Connect to Gemini Live Translate.
- Send PCM audio chunks.
- Receive translated PCM audio chunks.
- Maintain session state.
- Handle reconnection and errors.
- Support configurable target language.

Pseudo-interface:

```python
class GeminiLiveTranslateSession:
    def __init__(self, model, target_language, input_queue, output_queue):
        ...

    async def connect(self):
        ...

    async def send_audio(self):
        ...

    async def receive_audio(self):
        ...
```

### 10.3 TranslationPipeline

Responsibilities:

- Bind one input device to one Gemini session.
- Bind Gemini output to one output device.
- Run audio capture, Gemini streaming, and playback.

Pseudo-interface:

```python
class TranslationPipeline:
    def __init__(
        self,
        name,
        input_device,
        output_device,
        target_language,
        sample_rate_in=16000,
        sample_rate_out=24000,
    ):
        ...
```

### 10.4 BridgeController

Responsibilities:

- Start both pipelines.
- Stop both pipelines.
- Apply language profile.
- Apply device profile.
- Monitor latency and errors.
- Provide a single app-level control layer.

Pseudo-interface:

```python
class BridgeController:
    def __init__(self, incoming_pipeline, outgoing_pipeline):
        ...

    async def start(self):
        ...

    async def stop(self):
        ...
```

### 10.5 Frontend / UI

The UI should allow users to configure:

- my language,
- other person's language,
- incoming call audio input,
- user microphone input,
- headphone output,
- virtual microphone output,
- start/stop,
- mute original audio,
- push-to-talk,
- swap languages,
- latency display,
- connection status.

---

## 11. Suggested User Interface

A minimal UI could contain:

```text
Conversation Profile
--------------------
My language:             English
Other person's language: French

Audio Devices
-------------
Incoming call audio:     BlackHole 2ch
My microphone:           MacBook Microphone
Translation to me:       External Headphones
Translation to caller:   Virtual Microphone

Controls
--------
[Start Bridge]
[Stop Bridge]
[Swap Languages]
[Mute Original Audio]
[Push To Talk]

Status
------
Incoming pipeline: Connected / Listening / Translating / Speaking
Outgoing pipeline: Connected / Listening / Translating / Speaking
Estimated latency: 1.2s
Gemini status: Connected
```

---

## 12. Backend vs Local App Decision

### 12.1 Recommended MVP: Local-Only macOS App

For the user's personal use, the simplest design is:

```text
macOS app → Gemini API directly
```

Advantages:

- simpler architecture,
- lower latency,
- no separate server,
- easier to prototype,
- fewer moving parts.

Disadvantages:

- API key is stored locally,
- not ideal for public distribution,
- harder to manage billing or multi-user access.

### 12.2 Future Option: Backend-Assisted App

For distribution, the architecture could become:

```text
macOS app → backend server → Gemini API
```

Advantages:

- API key hidden from users,
- centralized authentication,
- centralized logging,
- easier billing and quota management,
- easier user management.

Disadvantages:

- more latency,
- more engineering complexity,
- server hosting cost,
- security responsibilities.

Recommendation:

```text
Start local-only. Add backend only if this becomes a product for other users.
```

---

## 13. Implementation Roadmap

### Phase 1: Audio Device Discovery and Routing Proof of Concept

Goal:

```text
Confirm that Python/macOS can read from and write to the required audio devices.
```

Tasks:

1. Install or configure BlackHole or Loopback.
2. Build a script to list input and output devices.
3. Modify the sample code to accept input/output device IDs or names.
4. Confirm that the app can read audio from a selected virtual device.
5. Confirm that the app can write audio to a selected output device.
6. Confirm that the call app can use the virtual output as a microphone input.

Deliverable:

```bash
python list_audio_devices.py
python audio_passthrough.py --input-device "BlackHole 2ch" --output-device "External Headphones"
```

---

### Phase 2: One-Way Translation

Goal:

```text
Translate caller audio into user's language.
```

Pipeline:

```text
Call audio → virtual input → Gemini → headphones
```

Deliverable:

```bash
python one_way_translate.py \
  --input-device "BlackHole 2ch" \
  --output-device "External Headphones" \
  --target-language "en"
```

Success condition:

```text
The user can hear translated caller speech through headphones.
```

---

### Phase 3: Two-Way Translation Bridge

Goal:

```text
Run two independent Gemini translation pipelines at once.
```

Pipeline:

```text
Caller → Gemini session A → User headphones
User   → Gemini session B → Virtual microphone → Caller
```

Deliverable:

```bash
python bridge.py \
  --incoming-input "Call Audio Virtual Device" \
  --incoming-output "External Headphones" \
  --incoming-target "en" \
  --outgoing-input "MacBook Microphone" \
  --outgoing-output "Virtual Microphone" \
  --outgoing-target "fr"
```

Success condition:

```text
The user hears the caller translated into the user's language.
The caller hears the user translated into the caller's language.
No significant feedback loop occurs.
```

---

### Phase 4: Basic UI

Goal:

```text
Replace CLI configuration with a simple macOS UI.
```

Candidate frameworks:

1. SwiftUI
   - Best native macOS experience.
   - Strong long-term option.

2. Electron
   - Easier if using web technologies.
   - Heavier runtime.

3. Tauri
   - Web UI with lighter footprint than Electron.
   - More setup complexity.

4. Python GUI
   - Fastest prototype.
   - Less polished.

Recommendation:

```text
Prototype with Python CLI first.
Then build SwiftUI frontend when the audio routing and Gemini pipeline work.
```

---

### Phase 5: Reliability and UX Improvements

Add:

- push-to-talk,
- mute original audio,
- language swap button,
- audio level meters,
- latency monitor,
- device reconnect handling,
- Gemini reconnect handling,
- manual fallback mode,
- emergency bypass mode,
- conversation profiles,
- auto-start profile for frequent contacts,
- transcript display,
- optional dual subtitles,
- error messages for wrong device routing.

---

## 14. Language Handling Design

The original issue was that Gemini output always follows the fixed target language.

For a two-way bridge, this should be handled by two target languages:

```json
{
  "my_language": "en",
  "other_person_language": "fr",
  "incoming_target_language": "en",
  "outgoing_target_language": "fr"
}
```

Example profiles:

```json
[
  {
    "name": "English ↔ French",
    "my_language": "en",
    "other_person_language": "fr",
    "incoming_target_language": "en",
    "outgoing_target_language": "fr"
  },
  {
    "name": "English ↔ Vietnamese",
    "my_language": "en",
    "other_person_language": "vi",
    "incoming_target_language": "en",
    "outgoing_target_language": "vi"
  },
  {
    "name": "Vietnamese ↔ French",
    "my_language": "vi",
    "other_person_language": "fr",
    "incoming_target_language": "vi",
    "outgoing_target_language": "fr"
  }
]
```

A future version could support automatic language detection per utterance, but the MVP should use explicit two-way language profiles.

---

## 15. Important Technical Risks

### 15.1 Feedback Loop

The biggest risk is accidentally routing translated audio back into the wrong input.

Mitigation:

```text
Use separate virtual devices.
Use headphones.
Do not play incoming translated audio through speakers.
Do not route caller original audio into the call microphone.
Do not route Gemini output back into Gemini input.
```

### 15.2 Latency

Expected latency sources:

- audio buffer size,
- Gemini streaming processing,
- translation generation,
- TTS generation,
- virtual audio routing,
- iPhone/Mac call relay latency,
- network latency.

Expected MVP latency:

```text
Approximately 1–2 seconds if optimized reasonably.
```

The exact latency must be measured during prototyping.

### 15.3 macOS/iPhone Call Routing

The iPhone-on-Mac call path may not always expose all desired input/output routing controls.

Mitigation:

- test with FaceTime/Continuity calls,
- test with normal calls relayed to Mac,
- test with Zoom/Teams/WhatsApp as easier initial targets,
- use Loopback if BlackHole routing is too limited.

### 15.4 Gemini API Behavior

Potential uncertainties:

- preview model stability,
- API quota,
- cost,
- latency,
- streaming behavior,
- support for target-language switching,
- how interruptions are handled,
- how echo-target-language affects output.

Mitigation:

- start from the official sample,
- keep the Gemini layer abstract,
- allow model/config changes from a config file,
- measure behavior empirically.

---

## 16. Suggested Initial File Structure

```text
gemini-mac-translate-bridge/
├── README.md
├── requirements.txt
├── .env.example
├── src/
│   ├── main.py
│   ├── bridge_controller.py
│   ├── audio_device_manager.py
│   ├── audio_stream.py
│   ├── gemini_live_session.py
│   ├── translation_pipeline.py
│   ├── config.py
│   └── logging_utils.py
├── scripts/
│   ├── list_audio_devices.py
│   ├── audio_passthrough.py
│   ├── one_way_translate.py
│   └── bridge_cli.py
├── configs/
│   ├── example_profile_en_fr.json
│   └── example_profile_en_vi.json
└── docs/
    ├── audio_routing.md
    ├── troubleshooting.md
    └── architecture.md
```

---

## 17. Suggested Environment Variables

```bash
GEMINI_API_KEY="your-api-key-here"
```

The original user-provided sample used:

```python
api_key=os.environ.get("GEMINI_API_KEY")
```

Some official Google examples may refer to `GOOGLE_API_KEY`. The implementation should support one or both environment variables for convenience.

---

## 18. Suggested CLI Interfaces

### 18.1 List Devices

```bash
python scripts/list_audio_devices.py
```

### 18.2 One-Way Translation

```bash
python scripts/one_way_translate.py \
  --input-device "BlackHole 2ch" \
  --output-device "External Headphones" \
  --target-language "en"
```

### 18.3 Two-Way Bridge

```bash
python scripts/bridge_cli.py \
  --incoming-input "Call Audio Virtual Device" \
  --incoming-output "External Headphones" \
  --incoming-target "en" \
  --outgoing-input "MacBook Microphone" \
  --outgoing-output "Virtual Microphone" \
  --outgoing-target "fr"
```

---

## 19. Suggested Configuration File

Example `configs/example_profile_en_fr.json`:

```json
{
  "profile_name": "English-French Call Bridge",
  "model": "models/gemini-3.5-live-translate-preview",
  "my_language": "en",
  "other_person_language": "fr",
  "incoming": {
    "input_device": "Call Audio Virtual Device",
    "output_device": "External Headphones",
    "target_language_code": "en"
  },
  "outgoing": {
    "input_device": "MacBook Microphone",
    "output_device": "Virtual Microphone",
    "target_language_code": "fr"
  },
  "audio": {
    "send_sample_rate": 16000,
    "receive_sample_rate": 24000,
    "channels": 1,
    "chunk_size": 1024,
    "format": "paInt16"
  },
  "features": {
    "push_to_talk": false,
    "mute_original_audio": true,
    "show_transcript": true,
    "latency_monitor": true
  }
}
```

---

## 20. Development Priorities

The AI agent or developer continuing this project should prioritize work in this order:

1. **Device selection support**
   - Modify the Gemini sample so input and output devices can be selected explicitly.

2. **Audio passthrough test**
   - Build a simple selected-input to selected-output passthrough script.

3. **One-way Gemini translation**
   - Route selected input into Gemini and selected output to headphones.

4. **Two-way bridge**
   - Run two independent sessions simultaneously.

5. **Feedback prevention**
   - Validate routing and ensure translated audio does not re-enter the wrong input.

6. **Basic UI**
   - Only after the CLI version works.

7. **Packaging**
   - Build a user-friendly macOS application later.

---

## 21. Key Design Decision Summary

| Area | Decision |
|---|---|
| Platform | Start with macOS, not iOS |
| Call type | Use existing iPhone/Mac call routing or any macOS call app |
| VoIP | Avoid for MVP |
| Translation model | Gemini 3.5 Live Translate preview initially |
| App style | Local macOS bridge app |
| Audio routing | Use virtual audio devices such as BlackHole or Loopback |
| Translation direction | Two Gemini sessions, one per direction |
| UI | CLI first, SwiftUI later |
| Backend | Not needed for MVP |
| Main risk | Audio feedback loop |
| First milestone | Selectable audio device input/output |

---

## 22. Practical Example Scenario

### User wants to call a French speaker

User language:

```text
English
```

Caller language:

```text
French
```

Routing:

```text
French caller audio
    → macOS call output
    → virtual audio input
    → Gemini session A target English
    → user headphones

User English microphone
    → Gemini session B target French
    → virtual microphone
    → call app input
    → French caller hears French
```

Expected experience:

- Caller speaks French.
- User hears English.
- User speaks English.
- Caller hears French.
- Original French audio is muted or not emphasized for the user.
- The caller does not hear the English original, only the French translation.

---

## 23. Notes for the Next AI Agent

If another AI agent continues this project, it should understand the following:

1. The project is not simply a web front-end.
2. The main engineering challenge is macOS audio routing.
3. The Gemini sample code is only a starting point.
4. The sample must be refactored for selected audio devices.
5. A real call bridge requires two simultaneous translation directions.
6. A local-only Python prototype is the recommended first implementation.
7. Do not start by building a polished UI.
8. First prove that audio routing works.
9. Then prove one-way translation.
10. Then build the two-way bridge.
11. Only after that should a native macOS UI be built.

---

## 24. Minimal MVP Definition

The MVP is successful if the following works:

```text
1. A call or meeting app outputs audio to a virtual audio device.
2. The Python bridge reads that audio.
3. Gemini translates it into the user's language.
4. The user hears the translated audio in headphones.
5. The user's microphone is translated into the other person's language.
6. The translated speech is sent to a virtual microphone.
7. The call or meeting app uses that virtual microphone as its input.
8. No severe feedback loop occurs.
```

---

## 25. Possible Future Enhancements

Future improvements could include:

- automatic language detection per utterance,
- speaker diarization,
- transcript logging,
- side-by-side subtitles,
- conversation memory,
- terminology glossary,
- medical/legal/business vocabulary modes,
- contact-specific language profiles,
- hotkeys,
- system tray/menu bar app,
- silence detection,
- push-to-talk mode,
- barge-in interruption support,
- adaptive latency tuning,
- support for multiple translation providers,
- fallback STT + translation + TTS pipeline if Gemini Live Translate is unavailable.

---

## 26. Final Recommendation

The recommended project path is:

```text
Build a local macOS audio bridge app using Python first.
Use Gemini Live Translate for the translation engine.
Use BlackHole or Loopback for audio routing.
Implement two independent translation sessions.
Validate routing and latency before investing in UI.
Move to SwiftUI only after the audio/translation core works reliably.
```

This architecture best matches the user's goal: a flexible translation bridge that can work with regular iPhone calls routed through a Mac and potentially with any macOS call/conference software.
