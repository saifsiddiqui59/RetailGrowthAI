// Feature4 timeline-only seek normalization. No draft/media authorization changes.
// Do not allow malformed UI, beat markers or pointer geometry to poison the
// React playhead with NaN/Infinity or an out-of-range position.
export function boundedFrameSeek(requestedSeconds, durationSeconds, fps) {
  if (!Number.isFinite(requestedSeconds) || !Number.isFinite(durationSeconds) ||
      durationSeconds <= 0 || (fps !== 24 && fps !== 30)) return null
  const bounded = Math.min(durationSeconds, Math.max(0, requestedSeconds))
  return Math.min(durationSeconds, Math.max(0, Math.round(bounded * fps) / fps))
}

// Scene click navigation must share the same frame boundary as timecode/keyboard.
// Invalid or out-of-bounds spans are not usable preview positions.
export function boundedSceneMidpointSeek(startSeconds, sceneDurationSeconds, durationSeconds, fps) {
  if (!Number.isFinite(startSeconds) || !Number.isFinite(sceneDurationSeconds) ||
      !Number.isFinite(durationSeconds) || startSeconds < 0 ||
      sceneDurationSeconds <= 0 || durationSeconds <= 0 ||
      startSeconds >= durationSeconds ||
      sceneDurationSeconds > durationSeconds - startSeconds + 1e-6) return null
  return boundedFrameSeek(startSeconds + sceneDurationSeconds / 2, durationSeconds, fps)
}
