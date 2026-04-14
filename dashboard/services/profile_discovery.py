from pathlib import Path

HERMES_DIR = Path.home() / ".hermes"


class ProfileDiscovery:
    """Scans ~/.hermes/ for the main agent and ~/.hermes/profiles/ for sub-agents."""

    def __init__(self, hermes_dir: Path, profiles_dir: Path):
        self._hermes_dir = hermes_dir
        self._profiles_dir = profiles_dir

    def list_profiles(self) -> list[dict]:
        """Return list of {name, is_main} dicts, main agent first."""
        result = []

        # Main agent: ~/.hermes/ is the main agent if it has config.yaml
        if (self._hermes_dir / "config.yaml").exists():
            result.append({"name": "__main__", "is_main": True})

        # Sub-agents: ~/.hermes/profiles/<name>/
        if self._profiles_dir.exists():
            for d in sorted(self._profiles_dir.iterdir()):
                if d.is_dir():
                    result.append({"name": d.name, "is_main": False})

        return result
