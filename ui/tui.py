"""
ui/tui.py — Interaktives Textual TUI Dashboard für Cachy-Sched-Pilot.
"""

from __future__ import annotations
import asyncio
from typing import List

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Button, Static, TabbedContent, TabPane, DataTable, Label

from core.detector import SystemDetector
from core.benchmark import SchedulerBenchmark, BenchmarkResult
from core.manager import SchedulerManager
from core.profiles import PROFILES

class SchedPilotApp(App):
    CSS = """
    Screen {
        background: #0d1117;
        color: #c9d1d9;
    }
    Header {
        background: #161b22;
        color: #58a6ff;
    }
    Footer {
        background: #161b22;
    }
    .panel-box {
        border: solid #30363d;
        background: #161b22;
        padding: 1 2;
        margin: 1;
        border-title-color: #58a6ff;
    }
    .status-highlight {
        color: #3fb950;
        text-style: bold;
    }
    .action-btn {
        margin: 1;
    }
    """

    TITLE = "⚡ Cachy-Sched-Pilot"
    SUB_TITLE = "Autonomous sched-ext (SCX) Tuner & Governor"

    def __init__(self):
        super().__init__()
        self.manager = SchedulerManager()
        self.benchmark = SchedulerBenchmark(iterations=800, target_sleep_us=150)
        self.bench_results: List[BenchmarkResult] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(initial="tab_dashboard"):
            with TabPane("🎮 Dashboard & Status", id="tab_dashboard"):
                yield VerticalScroll(
                    Static(id="telemetry_box", classes="panel-box"),
                    Horizontal(
                        Button("⚡ scx_lavd (Gaming)", id="btn_lavd", variant="primary", classes="action-btn"),
                        Button("🔨 scx_rusty (Compile)", id="btn_rusty", variant="success", classes="action-btn"),
                        Button("⚖️ scx_bpfland (Balanced)", id="btn_bpfland", variant="default", classes="action-btn"),
                        Button("💤 Kernel Stock (Default)", id="btn_default", variant="warning", classes="action-btn"),
                        id="switch_buttons"
                    ),
                    Static(id="action_status", classes="panel-box")
                )
            with TabPane("🏁 Micro-Benchmark", id="tab_bench"):
                yield VerticalScroll(
                    Horizontal(
                        Button("▶ Benchmark starten (Aktiver Scheduler)", id="btn_run_bench", variant="primary", classes="action-btn"),
                        Button("🔄 Alle installierten Schedulers testen", id="btn_run_bench_all", variant="success", classes="action-btn")
                    ),
                    Static(id="bench_progress_label", content="Bereit für Benchmark-Lauf."),
                    DataTable(id="bench_table", classes="panel-box")
                )
            with TabPane("🎯 Profile & Tuning", id="tab_profiles"):
                yield VerticalScroll(
                    DataTable(id="profiles_table", classes="panel-box")
                )
        yield Footer()

    def on_mount(self) -> None:
        self.update_telemetry()
        self.init_tables()
        self.set_interval(2.0, self.update_telemetry)

    def update_telemetry(self) -> None:
        cpu = SystemDetector.get_cpu_info()
        scx = SystemDetector.detect_scx_status()
        workload, procs = SystemDetector.detect_active_workload()

        state_color = "green" if scx.state == "enabled" else "yellow"
        text = (
            f"[bold cyan]CPU:[/] {cpu.model} ({cpu.logical_cores} Threads, {cpu.governor})\n"
            f"[bold cyan]Kernel:[/] {SystemDetector.get_kernel_release()}\n"
            f"[bold cyan]sched-ext Status:[/] [{state_color}]{scx.state.upper()}[/{state_color}]\n"
            f"[bold cyan]Aktiver Scheduler:[/] [bold green]{scx.active_scheduler}[/]\n"
            f"[bold cyan]Erkannte Workload:[/] [bold magenta]{workload}[/] ({', '.join(procs) or 'Keine Spezialprozesse'})\n"
            f"[bold cyan]Installierte Schedulers:[/] {', '.join(scx.installed_schedulers) or 'Keine'}"
        )
        box = self.query_one("#telemetry_box", Static)
        box.update(text)

    def init_tables(self) -> None:
        b_table = self.query_one("#bench_table", DataTable)
        b_table.add_columns("Scheduler", "Rating", "Ø Latenz", "P99 Spike", "Jitter", "Ctx Sw/s", "Gaming", "Throughput")

        p_table = self.query_one("#profiles_table", DataTable)
        p_table.add_columns("Profil", "Ziel-Scheduler", "Typ", "Beschreibung")
        for pid, p in PROFILES.items():
            p_table.add_row(p.name, p.target_scheduler, p.workload_type, p.description)

    async def on_button_pressed(self, event: Button.ButtonEvent) -> None:
        bid = event.button.id
        status_box = self.query_one("#action_status", Static)

        if bid == "btn_lavd":
            ok, msg = self.manager.switch_scheduler("scx_lavd")
            status_box.update(f"[{'green' if ok else 'red'}]{msg}[/]")
            self.update_telemetry()
        elif bid == "btn_rusty":
            ok, msg = self.manager.switch_scheduler("scx_rusty")
            status_box.update(f"[{'green' if ok else 'red'}]{msg}[/]")
            self.update_telemetry()
        elif bid == "btn_bpfland":
            ok, msg = self.manager.switch_scheduler("scx_bpfland")
            status_box.update(f"[{'green' if ok else 'red'}]{msg}[/]")
            self.update_telemetry()
        elif bid == "btn_default":
            ok, msg = self.manager.stop_active_scx()
            status_box.update(f"[{'green' if ok else 'red'}]{msg}[/]")
            self.update_telemetry()
        elif bid == "btn_run_bench":
            prog_label = self.query_one("#bench_progress_label", Static)
            prog_label.update("⏳ Benchmark läuft... bitte warten...")
            
            scx = SystemDetector.detect_scx_status()
            res = await asyncio.to_thread(self.benchmark.run_full_suite, scx.active_scheduler)
            
            b_table = self.query_one("#bench_table", DataTable)
            b_table.add_row(
                res.scheduler_name,
                res.overall_rating,
                f"{res.mean_latency_us} µs",
                f"{res.p99_latency_us} µs",
                f"±{res.jitter_std_us} µs",
                f"{res.ctx_switches_per_sec:,.0f}/s",
                str(res.gaming_latency_score),
                str(res.throughput_score)
            )
            prog_label.update("✅ Benchmark erfolgreich abgeschlossen!")
        elif bid == "btn_run_bench_all":
            prog_label = self.query_one("#bench_progress_label", Static)
            b_table = self.query_one("#bench_table", DataTable)
            scx = SystemDetector.detect_scx_status()
            sched_list = scx.installed_schedulers if scx.installed_schedulers else ["default"]

            prog_label.update(f"⏳ Starte Multi-Benchmark für {len(sched_list)} Scheduler...")
            for s_name in sched_list:
                prog_label.update(f"⏳ Benchmark für [bold cyan]{s_name}[/] läuft...")
                res = await asyncio.to_thread(self.benchmark.run_full_suite, s_name)
                b_table.add_row(
                    res.scheduler_name,
                    res.overall_rating,
                    f"{res.mean_latency_us} µs",
                    f"{res.p99_latency_us} µs",
                    f"±{res.jitter_std_us} µs",
                    f"{res.ctx_switches_per_sec:,.0f}/s",
                    str(res.gaming_latency_score),
                    str(res.throughput_score)
                )
            prog_label.update("✅ Alle Scheduler erfolgreich gebencht!")

def run_tui():
    app = SchedPilotApp()
    app.run()
