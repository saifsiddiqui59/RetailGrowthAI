"""Default thresholds and filler word lists for autoclip."""

from __future__ import annotations

# Case-insensitive whole-word / whole-phrase matching (longest phrases first in fillers.py).
DEFAULT_FILLER_WORDS: tuple[str, ...] = (
    "um",
    "uh",
    "erm",
    "ah",
    "hmm",
    "like",
    "you know",
    "i mean",
    "sort of",
    "basically",
    "actually",
)

# Prompt biases Whisper to emit filler tokens instead of silently dropping them.
FILLER_TRANSCRIBE_PROMPT = (
    "Um, uh, er, erm, ah, hmm, like, you know, I mean. Verbatim transcript with fillers."
)

# Gaps between words longer than this may contain audio fillers Whisper omitted.
FILLER_GAP_MIN_SEC = 0.35

# Gaps longer than this are treated as pauses, not fillers (handled by --max-pause).
FILLER_GAP_MAX_SEC = 1.1

# Word durations above expected * this ratio may include glued-on filler audio.
FILLER_OVERLONG_RATIO = 3.2

# Minimum RMS vs speech reference to treat an inter-word gap as voiced (filler).
FILLER_GAP_VOICE_RMS_RATIO = 0.32

# Default filler detection preset when --remove-fillers is enabled.
DEFAULT_FILLER_SENSITIVITY = "conservative"

# Padding around filler hits so cuts feel natural (plan: 50–100 ms).
FILLER_PADDING_SEC = 0.075

# Merge cut windows when gaps between them are at most this wide (plan: 200 ms).
CUT_MERGE_GAP_SEC = 0.2

# Minimum kept segment length after compose (used by compose; documented here for CLI defaults).
MIN_KEEP_SEGMENT_SEC = 0.3

# Short audio crossfade at compose joins (softens clicks; 0 disables).
DEFAULT_AUDIO_CROSSFADE_SEC = 0.03

# Refuse to remove more than this fraction of timeline without --force.
MAX_REMOVAL_RATIO = 0.4

# Retake detection: near-duplicate phrase restarts (keep later take).
RETAKE_MIN_WORDS = 3
RETAKE_MAX_WORDS = 12
RETAKE_MAX_GAP_SEC = 4.0
RETAKE_MIN_SIMILARITY = 0.72
RETAKE_MIN_BOUNDARY_GAP_SEC = 0.12

# Viral heuristic thresholds (Feature 5).
HOOK_WINDOW_3_SEC = 3.0
HOOK_WINDOW_5_SEC = 5.0
HOOK_DEAD_AIR_WINDOW_SEC = 15.0
SLOW_HOOK_WPM_THRESHOLD = 80.0
HIGH_FILLER_RATIO_THRESHOLD = 0.08
LONG_PAUSE_IN_CLIP_SEC = 2.0
CLIP_WINDOW_DURATIONS_SEC: tuple[float, ...] = (30.0, 60.0)
TOP_SUGGESTED_CLIPS = 3
MIN_INTERNAL_PAUSE_SEC = 0.3
