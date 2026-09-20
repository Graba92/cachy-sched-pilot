"""
core/detector.py — Low-Level Hardware, Kernel & sched-ext (SCX) Detection Engine.
Inspects CPU topology, live per-core load, scaling governors, EPP, sysfs knobs,
and detects kernel schedulers (EEVDF, BORE, cacULE, and sched-ext).
"""

from __future__ import annotations
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil

from core.i18n import t

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
class CpuCoreMetrics:
    core_id: int
    usage_percent: float
    frequency_mhz: float
    governor: str
    epp: str


@dataclass
class CpuInfo:
    model: str
    physical_cores: int
    logical_cores: int
    frequency_mhz: float
    governor: str
    epp: str
    arch: str
    per_core_load: List[float] = field(default_factory=list)


@dataclass
class SchedExtStatus:
    supported: bool
    sysfs_present: bool
    state: str  # "enabled", "disabled", "unsupported"
    active_scheduler: str
    kernel_scheduler_type: str  # "BORE", "EEVDF", "cacULE", "Generic"
    active_pid: Optional[int] = None
    installed_schedulers: List[str] = field(default_factory=list)
    scx_loader_installed: bool = False
    scx_loader_active: bool = False
    scxctl_installed: bool = False
    cmdline_flags: List[str] = field(default_factory=list)


