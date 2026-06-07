"""Hardware Layer - Hardware Monitoring with CPU, RAM, and Disk Pressure

Monitors RAM, disk, CPU, system load, and network identity.
Provides hardware-level context for execution decisions.
"""

import socket
import os
from typing import Tuple, Any, Optional, Dict

try:
    import psutil
except ImportError:
    psutil = None


class HWLayer:
    """Hardware monitoring with CPU pressure and system load using VBStyle pattern."""

    def __init__(self):
        """Initialize HWLayer with default configuration."""
        self._state: Dict[str, Any] = {}
        self._config: Dict[str, Any] = {}
        if psutil is None:
            raise ImportError("psutil is required for HWLayer. Install with: pip install psutil")

    def Run(self, command: str, params: Dict[str, Any]) -> Tuple[int, Any, Optional[str]]:
        """Execute hardware layer command following VBStyle pattern.

        Args:
            command: Command to execute ("snapshot", "read_state", "set_config")
            params: Parameters for the command

        Returns:
            Tuple3: (ok, data, error)
                - ok: 1 if success, 0 if failure
                - data: Result data if success, None if failure
                - error: Error message if failure, None if success
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
            return 0, None, f"HWLayer error: {str(e)}"

    def _snapshot(self) -> Tuple[int, Dict[str, Any], None]:
        """Capture current hardware state snapshot.

        Returns:
            Tuple3: (1, hardware_state_dict, None)
        """
        try:
            # RAM metrics
            ram = psutil.virtual_memory()
            ram_data = {
                "total_gb": round(ram.total / (1024 ** 3), 2),
                "available_gb": round(ram.available / (1024 ** 3), 2),
                "used_percent": ram.percent,
            }

            # Disk metrics
            disk = psutil.disk_usage("/")
            disk_data = {
                "total_gb": round(disk.total / (1024 ** 3), 2),
                "used_gb": round(disk.used / (1024 ** 3), 2),
                "free_gb": round(disk.free / (1024 ** 3), 2),
                "used_percent": disk.percent,
            }

            # CPU metrics
            cpu_data = {
                "usage_percent": psutil.cpu_percent(interval=0.1),
            }

            # Load average
            load_avg = os.getloadavg()
            load_data = {
                "1m": round(load_avg[0], 2),
                "5m": round(load_avg[1], 2),
                "15m": round(load_avg[2], 2),
            }

            # Network identity
            network_data = {
                "hostname": socket.gethostname(),
                "ip": socket.gethostbyname(socket.gethostname()),
            }

            state = {
                "ram": ram_data,
                "disk": disk_data,
                "cpu": cpu_data,
                "load": load_data,
                "network": network_data,
            }
            self._state = state
            return 1, state, None
        except Exception as e:
            return 0, None, str(e)

    def _read_state(self) -> Tuple[int, Dict[str, Any], None]:
        """Read current hardware state.

        Returns:
            Tuple3: (1, current_state, None)
        """
        return 1, self._state, None

    def _set_config(self, params: Dict[str, Any]) -> Tuple[int, Dict[str, Any], None]:
        """Update configuration.

        Args:
            params: Configuration parameters

        Returns:
            Tuple3: (1, updated_config, None)
        """
        self._config.update(params)
        return 1, self._config, None

    def read_state(self) -> Dict[str, Any]:
        """Convenience method to read current state."""
        return self._state

    def set_config(self, config: Dict[str, Any]) -> Tuple[int, Dict[str, Any], None]:
        """Convenience method to set configuration."""
        return self._set_config(config)
