"""OS Layer - Operating System State and Runtime Environment Detection

Captures system information: OS name, node, release, version, machine, processor.
Provides OS-level context for execution decisions.
"""

import platform
from typing import Tuple, Any, Optional, Dict


class OSLayer:
    """OS state and runtime environment detection using VBStyle pattern."""

    def __init__(self):
        """Initialize OSLayer with default configuration."""
        self._state: Dict[str, Any] = {}
        self._config: Dict[str, Any] = {}

    def Run(self, command: str, params: Dict[str, Any]) -> Tuple[int, Any, Optional[str]]:
        """Execute OS layer command following VBStyle pattern.

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
            return 0, None, f"OSLayer error: {str(e)}"

    def _snapshot(self) -> Tuple[int, Dict[str, Any], None]:
        """Capture current OS state snapshot.

        Returns:
            Tuple3: (1, os_state_dict, None)
        """
        try:
            state = {
                "system": platform.system(),
                "node": platform.node(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "implementation": platform.python_implementation(),
            }
            self._state = state
            return 1, state, None
        except Exception as e:
            return 0, None, str(e)

    def _read_state(self) -> Tuple[int, Dict[str, Any], None]:
        """Read current OS state.

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
