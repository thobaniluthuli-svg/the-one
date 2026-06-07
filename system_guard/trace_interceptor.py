"""Trace Interceptor - Automatic Execution Capture with Zero Manual Tagging

Wraps any class dynamically and intercepts all method calls automatically.
Captures execution packets for Report (runtime) and DBErrorManager (persistent storage).
"""

import time
import traceback
import functools
from typing import Callable, Any, Type, Dict, Optional, Tuple, List


class TraceInterceptor:
    """Automatic execution capture with zero manual tagging."""

    def __init__(self, report: Optional[Any] = None, db_error_manager: Optional[Any] = None):
        """Initialize TraceInterceptor with optional Report and DBErrorManager.

        Args:
            report: Report instance for runtime aggregation
            db_error_manager: DBErrorManager instance for persistent storage
        """
        self.report = report
        self.db_error_manager = db_error_manager
        self._wrapped_classes: List[str] = []

    def wrap(self, cls: Type) -> Type:
        """Dynamically wrap all methods in a class.

        Args:
            cls: Class to wrap

        Returns:
            Wrapped class with intercepted methods
        """
        original_methods = {}

        # Capture all methods
        for name in dir(cls):
            if name.startswith("_"):
                continue
            attr = getattr(cls, name)
            if callable(attr):
                original_methods[name] = attr

        # Create wrapper for each method
        for method_name, original_method in original_methods.items():

            def make_wrapper(orig_method, m_name):
                @functools.wraps(orig_method)
                def wrapper(self_inner, *args, **kwargs):
                    return TraceInterceptor._intercept(
                        self_inner,
                        cls.__name__,
                        m_name,
                        orig_method,
                        args,
                        kwargs,
                        self.report,
                        self.db_error_manager,
                    )

                return wrapper

            setattr(cls, method_name, make_wrapper(original_method, method_name))

        self._wrapped_classes.append(cls.__name__)
        return cls

    @staticmethod
    def _intercept(
        instance: Any,
        class_name: str,
        method_name: str,
        fn: Callable,
        args: Tuple,
        kwargs: Dict,
        report: Optional[Any],
        db_error_manager: Optional[Any],
    ) -> Any:
        """Core interceptor logic.

        Args:
            instance: Instance executing the method
            class_name: Name of the class
            method_name: Name of the method
            fn: Original function
            args: Positional arguments
            kwargs: Keyword arguments
            report: Report instance
            db_error_manager: DBErrorManager instance

        Returns:
            Original function result (or raises exception if occurred)

        Raises:
            Exception: If the original function raised
        """
        ts = time.time()
        status = "SUCCESS"
        result = None
        error_info = None

        try:
            result = fn(instance, *args, **kwargs)
            return result
        except Exception as e:
            status = "ERROR"
            tb_str = traceback.format_exc()
            error_info = {
                "type": e.__class__.__name__,
                "message": str(e),
                "trace": tb_str,
            }

            # Build and send packet
            packet = TraceInterceptor._build_packet(
                class_name, method_name, status, result, error_info, args, kwargs, ts
            )

            # Ingest to Report
            if report:
                report.Run("ingest", {"packet": packet})

            # Ingest to DB
            if db_error_manager:
                db_error_manager.ingest_error(packet)

            # Re-raise to maintain natural Python behavior
            raise

    @staticmethod
    def _build_packet(
        class_name: str,
        method_name: str,
        status: str,
        result: Any,
        error: Optional[Dict],
        args: Tuple,
        kwargs: Dict,
        ts: float,
    ) -> Dict[str, Any]:
        """Create execution packet.

        Args:
            class_name: Name of the class
            method_name: Name of the method
            status: "SUCCESS" or "ERROR"
            result: Result if success
            error: Error info dict if error
            args: Function arguments
            kwargs: Function keyword arguments
            ts: Timestamp

        Returns:
            Execution packet dictionary
        """
        packet = {
            "meta": {
                "ts": ts,
                "class": class_name,
                "method": method_name,
                "status": status,
            },
            "trace": {
                "args": str(args)[:500],  # Truncate large arguments
                "kwargs": str(kwargs)[:500],
            },
        }

        if status == "SUCCESS":
            packet["result"] = str(result)[:500]
        else:
            packet["error"] = error

        return packet
