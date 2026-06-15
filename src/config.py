import os
from dotenv import load_dotenv

load_dotenv()


def get_gemini_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY or GOOGLE_API_KEY not set. "
            "Create a .env file or set the environment variable."
        )
    return key


DEFAULT_MODEL = "models/gemini-3.5-live-translate-preview"

AUDIO_FORMAT = "paInt16"  # pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024
