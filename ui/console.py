"""
ui/console.py — Rich CLI Terminal Formatting & Tabellen-Renderer.
"""

from __future__ import annotations
from typing import List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.text import Text

from core.detector import SystemDetector, CpuInfo, SchedExtStatus
from core.benchmark import BenchmarkResult
from core.profiles import PROFILES

console = Console()

def render_banner() -> None:
    text = Text()
    text.append("⚡ CACHY-SCHED-PILOT ⚡\n", style="bold cyan")
    text.append("Autonomous sched-ext (SCX) Benchmark, Tuner & Workload Governor\n", style="bold white")
    text.append("Tailored for CachyOS / Arch Linux & Linux 6.12+ Sched-EXT Kernels", style="dim gray")
    panel = Panel(text, border_style="cyan", expand=False)
    console.print(panel)

def render_system_status(cpu: CpuInfo, scx: SchedExtStatus) -> None:
    table = Table(title="💻 System- & Sched-EXT Telemetrie", border_style="bright_blue", show_header=True)
    table.add_column("Komponente", style="bold cyan", width=22)
    table.add_column("Status / Details", style="white")

    table.add_row("Betriebssystem", f"CachyOS / Arch Linux (Kernel: {SystemDetector.get_kernel_release()})")
    table.add_row("Prozessor (CPU)", f"{cpu.model} ({cpu.logical_cores} Threads, {cpu.governor})")

    scx_state_style = "bold green" if scx.state == "enabled" else "bold yellow"
    table.add_row("sched-ext Status", f"[{scx_state_style}]{scx.state.upper()}[/{scx_state_style}]")
    
    active_sched_style = "bold green" if scx.state == "enabled" else "bold white"
    table.add_row("Aktiver Scheduler", f"[{active_sched_style}]{scx.active_scheduler}[/{active_sched_style}]")

    installed_str = ", ".join(scx.installed_schedulers) if scx.installed_schedulers else "[dim]Keine gefunden[/dim]"
    table.add_row("Installierte Schedulers", installed_str)

    workload, procs = SystemDetector.detect_active_workload()
    workload_color = "bold magenta" if workload == "GAMING" else "bold yellow" if workload == "COMPILING" else "dim green"
    proc_str = f" ({', '.join(procs)})" if procs else ""
    table.add_row("Erkannte Workload", f"[{workload_color}]{workload}{proc_str}[/{workload_color}]")

    console.print(table)

def render_benchmark_results(results: List[BenchmarkResult]) -> None:
    table = Table(title="🏁 Sched-EXT Micro-Benchmark Vergleich", border_style="green", show_header=True)
    table.add_column("Scheduler", style="bold cyan")
    table.add_column("Rating", justify="center", style="bold")
    table.add_column("Ø Latenz", justify="right")
    table.add_column("P99 Spike", justify="right")
    table.add_column("Jitter (StdDev)", justify="right")
    table.add_column("Ctx Switches/s", justify="right")
    table.add_column("Gaming Score", justify="right", style="bold green")
    table.add_column("Throughput Score", justify="right", style="bold magenta")

    for res in results:
        rating_color = "bold yellow" if res.overall_rating in ["S", "A+"] else "bold white"
        table.add_row(
            res.scheduler_name,
            f"[{rating_color}]{res.overall_rating}[/{rating_color}]",
            f"{res.mean_latency_us:.1f} µs",
            f"{res.p99_latency_us:.1f} µs",
            f"±{res.jitter_std_us:.1f} µs",
            f"{res.ctx_switches_per_sec:,.0f}/s",
            f"{res.gaming_latency_score:.1f}",
            f"{res.throughput_score:.1f}"
        )

    console.print(table)

def render_profiles() -> None:
    table = Table(title="🎯 Verfügbare Scheduler-Profile", border_style="magenta", show_header=True)
    table.add_column("Profil-ID", style="bold cyan")
    table.add_column("Ziel-Scheduler", style="bold green")
    table.add_column("Typ", style="yellow")
    table.add_column("Beschreibung", style="white")

    for pid, prof in PROFILES.items():
        table.add_row(pid, prof.target_scheduler, prof.workload_type, prof.description)

    console.print(table)

def render_doctor_report(report: dict) -> None:
    score = report.get("score", 0)
    score_color = "bold green" if score >= 80 else "bold yellow" if score >= 60 else "bold red"

    table = Table(title=f"🩺 Cachy-Sched-Pilot Doctor Report (System-Score: [{score_color}]{score}%[/{score_color}])", border_style="cyan", show_header=True)
    table.add_column("Prüfung", style="bold white", width=30)
    table.add_column("Status", justify="center", width=10)
    table.add_column("Details & Diagnose", style="white")

    for check in report.get("checks", []):
        st = check.get("status", "INFO")
        if st == "OK":
            st_str = "[bold green]✔ OK[/]"
        elif st == "WARN":
            st_str = "[bold yellow]⚠ WARN[/]"
        elif st == "FAIL":
            st_str = "[bold red]✘ FEHLER[/]"
        else:
            st_str = "[dim]ℹ INFO[/]"
        table.add_row(check.get("name", ""), st_str, check.get("msg", ""))

    console.print(table)

