"""
core/i18n.py — Internationalization (i18n) Engine for Cachy-Sched-Pilot.
Provides seamless German (de_DE) and English (en_US) translations with dynamic switching.
"""

from __future__ import annotations
import os
import locale
from typing import Dict, Any

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "de": {
        # App & Header
        "app_title": "⚡ Cachy-Sched-Pilot",
        "app_subtitle": "Autonomer sched-ext (SCX) Tuner, Benchmark & Governor für CachyOS / Arch Linux",
        "app_tagline": "Maßgeschneidert für CachyOS / Arch Linux & Linux 6.12+ Sched-EXT Kernel",
        
        # Navigation & Tabs
        "tab_dashboard": "🎮 Dashboard & Live-Telemetrie",
        "tab_bench": "🏁 Micro-Benchmark",
        "tab_doctor": "🩺 System-Diagnose (Doctor)",
        "tab_profiles": "🎯 Profile & Tuning",
        
        # Telemetry Labels
        "lbl_os": "Betriebssystem",
        "lbl_kernel": "Kernel",
        "lbl_cpu": "Prozessor (CPU)",
        "lbl_governor": "CPU Governor",
        "lbl_epp": "EPP (Energie-Präferenz)",
        "lbl_scx_status": "sched-ext Status",
        "lbl_active_sched": "Aktiver Scheduler",
        "lbl_installed_scheds": "Installierte Schedulers",
        "lbl_active_workload": "Erkannte Workload",
        "lbl_per_core_load": "Auslastung pro Kern",
        "lbl_threads": "Threads",
        "lbl_cores": "Kerne",
        "lbl_none": "Keine",
        "lbl_none_found": "Keine gefunden",
        "lbl_unknown": "Unbekannt",
        
        # Actions & Buttons
        "btn_switch_lavd": "⚡ scx_lavd (Gaming)",
        "btn_switch_rusty": "🔨 scx_rusty (Compile)",
        "btn_switch_bpfland": "⚖️ scx_bpfland (Balanced)",
        "btn_switch_default": "💤 Kernel Stock (Default)",
        "btn_run_bench": "▶ Benchmark starten (Aktiver Scheduler)",
        "btn_run_bench_all": "🔄 Alle installierten Schedulers testen",
        "btn_run_doctor": "🩺 Diagnose erneut ausführen",
        "btn_apply_profile": "Aktivieren",
        "btn_lang_toggle": "🌐 Sprache: Deutsch (Taste: L)",
        
        # Benchmark
        "bench_title": "Sched-EXT Micro-Benchmark Vergleich",
        "bench_col_sched": "Scheduler",
        "bench_col_rating": "Rating",
        "bench_col_mean_lat": "Ø Latenz",
        "bench_col_p99": "P99 Spike",
        "bench_col_jitter": "Jitter (StdDev)",
        "bench_col_ctx": "Ctx Sw/s",
        "bench_col_gaming": "Gaming Score",
        "bench_col_throughput": "Durchsatz Score",
        "bench_status_ready": "Bereit für Micro-Benchmark.",
        "bench_status_running": "⏳ Benchmark läuft... bitte warten...",
        "bench_status_done": "✅ Benchmark erfolgreich abgeschlossen!",
        "bench_status_all_done": "✅ Alle Scheduler erfolgreich getestet!",
        
        # Doctor / Diagnostic
        "doc_title": "Cachy-Sched-Pilot Doctor Report",
        "doc_score": "System-Score",
        "doc_col_check": "Prüfung",
        "doc_col_status": "Status",
        "doc_col_details": "Details & Empfehlung",
        "doc_check_kernel_scx": "Kernel sched-ext (sysfs)",
        "doc_check_cachy_kernel": "CachyOS Kernel Optimierungen",
        "doc_check_bpf_jit": "eBPF JIT Compiler",
        "doc_check_scx_binaries": "Installierte SCX Schedulers",
        "doc_check_scxctl": "scxctl D-Bus Client",
        "doc_check_privileges": "Ausführungsrechte & Polkit",
        "doc_ok": "✔ OK",
        "doc_warn": "⚠ WARNUNG",
        "doc_fail": "✘ FEHLER",
        "doc_info": "ℹ INFO",
        
        # Profiles
        "prof_title": "Verfügbare Scheduler-Profile",
        "prof_col_id": "Profil-ID",
        "prof_col_name": "Profil-Name",
        "prof_col_target": "Ziel-Scheduler",
        "prof_col_gov": "Governor / EPP",
        "prof_col_type": "Typ",
        "prof_col_desc": "Beschreibung",
        
        # Profile Descriptions
        "prof_gaming_name": "Gaming & E-Sports (Low Latency)",
        "prof_gaming_desc": "Minimiert Latenz-Jitter und 1% Low Drops für maximale FPS-Stabilität.",
        "prof_compile_name": "Compile & Multi-Core Rendering",
        "prof_compile_desc": "Maximaler Thread-Durchsatz für GCC, Rustc, Clang und Blender.",
        "prof_balanced_name": "Balanced Desktop & Media",
        "prof_balanced_desc": "Gleichmäßige Lastverteilung, reaktionsschnelle UI und flüssiges Browsing.",
        "prof_audio_name": "Pro Audio & DAW (Zero Xrun)",
        "prof_audio_desc": "Ultra-niedriger Jitter und garantierte Zeitscheiben für JACK, PipeWire und DAWs.",
        "prof_emulation_name": "Emulation & High-Cache (RPCS3/Ryujinx)",
        "prof_emulation_desc": "Optimiert für intensive JIT-Rekompilierung und Inter-Core Synchronisation.",
        "prof_powersave_name": "Power Saving & Akku-Schonung",
        "prof_powersave_desc": "Aggressive Energieeinsparung, Senkung von Taktung und Kern-Wakeups.",
        "prof_stock_name": "Kernel Default (BORE / EEVDF)",
        "prof_stock_desc": "Standardmäßiger Linux/CachyOS-Kernel-Scheduler ohne sched-ext.",
        
        # Messages & Status
        "msg_switched_success": "Scheduler '{sched}' erfolgreich aktiviert.",
        "msg_switched_fail": "Fehler beim Aktivieren von '{sched}': {err}",
        "msg_reverted_default": "Erfolgreich auf Kernel-Default zurückgekehrt.",
        "msg_stop_fail": "Scheduler konnte nicht beendet werden: {err}",
        "msg_already_default": "Bereits auf Standard-Kernel (sched-ext ist inaktiv).",
        "msg_crash_detected": "⚠️ WARNUNG: Crash von sched-ext erkannt! Automatischer Fallback auf Kernel-Default aktiv.",
        "msg_profile_applied": "Profil '{name}' erfolgreich angewendet.",
        "msg_not_installed": "Binary '{binary}' ist nicht im System-PATH installiert.",
        "msg_helper_not_found": "Backend-Helper '{path}' nicht gefunden.",
        "msg_privilege_error": "Root- oder Polkit-Berechtigung verweigert.",
        
        # CLI
        "cli_help_desc": "Cachy-Sched-Pilot — Autonomer sched-ext (SCX) Tuner & Governor für CachyOS / Arch Linux",
        "cli_help_status": "Aktuelle CPU-, Kernel- & sched-ext Telemetrie anzeigen",
        "cli_help_doctor": "Umfassende sched-ext & Kernel-Diagnose durchführen",
        "cli_help_bench": "Micro-Benchmark für den aktiven Scheduler ausführen",
        "cli_help_switch": "Scheduler wechseln (z. B. scx_lavd, scx_rusty, default)",
        "cli_help_profile": "Vordefiniertes Profil aktivieren (z. B. gaming, compile, balanced, powersave)",
        "cli_help_stop": "sched-ext beenden und auf Standard-Kernel zurückschalten",
        "cli_help_governor": "Autonomen Workload-Watcher starten (Gaming vs Compile)",
        "cli_help_tui": "Interaktives Terminal Dashboard (TUI) starten",
        "cli_help_json": "Ausgabe als maschinenlesbares JSON formatieren",
        "cli_help_lang": "Sprache erzwingen ('de' oder 'en')",
    },
    "en": {
        # App & Header
        "app_title": "⚡ Cachy-Sched-Pilot",
        "app_subtitle": "Autonomous sched-ext (SCX) Tuner, Benchmark & Governor for CachyOS / Arch Linux",
        "app_tagline": "Tailored for CachyOS / Arch Linux & Linux 6.12+ Sched-EXT Kernels",
        
        # Navigation & Tabs
        "tab_dashboard": "🎮 Dashboard & Live Telemetry",
        "tab_bench": "🏁 Micro-Benchmark",
        "tab_doctor": "🩺 System Diagnostics (Doctor)",
        "tab_profiles": "🎯 Profiles & Tuning",
        
        # Telemetry Labels
        "lbl_os": "Operating System",
        "lbl_kernel": "Kernel",
        "lbl_cpu": "Processor (CPU)",
        "lbl_governor": "CPU Governor",
        "lbl_epp": "EPP (Energy Preference)",
        "lbl_scx_status": "sched-ext Status",
        "lbl_active_sched": "Active Scheduler",
        "lbl_installed_scheds": "Installed Schedulers",
        "lbl_active_workload": "Detected Workload",
        "lbl_per_core_load": "Per-Core Utilization",
        "lbl_threads": "Threads",
        "lbl_cores": "Cores",
        "lbl_none": "None",
        "lbl_none_found": "None found",
        "lbl_unknown": "Unknown",
        
        # Actions & Buttons
        "btn_switch_lavd": "⚡ scx_lavd (Gaming)",
        "btn_switch_rusty": "🔨 scx_rusty (Compile)",
        "btn_switch_bpfland": "⚖️ scx_bpfland (Balanced)",
        "btn_switch_default": "💤 Stock Kernel (Default)",
        "btn_run_bench": "▶ Run Benchmark (Active Scheduler)",
        "btn_run_bench_all": "🔄 Benchmark All Installed Schedulers",
        "btn_run_doctor": "🩺 Re-run Diagnostics",
        "btn_apply_profile": "Apply",
        "btn_lang_toggle": "🌐 Language: English (Key: L)",
        
        # Benchmark
        "bench_title": "Sched-EXT Micro-Benchmark Comparison",
        "bench_col_sched": "Scheduler",
        "bench_col_rating": "Rating",
        "bench_col_mean_lat": "Mean Latency",
        "bench_col_p99": "P99 Spike",
        "bench_col_jitter": "Jitter (StdDev)",
        "bench_col_ctx": "Ctx Sw/s",
        "bench_col_gaming": "Gaming Score",
        "bench_col_throughput": "Throughput Score",
        "bench_status_ready": "Ready for micro-benchmark.",
        "bench_status_running": "⏳ Benchmark in progress... please wait...",
        "bench_status_done": "✅ Benchmark successfully completed!",
        "bench_status_all_done": "✅ All schedulers successfully tested!",
        
        # Doctor / Diagnostic
        "doc_title": "Cachy-Sched-Pilot Doctor Report",
        "doc_score": "System Score",
        "doc_col_check": "Check",
        "doc_col_status": "Status",
        "doc_col_details": "Details & Recommendation",
        "doc_check_kernel_scx": "Kernel sched-ext (sysfs)",
        "doc_check_cachy_kernel": "CachyOS Kernel Optimizations",
        "doc_check_bpf_jit": "eBPF JIT Compiler",
        "doc_check_scx_binaries": "Installed SCX Schedulers",
        "doc_check_scxctl": "scxctl D-Bus Client",
        "doc_check_privileges": "Execution Privileges & Polkit",
        "doc_ok": "✔ OK",
        "doc_warn": "⚠ WARN",
        "doc_fail": "✘ FAIL",
        "doc_info": "ℹ INFO",
        
        # Profiles
        "prof_title": "Available Scheduler Profiles",
        "prof_col_id": "Profile ID",
        "prof_col_name": "Profile Name",
        "prof_col_target": "Target Scheduler",
        "prof_col_gov": "Governor / EPP",
        "prof_col_type": "Type",
        "prof_col_desc": "Description",
        
        # Profile Descriptions
        "prof_gaming_name": "Gaming & E-Sports (Low Latency)",
        "prof_gaming_desc": "Minimizes latency jitter and 1% low drops for maximum frame pacing stability.",
        "prof_compile_name": "Compile & Multi-Core Rendering",
        "prof_compile_desc": "Maximum thread throughput for GCC, Rustc, Clang, and Blender rendering.",
        "prof_balanced_name": "Balanced Desktop & Media",
        "prof_balanced_desc": "Even load distribution, responsive UI, and smooth multitasking.",
        "prof_audio_name": "Pro Audio & DAW (Zero Xrun)",
        "prof_audio_desc": "Ultra-low jitter and guaranteed time slices for JACK, PipeWire, and DAWs.",
        "prof_emulation_name": "Emulation & High-Cache (RPCS3/Ryujinx)",
        "prof_emulation_desc": "Optimized for heavy JIT recompilation and inter-core cache synchronization.",
        "prof_powersave_name": "Power Saving & Battery Life",
        "prof_powersave_desc": "Aggressive power saving, lower frequencies, and minimized core wakeups.",
        "prof_stock_name": "Stock Kernel (BORE / EEVDF)",
        "prof_stock_desc": "Standard Linux/CachyOS kernel scheduler without sched-ext overhead.",
        
        # Messages & Status
        "msg_switched_success": "Scheduler '{sched}' successfully activated.",
        "msg_switched_fail": "Failed to activate '{sched}': {err}",
        "msg_reverted_default": "Successfully reverted to stock kernel scheduler.",
        "msg_stop_fail": "Could not stop scheduler: {err}",
        "msg_already_default": "Already running stock kernel (sched-ext is inactive).",
        "msg_crash_detected": "⚠️ WARNING: sched-ext crash detected! Automatic fallback to stock kernel active.",
        "msg_profile_applied": "Profile '{name}' successfully applied.",
        "msg_not_installed": "Binary '{binary}' is not installed in system PATH.",
        "msg_helper_not_found": "Backend helper '{path}' not found.",
        "msg_privilege_error": "Root or Polkit authorization denied.",
        
        # CLI
        "cli_help_desc": "Cachy-Sched-Pilot — Autonomous sched-ext (SCX) Tuner & Governor for CachyOS / Arch Linux",
        "cli_help_status": "Display CPU, kernel, and sched-ext telemetry",
        "cli_help_doctor": "Run comprehensive sched-ext & kernel diagnostic health check",
        "cli_help_bench": "Run micro-benchmark on active scheduler",
        "cli_help_switch": "Switch scheduler (e.g. scx_lavd, scx_rusty, default)",
        "cli_help_profile": "Apply pre-tuned profile (e.g. gaming, compile, balanced, powersave)",
        "cli_help_stop": "Stop sched-ext and revert to stock kernel scheduler",
        "cli_help_governor": "Start autonomous workload governor (Gaming vs Compile)",
        "cli_help_tui": "Launch interactive terminal dashboard (TUI)",
        "cli_help_json": "Format output as machine-readable JSON",
        "cli_help_lang": "Force language ('de' or 'en')",
    }
}