class SystemDetector:
    """Central low-level diagnostic suite for Linux kernel, CPU and sched-ext."""

    @staticmethod
    def get_kernel_release() -> str:
        return os.uname().release

    @staticmethod
    def get_kernel_version_info() -> str:
        try:
            return Path("/proc/version").read_text(encoding="utf-8").strip()
        except Exception:
            return os.uname().release

    @staticmethod
    def get_cmdline() -> str:
        try:
            return Path("/proc/cmdline").read_text(encoding="utf-8").strip()
        except Exception:
            return ""

    @staticmethod
    def is_cachyos() -> bool:
        try:
            os_release = Path("/etc/os-release").read_text(encoding="utf-8")
            return "cachyos" in os_release.lower()
        except Exception:
            return False

    @classmethod
    def detect_kernel_scheduler_type(cls) -> str:
        """
        Detects default underlying kernel scheduler:
        - BORE (Burst-Oriented Response Enhancer)
        - cacULE (Cache-Aware CFS replacement)
        - EEVDF (Earliest Eligible Virtual Deadline First - Linux 6.6+)
        """
        release = cls.get_kernel_release().lower()
        proc_ver = cls.get_kernel_version_info().lower()

        # Check BORE sysctl
        bore_sysctl = Path("/proc/sys/kernel/sched_bore")
        if bore_sysctl.exists() or "-bore" in release or "bore" in proc_ver:
            return "BORE"

        if "-cacule" in release or "cacule" in proc_ver:
            return "cacULE"

        # Check kernel version for modern EEVDF (6.6+)
        try:
            major, minor = map(int, release.split(".")[:2])
            if (major, minor) >= (6, 6):
                return "EEVDF"
        except Exception:
            pass

        return "EEVDF / CFS"

    @classmethod
    def get_cpu_info(cls) -> CpuInfo:
        model = "Unknown CPU"
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
        if not gov_path.exists():
            gov_path = Path("/sys/devices/system/cpu/cpufreq/policy0/scaling_governor")
        if gov_path.exists():
            try:
                governor = gov_path.read_text(encoding="utf-8").strip()
            except Exception:
                pass

        epp = "n/a"
        epp_path = Path("/sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference")
        if not epp_path.exists():
            epp_path = Path("/sys/devices/system/cpu/cpufreq/policy0/energy_performance_preference")
        if epp_path.exists():
            try:
                epp = epp_path.read_text(encoding="utf-8").strip()
            except Exception:
                pass

        # Per-core utilization
        try:
            per_core = psutil.cpu_percent(percpu=True, interval=None)
        except Exception:
            per_core = []

        return CpuInfo(
            model=model,
            physical_cores=psutil.cpu_count(logical=False) or 1,
            logical_cores=psutil.cpu_count(logical=True) or 1,
            frequency_mhz=freq,
            governor=governor,
            epp=epp,
            arch=os.uname().machine,
            per_core_load=per_core
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
        kernel_sched = cls.detect_kernel_scheduler_type()
        sysfs_present = SYSFS_SCHED_EXT.exists()
        cmdline = cls.get_cmdline()
        scx_flags = [word for word in cmdline.split() if "scx" in word or "sched" in word]

        if not sysfs_present:
            return SchedExtStatus(
                supported=False,
                sysfs_present=False,
                state="unsupported",
                active_scheduler=f"Stock Kernel ({kernel_sched})",
                kernel_scheduler_type=kernel_sched,
                installed_schedulers=cls.get_installed_scx_schedulers(),
                scx_loader_installed=bool(shutil.which("scx_loader")),
                scx_loader_active=False,
                cmdline_flags=scx_flags
            )

        state = "disabled"
        state_file = SYSFS_SCHED_EXT / "state"
        if state_file.exists():
            try:
                state = state_file.read_text(encoding="utf-8").strip()
            except Exception:
                state = "unknown"

        active_scheduler = f"Stock Kernel ({kernel_sched})"
        active_pid = None

        if state == "enabled":
            # Check process tree for running scx_* binaries
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

            # Fallback check sysfs root_type if process name not matched
            if active_pid is None:
                root_type_file = SYSFS_SCHED_EXT / "root_type"
                if root_type_file.exists():
                    try:
                        active_scheduler = f"scx ({root_type_file.read_text().strip()})"
                    except Exception:
                        active_scheduler = "scx (Active)"

        # scx_loader & scxctl
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
            kernel_scheduler_type=kernel_sched,
            active_pid=active_pid,
            installed_schedulers=cls.get_installed_scx_schedulers(),
            scx_loader_installed=scx_loader_inst,
            scx_loader_active=scx_loader_act,
            scxctl_installed=scxctl_inst,
            cmdline_flags=scx_flags
        )

    @staticmethod
    def detect_active_workload() -> Tuple[str, List[str]]:
        """
        Detects running workloads: Gaming, Emulation, Low-Latency Audio, Compiling, Media, or Idle.
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
        """Runs comprehensive diagnostics and health score calculations."""
        status = cls.detect_scx_status()
        cpu = cls.get_cpu_info()
        kernel = cls.get_kernel_release()
        is_cachy = cls.is_cachyos()

        # BPF JIT Check
        bpf_jit_enabled = False
        bpf_jit_file = Path("/proc/sys/net/core/bpf_jit_enable")
        if bpf_jit_file.exists():
            try:
                bpf_jit_enabled = bpf_jit_file.read_text(encoding="utf-8").strip() in ["1", "2"]
            except Exception:
                pass

        # Privilege Check
        has_root = os.geteuid() == 0
        has_pkexec = bool(shutil.which("pkexec"))
        has_sudo = bool(shutil.which("sudo"))

        checks = []
        # Check 1: Kernel Support
        if status.sysfs_present:
            checks.append({
                "name": t("doc_check_kernel_scx"),
                "status": "OK",
                "msg": f"/sys/kernel/sched_ext OK ({kernel} - {status.kernel_scheduler_type})"
            })
        else:
            checks.append({
                "name": t("doc_check_kernel_scx"),
                "status": "FAIL",
                "msg": "Kernel missing sched-ext support (/sys/kernel/sched_ext absent)"
            })

        # Check 2: CachyOS Kernel
        if is_cachy or "cachyos" in kernel.lower():
            checks.append({
                "name": t("doc_check_cachy_kernel"),
                "status": "OK",
                "msg": f"CachyOS kernel with {status.kernel_scheduler_type} optimization active"
            })
        else:
            checks.append({
                "name": t("doc_check_cachy_kernel"),
                "status": "WARN",
                "msg": "Generic kernel detected. CachyOS kernel with BORE/SCX recommended"
            })

        # Check 3: BPF JIT Compiler
        if bpf_jit_enabled:
            checks.append({
                "name": t("doc_check_bpf_jit"),
                "status": "OK",
                "msg": "eBPF JIT compiler active (/proc/sys/net/core/bpf_jit_enable)"
            })
        else:
            checks.append({
                "name": t("doc_check_bpf_jit"),
                "status": "WARN",
                "msg": "eBPF JIT disabled. May degrade SCX performance"
            })

        # Check 4: Installed Schedulers
        sched_count = len(status.installed_schedulers)
        if sched_count >= 3:
            checks.append({
                "name": t("doc_check_scx_binaries"),
                "status": "OK",
                "msg": f"{sched_count} schedulers ready ({', '.join(status.installed_schedulers)})"
            })
        elif sched_count > 0:
            checks.append({
                "name": t("doc_check_scx_binaries"),
                "status": "WARN",
                "msg": f"Only {sched_count} schedulers found: {', '.join(status.installed_schedulers)}"
            })
        else:
            checks.append({
                "name": t("doc_check_scx_binaries"),
                "status": "FAIL",
                "msg": "No SCX binaries found in PATH. Install 'scx-scheds'"
            })

        # Check 5: scxctl & D-Bus
        if status.scxctl_installed:
            checks.append({
                "name": t("doc_check_scxctl"),
                "status": "OK",
                "msg": "scxctl D-Bus control client installed and available"
            })
        else:
            checks.append({
                "name": t("doc_check_scxctl"),
                "status": "INFO",
                "msg": "scxctl not found (optional, used for D-Bus switching)"
            })

        # Check 6: Polkit & Privilege Separation
        polkit_policy = Path("/usr/share/polkit-1/actions/org.cachyos.schedpilot.policy")
        has_policy = polkit_policy.exists()
        if has_root:
            checks.append({
                "name": t("doc_check_privileges"),
                "status": "OK",
                "msg": "Running with full root privileges"
            })
        elif has_pkexec and has_policy:
            checks.append({
                "name": t("doc_check_privileges"),
                "status": "OK",
                "msg": "Polkit policy installed; unprivileged GUI execution authorized via pkexec"
            })
        elif has_pkexec or has_sudo:
            checks.append({
                "name": t("doc_check_privileges"),
                "status": "WARN",
                "msg": "Elevation available (pkexec/sudo), but system polkit policy not yet installed"
            })
        else:
            checks.append({
                "name": t("doc_check_privileges"),
                "status": "FAIL",
                "msg": "Neither pkexec nor sudo found. Schedulers cannot be managed unprivileged"
            })

        ok_count = sum(1 for c in checks if c["status"] == "OK")
        score = int((ok_count / len(checks)) * 100) if checks else 0

        return {
            "score": score,
            "kernel": kernel,
            "cpu": cpu,
            "status": status,
            "checks": checks
        }
