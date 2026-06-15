import asyncio
import logging
from typing import Optional

from google import genai
from google.genai import types

from src.config import DEFAULT_MODEL, get_gemini_api_key

logger = logging.getLogger(__name__)


class GeminiLiveSession:
    def __init__(
        self,
        target_language: str = "en",
        model: str = DEFAULT_MODEL,
        echo_target_language: bool = True,
    ) -> None:
        self._model = model
        self._target_language = target_language
        self._echo_target_language = echo_target_language
        self._client = genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=get_gemini_api_key(),
        )
        self._session: Optional[types.AsyncGenaiSession] = None

    @property
    def session(self) -> Optional[types.AsyncGenaiSession]:
        return self._session

    async def __aenter__(self) -> "GeminiLiveSession":
        await self.connect()
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    def _build_config(self) -> types.LiveConnectConfig:
        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            media_resolution="MEDIA_RESOLUTION_MEDIUM",
            context_window_compression=types.ContextWindowCompressionConfig(
                trigger_tokens=0,
                sliding_window=types.SlidingWindow(target_tokens=0),
            ),
            translation_config=types.TranslationConfig(
                target_language_code=self._target_language,
                echo_target_language=self._echo_target_language,
            ),
        )

    async def connect(self, retries: int = 3) -> None:
        config = self._build_config()
        last_error = None
        for attempt in range(retries):
            try:
                cm = self._client.aio.live.connect(
                    model=self._model,
                    config=config,
                )
                self._session = await cm.__aenter__()
                return
            except Exception as e:
                last_error = e
                logger.warning("Connection attempt %d/%d failed: %s", attempt + 1, retries, e)
                if attempt < retries - 1:
                    await asyncio.sleep(1)
        raise last_error  # type: ignore

    def send_audio(self, data: bytes) -> None:
        if self._session is None:
            raise RuntimeError("Session not connected")
        self._session.send_realtime_input(
            audio=types.Blob(data=data, mime_type="audio/pcm"),
        )

    async def receive(self):
        if self._session is None:
            raise RuntimeError("Session not connected")
        turn = self._session.receive()
        async for response in turn:
            yield response

    async def close(self) -> None:
        if self._session is not None:
            cm = self._session
            self._session = None
            await cm.close()
