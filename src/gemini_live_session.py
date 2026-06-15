import asyncio
import logging
from contextlib import _AsyncGeneratorContextManager
from typing import AsyncIterator, Optional

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
        self._cm: Optional[_AsyncGeneratorContextManager] = None

    @property
    def session(self) -> Optional[types.AsyncGenaiSession]:
        return self._session

    def _build_config(self) -> types.LiveConnectConfig:
        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
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
                self._cm = cm
                return
            except Exception as e:
                self._session = None
                self._cm = None
                last_error = e
                logger.warning("Connection attempt %d/%d failed: %s", attempt + 1, retries, e)
                if attempt < retries - 1:
                    await asyncio.sleep(1)
        raise last_error  # type: ignore

    async def send_audio(self, data: bytes) -> None:
        if self._session is None:
            raise RuntimeError("Session not connected")
        await self._session.send_realtime_input(
            audio=types.Blob(data=data, mime_type="audio/pcm"),
        )

    async def receive(self) -> AsyncIterator[types.LiveServerMessage]:
        if self._session is None:
            raise RuntimeError("Session not connected")
        turn = self._session.receive()
        async for response in turn:
            yield response

    async def close(self) -> None:
        cm = self._cm
        self._cm = None
        self._session = None
        if cm is not None:
            try:
                await cm.__aexit__(None, None, None)
            except Exception:
                pass
