"""
core/profiles.py — Pre-tuned Performance, Latency and Efficiency Profiles.
Pairs CPU schedulers with matching scaling governors and energy preference hints.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List

from core.i18n import t


@dataclass
class SchedProfile:
    id: str
    name_key: str
    target_scheduler: str
    governor: str
    epp: str
    desc_key: str
    recommended_flags: List[str]
    workload_type: str

    @property
    def name(self) -> str:
        return t(self.name_key)

    @property
    def description(self) -> str:
        return t(self.desc_key)


PROFILES: Dict[str, SchedProfile] = {
    "gaming": SchedProfile(
        id="gaming",
        name_key="prof_gaming_name",
        target_scheduler="scx_lavd",
        governor="performance",
        epp="performance",
        desc_key="prof_gaming_desc",
        recommended_flags=["--performance", "--pinned-slice-us", "3000"],
        workload_type="Gaming"
    ),
    "lowlatency": SchedProfile(
        id="lowlatency",
        name_key="prof_audio_name",
        target_scheduler="scx_lavd",
        governor="performance",
        epp="performance",
        desc_key="prof_audio_desc",
        recommended_flags=["--performance", "--pinned-slice-us", "1500"],
        workload_type="Audio / Low-Latency"
    ),
    "compile": SchedProfile(
        id="compile",
        name_key="prof_compile_name",
        target_scheduler="scx_rusty",
        governor="performance",
        epp="balance_performance",
        desc_key="prof_compile_desc",
        recommended_flags=[],
        workload_type="Compilation / Throughput"
    ),
    "balanced": SchedProfile(
        id="balanced",
        name_key="prof_balanced_name",
        target_scheduler="scx_bpfland",
        governor="schedutil",
        epp="balance_performance",
        desc_key="prof_balanced_desc",
        recommended_flags=[],
        workload_type="General Desktop"
    ),
    "powersave": SchedProfile(
        id="powersave",
        name_key="prof_powersave_name",
        target_scheduler="default",
        governor="powersave",
        epp="power",
        desc_key="prof_powersave_desc",
        recommended_flags=[],
        workload_type="Power Saving"
    ),
    "emulation": SchedProfile(
        id="emulation",
        name_key="prof_emulation_name",
        target_scheduler="scx_lavd",
        governor="performance",
        epp="performance",
        desc_key="prof_emulation_desc",
        recommended_flags=["--performance"],
        workload_type="Emulation"
    ),
    "stock": SchedProfile(
        id="stock",
        name_key="prof_stock_name",
        target_scheduler="default",
        governor="schedutil",
        epp="balance_performance",
        desc_key="prof_stock_desc",
        recommended_flags=[],
        workload_type="Kernel Default"
    )
}
