#!/usr/bin/env python3
"""List available audio input/output devices."""

import pyaudio


def main():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    num_devices = info.get("deviceCount")

    print("Input devices:")
    for i in range(num_devices):
        dev = p.get_device_info_by_host_api_device_index(0, i)
        if dev.get("maxInputChannels") > 0:
            print(f"  [{i}] {dev.get('name')}")

    print("\nOutput devices:")
    for i in range(num_devices):
        dev = p.get_device_info_by_host_api_device_index(0, i)
        if dev.get("maxOutputChannels") > 0:
            print(f"  [{i}] {dev.get('name')}")

    p.terminate()


if __name__ == "__main__":
    main()
