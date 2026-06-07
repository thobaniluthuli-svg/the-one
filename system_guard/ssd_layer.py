"""SSD Layer - Storage Pressure and Filesystem Health Monitoring

Monitors disk capacity, storage pressure signal, and IO activity.
"""

from typing import Tuple, Any, Optional, Dict

try:
    import psutil
except ImportError:
    psutil = None


class SSDLayer:
    """Storage pressure and filesystem health monitoring using VBStyle pattern."""

    def __init__(self):
        """Initialize SSDLayer with default configuration."""
        self._state: Dict[str, Any] = {}
        self._config: Dict[str, Any] = {}
        if psutil is None:
            raise ImportError("psutil is required for SSDLayer. Install with: pip install psutil")

    def Run(self, command: str, params: Dict[str, Any]) -> Tuple[int, Any, Optional[str]]:
        """Execute storage layer command following VBStyle pattern.

        Args:
            command: Command to execute ("snapshot", "read_state", "set_config")
            params: Parameters for the command

        Returns:
            Tuple3: (ok, data, error)
        """
        try:
            if command == "snapshot":
                return self._snapshot()
            elif command == "read_state":
                return self._read_state()
            elif command == "set_config":
                return self._set_config(params)
            else:
                return 0, None, f"Unknown command: {command}"
        except Exception as e:
            return 0, None, f"SSDLayer error: {str(e)}"

    def _snapshot(self) -> Tuple[int, Dict[str, Any], None]:
        """Capture current storage state snapshot.

        Returns:
            Tuple3: (1, storage_state_dict, None)
        """
        try:
            # Disk capacity
            disk = psutil.disk_usage("/")
            disk_data = {
                "total_gb": round(disk.total / (1024 ** 3), 2),
                "used_gb": round(disk.used / (1024 ** 3), 2),
                "free_gb": round(disk.free / (1024 ** 3), 2),
                "used_percent": disk.percent,
            }

            # IO activity
            io_counters = psutil.disk_io_counters()
            io_data = {
                "read_bytes": io_counters.read_bytes,
                "write_bytes": io_counters.write_bytes,
                "read_count": io_counters.read_count,
                "write_count": io_counters.write_count,
            }

            state = {
                "disk": disk_data,
                "io": io_data,
            }
            self._state = state
            return 1, state, None
        except Exception as e:
            return 0, None, str(e)

    def _read_state(self) -> Tuple[int, Dict[str, Any], None]:
        """Read current storage state.

        Returns:
            Tuple3: (1, current_state, None)
        """
        return 1, self._state, None

    def _set_config(self, params: Dict[str, Any]) -> Tuple[int, Dict[str, Any], None]:
        """Update configuration."""
        self._config.update(params)
        return 1, self._config, None

    def read_state(self) -> Dict[str, Any]:
        """Convenience method to read current state."""
        return self._state

    def set_config(self, config: Dict[str, Any]) -> Tuple[int, Dict[str, Any], None]:
        """Convenience method to set configuration."""
        return self._set_config(config)