class I18n:
    """Singleton localization helper."""
    _current_lang: str = "de"

    @classmethod
    def detect_system_language(cls) -> str:
        """Detect system language from environment variables."""
        lang_env = os.environ.get("LANG", "") or os.environ.get("LC_ALL", "")
        if lang_env.lower().startswith("de"):
            return "de"
        return "en"

    @classmethod
    def set_language(cls, lang: str) -> None:
        """Set active language ('de' or 'en')."""
        clean = lang.strip().lower()
        if clean in ("de", "de_de", "german", "deutsch"):
            cls._current_lang = "de"
        elif clean in ("en", "en_us", "en_gb", "english"):
            cls._current_lang = "en"
        else:
            cls._current_lang = "en"

    @classmethod
    def get_language(cls) -> str:
        return cls._current_lang

    @classmethod
    def toggle_language(cls) -> str:
        """Toggle between German and English."""
        cls._current_lang = "en" if cls._current_lang == "de" else "de"
        return cls._current_lang

    @classmethod
    def t(cls, key: str, **kwargs: Any) -> str:
        """Translate key to current language with optional string interpolation."""
        lang_dict = TRANSLATIONS.get(cls._current_lang, TRANSLATIONS["en"])
        template = lang_dict.get(key) or TRANSLATIONS["en"].get(key, key)
        if kwargs:
            try:
                return template.format(**kwargs)
            except Exception:
                return template
        return template


# Shorthand alias
t = I18n.t
