"""
core/manager.py — Scheduler Controller & Hot-Swapping Orchestrator.
Manages dynamic switching between sched-ext schedulers and kernel defaults,
governor application, safety fallbacks, and privileged execution via Polkit.
"""

from __future__ import annotations
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from core.config import ConfigManager
from core.detector import SystemDetector, KNOWN_SCHEDULERS, SYSFS_SCHED_EXT
from core.profiles import PROFILES, SchedProfile
from core.i18n import t


class SchedulerManager:
    """Controls loading, switching, and terminating sched-ext schedulers safely."""

    def __init__(self):
        self.config = ConfigManager.load()
        self._last_known_scx: Optional[str] = None

    @staticmethod
    def get_helper_path() -> Optional[str]:
        """Locates the privileged cachy-sched-helper binary."""
        # 1. System package locations
        system_paths = [
            "/usr/lib/cachy-sched-pilot/cachy-sched-helper",
            "/usr/bin/cachy-sched-helper",
            "/usr/local/bin/cachy-sched-helper"
        ]
        for p in system_paths:
            if os.path.isfile(p) and os.access(p, os.X_OK):
                return p

        # 2. Local development checkout path
        local_path = Path(__file__).resolve().parent.parent / "bin" / "cachy-sched-helper"
        if local_path.is_file() and os.access(str(local_path), os.X_OK):
            return str(local_path)

        # 3. Search PATH
        which_helper = shutil.which("cachy-sched-helper")
        if which_helper:
            return which_helper

        return None

    def execute_privileged(self, args: List[str]) -> Tuple[bool, str]:
        """
        Executes a command through the privileged helper via Polkit (pkexec) or directly if root.
        """
        helper = self.get_helper_path()
        if not helper:
            return False, t("msg_helper_not_found", path="cachy-sched-helper")

        if os.geteuid() == 0:
            cmd = [helper] + args
        else:
            if shutil.which("pkexec"):
                cmd = ["pkexec", helper] + args
            elif shutil.which("sudo"):
                cmd = ["sudo", helper] + args
            else:
                return False, t("msg_privilege_error")

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=12
            )
            if res.returncode == 0:
                out = res.stdout.strip() or "Success"
                return True, out
            err = res.stderr.strip() or res.stdout.strip() or "Privileged command failed"
            return False, err
        except subprocess.TimeoutExpired:
            return False, "Command timed out."
        except Exception as e:
            return False, str(e)

    def stop_active_scx(self) -> Tuple[bool, str]:
        """Stops all active scx_* schedulers and reverts to stock kernel."""
        status = SystemDetector.detect_scx_status()
        if status.state == "disabled":
            self._last_known_scx = None
            return True, t("msg_already_default")

        # Try privileged helper
        ok, msg = self.execute_privileged(["stop"])
        if ok:
            self._last_known_scx = None
            return True, t("msg_reverted_default")

        # Unprivileged fallback via scxctl (D-Bus)
        if status.scxctl_installed:
            try:
                res = subprocess.run(["scxctl", "stop"], capture_output=True, text=True, timeout=3)
                if res.returncode == 0:
                    self._last_known_scx = None
                    return True, t("msg_reverted_default")
            except Exception:
                pass

        return False, t("msg_stop_fail", err=msg)

    def switch_scheduler(self, scheduler_name: str, extra_args: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Switches to target scheduler safely using Polkit helper.
        Supports: scx_lavd, scx_rusty, scx_bpfland, default, etc.
        """
        sched_clean = scheduler_name.strip().lower()
        if sched_clean in ["default", "kernel", "bore", "eevdf", "none", "off", "stock"]:
            return self.stop_active_scx()

        # Normalize name
        binary_name = sched_clean if sched_clean.startswith("scx_") else f"scx_{sched_clean}"

        if not shutil.which(binary_name):
            return False, t("msg_not_installed", binary=binary_name)

        # Get custom flags from config if not passed
        custom_flags_map = self.config.get("custom_flags", {})
        flags = extra_args if extra_args is not None else custom_flags_map.get(binary_name, [])

        # Execute switch via privileged helper
        helper_args = ["switch", binary_name] + flags
        ok, msg = self.execute_privileged(helper_args)

        if ok:
            self._last_known_scx = binary_name
            time.sleep(0.3)
            return True, t("msg_switched_success", sched=binary_name)

        # Fallback to scxctl if helper failed or wasn't authorized
        short_name = binary_name.removeprefix("scx_")
        if shutil.which("scxctl"):
            try:
                res = subprocess.run(["scxctl", "switch", short_name], capture_output=True, text=True, timeout=4)
                if res.returncode == 0:
                    self._last_known_scx = binary_name
                    return True, t("msg_switched_success", sched=binary_name)
            except Exception:
                pass

        return False, t("msg_switched_fail", sched=binary_name, err=msg)

    def set_governor(self, governor: str) -> Tuple[bool, str]:
        """Sets CPU scaling governor."""
        return self.execute_privileged(["set-governor", governor])

    def set_epp(self, epp: str) -> Tuple[bool, str]:
        """Sets energy performance preference."""
        return self.execute_privileged(["set-epp", epp])

    def apply_profile(self, profile_id: str) -> Tuple[bool, str]:
        """
        Applies a pre-configured profile: sets scheduler, CPU governor, and EPP.
        """
        prof_id = profile_id.strip().lower()
        profile: Optional[SchedProfile] = PROFILES.get(prof_id)
        if not profile:
            # Check if matching by partial name
            for k, p in PROFILES.items():
                if prof_id in k:
                    profile = p
                    break

        if not profile:
            return False, f"Unknown profile: '{profile_id}'"

        # 1. Switch scheduler
        ok, sched_msg = self.switch_scheduler(profile.target_scheduler, profile.recommended_flags)
        if not ok and profile.target_scheduler != "default":
            return False, sched_msg

        # 2. Set Governor
        if profile.governor:
            self.set_governor(profile.governor)

        # 3. Set EPP
        if profile.epp:
            self.set_epp(profile.epp)

        return True, t("msg_profile_applied", name=profile.name)

    def check_and_recover_safety(self) -> Tuple[bool, Optional[str]]:
        """
        Safety Fallback Watcher:
        Checks if an active scx scheduler unexpectedly died or crashed.
        Automatically resets sysfs state to prevent system lockups.
        """
        if not self._last_known_scx:
            return False, None

        status = SystemDetector.detect_scx_status()
        # If we expected an SCX scheduler to run, but sched_ext is disabled or stopped:
        if status.state == "disabled":
            # Revert cleanup
            self.stop_active_scx()
            crashed_sched = self._last_known_scx
            self._last_known_scx = None
            msg = t("msg_crash_detected")
            return True, f"{msg} ({crashed_sched})"

        return False, None
