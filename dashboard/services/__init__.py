from pathlib import Path
from .profile_discovery import ProfileDiscovery, HERMES_DIR
from .status_checker import StatusChecker
from .process_control import ProcessControl
from .log_streamer import LogStreamer

HERMES_PROFILES_DIR = HERMES_DIR / "profiles"

discovery = ProfileDiscovery(HERMES_DIR, HERMES_PROFILES_DIR)
status = StatusChecker(HERMES_DIR, HERMES_PROFILES_DIR)
control = ProcessControl()
log_streamer = LogStreamer(HERMES_DIR, HERMES_PROFILES_DIR)
