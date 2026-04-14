import time
from pathlib import Path

from .profile_discovery import HERMES_DIR

VALID_LOG_TYPES = ["gateway.log", "agent.log", "errors.log"]


class LogStreamer:
    """Read recent log lines and stream new lines via SSE."""

    def __init__(self, hermes_dir: Path, profiles_dir: Path):
        self._hermes_dir = hermes_dir
        self._profiles_dir = profiles_dir
        self._file_positions: dict[str, int] = {}

    def _resolve_dir(self, profile_name: str, is_main: bool = False) -> Path:
        if is_main or profile_name == "__main__":
            return self._hermes_dir
        return self._profiles_dir / profile_name

    def get_recent_lines(self, profile_name: str, log_type: str, n_lines: int = 100, is_main: bool = False) -> str:
        """Return last N lines from the log file."""
        profile_dir = self._resolve_dir(profile_name, is_main)
        log_file = profile_dir / "logs" / log_type
        if not log_file.exists():
            return ""
        text = log_file.read_text(errors="replace")
        lines = text.splitlines()
        return "\n".join(lines[-n_lines:]) if lines else ""

    def stream_new_lines(self, profile_name: str, log_type: str, is_main: bool = False):
        """Generator that yields new log lines as SSE messages."""
        key = f"{profile_name}:{log_type}"
        profile_dir = self._resolve_dir(profile_name, is_main)
        log_file = profile_dir / "logs" / log_type

        if not log_file.exists():
            yield f"event: error\ndata: Log file not found: {log_type}\n\n"
            return

        # Initialize position at end of file
        if key not in self._file_positions:
            self._file_positions[key] = log_file.stat().st_size

        try:
            with open(log_file) as f:
                while True:
                    try:
                        current_size = log_file.stat().st_size
                    except FileNotFoundError:
                        yield f"event: error\ndata: Log file removed\n\n"
                        return

                    if current_size < self._file_positions.get(key, 0):
                        f.seek(0)
                        self._file_positions[key] = 0

                    f.seek(self._file_positions.get(key, 0))
                    new_lines = f.readlines()
                    if new_lines:
                        self._file_positions[key] = f.tell()
                        for line in new_lines:
                            yield f"event: log\ndata: {line.rstrip()}\n\n"

                    time.sleep(0.3)
        except GeneratorExit:
            self._file_positions.pop(key, None)
        except Exception as e:
            self._file_positions.pop(key, None)
            yield f"event: error\ndata: {e}\n\n"
