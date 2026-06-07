"""Network Layer - Network State, Connectivity, and Throughput Monitoring

Monitors network identity, live traffic, and interface mapping.
"""

import socket
from typing import Tuple, Any, Optional, Dict, List

try:
    import psutil
except ImportError:
    psutil = None


class NetworkLayer:
    """Network state and throughput monitoring using VBStyle pattern."""

    def __init__(self):
        """Initialize NetworkLayer with default configuration."""
        self._state: Dict[str, Any] = {}
        self._config: Dict[str, Any] = {}
        self._last_io: Dict[str, int] = {}
        if psutil is None:
            raise ImportError("psutil is required for NetworkLayer. Install with: pip install psutil")

    def Run(self, command: str, params: Dict[str, Any]) -> Tuple[int, Any, Optional[str]]:
        """Execute network layer command following VBStyle pattern.

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
            return 0, None, f"NetworkLayer error: {str(e)}"

    def _snapshot(self) -> Tuple[int, Dict[str, Any], None]:
        """Capture current network state snapshot.

        Returns:
            Tuple3: (1, network_state_dict, None)
        """
        try:
            # Network identity
            hostname = socket.gethostname()
            try:
                ip = socket.gethostbyname(hostname)
            except socket.gaierror:
                ip = "unknown"

            identity_data = {
                "hostname": hostname,
                "ip": ip,
            }

            # Traffic metrics
            net_io = psutil.net_io_counters()
            bytes_sent_delta = net_io.bytes_sent - self._last_io.get("bytes_sent", net_io.bytes_sent)
            bytes_recv_delta = net_io.bytes_recv - self._last_io.get("bytes_recv", net_io.bytes_recv)
            self._last_io["bytes_sent"] = net_io.bytes_sent
            self._last_io["bytes_recv"] = net_io.bytes_recv

            traffic_data = {
                "bytes_sent_delta": bytes_sent_delta,
                "bytes_recv_delta": bytes_recv_delta,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
            }

            # Interface mapping
            interfaces_data = {}
            try:
                if_addrs = psutil.net_if_addrs()
                for iface_name, iface_addrs in if_addrs.items():
                    interfaces_data[iface_name] = [
                        {"family": str(addr.family), "address": addr.address}
                        for addr in iface_addrs
                    ]
            except Exception:
                pass

            state = {
                "identity": identity_data,
                "traffic": traffic_data,
                "interfaces": interfaces_data,
            }
            self._state = state
            return 1, state, None
        except Exception as e:
            return 0, None, str(e)

    def _read_state(self) -> Tuple[int, Dict[str, Any], None]:
        """Read current network state.

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
