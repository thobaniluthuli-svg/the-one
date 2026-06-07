"""System Guard - Runtime Execution Safety Kernel for Python Workloads

A multi-layer system introspection, automatic execution capture, crash tracking,
persistent error storage, and constraint-based failure prevention framework.
"""

from .runtime import RuntimeGuard
from .crash_tracker import CrashTracker
from .crash_store import CrashStore
from .db_handler import DBHandler
from .crash_to_constraint import CrashToConstraint
from .ssd_layer import SSDLayer
from .network_layer import NetworkLayer
from .os_layer import OSLayer
from .hw_layer import HWLayer
from .report import Report
from .trace_interceptor import TraceInterceptor
from .db_error_manager import DBErrorManager

__version__ = "0.1.0"
__all__ = [
    "RuntimeGuard",
    "CrashTracker",
    "CrashStore",
    "DBHandler",
    "CrashToConstraint",
    "SSDLayer",
    "NetworkLayer",
    "OSLayer",
    "HWLayer",
    "Report",
    "TraceInterceptor",
    "DBErrorManager",
]
