"""
ui/console.py — Rich CLI Terminal Formatting, Tables and JSON Telemetry Exporter.
"""

from __future__ import annotations
import json
from typing import List, Dict, Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from core.detector import SystemDetector, CpuInfo, SchedExtStatus
from core.benchmark import BenchmarkResult
from core.profiles import PROFILES
from core.i18n import t, I18n

console = Console()


def render_banner() -> None:
    text = Text()
    text.append("⚡ CACHY-SCHED-PILOT ⚡\n", style="bold cyan")
    text.append(f"{t('app_subtitle')}\n", style="bold white")
    text.append(f"{t('app_tagline')}", style="dim gray")
    panel = Panel(text, border_style="cyan", expand=False)
    console.print(panel)


def render_system_status(cpu: CpuInfo, scx: SchedExtStatus) -> None:
    table = Table(title=f"💻 {t('app_title')} — Telemetrie", border_style="bright_blue", show_header=True)
    table.add_column("Komponente", style="bold cyan", width=24)
    table.add_column("Status / Details", style="white")

    table.add_row(t("lbl_os"), f"CachyOS / Arch Linux (Kernel: {SystemDetector.get_kernel_release()})")
    table.add_row("Kernel Scheduler", f"[bold green]{scx.kernel_scheduler_type}[/]")
    
    cpu_detail = f"{cpu.model} ({cpu.logical_cores} {t('lbl_threads')}, {cpu.frequency_mhz:.0f} MHz)"
    table.add_row(t("lbl_cpu"), cpu_detail)
    table.add_row(t("lbl_governor"), f"[yellow]{cpu.governor}[/] (EPP: [cyan]{cpu.epp}[/])")

    scx_state_style = "bold green" if scx.state == "enabled" else "bold yellow"
    table.add_row(t("lbl_scx_status"), f"[{scx_state_style}]{scx.state.upper()}[/{scx_state_style}]")
    
    active_sched_style = "bold green" if scx.state == "enabled" else "bold white"
    table.add_row(t("lbl_active_sched"), f"[{active_sched_style}]{scx.active_scheduler}[/{active_sched_style}]")

    installed_str = ", ".join(scx.installed_schedulers) if scx.installed_schedulers else f"[dim]{t('lbl_none_found')}[/dim]"
    table.add_row(t("lbl_installed_scheds"), installed_str)

    workload, procs = SystemDetector.detect_active_workload()
    workload_color = "bold magenta" if workload == "GAMING" else "bold yellow" if workload == "COMPILING" else "dim green"
    proc_str = f" ({', '.join(procs)})" if procs else ""
    table.add_row(t("lbl_active_workload"), f"[{workload_color}]{workload}{proc_str}[/{workload_color}]")

    if cpu.per_core_load:
        load_summary = " ".join([f"{int(c)}%" for c in cpu.per_core_load[:8]])
        if len(cpu.per_core_load) > 8:
            load_summary += f" ... (+{len(cpu.per_core_load)-8} cores)"
        table.add_row(t("lbl_per_core_load"), f"[cyan]{load_summary}[/]")

    console.print(table)


def get_status_dict() -> Dict[str, Any]:
    """Generates machine-readable telemetry dictionary for JSON output."""
    cpu = SystemDetector.get_cpu_info()
    scx = SystemDetector.detect_scx_status()
    workload, procs = SystemDetector.detect_active_workload()

    return {
        "kernel": {
            "release": SystemDetector.get_kernel_release(),
            "scheduler_type": scx.kernel_scheduler_type,
            "cmdline_flags": scx.cmdline_flags,
        },
        "cpu": {
            "model": cpu.model,
            "physical_cores": cpu.physical_cores,
            "logical_cores": cpu.logical_cores,
            "frequency_mhz": cpu.frequency_mhz,
            "governor": cpu.governor,
            "epp": cpu.epp,
            "per_core_load": cpu.per_core_load,
        },
        "sched_ext": {
            "supported": scx.supported,
            "state": scx.state,
            "active_scheduler": scx.active_scheduler,
            "active_pid": scx.active_pid,
            "installed_schedulers": scx.installed_schedulers,
            "scxctl_installed": scx.scxctl_installed,
            "scx_loader_active": scx.scx_loader_active,
        },
        "workload": {
            "detected": workload,
            "processes": procs,
        }
    }


def render_status_json() -> None:
    data = get_status_dict()
    print(json.dumps(data, indent=2))


def render_benchmark_results(results: List[BenchmarkResult]) -> None:
    table = Table(title=f"🏁 {t('bench_title')}", border_style="green", show_header=True)
    table.add_column(t("bench_col_sched"), style="bold cyan")
    table.add_column(t("bench_col_rating"), justify="center", style="bold")
    table.add_column(t("bench_col_mean_lat"), justify="right")
    table.add_column(t("bench_col_p99"), justify="right")
    table.add_column(t("bench_col_jitter"), justify="right")
    table.add_column(t("bench_col_ctx"), justify="right")
    table.add_column(t("bench_col_gaming"), justify="right", style="bold green")
    table.add_column(t("bench_col_throughput"), justify="right", style="bold magenta")

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
    table = Table(title=f"🎯 {t('prof_title')}", border_style="magenta", show_header=True)
    table.add_column(t("prof_col_id"), style="bold cyan")
    table.add_column(t("prof_col_name"), style="bold white")
    table.add_column(t("prof_col_target"), style="bold green")
    table.add_column(t("prof_col_gov"), style="yellow")
    table.add_column(t("prof_col_desc"), style="dim white")

    for pid, prof in PROFILES.items():
        gov_str = f"{prof.governor} / {prof.epp}"
        table.add_row(pid, prof.name, prof.target_scheduler, gov_str, prof.description)

    console.print(table)


def render_doctor_report(report: dict) -> None:
    score = report.get("score", 0)
    score_color = "bold green" if score >= 80 else "bold yellow" if score >= 60 else "bold red"

    title_str = f"🩺 {t('doc_title')} ({t('doc_score')}: [{score_color}]{score}%[/{score_color}])"
    table = Table(title=title_str, border_style="cyan", show_header=True)
    table.add_column(t("doc_col_check"), style="bold white", width=34)
    table.add_column(t("doc_col_status"), justify="center", width=12)
    table.add_column(t("doc_col_details"), style="white")

    for check in report.get("checks", []):
        st = check.get("status", "INFO")
        if st == "OK":
            st_str = f"[bold green]{t('doc_ok')}[/]"
        elif st == "WARN":
            st_str = f"[bold yellow]{t('doc_warn')}[/]"
        elif st == "FAIL":
            st_str = f"[bold red]{t('doc_fail')}[/]"
        else:
            st_str = f"[dim]{t('doc_info')}[/]"
        table.add_row(check.get("name", ""), st_str, check.get("msg", ""))

    console.print(table)
