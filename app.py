#!/usr/bin/env python3
"""
app.py — Cachy-Sched-Pilot CLI & TUI Master Orchestrator.
Autonomous sched-ext (SCX) Benchmark, Tuner & Workload Governor for CachyOS / Arch Linux.
"""

import argparse
import sys
from pathlib import Path

# Module-Pfad sicherstellen
sys.path.insert(0, str(Path(__file__).resolve().parent))

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
)

def cmd_status():
    render_banner()
    cpu = SystemDetector.get_cpu_info()
    scx = SystemDetector.detect_scx_status()
    render_system_status(cpu, scx)

def cmd_doctor():
    render_banner()
    report = SystemDetector.run_doctor()
    render_doctor_report(report)

def cmd_bench(iterations: int = 1200):
    render_banner()
    scx = SystemDetector.detect_scx_status()
    console.print(f"[bold cyan]Starte Micro-Benchmark für:[/] [bold green]{scx.active_scheduler}[/] ({iterations} Zyklen)...")
    bench = SchedulerBenchmark(iterations=iterations)
    res = bench.run_full_suite(scx.active_scheduler)
    render_benchmark_results([res])

def cmd_switch(target: str):
    mgr = SchedulerManager()
    ok, msg = mgr.switch_scheduler(target)
    if ok:
        console.print(f"[bold green]✔ {msg}[/]")
    else:
        console.print(f"[bold red]✘ {msg}[/]")
        sys.exit(1)

def cmd_stop():
    mgr = SchedulerManager()
    ok, msg = mgr.stop_active_scx()
    if ok:
        console.print(f"[bold green]✔ {msg}[/]")
    else:
        console.print(f"[bold red]✘ {msg}[/]")
        sys.exit(1)

def cmd_governor(interval: float = 3.0):
    render_banner()
    gov = AutopilotGovernor(log_cb=lambda s: console.print(s))
    gov.run_loop(poll_interval_sec=interval)

def cmd_tui():
    from ui.tui import run_tui
    run_tui()

def main():
    parser = argparse.ArgumentParser(
        description="Cachy-Sched-Pilot — Autonomous sched-ext (SCX) Tuner & Governor for CachyOS / Arch Linux"
    )
    subparsers = parser.add_subparsers(dest="command", help="Verfügbare Befehle")

    subparsers.add_parser("status", help="Aktuelle CPU-, Kernel- & sched-ext Telemetrie anzeigen")
    subparsers.add_parser("doctor", help="Umfassende sched-ext & Kernel-Diagnose durchführen")
    
    bench_parser = subparsers.add_parser("bench", help="Micro-Benchmark für den aktiven Scheduler ausführen")
    bench_parser.add_argument("--iterations", "-i", type=int, default=1200, help="Anzahl Test-Iterationen")

    switch_parser = subparsers.add_parser("switch", help="Scheduler wechseln (z. B. scx_lavd, scx_rusty, default)")
    switch_parser.add_argument("scheduler", help="Name des Ziel-Schedulers oder 'default'")

    subparsers.add_parser("stop", help="sched-ext beenden und auf Standard-Kernel zurückschalten")

    gov_parser = subparsers.add_parser("governor", help="Autonomen Workload-Watcher starten (Gaming vs Compile)")
    gov_parser.add_argument("--interval", "-t", type=float, default=3.0, help="Prüfintervall in Sekunden")

    subparsers.add_parser("profiles", help="Vorkonfigurierte Tuning-Profile anzeigen")
    subparsers.add_parser("tui", help="Interaktives Textual Terminal Dashboard starten")

    args = parser.parse_args()

    if not args.command:
        # Wenn kein Befehl übergeben wurde: Status anzeigen & TUI anbieten
        cmd_status()
        console.print("\n[dim]Tipp: Starte '[bold cyan]python app.py tui[/bold cyan]' für das interaktive Dashboard oder '[bold cyan]python app.py doctor[/bold cyan]' für Diagnose.[/dim]\n")
    elif args.command == "status":
        cmd_status()
    elif args.command == "doctor":
        cmd_doctor()
    elif args.command == "bench":
        cmd_bench(iterations=args.iterations)
    elif args.command == "switch":
        cmd_switch(args.scheduler)
    elif args.command == "stop":
        cmd_stop()
    elif args.command == "governor":
        cmd_governor(interval=args.interval)
    elif args.command == "profiles":
        render_profiles()
    elif args.command == "tui":
        cmd_tui()

if __name__ == "__main__":
    main()
