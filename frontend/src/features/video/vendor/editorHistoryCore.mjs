export function createEditorHistory(initial) {
  return { past: [], current: initial, future: [] };
}

export function pushEditorHistory(
  history,
  next, limit = 50,
) {
  const safeLimit = Math.max(1, Math.floor(limit));
  return {
    past: [...history.past, history.current].slice(-safeLimit),
    current: next,
    future: [],
  };
}

export function undoEditorHistory(history) {
  const previous = history.past.at(-1);
  if (previous === undefined) return { history, value: history.current, changed: false };
  const nextHistory = {
    past: history.past.slice(0, -1),
    current: previous,
    future: [history.current, ...history.future],
  };
  return { history: nextHistory, value: previous, changed: true };
}

export function redoEditorHistory(history) {
  const next = history.future[0];
  if (next === undefined) return { history, value: history.current, changed: false };
  const nextHistory = {
    past: [...history.past, history.current],
    current: next,
    future: history.future.slice(1),
  };
  return { history: nextHistory, value: next, changed: true };
}
