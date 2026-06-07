"""Crash Tracker - Crash Forensic Tracing with Exception Capture

Captures exceptions with full traceback and maintains crash history.
"""

import time
from typing import Dict, Any, List, Optional


class CrashTracker:
    """Crash forensic tracing with exception capture."""

    def __init__(self):
        """Initialize CrashTracker with empty crash history."""
        self._crashes: List[Dict[str, Any]] = []

    def capture(self, func_name: str, exc: Exception) -> Dict[str, Any]:
        """Capture exception with traceback.

        Args:
            func_name: Name of function where crash occurred
            exc: Exception that was raised

        Returns:
            Crash record dictionary
        """
        import traceback
        import inspect

        tb_str = traceback.format_exc()
        tb = exc.__traceback__

        # Extract origin info
        file_name = "unknown"
        line_no = 0
        if tb:
            frame = tb.tb_frame
            file_name = frame.f_code.co_filename
            line_no = tb.tb_lineno

        crash_record = {
            "timestamp": time.time(),
            "exception_type": exc.__class__.__name__,
            "message": str(exc),
            "traceback": tb_str,
            "file": file_name,
            "line": line_no,
            "function": func_name,
        }

        self._crashes.append(crash_record)
        return crash_record

    def all(self) -> List[Dict[str, Any]]:
        """Return all crash records.

        Returns:
            List of crash records
        """
        return self._crashes.copy()
