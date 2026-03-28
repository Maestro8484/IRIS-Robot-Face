"""
hardware/audio_io.py - Audio input/output and volume control
Microphone capture, PCM playback, interrupt listener, volume (wm8960).
"""
# TODO: move from assistant.py:
#   _find_mic_device_index, _find_wm8960_card, get_volume, set_volume
#   play_pcm, play_pcm_speaking, play_beep, play_double_beep
#   _playback_interrupt_listener, record_command
