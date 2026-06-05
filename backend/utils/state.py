"""
Simple in-memory state for real-time system status tracking.
Tracks components currently active (scraper, publisher) and their status.
"""

from typing import Dict, Any
from datetime import datetime

_system_state = {
    "scraper": {"status": "idle", "last_run": None, "message": "Ready"},
    "publisher": {"status": "idle", "last_run": None, "message": "Ready"},
}

def get_state() -> Dict[str, Any]:
    """Return a copy of the current system state."""
    return {
        k: dict(v) for k, v in _system_state.items()
    }

def update_state(component: str, status: str, message: str = ""):
    """Update the status of a specific component."""
    if component in _system_state:
        _system_state[component]["status"] = status
        _system_state[component]["message"] = message
        _system_state[component]["last_run"] = datetime.now().isoformat()
