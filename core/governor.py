"""
core/governor.py — Autonomer Workload-Governor & Auto-Pilot.
Überwacht laufende Prozesse und schaltet dynamisch auf den jeweils besten Scheduler um.
"""

from __future__ import annotations
import time
from typing import Callable, Optional

from core.detector import SystemDetector
from core.manager import SchedulerManager

class AutopilotGovernor:
    """Intelligenter Hintergrund-Governor zur automatischen Scheduler-Optimierung."""

    def __init__(self, manager: Optional[SchedulerManager] = None, log_cb: Optional[Callable[[str], None]] = None):
        self.manager = manager or SchedulerManager()
        self.log = log_cb or print
        self.current_mode = "IDLE_DESKTOP"
        self._running = False

    def step(self) -> None:
        mode, procs = SystemDetector.detect_active_workload()
        if mode == self.current_mode:
            return

        cfg = self.manager.config
        prev_mode = self.current_mode
        self.current_mode = mode

        if mode == "GAMING":
            target = cfg.get("gaming_scheduler", "scx_lavd")
            self.log(f"[Governor] 🎮 Gaming-Workload erkannt ({', '.join(procs)}). Schalte auf: {target}")
            self.manager.switch_scheduler(target)

        elif mode == "EMULATION":
            target = cfg.get("emulation_scheduler", "scx_lavd")
            self.log(f"[Governor] 🕹️ Emulations-Workload erkannt ({', '.join(procs)}). Schalte auf: {target}")
            self.manager.switch_scheduler(target)

        elif mode == "LOW_LATENCY_AUDIO":
            target = cfg.get("audio_scheduler", "scx_lavd")
            self.log(f"[Governor] 🎵 Low-Latency DAW-Workload erkannt ({', '.join(procs)}). Schalte auf: {target}")
            self.manager.switch_scheduler(target)

        elif mode == "COMPILING":
            target = cfg.get("compile_scheduler", "scx_rusty")
            self.log(f"[Governor] 🔨 Compile-Workload erkannt ({', '.join(procs)}). Schalte auf: {target}")
            self.manager.switch_scheduler(target)

        elif mode == "CONTENT_CREATION":
            target = cfg.get("content_scheduler", "scx_bpfland")
            self.log(f"[Governor] 🎬 Content-Creation Workload erkannt ({', '.join(procs)}). Schalte auf: {target}")
            self.manager.switch_scheduler(target)

        elif mode == "IDLE_DESKTOP":
            target = cfg.get("default_idle_scheduler", "default")
            self.log(f"[Governor] 💤 System im Leerlauf (vorher: {prev_mode}). Schalte auf: {target}")
            self.manager.switch_scheduler(target)

    def run_loop(self, poll_interval_sec: float = 3.0) -> None:
        self._running = True
        self.log(f"[Governor] Auto-Pilot gestartet. Prüfungsintervall: {poll_interval_sec}s.")
        try:
            while self._running:
                self.step()
                time.sleep(poll_interval_sec)
        except KeyboardInterrupt:
            self.log("[Governor] Auto-Pilot beendet.")
        finally:
            self._running = False

    def stop(self) -> None:
        self._running = False
