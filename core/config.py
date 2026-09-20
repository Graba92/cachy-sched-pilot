"""
core/config.py — XDG-Compliant Configuration Manager for Cachy-Sched-Pilot.
Handles TOML configuration loading, saving, and defaults according to XDG standards.
"""

from __future__ import annotations
import os
import tomllib
from pathlib import Path
from typing import Any, Dict, List, Optional

XDG_CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
USER_CONFIG_DIR = XDG_CONFIG_HOME / "sched-pilot"
USER_CONFIG_FILE = USER_CONFIG_DIR / "config.toml"
SYSTEM_CONFIG_FILE = Path("/etc/sched-pilot/config.toml")

# Legacy JSON path migration check
LEGACY_CONFIG_FILE = USER_CONFIG_DIR / "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "general": {
        "language": "de",
        "poll_interval_sec": 3.0,
        "auto_pilot": True,
        "safety_fallback": True,
    },
    "workloads": {
        "default_idle_scheduler": "default",
        "gaming_scheduler": "scx_lavd",
        "compile_scheduler": "scx_rusty",
        "audio_scheduler": "scx_lavd",
        "emulation_scheduler": "scx_lavd",
        "content_scheduler": "scx_bpfland",
        "powersave_scheduler": "default",
    },
    "custom_flags": {
        "scx_lavd": ["--performance"],
        "scx_bpfland": [],
        "scx_rusty": [],
        "scx_flash": [],
    },
    "governor_policy": {
        "gaming_governor": "performance",
        "gaming_epp": "performance",
        "compile_governor": "performance",
        "compile_epp": "balance_performance",
        "powersave_governor": "powersave",
        "powersave_epp": "power",
        "default_governor": "schedutil",
        "default_epp": "balance_performance",
    }
}


def dict_to_toml(data: Dict[str, Any]) -> str:
    """Simple, clean TOML serializer without external dependencies."""
    lines: List[str] = [
        "# Cachy-Sched-Pilot Configuration File",
        "# Generated automatically according to XDG specifications",
        ""
    ]
    
    for section, values in data.items():
        if isinstance(values, dict):
            lines.append(f"[{section}]")
            for k, v in values.items():
                if isinstance(v, bool):
                    lines.append(f"{k} = {'true' if v else 'false'}")
                elif isinstance(v, (int, float)):
                    lines.append(f"{k} = {v}")
                elif isinstance(v, list):
                    items = ", ".join(f'"{item}"' for item in v)
                    lines.append(f"{k} = [{items}]")
                elif isinstance(v, str):
                    lines.append(f'{k} = "{v}"')
            lines.append("")
        else:
            if isinstance(values, bool):
                lines.append(f"{section} = {'true' if values else 'false'}")
            elif isinstance(values, (int, float)):
                lines.append(f"{section} = {values}")
            elif isinstance(values, str):
                lines.append(f'{section} = "{values}"')
    return "\n".join(lines)


class ConfigManager:
    """Manages application configuration loading and saving."""

    @classmethod
    def get_config_path(cls) -> Path:
        """Determines effective configuration file path."""
        if USER_CONFIG_FILE.exists():
            return USER_CONFIG_FILE
        if SYSTEM_CONFIG_FILE.exists():
            return SYSTEM_CONFIG_FILE
        return USER_CONFIG_FILE

    @classmethod
    def load(cls) -> Dict[str, Any]:
        """Loads configuration from TOML, with system-fallback and defaults."""
        cfg_path = cls.get_config_path()
        cfg: Dict[str, Any] = {}

        # 1. System Config
        if SYSTEM_CONFIG_FILE.exists():
            try:
                with open(SYSTEM_CONFIG_FILE, "rb") as f:
                    cfg.update(tomllib.load(f))
            except Exception:
                pass

        # 2. User Config
        if USER_CONFIG_FILE.exists():
            try:
                with open(USER_CONFIG_FILE, "rb") as f:
                    user_cfg = tomllib.load(f)
                    for sec, vals in user_cfg.items():
                        if isinstance(vals, dict) and sec in cfg and isinstance(cfg[sec], dict):
                            cfg[sec].update(vals)
                        else:
                            cfg[sec] = vals
            except Exception:
                pass

        # 3. Apply missing defaults
        merged = False
        res = {}
        for section, sec_data in DEFAULT_CONFIG.items():
            res[section] = {}
            user_sec = cfg.get(section, {})
            if isinstance(sec_data, dict):
                for k, v in sec_data.items():
                    if k in user_sec:
                        res[section][k] = user_sec[k]
                    else:
                        res[section][k] = v
                        merged = True
            else:
                res[section] = cfg.get(section, sec_data)

        # If user config does not exist or was incomplete, write clean config
        if not USER_CONFIG_FILE.exists():
            cls.save(res)

        return res

    @classmethod
    def save(cls, data: Dict[str, Any]) -> None:
        """Saves configuration data into user config TOML file."""
        try:
            USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            content = dict_to_toml(data)
            USER_CONFIG_FILE.write_text(content, encoding="utf-8")
        except Exception:
            pass
