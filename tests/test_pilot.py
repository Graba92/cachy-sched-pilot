"""
tests/test_pilot.py — Comprehensive Unit Test Suite for Cachy-Sched-Pilot.
Tests hardware detection, i18n, XDG configuration, scheduler management,
safety fallbacks, profiles, and benchmarking calculations.
"""

import os
import sys
import unittest
from pathlib import Path

# Add repository root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from core.i18n import I18n, t
from core.config import ConfigManager, DEFAULT_CONFIG, dict_to_toml
from core.detector import SystemDetector, CpuInfo, SchedExtStatus
from core.benchmark import SchedulerBenchmark, BenchmarkResult
from core.manager import SchedulerManager
from core.profiles import PROFILES, SchedProfile
from app import build_parser


class TestCachySchedPilot(unittest.TestCase):
    """Test suite covering all core functional modules."""

    def setUp(self):
        I18n.set_language("de")

    def test_i18n_localization(self):
        """Test English and German translation strings and toggling."""
        I18n.set_language("de")
        self.assertEqual(I18n.get_language(), "de")
        self.assertIn("Telemetrie", t("tab_dashboard"))

        I18n.set_language("en")
        self.assertEqual(I18n.get_language(), "en")
        self.assertIn("Telemetry", t("tab_dashboard"))

        # Test toggle
        I18n.toggle_language()
        self.assertEqual(I18n.get_language(), "de")

        # Test string interpolation
        msg = t("msg_switched_success", sched="scx_lavd")
        self.assertIn("scx_lavd", msg)

    def test_config_xdg_and_toml(self):
        """Test XDG config loading and TOML serialization."""
        cfg = ConfigManager.load()
        self.assertIn("general", cfg)
        self.assertIn("workloads", cfg)
        self.assertIn("governor_policy", cfg)

        toml_str = dict_to_toml(DEFAULT_CONFIG)
        self.assertIn("[general]", toml_str)
        self.assertIn("gaming_scheduler", toml_str)

    def test_cpu_detection(self):
        """CPU detection must report valid core counts, governor, and per-core load."""
        cpu = SystemDetector.get_cpu_info()
        self.assertIsInstance(cpu, CpuInfo)
        self.assertGreaterEqual(cpu.logical_cores, 1)
        self.assertGreaterEqual(cpu.physical_cores, 1)
        self.assertTrue(len(cpu.model) > 0)
        self.assertIsInstance(cpu.per_core_load, list)
        self.assertIsInstance(cpu.governor, str)
        self.assertIsInstance(cpu.epp, str)

    def test_kernel_scheduler_type(self):
        """Kernel scheduler detector must identify EEVDF, BORE, or cacULE."""
        sched_type = SystemDetector.detect_kernel_scheduler_type()
        self.assertIn(sched_type, ["BORE", "cacULE", "EEVDF", "EEVDF / CFS"])

    def test_scx_status(self):
        """sched-ext status inspection must return structured data."""
        status = SystemDetector.detect_scx_status()
        self.assertIsInstance(status, SchedExtStatus)
        self.assertIn(status.state, ["enabled", "disabled", "unsupported", "unknown"])
        self.assertIsInstance(status.installed_schedulers, list)
        self.assertIsInstance(status.scxctl_installed, bool)

    def test_workload_detection(self):
        """Workload detection must return recognized workload category."""
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
        """Doctor health check must return diagnostic score and structured check items."""
        report = SystemDetector.run_doctor()
        self.assertIn("score", report)
        self.assertGreaterEqual(report["score"], 0)
        self.assertLessEqual(report["score"], 100)
        self.assertIn("checks", report)
        self.assertGreaterEqual(len(report["checks"]), 4)

    def test_profiles_integrity(self):
        """All pre-tuned profiles must have valid target schedulers and governors."""
        expected_profiles = [
            "gaming",
            "lowlatency",
            "compile",
            "balanced",
            "powersave",
            "emulation",
            "stock",
        ]
        for p_id in expected_profiles:
            self.assertIn(p_id, PROFILES)
            prof = PROFILES[p_id]
            self.assertTrue(len(prof.name) > 0)
            self.assertTrue(len(prof.target_scheduler) > 0)
            self.assertTrue(len(prof.governor) > 0)
            self.assertTrue(len(prof.epp) > 0)
            self.assertIsInstance(prof.recommended_flags, list)

    def test_benchmark_calculation(self):
        """Micro-benchmark suite must calculate valid mean latencies and ratings."""
        bench = SchedulerBenchmark(iterations=60, target_sleep_us=100)
        res = bench.run_full_suite("Test-Scheduler")
        self.assertIsInstance(res, BenchmarkResult)
        self.assertEqual(res.scheduler_name, "Test-Scheduler")
        self.assertGreater(res.mean_latency_us, 0)
        self.assertGreaterEqual(res.gaming_latency_score, 5.0)
        self.assertLessEqual(res.gaming_latency_score, 100.0)
        self.assertIn(res.overall_rating, ["S", "A+", "A", "B", "C"])

    def test_backend_helper_presence(self):
        """SchedulerManager must resolve the path to cachy-sched-helper."""
        helper_path = SchedulerManager.get_helper_path()
        self.assertIsNotNone(helper_path)
        self.assertTrue(Path(helper_path).exists())
        self.assertTrue(os.access(helper_path, os.X_OK))

    def test_safety_fallback(self):
        """Safety check should correctly identify crashed scheduler state."""
        mgr = SchedulerManager()
        # With no prior scx set:
        recovered, msg = mgr.check_and_recover_safety()
        self.assertFalse(recovered)
        self.assertIsNone(msg)

    def test_cli_parser(self):
        """CLI parser must parse top-level automation arguments correctly."""
        parser = build_parser()
        args = parser.parse_args(["--status", "--json", "--lang", "en"])
        self.assertTrue(args.status)
        self.assertTrue(args.json)
        self.assertEqual(args.lang, "en")

        args2 = parser.parse_args(["--set-profile", "gaming"])
        self.assertEqual(args2.set_profile, "gaming")

        args3 = parser.parse_args(["--set-sched", "scx_lavd"])
        self.assertEqual(args3.set_sched, "scx_lavd")


if __name__ == "__main__":
    unittest.main(verbosity=2)
