import json
import os
from pathlib import Path

from .profile_discovery import HERMES_DIR


class StatusChecker:
    """Reads gateway_state.json and verifies process is alive."""

    def __init__(self, hermes_dir: Path, profiles_dir: Path):
        self._hermes_dir = hermes_dir
        self._profiles_dir = profiles_dir

    def _resolve_dir(self, profile_name: str, is_main: bool = False) -> Path:
        """Resolve directory for a profile or the main agent."""
        if is_main or profile_name == "__main__":
            return self._hermes_dir
        return self._profiles_dir / profile_name

    def get_status(self, profile: dict) -> dict:
        """Return status dict for a profile dict with {name, is_main}."""
        name = profile["name"]
        is_main = profile.get("is_main", False)
        profile_dir = self._resolve_dir(name, is_main)

        state_file = profile_dir / "gateway_state.json"
        config_file = profile_dir / "config.yaml"

        # Read config.yaml for model info
        model = "unknown"
        if config_file.exists():
            for line in config_file.read_text().splitlines():
                stripped = line.strip()
                # Main agent: "default: deepseek-chat" (top-level)
                # Profile: "  default: qwen3.5-plus" (indented under model:)
                if stripped.startswith("default:") and ":" in stripped:
                    model = stripped.split(":", 1)[1].strip()
                    break

        # Try to read gateway state
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
            pid = state.get("pid")
            gateway_state = state.get("gateway_state", "unknown")
            platforms = state.get("platforms", {})
            active_agents = state.get("active_agents", 0)

            # Verify process is alive
            process_alive = False
            if pid:
                try:
                    os.kill(pid, 0)
                    process_alive = True
                except (OSError, ProcessLookupError):
                    process_alive = False

            feishu_connected = platforms.get("feishu", {}).get("state") == "connected"

            return {
                "name": name if not is_main else "main",
                "pid": pid,
                "model": model,
                "running": process_alive,
                "state": gateway_state if process_alive else "stopped",
                "feishu_connected": feishu_connected,
                "active_agents": active_agents,
                "is_main": is_main,
            }

        # No state file
        return {
            "name": name if not is_main else "main",
            "pid": None,
            "model": model,
            "running": False,
            "state": "stopped",
            "feishu_connected": False,
            "active_agents": 0,
            "is_main": is_main,
        }
