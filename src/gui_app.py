import asyncio
import logging
import queue
import threading
import time
from typing import Dict, List, Optional

import customtkinter as ctk

from src.audio_device_manager import AudioDeviceManager
from src.bridge_controller import BridgeController
from src.translation_pipeline import TranslationPipeline

logger = logging.getLogger(__name__)

LANGUAGES: Dict[str, str] = {
    "English": "en",
    "French": "fr",
    "Vietnamese": "vi",
    "Spanish": "es",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Russian": "ru",
    "Japanese": "ja",
    "Korean": "ko",
    "Chinese": "zh",
    "Arabic": "ar",
    "Dutch": "nl",
    "Polish": "pl",
    "Turkish": "tr",
}


class BridgeRunner:
    def __init__(self) -> None:
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._status_queue: queue.Queue = queue.Queue()
        self._running = False

    @property
    def status_queue(self) -> queue.Queue:
        return self._status_queue

    @property
    def running(self) -> bool:
        return self._running

    def start(
        self,
        incoming_input: str,
        incoming_output: str,
        incoming_target: str,
        outgoing_input: str,
        outgoing_output: str,
        outgoing_target: str,
        enable_outgoing: bool = True,
    ) -> None:
        self._stop_event.clear()
        self._running = True
        self._thread = threading.Thread(
            target=self._run_bridge,
            args=(
                incoming_input,
                incoming_output,
                incoming_target,
                outgoing_input,
                outgoing_output,
                outgoing_target,
                enable_outgoing,
            ),
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._running = False

    def _push_status(self, key: str, value: str) -> None:
        try:
            self._status_queue.put_nowait((key, value))
        except queue.Full:
            pass

    def _run_bridge(
        self,
        incoming_input: str,
        incoming_output: str,
        incoming_target: str,
        outgoing_input: str,
        outgoing_output: str,
        outgoing_target: str,
        enable_outgoing: bool = True,
    ) -> None:
        self._push_status("incoming", "starting")
        if enable_outgoing:
            self._push_status("outgoing", "starting")
        asyncio.run(
            self._bridge_task(
                incoming_input,
                incoming_output,
                incoming_target,
                outgoing_input,
                outgoing_output,
                outgoing_target,
                enable_outgoing,
            )
        )
        self._running = False
        self._push_status("incoming", "stopped")
        if enable_outgoing:
            self._push_status("outgoing", "stopped")
        self._push_status("bridge", "stopped")

    async def _bridge_task(
        self,
        incoming_input: str,
        incoming_output: str,
        incoming_target: str,
        outgoing_input: str,
        outgoing_output: str,
        outgoing_target: str,
        enable_outgoing: bool = True,
    ) -> None:
        incoming = TranslationPipeline(
            name="incoming",
            input_device=incoming_input,
            output_device=incoming_output,
            target_language=incoming_target,
        )
        outgoing = TranslationPipeline(
            name="outgoing",
            input_device=outgoing_input,
            output_device=outgoing_output,
            target_language=outgoing_target,
        )

        try:
            await incoming.connect()
            self._push_status("incoming", "connected")
            if enable_outgoing:
                await outgoing.connect()
                self._push_status("outgoing", "connected")
            else:
                self._push_status("outgoing", "disabled")

            async with asyncio.TaskGroup() as tg:
                tg.create_task(self._poll_stop(incoming, outgoing))
                tg.create_task(incoming.capture_task())
                tg.create_task(incoming.play_task())
                if enable_outgoing:
                    tg.create_task(outgoing.capture_task())
                    tg.create_task(outgoing.play_task())
        except Exception as e:
            logger.exception("Bridge error")
            self._push_status("bridge", f"error: {e}")
        finally:
            await incoming.disconnect()
            if enable_outgoing:
                await outgoing.disconnect()

    async def _poll_stop(self, incoming, outgoing) -> None:
        while not self._stop_event.is_set():
            await asyncio.sleep(0.5)
        incoming._running = False
        outgoing._running = False


class LIRelayApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("LIRelay — Live Lingua Relay")
        self.geometry("520x520")
        self.minsize(480, 480)
        ctk.set_appearance_mode("system")

        self._runner = BridgeRunner()
        self._mgr = AudioDeviceManager()
        self._devices_input: List[str] = []
        self._devices_output: List[str] = []
        self._refresh_devices()

        self._build_ui()
        self._poll_status()

    def _refresh_devices(self) -> None:
        inputs, outputs = self._mgr.list_all_devices()
        self._devices_input = [f"[{d.index}] {d.name}" for d in inputs]
        self._devices_output = [f"[{d.index}] {d.name}" for d in outputs]

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        # -- Title --
        title = ctk.CTkLabel(
            self,
            text="LIRelay — Live Lingua Relay",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        title.grid(row=0, column=0, pady=(16, 8), padx=20, sticky="w")

        subtitle = ctk.CTkLabel(
            self,
            text="macOS live translation audio bridge",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        subtitle.grid(row=1, column=0, pady=(0, 12), padx=20, sticky="w")

        # -- Languages --
        lang_frame = ctk.CTkFrame(self)
        lang_frame.grid(row=2, column=0, pady=6, padx=20, sticky="ew")
        lang_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(lang_frame, text="Languages", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=2, pady=(8, 6), padx=10, sticky="w"
        )

        ctk.CTkLabel(lang_frame, text="My language:").grid(row=1, column=0, padx=10, pady=4, sticky="w")
        self._my_lang = ctk.CTkOptionMenu(lang_frame, values=list(LANGUAGES.keys()))
        self._my_lang.set("English")
        self._my_lang.grid(row=1, column=1, padx=10, pady=4, sticky="ew")

        ctk.CTkLabel(lang_frame, text="Their language:").grid(row=2, column=0, padx=10, pady=4, sticky="w")
        self._their_lang = ctk.CTkOptionMenu(lang_frame, values=list(LANGUAGES.keys()))
        self._their_lang.set("Vietnamese")
        self._their_lang.grid(row=2, column=1, padx=10, pady=4, sticky="ew")

        # -- Devices --
        dev_frame = ctk.CTkFrame(self)
        dev_frame.grid(row=3, column=0, pady=6, padx=20, sticky="ew")
        dev_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(dev_frame, text="Audio Devices", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=2, pady=(8, 6), padx=10, sticky="w"
        )

        self._dev_widgets: Dict[str, ctk.CTkOptionMenu] = {}

        labels = [
            ("incoming_input", "Incoming (caller audio):"),
            ("incoming_output", "Your headphones:"),
            ("outgoing_input", "Your microphone:"),
            ("outgoing_output", "Outgoing (virtual mic):"),
        ]
        defaults = {
            "incoming_input": "BlackHole 2ch",
            "incoming_output": "Haut-parleurs",
            "outgoing_input": "MacBook",
            "outgoing_output": "BlackHole 16ch",
        }

        for i, (key, label) in enumerate(labels, start=1):
            ctk.CTkLabel(dev_frame, text=label).grid(
                row=i, column=0, padx=10, pady=4, sticky="w"
            )
            is_output = "output" in key or "headphone" in label.lower()
            choices = self._devices_output if is_output else self._devices_input
            default = self._pick_default(choices, defaults.get(key, ""))
            menu = ctk.CTkOptionMenu(dev_frame, values=choices)
            menu.set(default)
            menu.grid(row=i, column=1, padx=10, pady=4, sticky="ew")
            self._dev_widgets[key] = menu

        refresh_btn = ctk.CTkButton(
            dev_frame,
            text="↻ Refresh Devices",
            command=self._refresh_devices_ui,
        )
        refresh_btn.grid(row=len(labels) + 1, column=0, columnspan=2, padx=10, pady=(4, 8), sticky="ew")

        # -- Controls --
        ctrl_frame = ctk.CTkFrame(self)
        ctrl_frame.grid(row=4, column=0, pady=10, padx=20, sticky="ew")
        ctrl_frame.grid_columnconfigure(0, weight=1)
        ctrl_frame.grid_columnconfigure(1, weight=1)

        self._receive_only = ctk.CTkCheckBox(
            ctrl_frame,
            text="Receive only (no mic)",
            onvalue=True,
            offvalue=False,
        )
        self._receive_only.grid(row=0, column=0, columnspan=2, padx=8, pady=(8, 0), sticky="w")

        self._start_btn = ctk.CTkButton(
            ctrl_frame,
            text="▶  Start Bridge",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2d8c3c",
            hover_color="#237030",
            command=self._toggle_bridge,
        )
        self._start_btn.grid(row=1, column=0, padx=8, pady=8, sticky="ew")

        self._swap_btn = ctk.CTkButton(
            ctrl_frame,
            text="⇄  Swap Languages",
            command=self._swap_languages,
        )
        self._swap_btn.grid(row=1, column=1, padx=8, pady=8, sticky="ew")

        # -- Status --
        status_frame = ctk.CTkFrame(self)
        status_frame.grid(row=5, column=0, pady=6, padx=20, sticky="ew")
        status_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(status_frame, text="Status", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=2, pady=(8, 4), padx=10, sticky="w"
        )

        self._status_labels: Dict[str, ctk.CTkLabel] = {}
        for i, (key, label) in enumerate(
            [
                ("incoming", "Incoming pipeline:"),
                ("outgoing", "Outgoing pipeline:"),
                ("bridge", "Bridge:"),
            ]
        ):
            ctk.CTkLabel(status_frame, text=label).grid(
                row=i + 1, column=0, padx=10, pady=2, sticky="w"
            )
            lbl = ctk.CTkLabel(status_frame, text="idle", anchor="w")
            lbl.grid(row=i + 1, column=1, padx=10, pady=2, sticky="ew")
            self._status_labels[key] = lbl

        # -- Spacer --
        spacer = ctk.CTkLabel(self, text="")
        spacer.grid(row=6, column=0, sticky="ew")

    def _refresh_devices_ui(self) -> None:
        self._refresh_devices()
        for key, menu in self._dev_widgets.items():
            is_output = "output" in key
            choices = self._devices_output if is_output else self._devices_input
            menu.configure(values=choices)

    def _pick_default(self, choices: List[str], hint: str) -> str:
        for c in choices:
            if hint.lower() in c.lower():
                return c
        return choices[0] if choices else "—"

    def _toggle_bridge(self) -> None:
        if self._runner.running:
            self._runner.stop()
            self._start_btn.configure(text="▶  Start Bridge", fg_color="#2d8c3c")
            self._swap_btn.configure(state="normal")
        else:
            incoming_input = self._dev_widgets["incoming_input"].get().split("] ", 1)[-1]
            incoming_output = self._dev_widgets["incoming_output"].get().split("] ", 1)[-1]
            outgoing_input = self._dev_widgets["outgoing_input"].get().split("] ", 1)[-1]
            outgoing_output = self._dev_widgets["outgoing_output"].get().split("] ", 1)[-1]

            incoming_target = LANGUAGES[self._my_lang.get()]
            outgoing_target = LANGUAGES[self._their_lang.get()]

            self._runner.start(
                incoming_input=incoming_input,
                incoming_output=incoming_output,
                incoming_target=incoming_target,
                outgoing_input=outgoing_input,
                outgoing_output=outgoing_output,
                outgoing_target=outgoing_target,
                enable_outgoing=not self._receive_only.get(),
            )
            self._start_btn.configure(text="■  Stop Bridge", fg_color="#b32424")
            self._swap_btn.configure(state="disabled")

    def _swap_languages(self) -> None:
        my = self._my_lang.get()
        their = self._their_lang.get()
        self._my_lang.set(their)
        self._their_lang.set(my)

    def _poll_status(self) -> None:
        try:
            while True:
                key, value = self._runner.status_queue.get_nowait()
                if key in self._status_labels:
                    self._status_labels[key].configure(text=value)
        except queue.Empty:
            pass
        self.after(200, self._poll_status)

    def destroy(self) -> None:
        if self._runner.running:
            self._runner.stop()
        self._mgr.terminate()
        super().destroy()
