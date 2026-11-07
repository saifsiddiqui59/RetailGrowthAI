// Original splitVisualSegmentState from MartinDelophy/ai-video-editor@e1091feccca3be8832b507eb7e17c9e55eb2233a.
// Adaptation: use only the upstream pure splitter, avoiding unsupported
// visual-keyframe or GPU effects that cannot be rendered by HyperFrames.
import { cloneVisualSegment, makeId } from './timeline.js'
export function splitVisualSegmentState(source, firstDuration, secondDuration) {
  const playbackRate = source.type === "video"
    ? Math.max(0.25, Math.min(4, Number(source.playbackRate) || 1))
    : 1;
  const sourceStart = Math.max(0, Number(source.sourceStart) || 0);
  return [
    cloneVisualSegment(source, {
      id: makeId("visual"),
      duration: firstDuration,
      sourceDuration: source.type === "video" ? firstDuration * playbackRate : source.sourceDuration,
      sourceStart,
    }),
    cloneVisualSegment(source, {
      id: makeId("visual"),
      duration: secondDuration,
      sourceDuration: source.type === "video" ? secondDuration * playbackRate : source.sourceDuration,
      sourceStart: source.type === "video"
        ? sourceStart + firstDuration * playbackRate
        : sourceStart,
    }),
  ];
}

