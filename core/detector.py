"""
core/detector.py — Low-Level Hardware, Kernel & sched-ext (SCX) Erkennungs-Engine.
Ermittelt CPU-Topologie, aktive Kernel-Konfiguration und alle installierten SCX-Schedulers.
"""

from __future__ import annotations
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil

SYSFS_SCHED_EXT = Path("/sys/kernel/sched_ext")
KNOWN_SCHEDULERS = [
    "scx_lavd",
    "scx_bpfland",
    "scx_rusty",
    "scx_flash",
    "scx_central",
    "scx_nest",
    "scx_qmap",
    "scx_layered",
    "scx_simple",
    "scx_userland"
]

@dataclass
class CpuInfo:
    model: str
    physical_cores: int
    logical_cores: int
    frequency_mhz: float
    governor: str
    arch: str

@dataclass
class SchedExtStatus:
    supported: bool
    sysfs_present: bool
    state: str  # "enabled", "disabled", "unsupported"
    active_scheduler: str
    active_pid: Optional[int] = None
    installed_schedulers: List[str] = field(default_factory=list)
    scx_loader_installed: bool = False
    scx_loader_active: bool = False
    scxctl_installed: bool = False


class SystemDetector:
    """Zentrale Diagnose für Linux-Kernel, CPU-Architektur & sched-ext."""

    @staticmethod
    def get_kernel_release() -> str:
        return os.uname().release

    @staticmethod
    def is_cachyos() -> bool:
        try:
            os_release = Path("/etc/os-release").read_text(encoding="utf-8")
            return "cachyos" in os_release.lower()
        except Exception:
            return False

    @staticmethod
    def get_cpu_info() -> CpuInfo:
        model = "Unbekannte CPU"
        freq = 0.0
        try:
            with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
                for line in f:
                    if "model name" in line:
                        model = line.split(":", 1)[1].strip()
                        break
        except Exception:
            pass

        try:
            cpu_freq = psutil.cpu_freq()
            if cpu_freq and cpu_freq.current:
                freq = cpu_freq.current
        except Exception:
            pass

        governor = "unknown"
        gov_path = Path("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
        if gov_path.exists():
            try:
                governor = gov_path.read_text(encoding="utf-8").strip()
            except Exception:
                pass

        return CpuInfo(
            model=model,
            physical_cores=psutil.cpu_count(logical=False) or 1,
            logical_cores=psutil.cpu_count(logical=True) or 1,
            frequency_mhz=freq,
            governor=governor,
            arch=os.uname().machine
        )

    @classmethod
    def get_installed_scx_schedulers(cls) -> List[str]:
        installed = []
        for sched in KNOWN_SCHEDULERS:
            if shutil.which(sched):
                installed.append(sched)
        return installed

    @classmethod
    def detect_scx_status(cls) -> SchedExtStatus:
        sysfs_present = SYSFS_SCHED_EXT.exists()
        if not sysfs_present:
            return SchedExtStatus(
                supported=False,
                sysfs_present=False,
                state="unsupported",
                active_scheduler="default (kein sched-ext Support im Kernel)",
                installed_schedulers=cls.get_installed_scx_schedulers(),
                scx_loader_installed=bool(shutil.which("scx_loader")),
                scx_loader_active=False
            )

        state = "disabled"
        state_file = SYSFS_SCHED_EXT / "state"
        if state_file.exists():
            try:
                state = state_file.read_text(encoding="utf-8").strip()
            except Exception:
                state = "unknown"

        active_scheduler = "Default Kernel (EEVDF / BORE)"
        active_pid = None

        if state == "enabled":
            # Prozess-Scan nach aktiven scx_* Binaries
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    name = proc.info["name"] or ""
                    cmd = " ".join(proc.info["cmdline"] or [])
                    for s in KNOWN_SCHEDULERS:
                        if s in name or s in cmd:
                            active_scheduler = s
                            active_pid = proc.info["pid"]
                            break
                    if active_pid:
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        # scx_loader & scxctl Status
        scx_loader_inst = bool(shutil.which("scx_loader"))
        scxctl_inst = bool(shutil.which("scxctl"))
        scx_loader_act = False
        for srv in ["scx_loader.service", "scx.service"]:
            try:
                res = subprocess.run(
                    ["systemctl", "is-active", srv],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if res.stdout.strip() == "active":
                    scx_loader_act = True
                    break
            except Exception:
                pass

        return SchedExtStatus(
            supported=True,
            sysfs_present=True,
            state=state,
            active_scheduler=active_scheduler,
            active_pid=active_pid,
            installed_schedulers=cls.get_installed_scx_schedulers(),
            scx_loader_installed=scx_loader_inst,
            scx_loader_active=scx_loader_act,
            scxctl_installed=scxctl_inst
        )

    @staticmethod
    def detect_active_workload() -> Tuple[str, List[str]]:
        """
        Erkennt typische Workloads: Gaming, Emulation, Audio-Produktion, Compile,
        Content Creation oder Desktop-Idle.
        """
        gaming_procs = ["steam", "wine", "proton", "heroic", "lutris", "gamescope", "mangohud"]
        emulation_procs = ["rpcs3", "ryujinx", "yuzu", "cemu", "pcsx2", "dolphin-emu", "duckstation"]
        audio_procs = ["reaper", "ardour", "bitwig", "carla", "jackd", "qjackctl", "mixxx"]
        compile_procs = ["gcc", "g++", "clang", "clang++", "rustc", "cargo", "make", "ninja", "cmake"]
        media_procs = ["obs", "blender", "kdenlive", "ffmpeg", "handbrake"]

        detected_gaming = []
        detected_emu = []
        detected_audio = []
        detected_compile = []
        detected_media = []

        for p in psutil.process_iter(["name"]):
            try:
                name = (p.info["name"] or "").lower()
                for g in gaming_procs:
                    if g in name and g not in detected_gaming:
                        detected_gaming.append(g)
                for e in emulation_procs:
                    if e in name and e not in detected_emu:
                        detected_emu.append(e)
                for a in audio_procs:
                    if a in name and a not in detected_audio:
                        detected_audio.append(a)
                for c in compile_procs:
                    if c in name and c not in detected_compile:
                        detected_compile.append(c)
                for m in media_procs:
                    if m in name and m not in detected_media:
                        detected_media.append(m)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        if detected_gaming:
            return "GAMING", detected_gaming
        if detected_emu:
            return "EMULATION", detected_emu
        if detected_audio:
            return "LOW_LATENCY_AUDIO", detected_audio
        if detected_compile:
            return "COMPILING", detected_compile
        if detected_media:
            return "CONTENT_CREATION", detected_media
        return "IDLE_DESKTOP", []

    @classmethod
    def run_doctor(cls) -> Dict[str, Any]:
        """
        Führt eine lückenlose System- & Kernel-Diagnose für sched-ext durch.
        Prüft Kernel-Flags, BPF-JIT, D-Bus Tools, Berechtigungen und Tuning-Potential.
        """
        status = cls.detect_scx_status()
        cpu = cls.get_cpu_info()
        kernel = cls.get_kernel_release()
        is_cachy = cls.is_cachyos()

        # BPF JIT Prüfung
        bpf_jit_enabled = False
        bpf_jit_file = Path("/proc/sys/net/core/bpf_jit_enable")
        if bpf_jit_file.exists():
            try:
                bpf_jit_enabled = bpf_jit_file.read_text(encoding="utf-8").strip() in ["1", "2"]
            except Exception:
                pass

        # Polkit / Root Fähigkeit
        has_root = os.geteuid() == 0
        has_pkexec = bool(shutil.which("pkexec"))
        has_sudo = bool(shutil.which("sudo"))

        checks = []
        # Check 1: Kernel Support
        if status.sysfs_present:
            checks.append({"name": "Kernel sched-ext (sysfs)", "status": "OK", "msg": f"/sys/kernel/sched_ext vorhanden ({kernel})"})
        else:
            checks.append({"name": "Kernel sched-ext (sysfs)", "status": "FAIL", "msg": "sched-ext nicht unterstützt oder Modul nicht geladen"})

        # Check 2: CachyOS Kernel
        if is_cachy or "cachyos" in kernel.lower():
            checks.append({"name": "CachyOS Kernel Optimierungen", "status": "OK", "msg": "CachyOS Kernel mit BORE/SCX Patches aktiv"})
        else:
            checks.append({"name": "CachyOS Kernel Optimierungen", "status": "WARN", "msg": "Standard-Kernel erkannt. CachyOS-Kernel empfohlen für max. Performance"})

        # Check 3: BPF JIT Compiler
        if bpf_jit_enabled:
            checks.append({"name": "eBPF JIT Compiler", "status": "OK", "msg": "Aktiviert (/proc/sys/net/core/bpf_jit_enable)"})
        else:
            checks.append({"name": "eBPF JIT Compiler", "status": "WARN", "msg": "eBPF JIT ist deaktiviert. Kann SCX verlangsamen"})

        # Check 4: Installierte Schedulers
        sched_count = len(status.installed_schedulers)
        if sched_count >= 3:
            checks.append({"name": "Installierte SCX Schedulers", "status": "OK", "msg": f"{sched_count} Scheduler bereit ({', '.join(status.installed_schedulers)})"})
        elif sched_count > 0:
            checks.append({"name": "Installierte SCX Schedulers", "status": "WARN", "msg": f"Nur {sched_count} Scheduler gefunden: {', '.join(status.installed_schedulers)}"})
        else:
            checks.append({"name": "Installierte SCX Schedulers", "status": "FAIL", "msg": "Keine SCX-Binaries gefunden. Installiere 'scx-scheds'"})

        # Check 5: scxctl & scx_loader
        if status.scxctl_installed:
            checks.append({"name": "scxctl D-Bus Client", "status": "OK", "msg": "scxctl ist installiert und nutzbar"})
        else:
            checks.append({"name": "scxctl D-Bus Client", "status": "INFO", "msg": "scxctl nicht gefunden (optional, aber empfohlen für CachyOS)"})

        # Check 6: Berechtigungen
        if has_root:
            checks.append({"name": "Ausführungsrechte", "status": "OK", "msg": "Läuft mit Root-Privilegien"})
        elif has_pkexec or has_sudo:
            checks.append({"name": "Ausführungsrechte", "status": "OK", "msg": f"Elevation via {'pkexec (GUI/Polkit)' if has_pkexec else 'sudo'} möglich"})
        else:
            checks.append({"name": "Ausführungsrechte", "status": "WARN", "msg": "Weder pkexec noch sudo verfügbar"})

        # Gesamtbewertung
        ok_count = sum(1 for c in checks if c["status"] == "OK")
        score = int((ok_count / len(checks)) * 100) if checks else 0

        return {
            "score": score,
            "kernel": kernel,
            "cpu": cpu,
            "status": status,
            "checks": checks
        }

