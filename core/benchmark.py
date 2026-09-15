"""
core/benchmark.py — High-Precision Micro-Benchmark Suite für Linux CPU-Schedulers.
Misst Nanosekunden-Aufwachlatenzen, Scheduling-Jitter (P99-Spikes) und Kontextwechsel-Durchsatz.
"""

from __future__ import annotations
import math
import os
import threading
import time
from dataclasses import dataclass, asdict
from typing import Callable, Dict, List, Optional

@dataclass
class BenchmarkResult:
    scheduler_name: str
    samples_count: int
    mean_latency_us: float
    min_latency_us: float
    max_latency_us: float
    p95_latency_us: float
    p99_latency_us: float
    jitter_std_us: float
    ctx_switches_per_sec: float
    gaming_latency_score: float   # 0 - 100 (Höher = weniger Stuttering & minimale 1% Low Drops)
    throughput_score: float       # 0 - 100 (Höher = schnellere Multithread- & Batch-Leistung)
    overall_rating: str           # "S", "A+", "A", "B", "C"

class SchedulerBenchmark:
    """Führt standardisierte Nanosekunden-Latenz- & Durchsatz-Prüfungen durch."""

    def __init__(self, iterations: int = 1500, target_sleep_us: int = 150):
        self.iterations = iterations
        self.target_sleep_us = target_sleep_us

    def run_wakeup_latency_test(self, progress_callback: Optional[Callable[[float], None]] = None) -> List[float]:
        """
        Misst die Abweichung zwischen angefordertem Thread-Sleep und tatsächlichem Aufwachen.
        Dieser Wert ist der direkteste Indikator für Audio-Knackser und Micro-Stuttering in Spielen.
        """
        latencies_us: List[float] = []
        target_s = self.target_sleep_us / 1_000_000.0

        for i in range(self.iterations):
            t_start = time.perf_counter_ns()
            time.sleep(target_s)
            t_end = time.perf_counter_ns()

            actual_us = (t_end - t_start) / 1000.0
            delta_us = max(0.0, actual_us - self.target_sleep_us)
            latencies_us.append(delta_us)

            if progress_callback and (i % 150 == 0):
                progress_callback((i + 1) / self.iterations * 0.6)

        return latencies_us

    def run_context_switch_test(self, duration_sec: float = 0.5) -> float:
        """
        Ermittelt die Frequenz von OS-Thread-Yields und Kontextwechseln.
        """
        count = 0
        t_end = time.time() + duration_sec
        while time.time() < t_end:
            os.sched_yield()
            count += 1
        return count / duration_sec

    def run_full_suite(
        self,
        scheduler_name: str = "Active",
        progress_cb: Optional[Callable[[str, float], None]] = None
    ) -> BenchmarkResult:
        if progress_cb:
            progress_cb("Latenz- & Jitter-Test läuft...", 0.1)

        latencies = self.run_wakeup_latency_test(
            lambda p: progress_cb and progress_cb(f"Prüfe {scheduler_name} ({int(p*100)}%)...", p)
        )

        if progress_cb:
            progress_cb("Kontextwechsel-Durchsatz wird gemessen...", 0.75)

        ctx_switches = self.run_context_switch_test(duration_sec=0.5)

        if progress_cb:
            progress_cb("Berechne statistische Metriken & Scores...", 0.95)

        latencies.sort()
        n = len(latencies)
        mean_lat = sum(latencies) / n
        min_lat = latencies[0]
        max_lat = latencies[-1]
        p95 = latencies[int(n * 0.95)]
        p99 = latencies[int(n * 0.99)]

        variance = sum((x - mean_lat) ** 2 for x in latencies) / n
        jitter = math.sqrt(variance)

        # Score-Berechnung:
        # Gaming-Score: Niedrige P99-Latenz & niedriger Jitter sind kritisch
        # 10 us Mean / 30 us P99 = 100 Punkte, > 500 us = sinkt drastisch
        latency_penalty = (mean_lat * 0.4) + (p99 * 0.4) + (jitter * 0.2)
        gaming_score = max(5.0, min(100.0, 105.0 - (latency_penalty * 0.15)))

        # Durchsatz-Score: Kontextwechsel skaliert
        # 500k ctx/s ~ 100 Punkte
        throughput_score = max(5.0, min(100.0, (ctx_switches / 6000.0)))

        # Rating
        composite = (gaming_score * 0.65) + (throughput_score * 0.35)
        if composite >= 90:
            rating = "S"
        elif composite >= 80:
            rating = "A+"
        elif composite >= 70:
            rating = "A"
        elif composite >= 60:
            rating = "B"
        else:
            rating = "C"

        return BenchmarkResult(
            scheduler_name=scheduler_name,
            samples_count=n,
            mean_latency_us=round(mean_lat, 2),
            min_latency_us=round(min_lat, 2),
            max_latency_us=round(max_lat, 2),
            p95_latency_us=round(p95, 2),
            p99_latency_us=round(p99, 2),
            jitter_std_us=round(jitter, 2),
            ctx_switches_per_sec=round(ctx_switches, 1),
            gaming_latency_score=round(gaming_score, 1),
            throughput_score=round(throughput_score, 1),
            overall_rating=rating
        )
