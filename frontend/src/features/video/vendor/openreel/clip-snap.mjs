// Extracted from augani/openreel-video/packages/core/src/timeline/clip-manager.ts
// Pinned 367d7e90b61b5181f9861b852bb8b9d7a7d2954a; MIT © 2024-2026 Augustus Otu and Contributors.
// Original ClipManager.snapToGrid, with TS syntax removed. No action executor.
export class OpenReelClipSnapper {
  constructor({ snapToGridEnabled = true, gridSize = 1, snapThreshold = 8 } = {}) {
    this.snapToGridEnabled = snapToGridEnabled
    this.gridSize = gridSize
    this.snapThreshold = snapThreshold
  }
  snapToGrid(time, timeline, trackId, pixelsPerSecond, excludeClipId) {
    if (!this.snapToGridEnabled) {
      return { snappedTime: time, didSnap: false };
    }
    const timeThreshold = this.snapThreshold / pixelsPerSecond;

    let closestSnap = time;
    let closestDistance = Infinity;
    let snapTarget = undefined;

    // Snap to grid lines
    const gridSnap = Math.round(time / this.gridSize) * this.gridSize;
    const gridDistance = Math.abs(time - gridSnap);
    if (gridDistance < timeThreshold && gridDistance < closestDistance) {
      closestSnap = gridSnap;
      closestDistance = gridDistance;
      snapTarget = "grid";
    }

    // Snap to clip boundaries on the same track
    const track = timeline.tracks.find((t) => t.id === trackId);
    if (track) {
      for (const clip of track.clips) {
        if (clip.id === excludeClipId) continue;

        // Snap to clip start
        const startDistance = Math.abs(time - clip.startTime);
        if (startDistance < timeThreshold && startDistance < closestDistance) {
          closestSnap = clip.startTime;
          closestDistance = startDistance;
          snapTarget = "clip-start";
        }

        // Snap to clip end
        const clipEnd = clip.startTime + clip.duration;
        const endDistance = Math.abs(time - clipEnd);
        if (endDistance < timeThreshold && endDistance < closestDistance) {
          closestSnap = clipEnd;
          closestDistance = endDistance;
          snapTarget = "clip-end";
        }
      }
    }

    return {
      snappedTime: closestSnap,
      didSnap: closestDistance < timeThreshold,
      snapTarget,
    };
  }

}
