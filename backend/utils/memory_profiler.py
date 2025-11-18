"""
Memory Profiling and Monitoring Utilities
Provides tools to monitor and optimize memory usage
"""

import psutil
import gc
import sys
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("chatbot.memory")


class MemoryProfiler:
    """
    Memory profiling and monitoring for the application
    Tracks memory usage and provides optimization utilities
    """

    def __init__(self):
        self.process = psutil.Process()
        self.baseline_memory = None
        self.peak_memory = 0

    def get_memory_info(self) -> Dict[str, Any]:
        """
        Get current memory usage information

        Returns:
            Dictionary with memory statistics in MB
        """
        mem_info = self.process.memory_info()

        rss_mb = mem_info.rss / (1024 * 1024)  # Resident Set Size
        vms_mb = mem_info.vms / (1024 * 1024)  # Virtual Memory Size

        # Track peak memory
        if rss_mb > self.peak_memory:
            self.peak_memory = rss_mb

        # Get system-wide memory info
        system_mem = psutil.virtual_memory()

        return {
            "rss_mb": round(rss_mb, 2),
            "vms_mb": round(vms_mb, 2),
            "peak_mb": round(self.peak_memory, 2),
            "baseline_mb": round(self.baseline_memory, 2) if self.baseline_memory else None,
            "delta_mb": round(rss_mb - self.baseline_memory, 2) if self.baseline_memory else None,
            "system_total_mb": round(system_mem.total / (1024 * 1024), 2),
            "system_available_mb": round(system_mem.available / (1024 * 1024), 2),
            "system_percent": system_mem.percent,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def set_baseline(self) -> None:
        """Set current memory as baseline for delta calculations"""
        mem_info = self.process.memory_info()
        self.baseline_memory = mem_info.rss / (1024 * 1024)
        logger.info(f"Memory baseline set: {self.baseline_memory:.2f} MB")

    def force_garbage_collection(self) -> Dict[str, Any]:
        """
        Force garbage collection and return statistics

        Returns:
            Dictionary with GC statistics
        """
        logger.info("Running garbage collection...")

        # Get memory before GC
        mem_before = self.get_memory_info()["rss_mb"]

        # Run garbage collection
        collected = gc.collect()

        # Get memory after GC
        mem_after = self.get_memory_info()["rss_mb"]
        freed_mb = mem_before - mem_after

        stats = {
            "objects_collected": collected,
            "memory_before_mb": mem_before,
            "memory_after_mb": mem_after,
            "memory_freed_mb": round(freed_mb, 2),
            "gc_stats": {
                "generation_0": gc.get_count()[0],
                "generation_1": gc.get_count()[1],
                "generation_2": gc.get_count()[2],
            }
        }

        logger.info(f"GC freed {freed_mb:.2f} MB, collected {collected} objects")
        return stats

    def get_largest_objects(self, limit: int = 10) -> list:
        """
        Get the largest objects in memory (debugging)

        Args:
            limit: Number of objects to return

        Returns:
            List of tuples (type, size_bytes, count)
        """
        try:
            import objgraph
            return objgraph.most_common_types(limit=limit)
        except ImportError:
            logger.warning("objgraph not installed - install with: pip install objgraph")
            return []

    def log_memory_summary(self, context: str = "") -> None:
        """
        Log a summary of current memory usage

        Args:
            context: Context string to identify where this was called from
        """
        mem = self.get_memory_info()

        log_msg = f"Memory Usage"
        if context:
            log_msg += f" ({context})"
        log_msg += f": {mem['rss_mb']:.2f} MB"

        if mem['baseline_mb']:
            log_msg += f" (Δ{mem['delta_mb']:+.2f} MB from baseline)"

        log_msg += f" | Peak: {mem['peak_mb']:.2f} MB"
        log_msg += f" | System: {mem['system_percent']:.1f}%"

        logger.info(log_msg)


# Global memory profiler instance
memory_profiler = MemoryProfiler()


def get_memory_info() -> Dict[str, Any]:
    """Get current memory information"""
    return memory_profiler.get_memory_info()


def force_gc() -> Dict[str, Any]:
    """Force garbage collection and return statistics"""
    return memory_profiler.force_garbage_collection()


def log_memory(context: str = "") -> None:
    """Log current memory usage with optional context"""
    memory_profiler.log_memory_summary(context)


def set_memory_baseline() -> None:
    """Set current memory as baseline"""
    memory_profiler.set_baseline()
