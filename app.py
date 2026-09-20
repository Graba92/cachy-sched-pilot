#!/usr/bin/env python3
"""
app.py — Cachy-Sched-Pilot CLI & TUI Master Orchestrator.
Autonomous sched-ext (SCX) Benchmark, Tuner & Workload Governor for CachyOS / Arch Linux.
Supports full headless CLI automation, JSON telemetry, and interactive Textual TUI.
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

# Ensure root module import
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.i18n import I18n, t
from core.config import ConfigManager
from core.detector import SystemDetector
from core.benchmark import SchedulerBenchmark
from core.manager import SchedulerManager
from core.governor import AutopilotGovernor
from core.profiles import PROFILES
from ui.console import (
    console,
    render_banner,
    render_system_status,
    render_benchmark_results,
    render_profiles,
    render_doctor_report,
    render_status_json,
)


def cmd_status(json_format: bool = False) -> None:
    if json_format:
        render_status_json()
        return
    render_banner()
    cpu = SystemDetector.get_cpu_info()
    scx = SystemDetector.detect_scx_status()
    render_system_status(cpu, scx)


def cmd_doctor() -> None:
    render_banner()
    report = SystemDetector.run_doctor()
    render_doctor_report(report)


def cmd_bench(iterations: int = 1200) -> None:
    render_banner()
    scx = SystemDetector.detect_scx_status()
    console.print(f"[bold cyan]Micro-Benchmark:[/] [bold green]{scx.active_scheduler}[/] ({iterations} cycles)...")
    bench = SchedulerBenchmark(iterations=iterations)
    res = bench.run_full_suite(scx.active_scheduler)
    render_benchmark_results([res])


def cmd_switch(target: str) -> None:
    mgr = SchedulerManager()
    ok, msg = mgr.switch_scheduler(target)
    if ok:
        console.print(f"[bold green]✔ {msg}[/]")
    else:
        console.print(f"[bold red]✘ {msg}[/]")
        sys.exit(1)


def cmd_profile(profile_name: str) -> None:
    mgr = SchedulerManager()
    ok, msg = mgr.apply_profile(profile_name)
    if ok:
        console.print(f"[bold green]✔ {msg}[/]")
    else:
        console.print(f"[bold red]✘ {msg}[/]")
        sys.exit(1)


def cmd_stop() -> None:
    mgr = SchedulerManager()
    ok, msg = mgr.stop_active_scx()
    if ok:
        console.print(f"[bold green]✔ {msg}[/]")
    else:
        console.print(f"[bold red]✘ {msg}[/]")
        sys.exit(1)


def cmd_governor(interval: float = 3.0) -> None:
    render_banner()
    gov = AutopilotGovernor(log_cb=lambda s: console.print(s))
    gov.run_loop(poll_interval_sec=interval)


def cmd_tui(lang: str = "de") -> None:
    from ui.tui import run_tui
    run_tui(lang=lang)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cachy-sched-pilot",
        description=t("cli_help_desc")
    )

    # Top-level automation flags (for scripts, Hyprland/KDE keybindings, udev rules)
    parser.add_argument("--status", action="store_true", help=t("cli_help_status"))
    parser.add_argument("--json", action="store_true", help=t("cli_help_json"))
    parser.add_argument("--set-profile", metavar="PROFILE", type=str, help=t("cli_help_profile"))
    parser.add_argument("--set-sched", metavar="SCHEDULER", type=str, help=t("cli_help_switch"))
    parser.add_argument("--doctor", action="store_true", help=t("cli_help_doctor"))
    parser.add_argument("--bench", action="store_true", help=t("cli_help_bench"))
    parser.add_argument("--lang", choices=["de", "en"], default=None, help=t("cli_help_lang"))

    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    sub_status = subparsers.add_parser("status", help=t("cli_help_status"))
    sub_status.add_argument("--json", action="store_true", help=t("cli_help_json"))

    subparsers.add_parser("doctor", help=t("cli_help_doctor"))

    bench_parser = subparsers.add_parser("bench", help=t("cli_help_bench"))
    bench_parser.add_argument("--iterations", "-i", type=int, default=1200, help="Cycles")

    switch_parser = subparsers.add_parser("switch", help=t("cli_help_switch"))
    switch_parser.add_argument("scheduler", help="Scheduler name (e.g. scx_lavd, default)")

    prof_parser = subparsers.add_parser("profile", help=t("cli_help_profile"))
    prof_parser.add_argument("name", help="Profile name (e.g. gaming, compile, balanced, powersave)")

    subparsers.add_parser("stop", help=t("cli_help_stop"))

    gov_parser = subparsers.add_parser("governor", help=t("cli_help_governor"))
    gov_parser.add_argument("--interval", "-t", type=float, default=3.0, help="Interval in sec")

    subparsers.add_parser("profiles", help="Show pre-tuned scheduler profiles")
    subparsers.add_parser("tui", help=t("cli_help_tui"))

    return parser


def main() -> None:
    # Load configuration
    cfg = ConfigManager.load()
    default_lang = cfg.get("general", {}).get("language", "de")
    I18n.set_language(default_lang)

    parser = build_parser()
    args = parser.parse_args()

    # Override language if requested via CLI
    if args.lang:
        I18n.set_language(args.lang)

    # Handle Top-level automation flags first
    if args.status:
        cmd_status(json_format=args.json)
        return
    if args.set_profile:
        cmd_profile(args.set_profile)
        return
    if args.set_sched:
        cmd_switch(args.set_sched)
        return
    if args.doctor:
        cmd_doctor()
        return
    if args.bench:
        cmd_bench()
        return

    # Handle Subcommands
    if not args.command:
        # Default behavior: Print status & offer TUI/Doctor hint
        cmd_status(json_format=args.json)
        console.print(
            "\n[dim]Hint: Launch interactive TUI with '[bold cyan]cachy-sched-pilot tui[/bold cyan]' "
            "or diagnostics with '[bold cyan]cachy-sched-pilot doctor[/bold cyan]'.[/dim]\n"
        )
    elif args.command == "status":
        cmd_status(json_format=args.json)
    elif args.command == "doctor":
        cmd_doctor()
    elif args.command == "bench":
        cmd_bench(iterations=args.iterations)
    elif args.command == "switch":
        cmd_switch(args.scheduler)
    elif args.command == "profile":
        cmd_profile(args.name)
    elif args.command == "stop":
        cmd_stop()
    elif args.command == "governor":
        cmd_governor(interval=args.interval)
    elif args.command == "profiles":
        render_profiles()
    elif args.command == "tui":
        cmd_tui(lang=I18n.get_language())


if __name__ == "__main__":
    main()
