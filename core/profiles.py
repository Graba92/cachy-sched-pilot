"""
core/profiles.py — Vorkonfigurierte Scheduler-Profile für typische Anwendungsfälle.
"""

from dataclasses import dataclass
from typing import Dict, List

@dataclass
class SchedProfile:
    name: str
    target_scheduler: str
    description: str
    recommended_flags: List[str]
    workload_type: str

PROFILES: Dict[str, SchedProfile] = {
    "gaming_esports": SchedProfile(
        name="Gaming & E-Sports (Low Latency)",
        target_scheduler="scx_lavd",
        description="Minimiert Latenz-Jitter und 1% Low Drops für maximale FPS-Stabilität.",
        recommended_flags=["--performance", "--pinned-slice-us", "3000"],
        workload_type="Gaming"
    ),
    "heavy_compile": SchedProfile(
        name="Compile & Multi-Core Rendering",
        target_scheduler="scx_rusty",
        description="Maximaler Thread-Durchsatz für GCC, Rustc, Clang und Blender.",
        recommended_flags=[],
        workload_type="Compilation"
    ),
    "balanced_daily": SchedProfile(
        name="Balanced Desktop & Media",
        target_scheduler="scx_bpfland",
        description="Gleichmäßige Lastverteilung, reaktionsschnelle UI und flüssiges Browsing.",
        recommended_flags=[],
        workload_type="General"
    ),
    "kernel_stock": SchedProfile(
        name="Kernel Default (BORE / EEVDF)",
        target_scheduler="default",
        description="Standardmäßiger Linux/CachyOS-Kernel-Scheduler ohne sched-ext.",
        recommended_flags=[],
        workload_type="Native"
    )
}
