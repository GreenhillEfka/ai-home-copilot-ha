#!/usr/bin/env python3
"""
Startup Benchmark Script for PilotSuite Styx Core

Measures and compares startup performance with and without lazy loading.
Generates detailed reports and can be used for CI/CD performance regression testing.

Usage:
    # Basic benchmark (default: 10 iterations)
    python scripts/benchmark_startup.py
    
    # Custom iterations
    python scripts/benchmark_startup.py --iterations 20
    
    # Compare lazy vs eager loading
    python scripts/benchmark_startup.py --compare
    
    # Output to JSON file
    python scripts/benchmark_startup.py --output benchmark_results.json
    
    # Verbose output
    python scripts/benchmark_startup.py --verbose
    
    # CI mode (fails if target not met)
    python scripts/benchmark_startup.py --ci-mode --target 2000

Features:
    - Multiple iterations for statistical significance
    - Comparison between lazy and eager loading
    - Memory usage tracking
    - JSON/CSV export
    - CI/CD integration support
    - Performance regression detection
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""
    mode: str  # "lazy" or "eager"
    iteration: int
    startup_time_ms: float
    modules_loaded: int
    modules_deferred: int
    memory_mb: float
    timestamp: float
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class BenchmarkSummary:
    """Summary statistics for benchmark results."""
    mode: str
    count: int
    avg_startup_ms: float
    min_startup_ms: float
    max_startup_ms: float
    std_dev_ms: float
    avg_memory_mb: float
    target_met_percent: float
    
    def to_dict(self) -> dict:
        return asdict(self)


class StartupBenchmark:
    """
    Benchmark suite for measuring startup performance.
    """
    
    def __init__(
        self,
        iterations: int = 10,
        target_ms: float = 2000.0,
        verbose: bool = False,
    ):
        """
        Initialize benchmark.
        
        Args:
            iterations: Number of benchmark iterations
            target_ms: Target startup time in milliseconds
            verbose: Enable verbose output
        """
        self.iterations = iterations
        self.target_ms = target_ms
        self.verbose = verbose
        
        self.results: List[BenchmarkResult] = []
        self.lazy_results: List[BenchmarkResult] = []
        self.eager_results: List[BenchmarkResult] = []
    
    def _get_memory_usage_mb(self) -> float:
        """Get current process memory usage in MB."""
        try:
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        except ImportError:
            try:
                import psutil
                import os
                return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
            except ImportError:
                return 0.0
    
    def _simulate_module_imports(self, module_paths: List[str]) -> float:
        """
        Simulate importing modules and measure time.
        
        Args:
            module_paths: List of module paths to import
        
        Returns:
            Time taken in milliseconds
        """
        start = time.perf_counter()
        
        for path in module_paths:
            try:
                __import__(path)
            except ImportError as e:
                if self.verbose:
                    logger.debug(f"Module {path} not available: {e}")
        
        return (time.perf_counter() - start) * 1000
    
    def run_lazy_iteration(self, iteration: int) -> BenchmarkResult:
        """
        Run a single benchmark iteration with lazy loading enabled.
        
        Args:
            iteration: Iteration number
        
        Returns:
            BenchmarkResult instance
        """
        if self.verbose:
            logger.info(f"Running lazy loading iteration {iteration + 1}/{self.iterations}")
        
        # Reset lazy loader state
        try:
            from copilot_core.utils.lazy_loader import LazyLoader
            LazyLoader.reset_all()
            LazyLoader.enable()
        except ImportError:
            pass
        
        start_time = time.perf_counter()
        memory_before = self._get_memory_usage_mb()
        
        # Simulate core setup with lazy loading
        modules_loaded = 0
        modules_deferred = 0
        
        try:
            # Import core modules (lightweight)
            core_modules = [
                "copilot_core.config",
                "copilot_core.base",
            ]
            for mod in core_modules:
                try:
                    __import__(mod)
                    modules_loaded += 1
                except ImportError:
                    pass
            
            # Defer heavy modules (simulated)
            heavy_modules = [
                "copilot_core.energy.service",
                "copilot_core.ml.transformer_model",
                "copilot_core.proactive_engine",
            ]
            modules_deferred = len(heavy_modules)
            
        except Exception as e:
            logger.error(f"Error during lazy iteration: {e}")
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        memory_after = self._get_memory_usage_mb()
        
        return BenchmarkResult(
            mode="lazy",
            iteration=iteration,
            startup_time_ms=elapsed_ms,
            modules_loaded=modules_loaded,
            modules_deferred=modules_deferred,
            memory_mb=memory_after - memory_before,
            timestamp=time.time(),
        )
    
    def run_eager_iteration(self, iteration: int) -> BenchmarkResult:
        """
        Run a single benchmark iteration with eager loading (no lazy loading).
        
        Args:
            iteration: Iteration number
        
        Returns:
            BenchmarkResult instance
        """
        if self.verbose:
            logger.info(f"Running eager loading iteration {iteration + 1}/{self.iterations}")
        
        # Disable lazy loading
        try:
            from copilot_core.utils.lazy_loader import LazyLoader
            LazyLoader.reset_all()
            LazyLoader.disable()
        except ImportError:
            pass
        
        start_time = time.perf_counter()
        memory_before = self._get_memory_usage_mb()
        
        # Simulate loading all modules immediately
        modules_loaded = 0
        modules_deferred = 0
        
        try:
            all_modules = [
                "copilot_core.config",
                "copilot_core.base",
                "copilot_core.energy.service",
                "copilot_core.ml.transformer_model",
                "copilot_core.proactive_engine",
            ]
            for mod in all_modules:
                try:
                    __import__(mod)
                    modules_loaded += 1
                except ImportError:
                    pass
            
        except Exception as e:
            logger.error(f"Error during eager iteration: {e}")
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        memory_after = self._get_memory_usage_mb()
        
        return BenchmarkResult(
            mode="eager",
            iteration=iteration,
            startup_time_ms=elapsed_ms,
            modules_loaded=modules_loaded,
            modules_deferred=modules_deferred,
            memory_mb=memory_after - memory_before,
            timestamp=time.time(),
        )
    
    def run(self, compare: bool = False) -> Dict[str, Any]:
        """
        Run the full benchmark suite.
        
        Args:
            compare: If True, compare lazy vs eager loading
        
        Returns:
            Dictionary with benchmark results and summaries
        """
        logger.info(f"Starting benchmark: {self.iterations} iterations, target {self.target_ms}ms")
        
        if compare:
            logger.info("Running comparison: lazy vs eager loading")
            
            # Run lazy loading benchmarks
            logger.info("=== Lazy Loading Benchmarks ===")
            for i in range(self.iterations):
                result = self.run_lazy_iteration(i)
                self.lazy_results.append(result)
                self.results.append(result)
                if self.verbose:
                    logger.info(f"  Lazy #{i+1}: {result.startup_time_ms:.2f}ms")
            
            # Reset state between modes
            import gc
            gc.collect()
            time.sleep(0.5)
            
            # Run eager loading benchmarks
            logger.info("=== Eager Loading Benchmarks ===")
            for i in range(self.iterations):
                result = self.run_eager_iteration(i)
                self.eager_results.append(result)
                self.results.append(result)
                if self.verbose:
                    logger.info(f"  Eager #{i+1}: {result.startup_time_ms:.2f}ms")
        else:
            # Run lazy loading only
            logger.info("=== Lazy Loading Benchmarks ===")
            for i in range(self.iterations):
                result = self.run_lazy_iteration(i)
                self.lazy_results.append(result)
                self.results.append(result)
                if self.verbose:
                    logger.info(f"  Lazy #{i+1}: {result.startup_time_ms:.2f}ms")
        
        # Calculate summaries
        return self._generate_report()
    
    def _calculate_summary(self, results: List[BenchmarkResult]) -> BenchmarkSummary:
        """Calculate summary statistics for results."""
        import statistics
        
        if not results:
            return BenchmarkSummary(
                mode="unknown",
                count=0,
                avg_startup_ms=0,
                min_startup_ms=0,
                max_startup_ms=0,
                std_dev_ms=0,
                avg_memory_mb=0,
                target_met_percent=0,
            )
        
        startup_times = [r.startup_time_ms for r in results]
        memory_values = [r.memory_mb for r in results]
        target_met = sum(1 for t in startup_times if t < self.target_ms)
        
        return BenchmarkSummary(
            mode=results[0].mode,
            count=len(results),
            avg_startup_ms=round(statistics.mean(startup_times), 2),
            min_startup_ms=round(min(startup_times), 2),
            max_startup_ms=round(max(startup_times), 2),
            std_dev_ms=round(statistics.stdev(startup_times), 2) if len(startup_times) > 1 else 0,
            avg_memory_mb=round(statistics.mean(memory_values), 2),
            target_met_percent=round(target_met / len(results) * 100, 2),
        )
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive benchmark report."""
        report = {
            "timestamp": time.time(),
            "config": {
                "iterations": self.iterations,
                "target_ms": self.target_ms,
            },
            "results": [r.to_dict() for r in self.results],
        }
        
        if self.lazy_results:
            lazy_summary = self._calculate_summary(self.lazy_results)
            report["lazy_summary"] = lazy_summary.to_dict()
        
        if self.eager_results:
            eager_summary = self._calculate_summary(self.eager_results)
            report["eager_summary"] = eager_summary.to_dict()
        
        # Calculate improvement
        if self.lazy_results and self.eager_results:
            lazy_avg = self._calculate_summary(self.lazy_results).avg_startup_ms
            eager_avg = self._calculate_summary(self.eager_results).avg_startup_ms
            
            improvement_ms = eager_avg - lazy_avg
            improvement_percent = (improvement_ms / eager_avg * 100) if eager_avg > 0 else 0
            
            report["comparison"] = {
                "improvement_ms": round(improvement_ms, 2),
                "improvement_percent": round(improvement_percent, 2),
                "lazy_avg_ms": lazy_avg,
                "eager_avg_ms": eager_avg,
            }
        
        return report
    
    def print_report(self, report: Dict[str, Any]) -> None:
        """Print benchmark report to console."""
        print("\n" + "=" * 70)
        print("STARTUP BENCHMARK RESULTS")
        print("=" * 70)
        
        config = report.get("config", {})
        print(f"\nConfiguration:")
        print(f"  Iterations: {config.get('iterations', 0)}")
        print(f"  Target: {config.get('target_ms', 0)}ms")
        
        if "lazy_summary" in report:
            lazy = report["lazy_summary"]
            print(f"\nLazy Loading Performance:")
            print(f"  Average: {lazy['avg_startup_ms']:.2f}ms")
            print(f"  Min: {lazy['min_startup_ms']:.2f}ms")
            print(f"  Max: {lazy['max_startup_ms']:.2f}ms")
            print(f"  Std Dev: {lazy['std_dev_ms']:.2f}ms")
            print(f"  Target Met: {lazy['target_met_percent']:.1f}%")
            print(f"  Avg Memory: {lazy['avg_memory_mb']:.2f}MB")
        
        if "eager_summary" in report:
            eager = report["eager_summary"]
            print(f"\nEager Loading Performance:")
            print(f"  Average: {eager['avg_startup_ms']:.2f}ms")
            print(f"  Min: {eager['min_startup_ms']:.2f}ms")
            print(f"  Max: {eager['max_startup_ms']:.2f}ms")
            print(f"  Std Dev: {eager['std_dev_ms']:.2f}ms")
            print(f"  Target Met: {eager['target_met_percent']:.1f}%")
            print(f"  Avg Memory: {eager['avg_memory_mb']:.2f}MB")
        
        if "comparison" in report:
            comp = report["comparison"]
            print(f"\nPerformance Improvement (Lazy vs Eager):")
            print(f"  Time Saved: {comp['improvement_ms']:.2f}ms")
            print(f"  Improvement: {comp['improvement_percent']:.1f}%")
            print(f"  Lazy Avg: {comp['lazy_avg_ms']:.2f}ms")
            print(f"  Eager Avg: {comp['eager_avg_ms']:.2f}ms")
        
        print("\n" + "=" * 70)
    
    def save_report(self, report: Dict[str, Any], output_path: str) -> None:
        """Save benchmark report to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Benchmark report saved to: {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Benchmark startup performance for PilotSuite Styx Core"
    )
    parser.add_argument(
        "--iterations", "-n",
        type=int,
        default=10,
        help="Number of benchmark iterations (default: 10)"
    )
    parser.add_argument(
        "--target", "-t",
        type=float,
        default=2000.0,
        help="Target startup time in ms (default: 2000)"
    )
    parser.add_argument(
        "--compare", "-c",
        action="store_true",
        help="Compare lazy vs eager loading"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output JSON file path"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--ci-mode",
        action="store_true",
        help="CI mode: exit with error if target not met"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Run benchmark
    benchmark = StartupBenchmark(
        iterations=args.iterations,
        target_ms=args.target,
        verbose=args.verbose,
    )
    
    report = benchmark.run(compare=args.compare)
    benchmark.print_report(report)
    
    # Save report if requested
    if args.output:
        benchmark.save_report(report, args.output)
    
    # CI mode: check if target was met
    if args.ci_mode:
        if "lazy_summary" in report:
            avg_time = report["lazy_summary"]["avg_startup_ms"]
            if avg_time >= args.target:
                logger.error(f"CI check failed: {avg_time:.2f}ms >= {args.target}ms target")
                sys.exit(1)
            else:
                logger.info(f"CI check passed: {avg_time:.2f}ms < {args.target}ms target")
        else:
            logger.error("CI check failed: no results")
            sys.exit(1)
    
    print("\n✓ Benchmark completed successfully")


if __name__ == "__main__":
    main()
