"""
state/state_manager.py - Centralized runtime state
Replaces scattered globals in assistant.py.
Tracks: sleep, kids mode, speaking, interrupted, follow-up, conversation context.
"""
# TODO: replace globals from assistant.py:
#   _eyes_sleeping, _kids_mode, _speaking, _interrupted
#   _follow_up_active, conversation_history, _last_interaction
#   _person_context, _last_recognition_time
#   Also: flush_conversation_log, _context_watchdog
