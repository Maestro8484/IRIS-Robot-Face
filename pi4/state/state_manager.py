"""
state_manager.py - Centralized runtime state for IRIS assistant.

All mutable runtime state lives here. Import `state` wherever needed
instead of using module-level globals in assistant.py.

Usage:
    from state.state_manager import state
    state.kids_mode = True
    state.conversation_history.append(...)
"""
import threading


class StateManager:
    """Container for IRIS runtime state. Thread-safe for simple attribute access via GIL."""

    def __init__(self):
        self._lock = threading.Lock()

        # Conversation
        self.conversation_history: list = []
        self.last_interaction: float = 0.0

        # Operating modes
        self.kids_mode: bool = False
        self.eyes_sleeping: bool = False

        # Person recognition
        self.person_context: dict = {"name": None, "desc": ""}
        self.last_recognition_time: float = 0.0

    # ── Conversation helpers ──────────────────────────────────────────────────

    def clear_conversation(self):
        """Clear conversation history, person context, and recognition timer.
        Does NOT reset last_interaction (mode switches keep the timer running)."""
        with self._lock:
            self.conversation_history.clear()
            self.person_context = {"name": None, "desc": ""}
            self.last_recognition_time = 0.0

    def has_conversation(self) -> bool:
        return bool(self.conversation_history)

    # ── Person context ────────────────────────────────────────────────────────

    def set_person(self, name, desc: str = ""):
        with self._lock:
            self.person_context = {"name": name, "desc": desc}


# Module-level singleton — import `state` wherever runtime state is needed.
state = StateManager()
