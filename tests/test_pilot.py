"""
tests/test_pilot.py — Umfassende Test-Suite für Cachy-Sched-Pilot.
Prüft Erkennungs-Engine, Benchmark-Statistiken, Profil-Integrität und Manager-Logik.
"""

import os
import sys
import unittest
from pathlib import Path

# Basisverzeichnis zum Suchpfad hinzufügen
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from core.detector import SystemDetector, CpuInfo, SchedExtStatus
from core.benchmark import SchedulerBenchmark, BenchmarkResult
from core.manager import SchedulerManager, DEFAULT_CONFIG
from core.profiles import PROFILES
from core.governor import AutopilotGovernor


class TestCachySchedPilot(unittest.TestCase):
    """Testet alle Kernmodule von Cachy-Sched-Pilot."""

    def test_cpu_detection(self):
        """CPU-Erkennung muss gültige logische Cores und einen Modellnamen liefern."""
        cpu = SystemDetector.get_cpu_info()
        self.assertIsInstance(cpu, CpuInfo)
        self.assertGreaterEqual(cpu.logical_cores, 1)
        self.assertGreaterEqual(cpu.physical_cores, 1)
        self.assertTrue(len(cpu.model) > 0)

    def test_scx_status(self):
        """sched-ext Status muss strukturierte SchedExtStatus Instanz zurückgeben."""
        status = SystemDetector.detect_scx_status()
        self.assertIsInstance(status, SchedExtStatus)
        self.assertIn(status.state, ["enabled", "disabled", "unsupported", "unknown"])
        self.assertIsInstance(status.installed_schedulers, list)
        self.assertIsInstance(status.scxctl_installed, bool)

    def test_workload_detection(self):
        """Workload-Erkennung muss einen gültigen Workload-String und eine Liste liefern."""
        workload, procs = SystemDetector.detect_active_workload()
        valid_modes = [
            "GAMING",
            "EMULATION",
            "LOW_LATENCY_AUDIO",
            "COMPILING",
            "CONTENT_CREATION",
            "IDLE_DESKTOP",
        ]
        self.assertIn(workload, valid_modes)
        self.assertIsInstance(procs, list)

    def test_doctor_report(self):
        """Doctor-Diagnose muss Score und strukturierte Prüfungen zurückgeben."""
        report = SystemDetector.run_doctor()
        self.assertIn("score", report)
        self.assertGreaterEqual(report["score"], 0)
        self.assertLessEqual(report["score"], 100)
        self.assertIn("checks", report)
        self.assertGreaterEqual(len(report["checks"]), 4)

    def test_profiles_integrity(self):
        """Alle vordefinierten Tuning-Profile müssen gültige SchedProfile-Objekte sein."""
        expected_profiles = [
            "gaming_esports",
            "heavy_compile",
            "balanced_daily",
            "audio_pro",
            "emulation_heavy",
            "kernel_stock",
        ]
        for p_id in expected_profiles:
            self.assertIn(p_id, PROFILES)
            prof = PROFILES[p_id]
            self.assertTrue(len(prof.name) > 0)
            self.assertTrue(len(prof.target_scheduler) > 0)
            self.assertIsInstance(prof.recommended_flags, list)

    def test_benchmark_calculation(self):
        """Latenz- & Score-Berechnungen des Benchmarks müssen mathematisch konsistent sein."""
        bench = SchedulerBenchmark(iterations=50, target_sleep_us=100)
        res = bench.run_full_suite("Test-Scheduler")
        self.assertIsInstance(res, BenchmarkResult)
        self.assertEqual(res.scheduler_name, "Test-Scheduler")
        self.assertGreater(res.mean_latency_us, 0)
        self.assertGreaterEqual(res.gaming_latency_score, 5.0)
        self.assertLessEqual(res.gaming_latency_score, 100.0)
        self.assertIn(res.overall_rating, ["S", "A+", "A", "B", "C"])

    def test_manager_systemd_template(self):
        """Systemd-Template-Generierung muss gültige SCX_SCHEDULER Zeilen enthalten."""
        template = SchedulerManager.generate_systemd_template("scx_lavd", "--performance")
        self.assertIn('SCX_SCHEDULER="lavd"', template)
        self.assertIn('SCX_FLAGS="--performance"', template)

    def test_manager_config_defaults(self):
        """Manager-Konfiguration muss Standardwerte für alle Workload-Typen enthalten."""
        mgr = SchedulerManager()
        cfg = mgr.config
        for key in ["gaming_scheduler", "compile_scheduler", "audio_scheduler", "emulation_scheduler"]:
            self.assertIn(key, cfg)


if __name__ == "__main__":
    unittest.main(verbosity=2)
