"""
ui/tui.py — Interactive Textual Terminal Dashboard for Cachy-Sched-Pilot.
Provides real-time telemetry, per-core CPU bars, scheduler switching,
system health diagnostics, and micro-benchmarking with full de_DE/en_US i18n.
"""

from __future__ import annotations
import asyncio
import shutil
from typing import List, Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Button, Static, TabbedContent, TabPane, DataTable, Label, ProgressBar

from core.detector import SystemDetector
from core.benchmark import SchedulerBenchmark, BenchmarkResult
from core.manager import SchedulerManager
from core.profiles import PROFILES
from core.i18n import I18n, t


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
    .btn-disabled {
        opacity: 0.5;
    }
    #core_bars_box {
        background: #161b22;
        border: solid #30363d;
        padding: 1;
        margin: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Beenden / Quit", priority=True),
        Binding("r", "refresh_data", "Aktualisieren / Refresh"),
        Binding("l", "toggle_lang", "Sprache / Language"),
        Binding("b", "run_active_bench", "Benchmark"),
        Binding("d", "run_doctor_diag", "Doctor"),
    ]

    def __init__(self, lang: Optional[str] = None):
        super().__init__()
        if lang:
            I18n.set_language(lang)
        self.manager = SchedulerManager()
        self.benchmark = SchedulerBenchmark(iterations=600, target_sleep_us=150)
        self.bench_results: List[BenchmarkResult] = []

    def compose(self) -> ComposeResult:
        self.title = t("app_title")
        self.sub_title = t("app_subtitle")

        yield Header(show_clock=True)
        with TabbedContent(initial="tab_dashboard"):
            # Tab 1: Dashboard
            with TabPane(t("tab_dashboard"), id="tab_dashboard"):
                yield VerticalScroll(
                    Static(id="telemetry_box", classes="panel-box"),
                    Static(id="core_bars_box"),
                    Horizontal(
                        Button(t("btn_switch_lavd"), id="btn_lavd", variant="primary", classes="action-btn"),
                        Button(t("btn_switch_rusty"), id="btn_rusty", variant="success", classes="action-btn"),
                        Button(t("btn_switch_bpfland"), id="btn_bpfland", variant="default", classes="action-btn"),
                        Button(t("btn_switch_default"), id="btn_default", variant="warning", classes="action-btn"),
                        Button(t("btn_lang_toggle"), id="btn_lang", variant="primary", classes="action-btn"),
                        id="switch_buttons"
                    ),
                    Static(id="action_status", classes="panel-box")
                )

            # Tab 2: Micro-Benchmark
            with TabPane(t("tab_bench"), id="tab_bench"):
                yield VerticalScroll(
                    Horizontal(
                        Button(t("btn_run_bench"), id="btn_run_bench", variant="primary", classes="action-btn"),
                        Button(t("btn_run_bench_all"), id="btn_run_bench_all", variant="success", classes="action-btn")
                    ),
                    Static(id="bench_progress_label", content=t("bench_status_ready")),
                    DataTable(id="bench_table", classes="panel-box")
                )

            # Tab 3: System Doctor
            with TabPane(t("tab_doctor"), id="tab_doctor"):
                yield VerticalScroll(
                    Horizontal(
                        Button(t("btn_run_doctor"), id="btn_recheck_doctor", variant="primary", classes="action-btn"),
                        Static(id="doctor_score_label", classes="action-btn")
                    ),
                    DataTable(id="doctor_table", classes="panel-box")
                )

            # Tab 4: Profiles & Tuning
            with TabPane(t("tab_profiles"), id="tab_profiles"):
                yield VerticalScroll(
                    Horizontal(
                        Button("⚡ Gaming", id="btn_prof_gaming", variant="primary", classes="action-btn"),
                        Button("🎵 Audio DAW", id="btn_prof_audio", variant="primary", classes="action-btn"),
                        Button("🔨 Compile", id="btn_prof_compile", variant="success", classes="action-btn"),
                        Button("⚖️ Balanced", id="btn_prof_balanced", variant="default", classes="action-btn"),
                        Button("🔋 PowerSave", id="btn_prof_powersave", variant="warning", classes="action-btn"),
                    ),
                    DataTable(id="profiles_table", classes="panel-box")
                )

        yield Footer()

    def on_mount(self) -> None:
        self.update_telemetry()
        self.init_tables()
        self.run_doctor_check()
        self.validate_button_capabilities()
        self.set_interval(2.0, self.update_telemetry)

    def validate_button_capabilities(self) -> None:
        """Dynamically validates presence of binaries and disables unsupported buttons gracefully."""
        status = SystemDetector.detect_scx_status()
        if not status.supported:
            self.query_one("#btn_lavd", Button).disabled = True
            self.query_one("#btn_rusty", Button).disabled = True
            self.query_one("#btn_bpfland", Button).disabled = True
            return

        self.query_one("#btn_lavd", Button).disabled = not bool(shutil.which("scx_lavd"))
        self.query_one("#btn_rusty", Button).disabled = not bool(shutil.which("scx_rusty"))
        self.query_one("#btn_bpfland", Button).disabled = not bool(shutil.which("scx_bpfland"))

    def action_refresh_data(self) -> None:
        self.update_telemetry()

    def action_toggle_lang(self) -> None:
        new_lang = I18n.toggle_language()
        self.title = t("app_title")
        self.sub_title = t("app_subtitle")
        self.query_one("#btn_lang", Button).label = t("btn_lang_toggle")
        self.update_telemetry()
        self.init_tables()
        self.run_doctor_check()

    def action_run_active_bench(self) -> None:
        asyncio.create_task(self.execute_benchmark_single())

    def action_run_doctor_diag(self) -> None:
        self.run_doctor_check()

    def update_telemetry(self) -> None:
        # Check safety crash fallback
        recovered, crash_msg = self.manager.check_and_recover_safety()
        if recovered and crash_msg:
            self.query_one("#action_status", Static).update(f"[bold red]{crash_msg}[/]")

        cpu = SystemDetector.get_cpu_info()
        scx = SystemDetector.detect_scx_status()
        workload, procs = SystemDetector.detect_active_workload()

        state_color = "green" if scx.state == "enabled" else "yellow"
        text = (
            f"[bold cyan]{t('lbl_cpu')}:[/] {cpu.model} ({cpu.logical_cores} {t('lbl_threads')}, {cpu.frequency_mhz:.0f} MHz)\n"
            f"[bold cyan]{t('lbl_governor')}:[/] [yellow]{cpu.governor}[/] (EPP: [cyan]{cpu.epp}[/])\n"
            f"[bold cyan]{t('lbl_kernel')}:[/] {SystemDetector.get_kernel_release()} — Native Scheduler: [bold green]{scx.kernel_scheduler_type}[/]\n"
            f"[bold cyan]{t('lbl_scx_status')}:[/] [{state_color}]{scx.state.upper()}[/{state_color}]\n"
            f"[bold cyan]{t('lbl_active_sched')}:[/] [bold green]{scx.active_scheduler}[/]\n"
            f"[bold cyan]{t('lbl_active_workload')}:[/] [bold magenta]{workload}[/] ({', '.join(procs) or t('lbl_none')})\n"
            f"[bold cyan]{t('lbl_installed_scheds')}:[/] {', '.join(scx.installed_schedulers) or t('lbl_none_found')}"
        )
        box = self.query_one("#telemetry_box", Static)
        box.update(text)

        # Render Per-Core Visual Bars
        if cpu.per_core_load:
            core_lines = [f"[bold cyan]{t('lbl_per_core_load')}:[/]"]
            row_items = []
            for idx, load in enumerate(cpu.per_core_load):
                color = "green" if load < 40 else "yellow" if load < 75 else "red"
                bar_len = int(load / 10)
                bar_str = "■" * bar_len + " " * (10 - bar_len)
                row_items.append(f"C{idx:02d}: [{color}][{bar_str}] {load:4.1f}%[/{color}]")
                if len(row_items) == 4 or idx == len(cpu.per_core_load) - 1:
                    core_lines.append("   " + "  ".join(row_items))
                    row_items = []
            self.query_one("#core_bars_box", Static).update("\n".join(core_lines))

    def init_tables(self) -> None:
        # Benchmark Table
        b_table = self.query_one("#bench_table", DataTable)
        b_table.clear(columns=True)
        b_table.add_columns(
            t("bench_col_sched"),
            t("bench_col_rating"),
            t("bench_col_mean_lat"),
            t("bench_col_p99"),
            t("bench_col_jitter"),
            t("bench_col_ctx"),
            t("bench_col_gaming"),
            t("bench_col_throughput")
        )

        # Profiles Table
        p_table = self.query_one("#profiles_table", DataTable)
        p_table.clear(columns=True)
        p_table.add_columns(
            t("prof_col_id"),
            t("prof_col_name"),
            t("prof_col_target"),
            t("prof_col_gov"),
            t("prof_col_type"),
            t("prof_col_desc")
        )
        for pid, p in PROFILES.items():
            gov_str = f"{p.governor} / {p.epp}"
            p_table.add_row(pid, p.name, p.target_scheduler, gov_str, p.workload_type, p.description)

    def run_doctor_check(self) -> None:
        report = SystemDetector.run_doctor()
        score = report.get("score", 0)
        score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
        score_label = self.query_one("#doctor_score_label", Static)
        score_label.update(f"[bold {score_color}]{t('doc_score')}: {score}%[/]")

        d_table = self.query_one("#doctor_table", DataTable)
        d_table.clear(columns=True)
        d_table.add_columns(t("doc_col_check"), t("doc_col_status"), t("doc_col_details"))

        for c in report.get("checks", []):
            st = c.get("status", "INFO")
            if st == "OK":
                st_str = f"[bold green]{t('doc_ok')}[/]"
            elif st == "WARN":
                st_str = f"[bold yellow]{t('doc_warn')}[/]"
            elif st == "FAIL":
                st_str = f"[bold red]{t('doc_fail')}[/]"
            else:
                st_str = f"[dim]{t('doc_info')}[/]"
            d_table.add_row(c.get("name", ""), st_str, c.get("msg", ""))

    async def execute_benchmark_single(self) -> None:
        prog_label = self.query_one("#bench_progress_label", Static)
        prog_label.update(f"[bold yellow]{t('bench_status_running')}[/]")
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
        prog_label.update(f"[bold green]{t('bench_status_done')}[/]")

    async def execute_benchmark_all(self) -> None:
        prog_label = self.query_one("#bench_progress_label", Static)
        b_table = self.query_one("#bench_table", DataTable)
        scx = SystemDetector.detect_scx_status()
        sched_list = scx.installed_schedulers if scx.installed_schedulers else ["default"]

        for s_name in sched_list:
            prog_label.update(f"⏳ Running benchmark for [bold cyan]{s_name}[/]...")
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
        prog_label.update(f"[bold green]{t('bench_status_all_done')}[/]")

    async def on_button_pressed(self, event: Button.ButtonEvent) -> None:
        bid = event.button.id
        status_box = self.query_one("#action_status", Static)

        # Scheduler switches
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
        elif bid == "btn_lang":
            self.action_toggle_lang()

        # Benchmarks
        elif bid == "btn_run_bench":
            await self.execute_benchmark_single()
        elif bid == "btn_run_bench_all":
            await self.execute_benchmark_all()

        # Doctor
        elif bid == "btn_recheck_doctor":
            self.run_doctor_check()

        # Profiles
        elif bid == "btn_prof_gaming":
            ok, msg = self.manager.apply_profile("gaming")
            status_box.update(f"[{'green' if ok else 'red'}]{msg}[/]")
            self.update_telemetry()
        elif bid == "btn_prof_audio":
            ok, msg = self.manager.apply_profile("lowlatency")
            status_box.update(f"[{'green' if ok else 'red'}]{msg}[/]")
            self.update_telemetry()
        elif bid == "btn_prof_compile":
            ok, msg = self.manager.apply_profile("compile")
            status_box.update(f"[{'green' if ok else 'red'}]{msg}[/]")
            self.update_telemetry()
        elif bid == "btn_prof_balanced":
            ok, msg = self.manager.apply_profile("balanced")
            status_box.update(f"[{'green' if ok else 'red'}]{msg}[/]")
            self.update_telemetry()
        elif bid == "btn_prof_powersave":
            ok, msg = self.manager.apply_profile("powersave")
            status_box.update(f"[{'green' if ok else 'red'}]{msg}[/]")
            self.update_telemetry()


def run_tui(lang: Optional[str] = None):
    app = SchedPilotApp(lang=lang)
    app.run()
