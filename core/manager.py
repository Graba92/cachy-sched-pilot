"""
core/manager.py — Scheduler Controller & Hot-Swapping Orchestrator.
Ermöglicht nahtloses Wechseln zwischen scx_* Schedulern und dem Kernel-Default.
"""

from __future__ import annotations
import json
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from core.detector import SystemDetector, KNOWN_SCHEDULERS

CONFIG_DIR = Path.home() / ".config" / "cachy-sched-pilot"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "auto_pilot": True,
    "default_idle_scheduler": "default",
    "gaming_scheduler": "scx_lavd",
    "compile_scheduler": "scx_rusty",
    "audio_scheduler": "scx_lavd",
    "emulation_scheduler": "scx_lavd",
    "content_scheduler": "scx_bpfland",
    "custom_flags": {
        "scx_lavd": ["--performance"],
        "scx_bpfland": [],
        "scx_rusty": []
    }
}

class SchedulerManager:
    """Steuert das Laden, Wechseln und Beenden von sched-ext Schedulern."""

    def __init__(self):
        self.config = self.load_config()

    def load_config(self) -> dict:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                # Fehlende Default-Schlüssel ergänzen
                updated = False
                for k, v in DEFAULT_CONFIG.items():
                    if k not in data:
                        data[k] = v
                        updated = True
                if updated:
                    CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
                return data
            except Exception:
                pass
        CONFIG_FILE.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")
        return DEFAULT_CONFIG

    def save_config(self, cfg: dict) -> None:
        self.config = cfg
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    def stop_active_scx(self) -> Tuple[bool, str]:
        """Stoppt alle aktiven scx_* Scheduler und kehrt zum Kernel-Default zurück."""
        status = SystemDetector.detect_scx_status()
        if status.state == "disabled":
            return True, "Bereits auf Standard-Kernel (sched-ext ist inaktiv)."

        stopped_any = False

        # 1. Wenn scxctl verfügbar ist, D-Bus Stopp bevorzugen
        if status.scxctl_installed:
            try:
                res = subprocess.run(["scxctl", "stop"], capture_output=True, text=True, timeout=3)
                if res.returncode == 0:
                    stopped_any = True
            except Exception:
                pass

        # 2. Wenn scx_loader läuft:
        if status.scx_loader_active:
            for srv in ["scx_loader.service", "scx.service"]:
                try:
                    subprocess.run(["systemctl", "stop", srv], check=False, timeout=3)
                    stopped_any = True
                except Exception:
                    pass

        # 3. Bestehende scx-Prozesse per kill beenden
        for sched in KNOWN_SCHEDULERS:
            try:
                subprocess.run(["killall", "-SIGINT", sched], capture_output=True, timeout=2)
                stopped_any = True
            except Exception:
                pass

        time.sleep(0.5)
        new_status = SystemDetector.detect_scx_status()
        if new_status.state == "disabled":
            return True, "Erfolgreich auf Standard-Kernel-Scheduler zurückgekehrt."
        return False, f"Scheduler konnte nicht vollständig beendet werden. Status: {new_status.state}"

    def switch_scheduler(self, scheduler_name: str, extra_args: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Aktiviert einen bestimmten SCX-Scheduler oder 'default' für den Kernel-Standard.
        Unterstützt scxctl (D-Bus), systemd und direktes Spawnen.
        """
        sched_clean = scheduler_name.strip().lower()
        if sched_clean in ["default", "kernel", "bore", "eevdf", "none", "off"]:
            return self.stop_active_scx()

        # scx_ Prefix normalisieren
        binary_name = sched_clean if sched_clean.startswith("scx_") else f"scx_{sched_clean}"
        short_name = sched_clean.removeprefix("scx_")

        if not shutil.which(binary_name):
            return False, f"Binary '{binary_name}' ist nicht im System-PATH installiert."

        # 1. Versuch via scxctl, falls keine extra_args übergeben wurden
        flags = extra_args or self.config.get("custom_flags", {}).get(binary_name, [])
        if not flags and shutil.which("scxctl"):
            try:
                res = subprocess.run(["scxctl", "switch", short_name], capture_output=True, text=True, timeout=4)
                if res.returncode == 0:
                    time.sleep(0.4)
                    new_status = SystemDetector.detect_scx_status()
                    if new_status.state == "enabled":
                        return True, f"Scheduler '{binary_name}' erfolgreich via scxctl aktiviert (D-Bus)."
            except Exception:
                pass

        # 2. Alten Scheduler stoppen und direkt spawnen
        self.stop_active_scx()
        time.sleep(0.3)

        cmd = [binary_name] + flags

        # Start im Hintergrund via pkexec / sudo oder direkt falls Root
        if os.geteuid() == 0:
            full_cmd = cmd
        else:
            if shutil.which("pkexec"):
                full_cmd = ["pkexec"] + cmd
            else:
                full_cmd = ["sudo", "-n"] + cmd

        try:
            proc = subprocess.Popen(
                full_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            time.sleep(0.6)

            new_status = SystemDetector.detect_scx_status()
            if new_status.state == "enabled":
                return True, f"Scheduler '{binary_name}' erfolgreich aktiviert (PID: {new_status.active_pid or proc.pid})."
            else:
                return False, f"Start von '{binary_name}' initiiert, sched-ext meldet jedoch 'disabled'. Root-Rechte erforderlich."
        except Exception as e:
            return False, f"Fehler beim Starten von {binary_name}: {e}"

    @staticmethod
    def generate_systemd_template(scheduler_name: str, extra_flags: str = "") -> str:
        """
        Generiert die empfohlene Konfiguration für /etc/default/scx
        zur dauerhaften Aktivierung beim Booten in CachyOS.
        """
        short_name = scheduler_name.strip().removeprefix("scx_")
        template = f"""# CachyOS sched-ext Boot-Konfiguration (/etc/default/scx)
# Generiert von Cachy-Sched-Pilot
SCX_SCHEDULER="{short_name}"
SCX_FLAGS="{extra_flags}"
"""
        return template

