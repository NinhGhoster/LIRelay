from typing import Dict, List, Optional, Tuple

import pyaudio


class AudioDeviceInfo:
    def __init__(self, index: int, name: str, channels_in: int, channels_out: int, default_sample_rate: float):
        self.index = index
        self.name = name
        self.channels_in = channels_in
        self.channels_out = channels_out
        self.default_sample_rate = default_sample_rate

    def __repr__(self) -> str:
        return f"AudioDeviceInfo[{self.index}]: {self.name}"


class AudioDeviceManager:
    def __init__(self) -> None:
        self._pya = pyaudio.PyAudio()

    def terminate(self) -> None:
        self._pya.terminate()

    def list_input_devices(self) -> List[AudioDeviceInfo]:
        return self._list_devices(max_input_channels=lambda c: c > 0)

    def list_output_devices(self) -> List[AudioDeviceInfo]:
        return self._list_devices(max_output_channels=lambda c: c > 0)

    def list_all_devices(self) -> Tuple[List[AudioDeviceInfo], List[AudioDeviceInfo]]:
        return self.list_input_devices(), self.list_output_devices()

    def _list_devices(
        self,
        max_input_channels=lambda c: True,
        max_output_channels=lambda c: True,
    ) -> List[AudioDeviceInfo]:
        devices: List[AudioDeviceInfo] = []
        for i in range(self._pya.get_device_count()):
            info = self._pya.get_device_info_by_index(i)
            if max_input_channels(info["maxInputChannels"]) or max_output_channels(info["maxOutputChannels"]):
                devices.append(
                    AudioDeviceInfo(
                        index=i,
                        name=info["name"],
                        channels_in=info["maxInputChannels"],
                        channels_out=info["maxOutputChannels"],
                        default_sample_rate=info["defaultSampleRate"],
                    )
                )
        return devices

    def find_device(self, name_or_index: str) -> Optional[AudioDeviceInfo]:
        try:
            index = int(name_or_index)
            info = self._pya.get_device_info_by_index(index)
            return AudioDeviceInfo(
                index=index,
                name=info["name"],
                channels_in=info["maxInputChannels"],
                channels_out=info["maxOutputChannels"],
                default_sample_rate=info["defaultSampleRate"],
            )
        except (ValueError, IndexError):
            pass
        for i in range(self._pya.get_device_count()):
            info = self._pya.get_device_info_by_index(i)
            if name_or_index.lower() in info["name"].lower():
                return AudioDeviceInfo(
                    index=i,
                    name=info["name"],
                    channels_in=info["maxInputChannels"],
                    channels_out=info["maxOutputChannels"],
                    default_sample_rate=info["defaultSampleRate"],
                )
        return None

    def open_input_stream(self, device_index: int, sample_rate: int = 16000, chunk_size: int = 1024):
        return self._pya.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=chunk_size,
        )

    def open_output_stream(self, device_index: int, sample_rate: int = 24000, chunk_size: int = 1024):
        return self._pya.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            output=True,
            output_device_index=device_index,
            frames_per_buffer=chunk_size,
        )
