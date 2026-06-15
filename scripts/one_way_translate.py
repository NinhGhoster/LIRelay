#!/usr/bin/env python3
"""One-way translation: input device → Gemini → output device."""

import argparse
import asyncio
import logging

from src.logging_utils import setup_logging
from src.translation_pipeline import TranslationPipeline


async def main() -> None:
    parser = argparse.ArgumentParser(description="One-way Gemini translation")
    parser.add_argument("--input-device", "-i", required=True, help="Input device name or index")
    parser.add_argument("--output-device", "-o", required=True, help="Output device name or index")
    parser.add_argument("--target-language", "-l", required=True, help="Target language code (e.g. en, fr, vi)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    setup_logging("DEBUG" if args.verbose else "INFO")

    pipeline = TranslationPipeline(
        name="one-way",
        input_device=args.input_device,
        output_device=args.output_device,
        target_language=args.target_language,
    )
    try:
        await pipeline.run()
    except KeyboardInterrupt:
        pass
    finally:
        await pipeline.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
