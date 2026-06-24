import asyncio
import logging
from typing import Tuple

from src.translation_pipeline import TranslationPipeline

logger = logging.getLogger(__name__)


class BridgeController:
    def __init__(
        self,
        incoming_pipeline: TranslationPipeline,
        outgoing_pipeline: TranslationPipeline,
    ) -> None:
        self.incoming = incoming_pipeline
        self.outgoing = outgoing_pipeline

    async def start(self, enable_outgoing: bool = True) -> None:
        await self.incoming.connect()
        if enable_outgoing:
            await self.outgoing.connect()

        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.incoming.capture_task())
            tg.create_task(self.incoming.play_task())
            if enable_outgoing:
                tg.create_task(self.outgoing.capture_task())
                tg.create_task(self.outgoing.play_task())

    async def stop(self) -> None:
        await self.incoming.disconnect()
        await self.outgoing.disconnect()
