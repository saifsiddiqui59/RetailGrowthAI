// Feature4 timeline-only seek normalization. No draft/media authorization changes.
// Do not allow malformed UI, beat markers or pointer geometry to poison the
// React playhead with NaN/Infinity or an out-of-range position.
export function boundedFrameSeek(requestedSeconds, durationSeconds, fps) {
  if (!Number.isFinite(requestedSeconds) || !Number.isFinite(durationSeconds) ||
      durationSeconds <= 0 || (fps !== 24 && fps !== 30)) return null
  const bounded = Math.min(durationSeconds, Math.max(0, requestedSeconds))
  return Math.min(durationSeconds, Math.max(0, Math.round(bounded * fps) / fps))
}
