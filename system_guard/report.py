"""Report - Schema-Free VBSTYLE Report Assembler

Aggregates layer outputs without defining structure.
Dynamic layer registration and schema-free output.
"""

import time
import inspect
from typing import Tuple, Any, Optional, Dict, List


class Report:
    """Schema-free VBSTYLE report assembler."""

    def __init__(self):
        """Initialize Report with empty layer registry."""
        self._layers: Dict[str, Any] = {}
        self._vbmeta: Dict[str, List[str]] = {}
        self._packets: List[Dict[str, Any]] = []

    def Run(self, command: str, params: Dict[str, Any]) -> Tuple[int, Any, Optional[str]]:
        """Execute report command following VBStyle pattern.

        Args:
            command: Command to execute
            params: Parameters for the command

        Returns:
            Tuple3: (ok, data, error)
        """
        try:
            if command == "attach_layer":
                return self._attach_layer(params)
            elif command == "build":
                return self._build(params)
            elif command == "snapshot":
                return self._snapshot(params)
            elif command == "ingest":
                return self._ingest(params)
            else:
                return 0, None, f"Unknown command: {command}"
        except Exception as e:
            return 0, None, f"Report error: {str(e)}"

    def _attach_layer(self, params: Dict[str, Any]) -> Tuple[int, Dict[str, Any], None]:
        """Register a layer for aggregation.

        Args:
            params: Should contain 'name' and 'layer' keys

        Returns:
            Tuple3: (1, attachment_info, None)
        """
        name = params.get("name")
        layer = params.get("layer")

        if not name or not layer:
            return 0, None, "Missing 'name' or 'layer' in params"

        self._layers[name] = layer
        self._vbmeta[name] = self._extract_tags(layer)

        return 1, {"name": name, "attached": True}, None

    def _extract_tags(self, obj: Any) -> List[str]:
        """Extract VBMETA tags from class source.

        Args:
            obj: Object to extract tags from

        Returns:
            List of extracted tags
        """
        try:
            source = inspect.getsource(obj.__class__)
            tags = []
            for line in source.split("\n"):
                if "VBMETA" in line or "VBStyle" in line:
                    tags.append(line.strip())
            return tags
        except Exception:
            return []

    def _build(self, params: Dict[str, Any]) -> Tuple[int, Dict[str, Any], None]:
        """Run all layers and aggregate results.

        Returns:
            Tuple3: (1, aggregated_report, None)
        """
        payload = {}

        for name, layer in self._layers.items():
            try:
                ok, data, error = layer.Run("snapshot", {})
                payload[name] = {"ok": ok, "data": data, "error": error}
            except Exception as e:
                payload[name] = {"ok": 0, "data": None, "error": str(e)}

        report = {
            "meta": {
                "ts": time.time(),
                "type": "VBSTYLE_REPORT",
            },
            "payload": payload,
            "vbmeta": self._vbmeta,
        }

        return 1, report, None

    def _snapshot(self, params: Dict[str, Any]) -> Tuple[int, Dict[str, Any], None]:
        """Debug view of internal state.

        Returns:
            Tuple3: (1, snapshot_info, None)
        """
        snapshot = {
            "layers_registered": list(self._layers.keys()),
            "packets_ingested": len(self._packets),
            "vbmeta_count": len(self._vbmeta),
        }
        return 1, snapshot, None

    def _ingest(self, params: Dict[str, Any]) -> Tuple[int, Dict[str, Any], None]:
        """Accept execution packets from TraceInterceptor.

        Args:
            params: Should contain 'packet' key

        Returns:
            Tuple3: (1, ingestion_info, None)
        """
        packet = params.get("packet")
        if not packet:
            return 0, None, "Missing 'packet' in params"

        self._packets.append(packet)
        return 1, {"packets_stored": len(self._packets)}, None

    def read_state(self) -> Dict[str, Any]:
        """Convenience method to read current state."""
        return {
            "layers": list(self._layers.keys()),
            "packets": len(self._packets),
        }

    def set_config(self, config: Dict[str, Any]) -> Tuple[int, Dict[str, Any], None]:
        """Convenience method to set configuration."""
        return 1, config, None
