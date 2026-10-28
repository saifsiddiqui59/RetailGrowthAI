// Copied functional subset from augani/openreel-video/apps/web/src/utils/timeline-item-actions.ts
// Pinned 367d7e90b61b5181f9861b852bb8b9d7a7d2954a; MIT © 2024-2026 Augustus Otu and Contributors.
// Removed TypeScript types and store-mutating handlers. Pure track/clip selection only.
export function getTimelineItemRanges(project) {
  const items = [];

  for (const track of project.timeline.tracks) {
    for (const clip of track.clips) {
      items.push({
        id: clip.id,
        trackId: track.id,
        startTime: clip.startTime,
        duration: clip.duration,
        kind: "media",
      });
    }
  }

  const append = (clips, kind) => {
    for (const clip of clips ?? []) {
      items.push({ ...clip, kind });
    }
  };

  append(project.textClips, "text");
  append(project.shapeClips, "shape");
  append(project.svgClips, "svg");
  append(project.stickerClips, "sticker");

  return items;
}

export function getSplittableTimelineItemIds(
  project, selectedIds, time) {
  const selected = new Set(selectedIds);
  return getTimelineItemRanges(project)
    .filter(
      (item) =>
        selected.has(item.id) &&
        time > item.startTime &&
        time < item.startTime + item.duration,
    )
    .map((item) => item.id);
}

export function getTimelineSelectionItems(project) {
  return getTimelineItemRanges(project).map(toSelectionItem);
}

/** Select every media or overlay clip assigned to one timeline track. */
export function getTimelineTrackSelection(
  project, trackId) {
  return getTimelineItemRanges(project)
    .filter((item) => item.trackId === trackId)
    .sort((left, right) =>
      left.startTime === right.startTime
        ? left.id.localeCompare(right.id)
        : left.startTime - right.startTime,
    )
    .map(toSelectionItem);
}

function toSelectionItem(item) {
  return {
    id: item.id,
    trackId: item.trackId,
    type: item.kind === "media" ? "clip" : item.kind === "text" ? "text-clip" : "shape-clip",
  };
}

