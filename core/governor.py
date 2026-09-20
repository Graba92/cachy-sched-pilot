"""
core/governor.py — Autonomous Workload Governor & Auto-Pilot.
Monitors processes and automatically switches schedulers and power profiles
with integrated safety fallback crash protection.
"""

from __future__ import annotations
import time
from typing import Callable, Optional

from core.detector import SystemDetector
from core.manager import SchedulerManager
from core.i18n import t


class AutopilotGovernor:
    """Intelligent background watcher for automatic scheduler and profile switching."""

    def __init__(self, manager: Optional[SchedulerManager] = None, log_cb: Optional[Callable[[str], None]] = None):
        self.manager = manager or SchedulerManager()
        self.log = log_cb or print
        self.current_mode = "IDLE_DESKTOP"
        self._running = False

    def step(self) -> None:
        # 1. Safety Crash Check
        recovered, crash_msg = self.manager.check_and_recover_safety()
        if recovered and crash_msg:
            self.log(f"[bold red]{crash_msg}[/]")
            self.current_mode = "IDLE_DESKTOP"
            return

        # 2. Workload Detection
        mode, procs = SystemDetector.detect_active_workload()
        if mode == self.current_mode:
            return

        prev_mode = self.current_mode
        self.current_mode = mode

        if mode == "GAMING":
            self.log(f"🎮 [bold cyan]Gaming[/] ({', '.join(procs)}) -> Profile: [bold green]gaming[/]")
            self.manager.apply_profile("gaming")

        elif mode == "EMULATION":
            self.log(f"🕹️ [bold cyan]Emulation[/] ({', '.join(procs)}) -> Profile: [bold green]emulation[/]")
            self.manager.apply_profile("emulation")

        elif mode == "LOW_LATENCY_AUDIO":
            self.log(f"🎵 [bold cyan]Low-Latency Audio[/] ({', '.join(procs)}) -> Profile: [bold green]lowlatency[/]")
            self.manager.apply_profile("lowlatency")

        elif mode == "COMPILING":
            self.log(f"🔨 [bold cyan]Compilation[/] ({', '.join(procs)}) -> Profile: [bold green]compile[/]")
            self.manager.apply_profile("compile")

        elif mode == "CONTENT_CREATION":
            self.log(f"🎬 [bold cyan]Content Creation[/] ({', '.join(procs)}) -> Profile: [bold green]balanced[/]")
            self.manager.apply_profile("balanced")

        elif mode == "IDLE_DESKTOP":
            self.log(f"💤 [dim]Idle Desktop[/] (prev: {prev_mode}) -> Profile: [bold green]stock[/]")
            self.manager.apply_profile("stock")

    def run_loop(self, poll_interval_sec: float = 3.0) -> None:
        self._running = True
        self.log(f"🚀 Auto-Pilot started (Interval: {poll_interval_sec}s). Press Ctrl+C to exit.")
        try:
            while self._running:
                self.step()
                time.sleep(poll_interval_sec)
        except KeyboardInterrupt:
            self.log("\n🛑 Auto-Pilot stopped.")
        finally:
            self._running = False

    def stop(self) -> None:
        self._running = False
