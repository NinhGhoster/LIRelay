#!/usr/bin/env python3
"""Two-way translation bridge: two independent Gemini pipelines."""

import argparse
import asyncio

from src.bridge_controller import BridgeController
from src.logging_utils import setup_logging
from src.translation_pipeline import TranslationPipeline


async def main() -> None:
    parser = argparse.ArgumentParser(description="Two-way Gemini translation bridge")

    inc = parser.add_argument_group("Incoming (caller → you)")
    inc.add_argument("--incoming-input", required=True, help="Incoming call audio device")
    inc.add_argument("--incoming-output", required=True, help="Your headphone device")
    inc.add_argument("--incoming-target", required=True, help="Incoming target language code")

    out = parser.add_argument_group("Outgoing (you → caller)")
    out.add_argument("--outgoing-input", required=True, help="Your microphone device")
    out.add_argument("--outgoing-output", required=True, help="Virtual mic device for call")
    out.add_argument("--outgoing-target", required=True, help="Outgoing target language code")

    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    setup_logging("DEBUG" if args.verbose else "INFO")

    incoming = TranslationPipeline(
        name="incoming",
        input_device=args.incoming_input,
        output_device=args.incoming_output,
        target_language=args.incoming_target,
    )
    outgoing = TranslationPipeline(
        name="outgoing",
        input_device=args.outgoing_input,
        output_device=args.outgoing_output,
        target_language=args.outgoing_target,
    )
    bridge = BridgeController(incoming, outgoing)

    try:
        print("Starting bridge... Press Ctrl+C to stop.")
        await bridge.start()
    except KeyboardInterrupt:
        pass
    finally:
        print("\nShutting down...")
        await bridge.stop()


if __name__ == "__main__":
    asyncio.run(main())
