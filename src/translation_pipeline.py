import asyncio
import logging
from typing import Optional

import pyaudio

from src.audio_device_manager import AudioDeviceManager
from src.config import CHUNK_SIZE, RECEIVE_SAMPLE_RATE, SEND_SAMPLE_RATE
from src.gemini_live_session import GeminiLiveSession

logger = logging.getLogger(__name__)


class TranslationPipeline:
    def __init__(
        self,
        name: str,
        input_device: str,
        output_device: str,
        target_language: str,
    ) -> None:
        self.name = name
        self.input_device = input_device
        self.output_device = output_device
        self.target_language = target_language

        self._mgr = AudioDeviceManager()
        self._session = GeminiLiveSession(target_language=target_language)
        self._in_dev = None
        self._out_dev = None
        self._running = False

    async def connect(self) -> None:
        self._in_dev = self._mgr.find_device(self.input_device)
        if not self._in_dev:
            raise ValueError(f"Input device not found: {self.input_device}")
        self._out_dev = self._mgr.find_device(self.output_device)
        if not self._out_dev:
            raise ValueError(f"Output device not found: {self.output_device}")

        logger.info("[%s] Connecting to Gemini...", self.name)
        await self._session.connect()
        logger.info("[%s] Connected.", self.name)
        self._running = True

    async def capture_task(self) -> None:
        assert self._in_dev is not None
        in_stream = self._mgr.open_input_stream(self._in_dev.index, SEND_SAMPLE_RATE, CHUNK_SIZE)
        try:
            while self._running:
                data = await asyncio.to_thread(in_stream.read, CHUNK_SIZE, exception_on_overflow=False)
                await self._session.send_audio(data)
        finally:
            in_stream.close()

    async def play_task(self) -> None:
        assert self._out_dev is not None
        out_stream = self._mgr.open_output_stream(self._out_dev.index, RECEIVE_SAMPLE_RATE, CHUNK_SIZE)
        try:
            async for response in self._session.receive():
                if not self._running:
                    break
                if data := response.data:
                    await asyncio.to_thread(out_stream.write, data)
                if text := response.text:
                    print(f"\n[{self.name}] {text}")
        finally:
            out_stream.close()

    async def disconnect(self) -> None:
        self._running = False
        await self._session.close()
        self._mgr.terminate()

    async def run(self) -> None:
        await self.connect()
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.capture_task())
            tg.create_task(self.play_task())
