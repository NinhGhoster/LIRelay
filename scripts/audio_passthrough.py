#!/usr/bin/env python3
"""Audio passthrough: read from input device, write to output device (no translation)."""

import argparse
import asyncio
import logging

import pyaudio

from src.audio_device_manager import AudioDeviceManager
from src.config import CHUNK_SIZE, SEND_SAMPLE_RATE, RECEIVE_SAMPLE_RATE


async def passthrough(input_device: str, output_device: str, duration: int) -> None:
    mgr = AudioDeviceManager()
    try:
        in_dev = mgr.find_device(input_device)
        if not in_dev:
            print(f"Input device not found: {input_device}")
            return
        out_dev = mgr.find_device(output_device)
        if not out_dev:
            print(f"Output device not found: {output_device}")
            return

        print(f"Input:  [{in_dev.index}] {in_dev.name}")
        print(f"Output: [{out_dev.index}] {out_dev.name}")
        print(f"Passthrough running for {duration}s... Press Ctrl+C to stop.")

        in_stream = mgr.open_input_stream(in_dev.index, SEND_SAMPLE_RATE, CHUNK_SIZE)
        out_stream = mgr.open_output_stream(out_dev.index, RECEIVE_SAMPLE_RATE, CHUNK_SIZE)

        start = asyncio.get_event_loop().time()
        while True:
            data = await asyncio.to_thread(in_stream.read, CHUNK_SIZE, exception_on_overflow=False)
            await asyncio.to_thread(out_stream.write, data)
            if duration > 0 and (asyncio.get_event_loop().time() - start) > duration:
                break

        in_stream.close()
        out_stream.close()
    finally:
        mgr.terminate()


def main() -> None:
    parser = argparse.ArgumentParser(description="Audio passthrough — input → output")
    parser.add_argument("--input-device", "-i", required=True, help="Input device name or index")
    parser.add_argument("--output-device", "-o", required=True, help="Output device name or index")
    parser.add_argument("--duration", "-d", type=int, default=0, help="Duration in seconds (0 = infinite)")
    args = parser.parse_args()
    try:
        asyncio.run(passthrough(args.input_device, args.output_device, args.duration))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
