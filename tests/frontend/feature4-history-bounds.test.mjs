import test from 'node:test'
import assert from 'node:assert/strict'
import {
  createEditorHistory, pushEditorHistory, undoEditorHistory, redoEditorHistory,
} from '../../frontend/src/features/video/vendor/editorHistoryCore.mjs'

test('F4-09: adapted timeline undo retains only the last 50 snapshots', () => {
  let history = createEditorHistory({ frame: 0 })
  for (let frame = 1; frame <= 150; frame++)
    history = pushEditorHistory(history, { frame })
  assert.equal(history.past.length, 50)
  assert.equal(history.past[0].frame, 100)
  assert.equal(history.current.frame, 150)
  for (let i = 0; i < 50; i++) {
    const result = undoEditorHistory(history)
    assert.equal(result.changed, true)
    history = result.history
  }
  assert.equal(history.current.frame, 100)
  assert.equal(undoEditorHistory(history).changed, false)
  for (let i = 0; i < 50; i++) history = redoEditorHistory(history).history
  assert.equal(history.current.frame, 150)
  assert.equal(redoEditorHistory(history).changed, false)
})

test('F4-09: invalid/unbounded custom history limits fail to bounded defaults', () => {
  for (const limit of [NaN, Infinity, -Infinity, 'not-a-number']) {
    let history = createEditorHistory({ frame: 0 })
    for (let frame = 1; frame <= 80; frame++)
      history = pushEditorHistory(history, { frame }, limit)
    assert.equal(history.past.length, 50, String(limit))
  }
  let limited = createEditorHistory({ frame: 0 })
  for (let frame = 1; frame <= 10; frame++)
    limited = pushEditorHistory(limited, { frame }, 0)
  assert.equal(limited.past.length, 1)
  limited = createEditorHistory({ frame: 0 })
  for (let frame = 1; frame <= 10; frame++)
    limited = pushEditorHistory(limited, { frame }, 2.9)
  assert.equal(limited.past.length, 2)
})

test('F4-09: upstream history branching clears redo even for a same-reference edit', () => {
  const first = { frame: 0 }
  const second = { frame: 1 }
  const history = pushEditorHistory(createEditorHistory(first), second)
  const undone = undoEditorHistory(history).history
  assert.equal(redoEditorHistory(undone).value, second)
  const branch = pushEditorHistory(undone, first)
  assert.equal(branch.current, first)
  assert.equal(branch.future.length, 0)
  assert.equal(redoEditorHistory(branch).changed, false)
  assert.equal(history.current, second)
})
