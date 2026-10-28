"""Detect spoken retakes (false starts) and cut the abandoned take."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from autoclip.constants import (
    CUT_MERGE_GAP_SEC,
    RETAKE_MAX_GAP_SEC,
    RETAKE_MAX_WORDS,
    RETAKE_MIN_BOUNDARY_GAP_SEC,
    RETAKE_MIN_SIMILARITY,
    RETAKE_MIN_WORDS,
)
from autoclip.models import CutWindow, Transcript, WordTimestamp, merge_cut_windows

_TOKEN_RE = re.compile(r"[a-z0-9']+")


def detect_retake_cuts(
    transcript: Transcript,
    *,
    min_words: int = RETAKE_MIN_WORDS,
    max_words: int = RETAKE_MAX_WORDS,
    max_gap_sec: float = RETAKE_MAX_GAP_SEC,
    min_similarity: float = RETAKE_MIN_SIMILARITY,
    min_boundary_gap_sec: float = RETAKE_MIN_BOUNDARY_GAP_SEC,
    merge_gap_sec: float = CUT_MERGE_GAP_SEC,
) -> list[CutWindow]:
    """
    Find abandoned takes that are restarted with a near-duplicate phrase.

    Keeps the later take and returns cut windows covering the earlier attempt
    plus any stumble/reset between the two.
    """
    if min_words < 2 or max_words < min_words:
        return []

    words = _iter_words(transcript)
    if len(words) < min_words * 2:
        return []

    tokens = [_normalize_token(w.word) for w in words]
    if sum(1 for t in tokens if t) < min_words * 2:
        return []

    candidates: list[tuple[int, int, int, float]] = []
    # (abandoned_start, restart_start, match_len, similarity)

    for n in range(max_words, min_words - 1, -1):
        for i in range(0, len(words) - 2 * n + 1):
            abandoned_tokens = tokens[i : i + n]
            if not all(abandoned_tokens):
                continue

            abandoned_end = words[i + n - 1].end
            j = i + n
            while j + n <= len(words):
                gap = words[j].start - abandoned_end
                if gap > max_gap_sec:
                    break
                if gap < 0:
                    j += 1
                    continue

                restart_tokens = tokens[j : j + n]
                if not all(restart_tokens):
                    j += 1
                    continue

                similarity = _token_similarity(abandoned_tokens, restart_tokens)
                if similarity < min_similarity:
                    j += 1
                    continue

                continues = j + n < len(words)
                has_boundary = gap >= min_boundary_gap_sec
                if not continues and not has_boundary:
                    j += 1
                    continue

                candidates.append((i, j, n, similarity))
                break

    if not candidates:
        return []

    # Longest, most similar matches first; then earliest on the timeline.
    candidates.sort(key=lambda item: (-item[2], -item[3], item[0]))

    used = [False] * len(words)
    cuts: list[CutWindow] = []

    for i, j, _n, _sim in candidates:
        if any(used[k] for k in range(i, j)):
            continue
        cut_start = words[i].start
        cut_end = words[j].start
        if cut_end <= cut_start:
            continue
        for k in range(i, j):
            used[k] = True
        cuts.append(CutWindow(start=cut_start, end=cut_end, kind="retake"))

    return merge_cut_windows(cuts, gap_sec=merge_gap_sec)


def _iter_words(transcript: Transcript) -> list[WordTimestamp]:
    words: list[WordTimestamp] = []
    for segment in transcript.segments:
        words.extend(segment.words)
    return words


def _normalize_token(word: str) -> str:
    match = _TOKEN_RE.search(word.lower())
    return match.group(0) if match else ""


def _token_similarity(left: list[str], right: list[str]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    if left == right:
        return 1.0
    matcher = SequenceMatcher(a=left, b=right, autojunk=False)
    return matcher.ratio()
