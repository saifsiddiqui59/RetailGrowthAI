# F4 historical #779 and #966 exact full patch archive — 2026-11-19

**Source archaeology only, not production code integration or Feature4 DONE.** Original #779 stacked onto parent F4 #322, and older #966 canonical integration documentation diverges from newer main. This file preserves all original changed-path hunks before any UNMERGED draft/doc PR closure. It does not modify shared interfaces, original feature task IDs or actual current runtime.

- [#779](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/779) original HEAD `c1d66e9b3903c45ae4cc9930ad1362a38b3f8843`; 51 changed paths retained verbatim.
- [#966](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/966) original HEAD `9962da1764d54b199fc069e9cf0f02f911849327`; 7 changed paths retained verbatim.

Original #322 remains OPEN/DRAFT for all unique UI, reviewer, private asset storage and full render/visual acceptance; #993 integrated only a few F4 CPU technical QA slices with exact head/fresh-main 4/4. Original #779 path changes are **not all integrated**; original source hunks archived here for future selective current-main port. Historical #966 carries F4/F3 documentation; it is not proof of accepted hosted F3 or F4.

## Original #779 HEAD c1d66e9b3903c45ae4cc9930ad1362a38b3f8843
https://github.com/saifsiddiqui59/RetailGrowthAI/pull/779/files

### frontend/e2e/fixtures/timeline-studio-harness.jsx
~~~~diff
@@ -2,6 +2,7 @@
 import React from 'react'
 import { createRoot } from 'react-dom/client'
 import VideoStudio from '../../src/features/video/VideoStudio.jsx'
+import TimelineStudioSurface from '../../src/features/video/TimelineStudioSurface.jsx'
 
 export function mountFeature4({shop,approved,seedCompletedRender=false,seedOwnerRejectedRender=false}) {
   const holder=document.createElement('div')
@@ -75,3 +76,38 @@ export function mountFeature4BeatLane({shop, authorized=true,approvedDirection=f
     }))
   })
 }
+
+
+// Race-only Playwright harness. Two isolated synthetic shops, no API or real
+// media rights. Changing the owner/draft while dragging must discard the
+// original pointer-up event before any unreviewed edit reaches onChange.
+export function mountFeature4ResizeRace({shop}) {
+  const holder = document.createElement('div')
+  holder.id = 'feature4-resize-race'
+  document.getElementById('root')?.setAttribute('hidden', '')
+  document.body.appendChild(holder)
+  const root = createRoot(holder)
+  window.__feature4ResizeWrites = []
+  const render = (currentShop, approved = false) => {
+    const scenes = Array.from({length:3}, (_, i) => ({
+      start:i*5, duration:5, headline:['Intro','Product','End card'][i],
+      asset_id:'photo1', animation_preset:'fade', transition:'cut',
+    }))
+    const draft = {
+      version:'rg_video_v2', mode:'media', shop_id:currentShop,
+      duration_seconds:15, template:'cinematic',
+      output:{width:540,height:960,fps:24},scenes,
+      cta:'Test only',music_asset_id:null,voiceover_asset_id:null,
+    }
+    const media = [{id:'photo1',kind:'image',authorized:true,shop_id:currentShop}]
+    root.render(React.createElement(React.Fragment,null,
+      React.createElement('output',{'data-testid':'f4-resize-active-shop'},currentShop),
+      React.createElement(TimelineStudioSurface,{
+        draft,mediaAssets:media,musicAssets:[],approvedDirection:approved,
+        selectedSceneIndex:0,onSelectScene:()=>{},
+        onChange:next=>window.__feature4ResizeWrites.push(next),
+      })))
+  }
+  window.__feature4ResizeChangeContext = render
+  render(shop)
+}
~~~~

### frontend/e2e/timeline-studio.spec.mjs
~~~~diff
@@ -301,3 +301,67 @@ test('real React beat lane never renders unapproved or foreign-shop audio marker
  await expect(page.getByLabel('Proposed music beat positions; server verification required')).toHaveCount(0)
  await expect(page.getByRole('textbox',{name:'Playhead timecode'})).toHaveValue('00:00:00:00')
 })
+
+
+test('stale caption resize aborts across synthetic shop switch or approval lock',async ({page})=>{
+ await page.setViewportSize({width:1280,height:850})
+ await page.goto('/')
+ await page.evaluate(async shop=>{
+   const fixture=await import('/e2e/fixtures/timeline-studio-harness.jsx')
+   fixture.mountFeature4ResizeRace({shop})
+ },SHOP)
+ await expect(page.getByTestId('f4-resize-active-shop')).toHaveText(SHOP)
+ const endHandle=page.locator('.caption-segment').first()
+   .locator('.caption-resize-handle.is-end')
+ const fireDown=async pointerId=>endHandle.dispatchEvent('pointerdown',{
+   pointerId,button:0,isPrimary:true,clientX:100,clientY:100
+ })
+ const fireUp=async pointerId=>page.evaluate(id=>{
+   window.dispatchEvent(new PointerEvent('pointerup',{
+     pointerId:id,button:0,isPrimary:true,clientX:150,clientY:100,bubbles:true
+   }))
+ },pointerId)
+ const OTHER='44444444-4444-4444-8444-444444444444'
+ await fireDown(21)
+ await page.evaluate(other=>window.__feature4ResizeChangeContext(other),OTHER)
+ await expect(page.getByTestId('f4-resize-active-shop')).toHaveText(OTHER)
+ await fireUp(21)
+ expect(await page.evaluate(()=>window.__feature4ResizeWrites.length)).toBe(0)
+ // Same tenant, but freshly approved direction becomes immutable mid-drag.
+ await fireDown(22)
+ await page.evaluate(other=>window.__feature4ResizeChangeContext(other,true),OTHER)
+ await expect(page.getByRole('button',{name:'Split video at playhead'})).toBeDisabled()
+ await fireUp(22)
+ expect(await page.evaluate(()=>window.__feature4ResizeWrites.length)).toBe(0)
+ // Explicit pointer cancel must also prevent a late synthetic pointer-up.
+ await page.evaluate(other=>window.__feature4ResizeChangeContext(other,false),OTHER)
+ await expect(page.getByTestId('f4-resize-active-shop')).toHaveText(OTHER)
+ await fireDown(23)
+ await page.evaluate(()=>{
+   window.dispatchEvent(new PointerEvent('pointercancel',{
+     pointerId:23,isPrimary:true,bubbles:true
+   }))
+ })
+ await fireUp(23)
+ expect(await page.evaluate(()=>window.__feature4ResizeWrites.length)).toBe(0)
+})
+
+test('cancelled native clip drag cannot reorder on a later unrelated drop',async ({page})=>{
+ await mount(page)
+ const clips=page.locator('[data-timeline-segment-track="image"]')
+ const original=await clips.evaluateAll(nodes=>nodes.map(node=>node.getAttribute('aria-label')))
+ await clips.nth(0).evaluate(el=>{
+   const transfer=new DataTransfer()
+   el.dispatchEvent(new DragEvent('dragstart',{bubbles:true,cancelable:true,dataTransfer:transfer}))
+   el.dispatchEvent(new DragEvent('dragend',{bubbles:true,cancelable:true,dataTransfer:transfer}))
+ })
+ await clips.nth(2).evaluate(el=>{
+   el.dispatchEvent(new DragEvent('drop',{bubbles:true,cancelable:true,dataTransfer:new DataTransfer()}))
+ })
+ await expect.poll(()=>clips.evaluateAll(nodes=>nodes.map(node=>node.getAttribute('aria-label'))))
+   .toEqual(original)
+ await page.getByRole('button',{name:'Submit authorized render'}).click()
+ await expect.poll(()=>page.evaluate(()=>window.__feature4Renders.length)).toBe(1)
+ const submitted=await page.evaluate(()=>window.__feature4Renders[0].scenes.map(scene=>scene.headline))
+ expect(submitted).toEqual(original.map(label=>label.replace(/^Scene \d+: /,'')))
+})
~~~~

### frontend/src/features/video/TimelineStudioSurface.jsx
~~~~diff
@@ -7,6 +7,7 @@ import { studioReorder, studioSplit, studioDuplicate, studioTrimPair, studioSour
 import { FrameTimecodeInput } from './vendor/openreel/FrameTimecodeInput.jsx'
 import { OpenReelClipSnapper } from './vendor/openreel/clip-snap.mjs'
 import { proposedBeatMarkers } from './beat-preview.mjs'
+import { boundedFrameSeek, boundedSceneMidpointSeek } from './frame-seek.mjs'
 import { getTimelineItemRanges, getTimelineTrackSelection, getSplittableTimelineItemIds } from './vendor/openreel/timeline-item-actions.mjs'
 import './TimelineStudioSurface.css'
 
@@ -23,6 +24,14 @@ export default function TimelineStudioSurface({ draft, onChange, onSelectScene,
   const dragFrom = useRef(null)
   const lastSent = useRef(null)
   const handlers = useRef({})
+  const pendingResize = useRef(null)
+  const liveDraft = useRef(draft)
+  const liveApproval = useRef(approvedDirection)
+  liveDraft.current = draft
+  liveApproval.current = approvedDirection
+  // An in-flight pointer resize must never apply an obsolete tenant/draft
+  // after account switch, approval lock, external draft update or unmount.
+  useEffect(() => () => pendingResize.current?.cancel(), [draft, approvedDirection])
   useEffect(() => {
     if (draft !== lastSent.current) {
       setHistory(createEditorHistory(draft))
@@ -61,6 +70,8 @@ export default function TimelineStudioSurface({ draft, onChange, onSelectScene,
     spans[selected] && playhead - spans[selected].start >= .5 &&
     spans[selected].end - playhead >= .5
   const seekToFrame = (seconds, withSnap = false) => {
+    // Reject nonfinite inputs before beat/grid snap calculations.
+    if (!Number.isFinite(seconds)) return
     let requested = seconds
     if (withSnap && snapEnabled) {
       const nearest = beatMarkers.length ? beatMarkers.reduce((a,b) =>
@@ -74,8 +85,8 @@ export default function TimelineStudioSurface({ draft, onChange, onSelectScene,
         if (snap.didSnap) requested = snap.snappedTime
       }
     }
-    const position = Math.min(draft.duration_seconds,
-      Math.max(0, Math.round(requested * previewFps) / previewFps))
+    const position = boundedFrameSeek(requested, draft.duration_seconds, previewFps)
+    if (position === null) return
     setPlayhead(position)
     const index = spans.findIndex(span => position >= span.start && position < span.end)
     if (index >= 0) onSelectScene(index)
@@ -111,23 +122,40 @@ export default function TimelineStudioSurface({ draft, onChange, onSelectScene,
   handlers.current = {
     startTimelineClipDrag: (_event,track,_id,index) => { if(track==='caption')onSelectScene(index) },
     showTrackContextMenu: event => event.preventDefault(),
-    selectCaptionClip: (_event,_id,index,start) => { onSelectScene(index); setPlayhead(start) },
+    selectCaptionClip: (_event,_id,index,start) => {
+      const position = boundedFrameSeek(start, draft.duration_seconds, previewFps)
+      if (position !== null) { onSelectScene(index); setPlayhead(position) }
+    },
     startCaptionResize: (event,_id,index,edge) => {
       const boundary = edge === 'start' ? index - 1 : index
-      if (approvedDirection || boundary < 0 || boundary >= draft.scenes.length - 1) return
+      if (approvedDirection || boundary < 0 || boundary >= draft.scenes.length - 1 ||
+          event.button !== 0 || event.isPrimary === false) return
       event.stopPropagation()
+      // No duplicate listeners or stale closure may outlive an edit gesture.
+      pendingResize.current?.cancel()
       const target = event.currentTarget.closest('.f4-studio-track-body')
       const width = target?.getBoundingClientRect().width || 1
       const startX = event.clientX
+      const pointerId = event.pointerId
       const original = draft
-      const release = e => {
+      const cancel = () => {
         window.removeEventListener('pointerup', release)
-        const delta = (e.clientX - startX) * draft.duration_seconds / width
+        window.removeEventListener('pointercancel', abort)
+        if (pendingResize.current?.cancel === cancel) pendingResize.current = null
+      }
+      const abort = e => { if (e.pointerId === pointerId) cancel() }
+      const release = e => {
+        if (e.pointerId !== pointerId) return
+        cancel()
+        if (liveDraft.current !== original || liveApproval.current) return
+        const delta = (e.clientX - startX) * original.duration_seconds / width
         if (Math.abs(delta) > 0.03) {
           change(() => studioTrimPair(original, boundary, Math.round(delta * 10) / 10, mediaAssets))
         }
       }
-      window.addEventListener('pointerup', release, { once: true })
+      pendingResize.current = {cancel}
+      window.addEventListener('pointerup', release)
+      window.addEventListener('pointercancel', abort)
     },
     startAudioSegmentMove: () => {},
     selectAudioClip: () => {},
@@ -226,10 +254,27 @@ export default function TimelineStudioSurface({ draft, onChange, onSelectScene,
             className={'f4-ts-clip '+(selected===i?'is-selected':'')}
             style={{left:span.start/draft.duration_seconds*100+'%',
               width:span.duration/draft.duration_seconds*100+'%'}}
-            onDragStart={()=>{dragFrom.current=i}}
-            onDragOver={e=>e.preventDefault()}
-            onDrop={e=>{e.preventDefault();if(dragFrom.current!==null){move(dragFrom.current,i);onSelectScene(i)}dragFrom.current=null}}
-            onClick={()=>{onSelectScene(i);setPlayhead(span.start+span.duration/2)}}
+            onDragStart={e=>{
+              if (approvedDirection) { e.preventDefault(); return }
+              dragFrom.current=i
+            }}
+            onDragEnd={()=>{dragFrom.current=null}}
+            onDragOver={e=>{if (dragFrom.current!==null && !approvedDirection)e.preventDefault()}}
+            onDrop={e=>{
+              if (dragFrom.current===null || approvedDirection) return
+              e.preventDefault()
+              const from=dragFrom.current
+              dragFrom.current=null
+              if (from!==i && from>=0 && from<draft.scenes.length) {
+                move(from,i)
+                onSelectScene(i)
+              }
+            }}
+            onClick={()=>{
+              const position = boundedSceneMidpointSeek(span.start, span.duration,
+                draft.duration_seconds, previewFps)
+              if (position !== null) { onSelectScene(i); setPlayhead(position) }
+            }}
             aria-label={'Scene '+(i+1)+': '+(draft.scenes[i].headline)}>
             <span className="f4-ts-clip-index">{i+1}</span>
             <span className="f4-ts-clip-title">{draft.scenes[i].headline}</span>
~~~~

### frontend/src/features/video/frame-seek.mjs
~~~~diff
@@ -0,0 +1,20 @@
+// Feature4 timeline-only seek normalization. No draft/media authorization changes.
+// Do not allow malformed UI, beat markers or pointer geometry to poison the
+// React playhead with NaN/Infinity or an out-of-range position.
+export function boundedFrameSeek(requestedSeconds, durationSeconds, fps) {
+  if (!Number.isFinite(requestedSeconds) || !Number.isFinite(durationSeconds) ||
+      durationSeconds <= 0 || (fps !== 24 && fps !== 30)) return null
+  const bounded = Math.min(durationSeconds, Math.max(0, requestedSeconds))
+  return Math.min(durationSeconds, Math.max(0, Math.round(bounded * fps) / fps))
+}
+
+// Scene click navigation must share the same frame boundary as timecode/keyboard.
+// Invalid or out-of-bounds spans are not usable preview positions.
+export function boundedSceneMidpointSeek(startSeconds, sceneDurationSeconds, durationSeconds, fps) {
+  if (!Number.isFinite(startSeconds) || !Number.isFinite(sceneDurationSeconds) ||
+      !Number.isFinite(durationSeconds) || startSeconds < 0 ||
+      sceneDurationSeconds <= 0 || durationSeconds <= 0 ||
+      startSeconds >= durationSeconds ||
+      sceneDurationSeconds > durationSeconds - startSeconds + 1e-6) return null
+  return boundedFrameSeek(startSeconds + sceneDurationSeconds / 2, durationSeconds, fps)
+}
~~~~

### tests/frontend/feature4-frame-seek.test.mjs
~~~~diff
@@ -0,0 +1,35 @@
+import test from 'node:test'
+import assert from 'node:assert/strict'
+import { boundedFrameSeek, boundedSceneMidpointSeek } from '../../frontend/src/features/video/frame-seek.mjs'
+
+test('F4-08 seek clamps to approved duration and whole frames', () => {
+  assert.equal(boundedFrameSeek(-10, 30, 24), 0)
+  assert.equal(boundedFrameSeek(99, 30, 24), 30)
+  assert.equal(boundedFrameSeek(1 / 24, 30, 24), 1 / 24)
+  assert.equal(boundedFrameSeek(0.08, 30, 30), 2 / 30)
+  assert.equal(boundedFrameSeek(10.05, 10.05, 24), 10.041666666666666)
+})
+test('F4-08 rejects nonfinite and malformed seeks instead of poisoning playhead', () => {
+  for (const value of [NaN, Infinity, -Infinity, undefined, null, '12', {}]) {
+    assert.equal(boundedFrameSeek(value, 30, 24), null)
+  }
+  for (const duration of [0, -1, NaN, Infinity, '30']) {
+    assert.equal(boundedFrameSeek(1, duration, 24), null)
+  }
+  assert.equal(boundedFrameSeek(1, 30, 0), null)
+  assert.equal(boundedFrameSeek(1, 30, 60), null)
+})
+
+test('F4-08 scene and caption clicks resolve to finite bounded frames', () => {
+  assert.equal(boundedSceneMidpointSeek(0, 5, 30, 24), 2.5)
+  assert.equal(boundedSceneMidpointSeek(4, 3, 30, 30), 5.5)
+  assert.equal(boundedSceneMidpointSeek(29, 1, 30, 24), 29.5)
+  assert.equal(boundedFrameSeek(1.08, 30, 24), 26 / 24)
+})
+test('F4-08 rejects malformed or crossing scene spans', () => {
+  for (const [start, length, duration] of [
+    [NaN, 3, 30], [0, Infinity, 30], [-1, 2, 30],
+    [0, 0, 30], [30, 1, 30], [29, 2, 30],
+    [0, 3, Infinity], [0, 3, 0], ['1', 2, 30],
+  ]) assert.equal(boundedSceneMidpointSeek(start, length, duration, 24), null)
+})
~~~~

### tests/media/test_feature4_audio_master.py
~~~~diff
@@ -1,4 +1,6 @@
 """Actual H264 stream-copy + loudness mastering tests (synthetic audio only)."""
+import hashlib
+import stat
 import subprocess
 import sys
 import tempfile
@@ -81,5 +83,146 @@ def test_wrong_duration_invalid_and_symlink_inputs_fail(self):
             master_private_audio(self.source,self.output,expected_seconds=15)
         self.assertFalse(self.output.exists())
 
+
+    def test_existing_proof_is_rejected_before_any_mastering(self):
+        proof=self.root/"already.json"
+        proof.write_text("existing approved receipt",encoding="utf-8")
+        argv=["feature4_audio_master.py","--source",str(self.source),
+              "--output",str(self.output),"--duration","15",
+              "--report",str(proof)]
+        with patch.object(sys,"argv",argv), patch.object(
+                audio_master,"master_private_audio",
+                side_effect=AssertionError("must not encode before proof preflight")):
+            with self.assertRaises(SystemExit) as caught:
+                audio_master.main()
+        self.assertEqual(caught.exception.code,2)
+        self.assertEqual(proof.read_text(encoding="utf-8"),"existing approved receipt")
+        self.assertFalse(self.output.exists())
+
+    def test_report_write_failure_invalidates_only_matching_private_master(self):
+        proof=self.root/"proof.json"
+        original_open=audio_master._open_private_report
+        original=b"offline-synthetic-master"
+        for replace_output in (False, True):
+            with self.subTest(replace_output=replace_output):
+                self.output.unlink(missing_ok=True)
+                def fake_master(*_args, **_kwargs):
+                    self.output.write_bytes(original)
+                    if replace_output:
+                        self.output.write_bytes(b"other-process-output")
+                    return {"master_sha256":hashlib.sha256(original).hexdigest(),
+                            "status":"PRIVATE_AUDIO_MASTERED_NOT_PUBLISHED"}
+                def fail_proof_open(path,*args,**kwargs):
+                    if path==proof:
+                        raise OSError("simulated proof disk failure")
+                    return original_open(path)
+                argv=["feature4_audio_master.py","--source",str(self.source),
+                      "--output",str(self.output),"--duration","15",
+                      "--report",str(proof)]
+                with patch.object(sys,"argv",argv), patch.object(
+                        audio_master,"master_private_audio",side_effect=fake_master), patch.object(
+                        audio_master,"_open_private_report",new=fail_proof_open):
+                    with self.assertRaises(SystemExit) as caught:
+                        audio_master.main()
+                self.assertEqual(caught.exception.code,2)
+                self.assertEqual(self.output.exists(),replace_output)
+                if replace_output:
+                    self.assertEqual(self.output.read_bytes(),b"other-process-output")
+                self.assertFalse(proof.exists())
+
+    def test_partial_proof_write_failure_removes_owned_receipt_and_output(self):
+        proof=self.root/"partial.json"
+        original_open=audio_master._open_private_report
+        payload=b"synthetic-private-master"
+        class FailingProof:
+            def __init__(self,stream):
+                self.stream=stream
+            def __enter__(self):
+                return self
+            def __exit__(self,*_args):
+                self.stream.close()
+            def fileno(self):
+                return self.stream.fileno()
+            def write(self,_value):
+                self.stream.write("{")
+                self.stream.flush()
+                raise OSError("simulated partial proof write")
+        def fake_open(path,*args,**kwargs):
+            stream=original_open(path,*args,**kwargs)
+            if path==proof:
+                return FailingProof(stream)
+            return stream
+        def fake_master(*_args,**_kwargs):
+            self.output.write_bytes(payload)
+            return {"master_sha256":hashlib.sha256(payload).hexdigest(),
+                    "status":"PRIVATE_AUDIO_MASTERED_NOT_PUBLISHED"}
+        argv=["feature4_audio_master.py","--source",str(self.source),
+              "--output",str(self.output),"--duration","15",
+              "--report",str(proof)]
+        with patch.object(sys,"argv",argv), patch.object(
+                audio_master,"master_private_audio",side_effect=fake_master), patch.object(
+                audio_master,"_open_private_report",new=fake_open):
+            with self.assertRaises(SystemExit) as caught:
+                audio_master.main()
+        self.assertEqual(caught.exception.code,2)
+        self.assertFalse(proof.exists())
+        self.assertFalse(self.output.exists())
+
+    def test_proof_fsync_failure_invalidates_receipt_and_output(self):
+        proof=self.root/"fsync-fail.json"
+        payload=b"synthetic-private-master"
+        def fake_master(*_args,**_kwargs):
+            self.output.write_bytes(payload)
+            return {"master_sha256":hashlib.sha256(payload).hexdigest(),
+                    "status":"PRIVATE_AUDIO_MASTERED_NOT_PUBLISHED"}
+        argv=["feature4_audio_master.py","--source",str(self.source),
+              "--output",str(self.output),"--duration","15",
+              "--report",str(proof)]
+        with patch.object(sys,"argv",argv), patch.object(
+                audio_master,"master_private_audio",side_effect=fake_master), patch.object(
+                audio_master.os,"fsync",side_effect=OSError("simulated durability failure")):
+            with self.assertRaises(SystemExit) as caught:
+                audio_master.main()
+        self.assertEqual(caught.exception.code,2)
+        self.assertFalse(proof.exists())
+        self.assertFalse(self.output.exists())
+
+    def test_proof_receipt_owner_only_even_under_permissive_umask(self):
+        proof=self.root/"owner-only.json"
+        payload=b"synthetic-private-master"
+        def fake_master(*_args,**_kwargs):
+            self.output.write_bytes(payload)
+            return {"master_sha256":hashlib.sha256(payload).hexdigest(),
+                    "status":"PRIVATE_AUDIO_MASTERED_NOT_PUBLISHED",
+                    "source_audio_mean_db":-28.0,
+                    "mastered_audio_mean_db":-16.0}
+        argv=["feature4_audio_master.py","--source",str(self.source),
+              "--output",str(self.output),"--duration","15",
+              "--report",str(proof)]
+        import os
+        old_umask=os.umask(0)
+        try:
+            with patch.object(sys,"argv",argv), patch.object(
+                    audio_master,"master_private_audio",side_effect=fake_master):
+                audio_master.main()
+        finally:
+            os.umask(old_umask)
+        self.assertEqual(stat.S_IMODE(proof.stat().st_mode),0o600)
+        self.assertEqual(proof.read_text(encoding="utf-8").count(
+                         "PRIVATE_AUDIO_MASTERED_NOT_PUBLISHED"),1)
+
+    def test_proof_preflight_rejects_symlink_parent_and_non_json(self):
+        private=self.root/"private"
+        private.mkdir()
+        linked=self.root/"linked"
+        linked.symlink_to(private,target_is_directory=True)
+        nested=linked/"nested"
+        (private/"nested").mkdir()
+        for path in (linked/"proof.json",nested/"proof.json",private/"proof.txt",private/"missing"/"proof.json"):
+            with self.assertRaisesRegex(AudioMasterError,"private JSON"):
+                audio_master._private_report_path(path)
+        self.assertEqual(audio_master._private_report_path(private/"new.json"),
+                         private/"new.json")
+
 if __name__=="__main__":
     unittest.main()
~~~~

### tests/media/test_feature4_cpu_matrix.py
~~~~diff
@@ -0,0 +1,135 @@
+"""F4-14 proof-only matrix checks; every media probe is mocked (not a real encode)."""
+from __future__ import annotations
+
+import hashlib
+import json
+from pathlib import Path
+import sys
+import tempfile
+import unittest
+from unittest.mock import patch
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT / "video-engine"))
+from feature4_cpu_matrix import aggregate_cpu_matrix, CpuMatrixError
+
+
+HEAD = "b" * 40
+
+
+class CpuMatrixTests(unittest.TestCase):
+    def setUp(self):
+        ctx = tempfile.TemporaryDirectory(prefix="f4-cpu-envelope-")
+        self.addCleanup(ctx.cleanup)
+        self.root = Path(ctx.name)
+        self.manifest = {
+            "schema": "feature4_cpu_matrix_inputs_v1",
+            "source_commit": HEAD, "renders": []
+        }
+        for duration in (15, 30, 60):
+            media = bytes([duration]) * 5000
+            sha = hashlib.sha256(media).hexdigest()
+            (self.root / f"clip-{duration}.mp4").write_bytes(media)
+            row = {"seconds": duration, "path": f"clip-{duration}.mp4",
+                   "sha256": sha, "benchmark": f"clip-{duration}.json"}
+            self.manifest["renders"].append(row)
+            data = {
+                "kind": "OFFLINE_SYNTHETIC_HYPERFRAMES_CPU_BENCHMARK_NOT_AZURE",
+                "source_commit_claim": HEAD,
+                "output_sha256": sha,
+                "output_bytes": len(media),
+                "output_hash_type": "SHA256_STABLE_LOCAL_REGULAR_FILE_ONLY",
+                "duration_seconds": duration, "width": 1080, "height": 1920,
+                "fps": 24, "cloud_or_gpu_inference": False,
+                "measured_on_azure_functions": False,
+                "commercial_visual_quality_accepted": False,
+                "azure_runtime_memory_verified": False, "azure_cost_inr": None,
+                "wall_seconds": duration * 2.0,
+                "max_sampled_process_tree_rss_bytes": duration * 1000000,
+                "max_sampled_cpu_seconds_lower_bound": duration * .8,
+                "sampling_interval_seconds": .2,
+                "samples": 40, "max_observed_process_count": 2,
+            }
+            (self.root / row["benchmark"]).write_text(json.dumps(data), encoding="utf-8")
+
+    def _check(self):
+        def probe(path, *, duration, width, height, fps):
+            self.assertEqual((width, height, fps), (1080, 1920, 24))
+            self.assertEqual(path.name, f"clip-{duration}.mp4")
+            return {"bytes": path.stat().st_size, "duration_seconds": duration}
+        with patch("feature4_export_matrix.verify_mp4", side_effect=probe):
+            return aggregate_cpu_matrix(self.manifest, self.root, expected_head=HEAD)
+
+    def _edit_receipt(self, seconds, key, value):
+        p = self.root / f"clip-{seconds}.json"
+        record = json.loads(p.read_text())
+        record[key] = value
+        p.write_text(json.dumps(record))
+
+    def test_three_lengths_sha_tied_without_false_cloud_acceptance(self):
+        result = self._check()
+        self.assertEqual([r["seconds"] for r in result["renders"]], [15, 30, 60])
+        self.assertEqual(result["max_measured_wall_seconds"], 120)
+        self.assertEqual(result["max_sampled_rss_bytes_lower_bound"], 60000000)
+        self.assertFalse(result["cloud_budget_accepted"])
+        self.assertFalse(result["code_commit_attested_by_ci"])
+        self.assertFalse(result["commercial_release_eligible"])
+
+    def test_missing_duplicate_head_and_path_escape_fail_closed(self):
+        self.manifest["source_commit"] = "a" * 40
+        with self.assertRaises(CpuMatrixError):
+            self._check()
+        self.manifest["source_commit"] = HEAD
+        self.manifest["renders"][2]["seconds"] = 30
+        with self.assertRaises(CpuMatrixError):
+            self._check()
+        self.manifest["renders"][2]["seconds"] = 60
+        self.manifest["renders"][0]["benchmark"] = "../another-tenant.json"
+        with self.assertRaises(CpuMatrixError):
+            self._check()
+
+    def test_encoded_source_mutation_cannot_pass_even_with_receipt(self):
+        target = self.root / "clip-15.mp4"
+        target.write_bytes(target.read_bytes() + b"unapproved")
+        with self.assertRaisesRegex(CpuMatrixError, "encoded MP4"):
+            self._check()
+
+    def test_forged_sha_budget_or_bool_as_int_rejected(self):
+        for key, value in (
+            ("source_commit_claim", "0" * 40),
+            ("output_sha256", "f" * 64),
+            ("output_bytes", 4),
+            ("cloud_or_gpu_inference", True),
+            ("measured_on_azure_functions", True),
+            ("commercial_visual_quality_accepted", True),
+            ("azure_runtime_memory_verified", True),
+            ("azure_cost_inr", 100),
+            ("wall_seconds", float("nan")),
+            ("max_sampled_process_tree_rss_bytes", -3),
+            ("max_sampled_cpu_seconds_lower_bound", 0),
+            ("samples", True),
+            ("max_observed_process_count", 0),
+            ("output_hash_type", "not-original"),
+        ):
+            with self.subTest(key=key):
+                path = self.root / "clip-30.json"
+                original = path.read_text()
+                self._edit_receipt(30, key, value)
+                with self.assertRaises(CpuMatrixError):
+                    self._check()
+                path.write_text(original)
+
+    def test_missing_symlinked_or_oversized_json_not_read(self):
+        receipt = self.root / "clip-30.json"
+        receipt.unlink()
+        receipt.symlink_to(self.root / "clip-15.json")
+        with self.assertRaises(CpuMatrixError):
+            self._check()
+        receipt.unlink()
+        receipt.write_bytes(b"x" * 65536)
+        with self.assertRaises(CpuMatrixError):
+            self._check()
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

### tests/media/test_feature4_cross_feature.py
~~~~diff
@@ -11,6 +11,7 @@
 sys.path.insert(0, str(ROOT / "video-engine"))
 from creative_contract import (CreativeContractError, PremiumMotionUnavailable,
                                compile_creative_reel, render_inputs)  # noqa: E402
+from professional import VideoPlanError
 
 SHOP = "11111111-1111-4111-8111-111111111111"
 CAMPAIGN = "22222222-2222-4222-8222-222222222222"
@@ -273,6 +274,22 @@ def test_bad_scene_order_and_unsafe_template_rejected(self):
         with self.assertRaisesRegex(CreativeContractError, "forbidden"):
             render_inputs(self.request, self.manifest)
 
+    def test_reviewed_cross_feature_source_gain_reaches_renderer(self):
+        self.make_assets(with_video=True)
+        self.request["audio_mix"] = {"source": .65}
+        lowered = render_inputs(self.request, self.manifest)
+        self.assertEqual(lowered.plan["audio_mix"], {"source": .65})
+        output = compile_creative_reel(
+            self.request, self.manifest, self.assets, self.root / "mixed-gain")
+        page = (output / "index.html").read_text()
+        self.assertIn('data-track-index="0" data-volume="0.65"', page)
+        for bad in ({"music": .5}, {"source": float("nan")},
+                    {"source": True}, {"source": 1.01}, {"voiceover": .5}):
+            with self.subTest(bad=bad):
+                self.request["audio_mix"] = bad
+                with self.assertRaises(VideoPlanError):
+                    render_inputs(self.request, self.manifest)
+
     def test_retry_is_same_logical_job_no_usage_mutation(self):
         self.make_assets(with_video=True)
         first = render_inputs(self.request, self.manifest)
~~~~

### tests/media/test_feature4_duplicate_project.py
~~~~diff
@@ -0,0 +1,34 @@
+"""F4-04: actual upstream JS duplicate -> Python compiler -> mock HyperFrames HTML.
+
+An encoded source asset may be created locally; no real customer media is approved. The opt-in 30s encoded
+video regression is a separate acceptance gate, never a production sample.
+"""
+import sys
+import tempfile
+import unittest
+from pathlib import Path
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT / "video-engine"))
+from demo_feature4_edited_reel import make_edited_project
+
+
+class DuplicateEditorProjectTests(unittest.TestCase):
+    def test_duplicate_editor_compiles_real_private_mock_project(self):
+        with tempfile.TemporaryDirectory(prefix="f4-duplicate-fixture-") as tmp:
+            result = make_edited_project(Path(tmp) / "duplicate", operation="duplicate")
+            page = (Path(result["project"]) / "index.html").read_text(encoding="utf-8")
+            self.assertEqual(result["editor_operation"], "duplicate")
+            self.assertEqual(result["source_video_inpoints_seconds"], [0, 0])
+            self.assertEqual(result["video_clip_count"], 2)
+            self.assertEqual(result["approved_sfx_count"], 1)
+            self.assertEqual(page.count('class="footage clip"'), 2)
+            self.assertGreaterEqual(page.count('data-media-start="0"'), 2)
+            self.assertNotIn("90% OFF", page)
+            self.assertEqual(result["visual_quality_status"], "OWNER_REJECTED")
+            self.assertFalse(result["commercial_release_eligible"])
+            self.assertFalse(result["real_ai_motion"])
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

### tests/media/test_feature4_edited_export_qa.py
~~~~diff
@@ -22,18 +22,30 @@ def setUp(self):
         self.profile = {"width": 540, "height": 960, "seconds": 30.0}
         self.valid = (bytes([20])*9216, bytes([70])*9216,
                       bytes([24])*9216, bytes([120])*9216)
+        self.split_probes = (bytes([21])*9216, bytes([25])*9216,
+                             bytes([70])*9216, bytes([70])*9216,
+                             bytes([24])*9216, bytes([120])*9216)
 
-    def prove(self, frames=None):
+    def prove(self, frames=None, *, operation="split_reorder", motion=None, boundary=None):
+        decoded = list(frames if frames is not None else self.valid)
+        if operation == "split_reorder":
+            decoded += list(motion if motion is not None else self.split_probes[:2])
+            decoded += list(boundary if boundary is not None else self.split_probes[2:])
         with patch.object(qa, "inspect_mp4", return_value=self.profile), \
-             patch.object(qa, "_frame", side_effect=list(frames or self.valid)):
-            return verify_mock_editor_output(self.file)
+             patch.object(qa, "_frame", side_effect=decoded):
+            return verify_mock_editor_output(self.file, operation=operation)
 
     def test_valid_decoded_pattern_is_source_sha_bound_not_product_approval(self):
         proof = self.prove()
         self.assertEqual(proof["timeline_starts_seconds"], [0, 4, 14, 20])
         self.assertEqual(proof["source_sha256"],
                          hashlib.sha256(self.file.read_bytes()).hexdigest())
         self.assertFalse(proof["exact_inpoint_frame_verified"])
+        self.assertEqual(proof["first_video_encoded_motion_delta"], 1.0)
+        self.assertEqual(proof["trimmed_video_encoded_motion_delta"], 1.0)
+        self.assertEqual(proof["boundary_probe_times_seconds"], [5, 13, 15, 21])
+        self.assertTrue(proof["boundary_scene_family_verified"])
+        self.assertFalse(proof["exact_transition_frame_verified"])
         self.assertFalse(proof["human_visual_approval"])
         self.assertFalse(proof["commercial_release_eligible"])
 
@@ -45,8 +57,67 @@ def test_replayed_video_or_wrong_scene_order_denied(self):
                  self.assertRaises(EditorExportProofError):
                 self.prove(frames)
 
+    def test_duplicate_encoded_replay_is_distinct_from_split_reorder(self):
+        # Verified upstream JS duplicate produces photo/video/video/offer.
+        # Two real decoded video frames at matching source offsets must repeat.
+        f = lambda luma: bytes([luma]) * 9216
+        duplicate = (f(20), f(70), f(72), f(120))
+        proof = self.prove(duplicate, operation="duplicate")
+        self.assertEqual(proof["schema"], "feature4_duplicated_30s_pixel_parity_v1")
+        self.assertEqual(proof["editor_operation"], "duplicate")
+        self.assertEqual(proof["timeline_starts_seconds"], [0, 10, 15, 20])
+        self.assertEqual(proof["pixel_times_seconds"], [2, 11.5, 16.5, 25])
+        self.assertLess(proof["repeated_source_video_delta"], 8)
+        self.assertFalse(proof["exact_inpoint_frame_verified"])
+        self.assertFalse(proof["commercial_release_eligible"])
+        for rejected in ((f(20), f(70), f(91), f(120)),
+                         (f(20), f(70), f(72), f(21)),
+                         (f(70), f(20), f(72), f(120))):
+            with self.subTest(rejected=rejected[0][0]):
+                with self.assertRaises(EditorExportProofError):
+                    self.prove(rejected, operation="duplicate")
+
+    def test_unknown_edit_operation_denied_before_media_probe(self):
+        with patch.object(qa, "inspect_mp4") as probe:
+            with self.assertRaisesRegex(EditorExportProofError, "Unknown"):
+                verify_mock_editor_output(self.file, operation="unreviewed")
+            probe.assert_not_called()
+
+    def test_malformed_decoded_frames_cannot_pass_pixel_parity(self):
+        # Original F4-04 #723 negative cases, retained alongside duplicate QA.
+        v1, p1, v2, p2 = self.valid
+        for name, frames in (
+            ("truncated-first-video", (v1[:-1], p1, v2, p2)),
+            ("oversized-product-frame", (v1, p1 + b"\x00", v2, p2)),
+            ("wrong-decoder-type", (v1, p1, bytearray(v2), p2)),
+            ("empty-frame", (v1, p1, b"", p2)),
+        ):
+            with self.subTest(case=name), self.assertRaisesRegex(
+                    EditorExportProofError, "Malformed encoded editor grayscale frame"):
+                self.prove(frames)
+
+    def test_frozen_source_video_segments_are_denied(self):
+        first, photo, trimmed, offer = self.valid
+        moving_first, moving_trimmed = self.split_probes[:2]
+        for motion in ((first, moving_trimmed), (moving_first, trimmed), (first, trimmed)):
+            with self.subTest(motion=motion[0][0]), self.assertRaisesRegex(
+                    EditorExportProofError, "order/inpoint"):
+                self.prove(motion=motion)
+
+    def test_delayed_or_replaced_cut_boundary_frames_denied(self):
+        video, product, trimmed, offer = self.valid
+        for name, probes in (
+            ("first photo starts late", (video, product, trimmed, offer)),
+            ("first photo ends early", (product, offer, trimmed, offer)),
+            ("second video starts late", (product, product, product, offer)),
+            ("offer starts late", (product, product, trimmed, product)),
+        ):
+            with self.subTest(name=name), self.assertRaisesRegex(
+                    EditorExportProofError, "order/inpoint"):
+                self.prove(boundary=probes)
+
     def test_mutated_input_and_wrong_duration_denied(self):
-        frames = list(self.valid)
+        frames = list(self.valid) + list(self.split_probes)
         def decode(src, at):
             if at == 2.0:
                 with self.file.open("ab") as handle:
~~~~

### tests/media/test_feature4_encoded_motion_qa.py
~~~~diff
@@ -1,13 +1,16 @@
 """Actually encoded MP4 motion verification cannot be bypassed by frozen video."""
+import os
 import subprocess
 import sys
 import tempfile
 import unittest
 from pathlib import Path
+from unittest.mock import patch
 
 ROOT=Path(__file__).resolve().parents[2]
 sys.path.insert(0,str(ROOT/"video-engine"))
 from feature4_encoded_motion_qa import verify_moving_scenes, MotionProofError
+import feature4_encoded_motion_qa as motion
 
 class EncodedMotionTests(unittest.TestCase):
     def setUp(self):
@@ -45,6 +48,47 @@ def test_still_video_and_wrong_duration_fail_closed(self):
         with self.assertRaises(MotionProofError):
             verify_moving_scenes(self.movie,seconds=15,scene_starts=[0])
 
+    def test_motion_original_bytes_and_inode_stable_during_sampling(self):
+        self.encode(moving=True)
+        authorized_bytes = self.movie.read_bytes()
+        actual = motion._frame
+        for variant in ("append", "same-content-atomic-swap"):
+            with self.subTest(variant=variant):
+                self.movie.write_bytes(authorized_bytes)
+                touched = [False]
+                def change_source_after_real_decode(path, at):
+                    result = actual(path, at)
+                    if not touched[0]:
+                        touched[0] = True
+                        if variant == "append":
+                            with self.movie.open("ab") as stream:
+                                stream.write(b"unauthorized-suffix")
+                        else:
+                            replacement = self.root / "different-inode.mp4"
+                            replacement.write_bytes(authorized_bytes)
+                            os.replace(replacement, self.movie)
+                    return result
+                with patch.object(motion, "_frame",
+                                  side_effect=change_source_after_real_decode):
+                    with self.assertRaisesRegex(MotionProofError, "source changed"):
+                        verify_moving_scenes(
+                            self.movie, seconds=15, scene_starts=[0,5,10])
+                self.assertTrue(touched[0])
+
+    def test_invalid_nan_motion_threshold_and_cross_scene_probes_rejected(self):
+        for kwargs in (
+            {"threshold": float("nan")},
+            {"threshold": float("inf")},
+            {"sample_offset": float("nan")},
+            {"separation": float("nan")},
+            {"sample_offset": True},
+            {"scene_starts": [0, 1, 10]},
+        ):
+            params = {"seconds": 15, "scene_starts": [0,5,10]}
+            params.update(kwargs)
+            with self.subTest(kwargs=kwargs), self.assertRaises(MotionProofError):
+                verify_moving_scenes(self.movie, **params)
+
     def test_forged_scene_offsets_rejected(self):
         for starts in ([-1], [20], [5,5], [float("nan")], [],list(range(11))):
             with self.assertRaises(MotionProofError):
~~~~

### tests/media/test_feature4_export_matrix.py
~~~~diff
@@ -0,0 +1,107 @@
+"""F4-03 local 15/30/60 immutable encoded matrix; source test doubles never claim real render."""
+from __future__ import annotations
+
+import hashlib
+import sys
+import tempfile
+import unittest
+from pathlib import Path
+from unittest.mock import patch
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT / "video-engine"))
+from feature4_export_matrix import MatrixEvidenceError, verify_export_matrix
+
+
+HEAD = "a" * 40
+
+
+class OfflineExportMatrixTests(unittest.TestCase):
+    def setUp(self):
+        temp = tempfile.TemporaryDirectory(prefix="f4-matrix-")
+        self.addCleanup(temp.cleanup)
+        self.root = Path(temp.name)
+        self.rows = []
+        for duration in (15, 30, 60):
+            name = f"synthetic-{duration}s.mp4"
+            data = bytes([duration]) * 4096
+            (self.root / name).write_bytes(data)
+            self.rows.append({"seconds": duration, "path": name,
+                              "sha256": hashlib.sha256(data).hexdigest()})
+        self.manifest = {"schema": "feature4_export_matrix_inputs_v1",
+                         "source_commit": HEAD, "renders": self.rows}
+
+    def proof(self):
+        def local_probe(path, *, duration, width, height, fps):
+            self.assertEqual((width, height, fps), (1080, 1920, 24))
+            self.assertTrue(path.name.endswith(f"{duration}s.mp4"))
+            return {"bytes": path.stat().st_size, "duration_seconds": duration,
+                    "width": width, "height": height, "fps": fps,
+                    "video_codec": "h264", "audio_codec": "aac"}
+        with patch("feature4_export_matrix.verify_mp4", side_effect=local_probe):
+            return verify_export_matrix(self.manifest, self.root, expected_head=HEAD)
+
+    def test_all_three_actual_filenames_sha_bound_without_release_approval(self):
+        result = self.proof()
+        self.assertEqual(result["status"],
+                         "ALL_THREE_LOCAL_ENCODED_PROFILES_TECHNICALLY_CHECKED")
+        self.assertEqual([x["seconds"] for x in result["renders"]], [15, 30, 60])
+        self.assertTrue(all(len(x["sha256"]) == 64 for x in result["renders"]))
+        self.assertFalse(result["commercial_release_eligible"])
+        self.assertFalse(result["code_commit_attested_by_ci"])
+        self.assertFalse(result["human_visual_approval"])
+
+    def test_incomplete_duplicate_forged_or_stale_head_denied(self):
+        for variant in ("missing", "duplicate", "stale", "tamper", "fake_sha"):
+            with self.subTest(variant=variant):
+                self.setUp_case(variant)
+                with self.assertRaises(MatrixEvidenceError):
+                    self.proof()
+
+    def setUp_case(self, variant):
+        import copy
+        # Restore records from local media, not a previously mutated list.
+        self.rows = [{"seconds": x, "path": f"synthetic-{x}s.mp4",
+                      "sha256": hashlib.sha256(bytes([x]) * 4096).hexdigest()}
+                     for x in (15, 30, 60)]
+        self.manifest = {"schema": "feature4_export_matrix_inputs_v1",
+                         "source_commit": HEAD, "renders": copy.deepcopy(self.rows)}
+        if variant == "missing":
+            self.manifest["renders"].pop()
+        elif variant == "duplicate":
+            self.manifest["renders"][2]["seconds"] = 30
+        elif variant == "stale":
+            self.manifest["source_commit"] = "b" * 40
+        elif variant == "tamper":
+            (self.root / "synthetic-30s.mp4").write_bytes(b"changed" * 700)
+        elif variant == "fake_sha":
+            self.manifest["renders"][1]["sha256"] = "f" * 64
+
+    def test_cross_shop_path_and_symlink_denied_before_probe(self):
+        for invalid in ("../foreign.mp4", "/tmp/foreign.mp4", "dir/other.mp4",
+                        "http://example.invalid/clip.mp4", "other\\foreign.mp4"):
+            with self.subTest(path=invalid):
+                self.manifest["renders"][0]["path"] = invalid
+                with patch("feature4_export_matrix.verify_mp4") as inspect:
+                    with self.assertRaises(MatrixEvidenceError):
+                        self.proof()
+                    inspect.assert_not_called()
+        self.manifest["renders"][0]["path"] = "symlink.mp4"
+        (self.root / "symlink.mp4").symlink_to(self.root / "synthetic-15s.mp4")
+        with self.assertRaisesRegex(MatrixEvidenceError, "unsafe"):
+            self.proof()
+
+    def test_modified_during_ffprobe_denied_by_rehash(self):
+        original = self.root / "synthetic-30s.mp4"
+        def modify(path, *, duration, width, height, fps):
+            if duration == 30:
+                with original.open("ab") as out:
+                    out.write(b"tamper")
+            return {"bytes": (path.stat().st_size - (6 if duration == 30 else 0))}
+        with patch("feature4_export_matrix.verify_mp4", side_effect=modify):
+            with self.assertRaises(MatrixEvidenceError):
+                verify_export_matrix(self.manifest, self.root, expected_head=HEAD)
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

### tests/media/test_feature4_hyperframes_benchmark.py
~~~~diff
@@ -1,13 +1,16 @@
 """Cheap, no-render checks for F4-08/12 sample measurement integrity."""
+import hashlib
+import json
 import os
 from pathlib import Path
 import sys
+import tempfile
 import unittest
 
 ROOT = Path(__file__).resolve().parents[2]
 sys.path.insert(0, str(ROOT / "video-engine" / "hyperframes"))
 
-from benchmark_render import parse_proc_stat, sample_process_group, benchmark
+from benchmark_render import parse_proc_stat, sample_process_group, benchmark, verified_output_sha256
 
 
 class HyperFramesBenchTests(unittest.TestCase):
@@ -26,6 +29,49 @@ def test_sampling_current_process_group_has_nonzero_rss(self):
         self.assertGreaterEqual(ticks, 0)
         self.assertGreaterEqual(count, 1)
 
+    def test_benchmark_receipt_hashes_real_stable_original_bytes(self):
+        with tempfile.TemporaryDirectory() as folder:
+            path = Path(folder) / "synthetic-render.mp4"
+            data = b"test-only-render" * 200
+            path.write_bytes(data)
+            size, digest = verified_output_sha256(path)
+            self.assertEqual(size, len(data))
+            self.assertEqual(digest, hashlib.sha256(data).hexdigest())
+            self.assertEqual(len(digest), 64)
+
+    def test_rejects_symlink_truncated_and_missing_benchmark_source(self):
+        with tempfile.TemporaryDirectory() as folder:
+            root = Path(folder)
+            real = root / "original.mp4"
+            real.write_bytes(b"dummy" * 500)
+            alias = root / "foreign.mp4"
+            alias.symlink_to(real)
+            for candidate in (alias, root / "missing.mp4"):
+                with self.subTest(path=candidate), self.assertRaises(ValueError):
+                    verified_output_sha256(candidate)
+            real.write_bytes(b"short")
+            with self.assertRaisesRegex(ValueError, "nonempty"):
+                verified_output_sha256(real)
+
+    def test_existing_output_or_receipt_rejected_before_any_render(self):
+        with tempfile.TemporaryDirectory() as folder:
+            root = Path(folder)
+            project = root / "project"
+            project.mkdir()
+            (project / "render-config.json").write_text(json.dumps({
+                "contract_version": "rg_video_v2",
+                "renderer": "hyperframes", "duration_seconds": 30,
+                "width": 540, "height": 960, "fps": 24,
+            }), encoding="utf-8")
+            output = root / "render.mp4"
+            report = root / "report.json"
+            for occupied in (output, report):
+                occupied.write_bytes(b"already here")
+                with self.subTest(occupied=occupied), self.assertRaisesRegex(
+                        ValueError, "destinations must be new"):
+                    benchmark(project, output, report)
+                occupied.unlink()
+
     def test_rejects_unbounded_timeout_before_loading_project(self):
         for value in (0, 781, True, 20.5):
             with self.subTest(value=value), self.assertRaises(ValueError):
~~~~

### tests/media/test_feature4_professional.py
~~~~diff
@@ -13,7 +13,11 @@
 
 ROOT = Path(__file__).resolve().parents[2]
 sys.path.insert(0, str(ROOT / "video-engine"))
-from professional import VideoPlanError, compile_composition, validate  # noqa: E402
+from professional import (
+    VideoPlanError, compile_composition, validate, checked_audio_mix,
+    SUPPORTED_ANIMATIONS, SUPPORTED_TRANSITIONS,
+)  # noqa: E402
+from creative_contract import ANIMATIONS, TRANSITIONS  # noqa: E402
 
 SHOP = "11111111-1111-4111-8111-111111111111"
 OTHER = "22222222-2222-4222-8222-222222222222"
@@ -90,6 +94,93 @@ def test_full_hd_compiler_records_exact_dimensions_and_fps(self):
         # On portrait export the product artwork must stop before the lower-third copy.
         self.assertIn(".role-product .photo-wrap{top:6%;height:66%", page)
 
+    def test_all_supported_editor_effects_compile_to_actual_css_keyframes(self):
+        """F4-05 source parity; no fake encoded-video/Chromium frame claim."""
+        self.assertEqual(ANIMATIONS, SUPPORTED_ANIMATIONS)
+        self.assertEqual(TRANSITIONS, SUPPORTED_TRANSITIONS)
+        animations = ("subtle_zoom", "fade", "slide", "pop", "glow")
+        transitions = ("fade", "slide", "cut")
+        self.plan["scenes"] = [{
+            "start": i * 3, "duration": 3, "headline": f"REVIEWED SCENE {i}",
+            "animation_preset": preset,
+            "transition": transitions[i % len(transitions)],
+        } for i, preset in enumerate(animations)]
+        output = compile_composition(self.plan, self.manifest, self.media, self.output)
+        page = (output / "index.html").read_text(encoding="utf-8")
+        for preset in animations:
+            with self.subTest(preset=preset):
+                self.assertIn(f"anim-{preset}", page)
+        for transition in transitions:
+            with self.subTest(transition=transition):
+                self.assertIn(f"trans-{transition}", page)
+        for keyframe in ("presetSubtleZoom", "presetFade", "presetSlide",
+                         "presetGlow", "promoPop", "editorialFade", "editorialSlide"):
+            with self.subTest(keyframe=keyframe):
+                self.assertIn(f"@keyframes {keyframe}", page)
+        for selector in (".anim-subtle_zoom .glass{animation:presetSubtleZoom",
+                         ".anim-fade .glass{animation:presetFade",
+                         ".anim-slide .glass{animation:presetSlide",
+                         ".anim-pop .glass{animation:promoPop",
+                         ".anim-glow .glass{animation:presetGlow",
+                         ".scene.trans-fade{animation:editorialFade",
+                         ".scene.trans-slide{animation:editorialSlide",
+                         ".scene.trans-cut{animation:none"):
+            with self.subTest(selector=selector):
+                self.assertIn(selector, page)
+        self.assertNotIn("<script", page)
+
+    def test_unsupported_effects_are_rejected_before_compilation(self):
+        for name, value in (("animation_preset", "3d_rotate"),
+                            ("animation_preset", "fade;position:absolute"),
+                            ("transition", "glitch"),
+                            ("transition", "slide;opacity:0")):
+            with self.subTest(name=name, value=value):
+                trial = copy.deepcopy(self.plan)
+                trial["scenes"][0][name] = value
+                with self.assertRaisesRegex(VideoPlanError, "Unknown"):
+                    validate(trial, self.manifest, self.media)
+
+    def test_approved_music_gain_changes_actual_renderer_audio_track(self):
+        self.audio()
+        self.plan["audio_mix"] = {"music": .37}
+        output = compile_composition(self.plan, self.manifest, self.media, self.output)
+        page = (output / "index.html").read_text()
+        self.assertIn('data-track-index="5" data-volume="0.37"', page)
+
+    def test_bounded_narration_and_sfx_gains_retaining_music_ducking(self):
+        self.audio()
+        self.manifest["assets"]["voice"] = {
+            "kind": "audio", "path": "music.wav", "rights": copy.deepcopy(RIGHTS),
+        }
+        self.manifest["assets"]["effect"] = {
+            "kind": "audio", "path": "music.wav", "rights": copy.deepcopy(RIGHTS),
+        }
+        self.plan["voiceover_asset_id"] = "voice"
+        self.plan["scenes"][1]["sfx_asset_id"] = "effect"
+        self.plan["audio_mix"] = {
+            "music": .8, "voiceover": .72, "sfx": .15,
+        }
+        page = (compile_composition(
+            self.plan, self.manifest, self.media, self.output) / "index.html").read_text()
+        self.assertIn('data-track-index="7" data-volume="0.72"', page)
+        self.assertIn('data-track-index="6" data-volume="0.15"', page)
+        self.assertIn('data-track-index="5" data-volume="0.12"', page)
+        self.assertNotIn('data-track-index="5" data-volume="0.8"', page)
+
+    def test_audio_gain_rejects_inert_unknown_and_nonfinite_controls(self):
+        for mix in (
+            {"music": 1}, {"sfx": 0}, {"voiceover": .5}, {"source": .5},
+            {"music": float("nan")}, {"source": True}, {"music": -.1},
+            {"music": .009}, {"unknown_track": 1}, {"music": "0.5"},
+        ):
+            with self.subTest(mix=mix), self.assertRaises(VideoPlanError):
+                validate({**self.plan, "audio_mix": mix}, self.manifest, self.media)
+        for mix in ([], "music=1", {"music": float("inf")}):
+            with self.subTest(mix=mix), self.assertRaises(VideoPlanError):
+                checked_audio_mix(
+                    mix, has_music=True, has_voice=False,
+                    has_source=False, has_sfx=False)
+
     def test_sixty_second_script_acceptance_without_expensive_render(self):
         self.plan["duration_seconds"] = 60
         for index, scene in enumerate(self.plan["scenes"]):
~~~~

### tests/media/test_feature4_scene_visibility.py
~~~~diff
@@ -47,7 +47,11 @@ def test_three_actual_nonblank_encoded_scenes_pass_not_commercial_approval(self)
         self.assertFalse(report["commercial_release_eligible"])
         self.assertFalse(report["unexpected_overlay_absence_verified"])
         self.assertEqual(len(report["checked_scenes"][0]["samples"]),5)
-        self.assertEqual(report["schema"],"feature4_scene_visibility_v2")
+        self.assertEqual(report["schema"],"feature4_scene_visibility_v3")
+        self.assertTrue(report["continuous_full_reel_black_scan"])
+        self.assertEqual(report["continuous_black_hold_threshold_seconds"],.65)
+        self.assertEqual(report["continuous_long_black_holds_count"],0)
+        self.assertFalse(report["sub_threshold_blank_frames_certified_absent"])
         self.assertEqual(report["sample_fractions"],[.15,.30,.50,.70,.85])
         self.assertFalse(report["short_blank_frames_excluded_by_sampling"])
         self.assertGreater(report["checked_scenes"][0]["samples"][0]["mean_luma"],14)
@@ -78,6 +82,32 @@ def test_actual_middle_black_interval_old_two_samples_missed(self):
         with self.assertRaisesRegex(VisibilityProofError,"blank/black"):
             verify_scene_visibility(self.path,seconds=15,scenes=SCENES)
 
+    def test_blackdetect_log_parses_numeric_events_not_literal_backslashes(self):
+        sample="[blackdetect @ 0x1] black_start:1.6 black_end:2.4 black_duration:0.8"
+        match=feature4_scene_visibility._BLACK_HOLD_RX.search(sample)
+        self.assertIsNotNone(match)
+        self.assertEqual(tuple(map(float,match.groups())),(1.6,2.4,0.8))
+
+    def test_sustained_black_hold_between_all_five_interior_probes_rejected(self):
+        # First five-second scene: red 1.6s, BLACK .8s, red 2.6s.
+        # Interior samples .75/1.5/2.5/3.5/4.25 all see nonblack red.
+        parts=[("red",1.6),("black",.8),("red",2.6),
+               ("blue",5),("green",5)]
+        args=["ffmpeg","-nostdin","-hide_banner","-loglevel","error"]
+        for color,duration in parts:
+            args+=["-f","lavfi","-i",
+                   f"color=c={color}:s=540x960:r=12:d={duration}"]
+        args+=["-f","lavfi","-i","sine=frequency=430:duration=15",
+               "-filter_complex","".join(f"[{i}:v]" for i in range(5))
+                 +"concat=n=5:v=1:a=0[v]",
+               "-map","[v]","-map","5:a:0",
+               "-c:v","libx264","-preset","ultrafast","-pix_fmt","yuv420p",
+               "-c:a","aac","-b:a","48k","-threads","2","-shortest",str(self.path)]
+        subprocess.run(args,check=True,capture_output=True,timeout=120)
+        # The real FFmpeg full-frame scan rejects what five probes miss.
+        with self.assertRaisesRegex(VisibilityProofError,"continuous black hold"):
+            verify_scene_visibility(self.path,seconds=15,scenes=SCENES)
+
     def test_encoded_media_changed_during_sampling_rejected(self):
         self.source()
         original=feature4_scene_visibility._pixel_frame
~~~~

### tests/media/test_feature4_scene_visibility_receipt.py
~~~~diff
@@ -25,7 +25,11 @@ def setUp(self):
         self.windows=[{"start":i*5.0,"duration":5.0} for i in range(12)]
         self.prov={"scene_windows":self.windows}
         self.report={
-            "schema":"feature4_scene_visibility_v2",
+            "schema":"feature4_scene_visibility_v3",
+            "continuous_full_reel_black_scan":True,
+            "continuous_black_hold_threshold_seconds":.65,
+            "continuous_long_black_holds_count":0,
+            "sub_threshold_blank_frames_certified_absent":False,
             "sample_fractions":[.15,.30,.50,.70,.85],
             "short_blank_frames_excluded_by_sampling":False,
             "status":"SAMPLED_SCENES_NOT_BLANK_NOT_CONTENT_APPROVAL",
@@ -96,6 +100,19 @@ def test_missing_center_sample_or_forged_black_flag_rejected(self):
         with self.assertRaises(MinuteProofError):
             self.verify()
 
+    def test_missing_or_forged_continuous_scan_evidence_rejected(self):
+        for key,bad in (("continuous_full_reel_black_scan",False),
+                        ("continuous_black_hold_threshold_seconds",99),
+                        ("continuous_long_black_holds_count",True),
+                        ("continuous_long_black_holds_count",1),
+                        ("sub_threshold_blank_frames_certified_absent",True)):
+            original=self.report[key]
+            self.report[key]=bad
+            self.persist()
+            with self.subTest(key=key,bad=bad),self.assertRaises(MinuteProofError):
+                self.verify()
+            self.report[key]=original
+
     def test_legacy_two_frame_proof_is_no_longer_accepted(self):
         self.report["schema"]="feature4_scene_visibility_v1"
         self.report["checked_scenes"][0]["samples"]=[
~~~~

### tests/media/test_feature4_visibility_window_integrity.py
~~~~diff
@@ -0,0 +1,102 @@
+"""Feature #4 F4-02: no positive 60s visibility receipt for gapped/overlapping time."""
+import sys
+import unittest
+from pathlib import Path
+from unittest.mock import patch
+
+ROOT = Path(__file__).resolve().parents[2]
+sys.path.insert(0, str(ROOT / "video-engine"))
+from feature4_minute_quality_receipt import (
+    MinuteProofError, validate_visibility_evidence,
+)
+
+FRACTIONS = [.15, .30, .50, .70, .85]
+SOURCE_SHA = "a" * 64
+
+
+def fixture():
+    windows = [{"start": 5 * i, "duration": 5} for i in range(12)]
+    scenes = []
+    for window in windows:
+        scenes.append({
+            "scene_start": window["start"],
+            "duration": window["duration"],
+            "sustained_near_black": False,
+            "samples": [
+                {"time_seconds": round(window["start"] + fraction * window["duration"], 3),
+                 "mean_luma": 75.0, "near_black_fraction": 0.0}
+                for fraction in FRACTIONS
+            ],
+        })
+    provenance = {"scene_windows": windows}
+    proof = {
+        "schema": "feature4_scene_visibility_v3",
+        "status": "SAMPLED_SCENES_NOT_BLANK_NOT_CONTENT_APPROVAL",
+        "source_sha256": SOURCE_SHA,
+        "seconds": 60,
+        "checked_scene_count": 12,
+        "sample_fractions": FRACTIONS,
+        "continuous_full_reel_black_scan": True,
+        "continuous_black_hold_threshold_seconds": .65,
+        "continuous_long_black_holds_count": 0,
+        "sub_threshold_blank_frames_certified_absent": False,
+        "short_blank_frames_excluded_by_sampling": False,
+        "sustained_near_black_count": 0,
+        "commercial_release_eligible": False,
+        "garment_identity_verified": False,
+        "unexpected_overlay_absence_verified": False,
+        "checked_scenes": scenes,
+    }
+    return provenance, proof
+
+
+class VisibilityWindowIntegrityTests(unittest.TestCase):
+    def check(self, provenance, proof):
+        with patch("feature4_minute_quality_receipt._record", side_effect=[provenance, proof]), \
+             patch("feature4_minute_quality_receipt._sha", return_value=SOURCE_SHA):
+            return validate_visibility_evidence(
+                original=Path("private-stock-fixture.mp4"),
+                provenance=Path("private-provenance.json"),
+                visibility_proof=Path("private-visibility.json"),
+            )
+
+    def test_valid_contiguous_minute_is_technical_only(self):
+        provenance, proof = fixture()
+        result = self.check(provenance, proof)
+        self.assertEqual(result["checked_scene_count"], 12)
+        self.assertIs(result["commercial_release_eligible"], False)
+
+    def test_both_matching_json_timelines_cannot_skip_or_repeat_time(self):
+        for altered_start in (24.5, 25.5):
+            with self.subTest(altered_start=altered_start):
+                provenance, proof = fixture()
+                provenance["scene_windows"][5]["start"] = altered_start
+                proof["checked_scenes"][5]["scene_start"] = altered_start
+                proof["checked_scenes"][5]["samples"] = [
+                    {"time_seconds": round(altered_start + fraction * 5, 3),
+                     "mean_luma": 75.0, "near_black_fraction": 0.0}
+                    for fraction in FRACTIONS
+                ]
+                with self.assertRaisesRegex(MinuteProofError, "not contiguous"):
+                    self.check(provenance, proof)
+
+    def test_full_minute_and_finite_positive_windows_required(self):
+        for bad_duration in (0, -5, float("nan"), float("inf"), 4):
+            with self.subTest(bad_duration=bad_duration):
+                provenance, proof = fixture()
+                provenance["scene_windows"][-1]["duration"] = bad_duration
+                proof["checked_scenes"][-1]["duration"] = bad_duration
+                with self.assertRaisesRegex(
+                    MinuteProofError, "not contiguous|full minute"
+                ):
+                    self.check(provenance, proof)
+
+    def test_window_shape_must_be_exact(self):
+        provenance, proof = fixture()
+        provenance["scene_windows"][0]["approval"] = True
+        with self.assertRaisesRegex(MinuteProofError, "not contiguous"):
+            self.check(provenance, proof)
+
+
+if __name__ == "__main__":
+    unittest.main()
~~~~

### tests/media/test_feature4_worker_handoff.py
~~~~diff
@@ -4,14 +4,20 @@
 manifest, lose a tenant fence, double-claim/bill or expose unapproved output.
 """
 import copy
+import hashlib
+import os
 import sys
+import tempfile
 import unittest
 from pathlib import Path
+from unittest.mock import patch
 
 ROOT = Path(__file__).resolve().parents[2]
 sys.path.insert(0, str(ROOT / "video-engine"))
+import feature4_worker_handoff
 from feature4_worker_handoff import (  # noqa: E402
     Feature4ClaimBusy, Feature4HandoffError, process_feature4_render,
+    _staged_fingerprint, MAX_TOTAL_STAGED_BYTES,
 )
 
 SHOP = "11111111-1111-4111-8111-111111111111"
@@ -169,6 +175,70 @@ def test_auth_revocation_and_lost_claim_abort_without_public_output(self):
         self.assertEqual(self.media.uploads, [])
         self.assertEqual(self.admin.completions, [])
 
+    def test_stale_claim_preflight_denies_private_download_and_render(self):
+        self.admin.current = False
+        def forbidden_render(*args):
+            self.fail("stale claim must never invoke CPU renderer")
+        self.assertEqual(process_feature4_render(
+            JOB, self.admin, self.media, render_fn=forbidden_render), "STALE")
+        self.assertEqual(self.media.downloads, [])
+        self.assertEqual(self.media.uploads, [])
+        self.assertEqual(self.admin.failures, [])
+
+    def test_claim_revoked_after_staging_never_reaches_cpu_renderer(self):
+        # First lease check before downloading passes; second after stage fails.
+        self.admin.claim_checks = 0
+        def current(_claim):
+            self.admin.claim_checks += 1
+            return self.admin.claim_checks == 1
+        self.admin.feature4_claim_current = current
+        def forbidden_render(*args):
+            self.fail("stale post-staging claim must never start CPU renderer")
+        self.assertEqual(process_feature4_render(
+            JOB, self.admin, self.media, render_fn=forbidden_render), "STALE")
+        self.assertEqual(len(self.media.downloads), 1)
+        self.assertEqual(self.media.uploads, [])
+        self.assertEqual(self.admin.completions, [])
+        self.assertEqual(self.admin.failures, [])
+
+    def test_same_content_inode_replacement_during_hash_is_rejected(self):
+        # A stable open FD still reads old bytes after same-content os.replace.
+        with tempfile.TemporaryDirectory(prefix="f4-inode-") as folder:
+            root = Path(folder)
+            original = root / "asset.png"
+            original.write_bytes(b"original synthetic bytes" * 100)
+            original_bytes = original.read_bytes()
+            make_digest = hashlib.sha256
+            class ReplacingDigest:
+                def __init__(self):
+                    self.digest = make_digest()
+                    self.changed = False
+                def update(self, data):
+                    self.digest.update(data)
+                    if not self.changed:
+                        self.changed = True
+                        replacement = root / "new-asset.png"
+                        replacement.write_bytes(original_bytes)
+                        os.replace(replacement, original)
+                def hexdigest(self):
+                    return self.digest.hexdigest()
+            with patch.object(feature4_worker_handoff.hashlib, "sha256",
+                              side_effect=lambda: ReplacingDigest()):
+                with self.assertRaisesRegex(
+                        Feature4HandoffError, "path changed while hashing"):
+                    _staged_fingerprint(original)
+
+    def test_zero_or_oversized_staged_media_denied_before_hashing(self):
+        with tempfile.TemporaryDirectory(prefix="f4-limit-") as folder:
+            path = Path(folder) / "asset.mp4"
+            path.write_bytes(b"")
+            with self.assertRaisesRegex(Feature4HandoffError, "nonempty bounded"):
+                _staged_fingerprint(path)
+            with path.open("wb") as f:
+                f.truncate(MAX_TOTAL_STAGED_BYTES + 1)
+            with self.assertRaisesRegex(Feature4HandoffError, "nonempty bounded"):
+                _staged_fingerprint(path)
+
     def test_fencing_race_on_finalization_has_no_signed_url(self):
         self.admin.can_finalize = False
         self.assertEqual(self.run_worker(), "STALE")
@@ -209,6 +279,32 @@ def test_bundle_extraneous_private_asset_fails_closed(self):
             self.run_worker()
         self.assertEqual(self.media.downloads, [])
 
+    def test_local_staged_source_mutation_or_symlink_swap_fails_before_upload(self):
+        # Genuine CPU render must consume unchanged original downloaded bytes;
+        # a forged probe/result from a renderer is not a waiver.
+        for variant in ("overwrite", "append", "symlink"):
+            with self.subTest(variant=variant):
+                self.media = Media()
+                self.admin.failures.clear()
+                self.admin.completions.clear()
+                def swapped(request, manifest, staged, output):
+                    result = fake_render(request, manifest, staged, output)
+                    source = next(staged.iterdir())
+                    if variant == "overwrite":
+                        source.write_bytes(b"different synthetic source media")
+                    elif variant == "append":
+                        with source.open("ab") as stream:
+                            stream.write(b"tampered")
+                    else:
+                        source.unlink()
+                        source.symlink_to(output / (JOB + ".mp4"))
+                    return result
+                with self.assertRaises(Feature4HandoffError):
+                    process_feature4_render(JOB, self.admin, self.media, render_fn=swapped)
+                self.assertEqual(self.media.uploads, [])
+                self.assertEqual(self.admin.completions, [])
+                self.assertEqual(self.admin.failures, [("INVALID_RENDER_INPUT", True)])
+
     def test_renderer_wrong_output_or_cross_job_denied(self):
         def malicious(*args):
             result = fake_render(*args)
~~~~

### video-engine/FEATURE4_31_TASK_PARALLEL_TRACKER_20261029.md
~~~~diff
@@ -69,3 +69,31 @@ PR #322 (DRAFT). Feature4 owner: `feat/feature4-professional-video-studio`. Revi
 - **Implemented, source+local archive evidence:** The existing exact Timeline Studio JS split/reorder `[0,4,14,20]` → trusted Python compiler → 30s 540p HyperFrames **encoded mock** now runs `feature4_edited_export_qa.py` in the same existing media CI job; no second render. It verifies 30s H264/AAC, hashes source before/after four actual FFmpeg decoded scenes (2/7/16/24s), rejects gross swapped/missing shots and identical second video replay, and emits fail-closed technical-only report. Importantly this is a **synthetic owner-rejected technical fixture**, not garment/product visual quality or exact-frame inpoint proof.
 - **Actual archived prior 30s edited MP4**, SHA-256 `1c69ede47eac07a2dba118ceca59beca118f337d67e801b7eecc4bbe94b57153`, 30.000s/540x960, passed the same local four-frame decoder/proof: video-pair delta 3.53; photo-pair 19.017; minimum video/photo 21.095. Four focused negative/positive Python tests pass locally, covering forged order, false replay, source mutation, wrong duration, and symlinks.
 - **Status against 31 tasks**: progress on **#4**, with the 30s split/reorder encoded mock *technical regression slice* complete locally; duplication encoded pixels and real customer 30s footage remain open, so DO NOT relabel the full #4 (or MVP) as commercially complete. First run exact-head branch 4/4 and merged-base PR CI; shared ZIP issue #22 remains coordinator-owned. This batch touches only Feature4-owned CI harness, source, tests and docs. No GPU, cloud, WineShopPOS or production change.
+
+## 2026-10-29 — F4-04 independent encoded duplication parity batch
+
+- Task **F4-04** remains IN PROGRESS until coordinator-reviewed integration and fresh main 4/4 CI. Stacked branch `feat/feature4-encoded-duplicate-parity-20261029` is isolated from coordinator/shared files and based on Feature4 #322 head `e32a8da61a6272666d757b6c51b0ec2576d7602f`.
+- Reuses exact pinned Timeline Studio JS `studioDuplicate` via `duplicated_draft()`; trusted Python `compile_approved_storyboard` and the existing HyperFrames real 30s 540p H264/AAC CPU media job now physically encode both split/reorder and **separate 10/5/5/10 duplicate** actions. The real decoder checks two encoded replay positions 11.5s and 16.5s, distinct photo segments and source SHA; tests reject advanced replay, forged photo pairs, unexpected operations and missing proof. No GPU, paid inference, PROD, customer or WineShopPOS media.
+- This is a deterministic **OWNER-REJECTED synthetic fixture**, not real retailer footage, commercial quality, or exact original-frame matching. Remain explicit `commercial_release_eligible=false`; source and QA are only complete after final branch/stack PR full four-job CI. Source-implemented is not integrated DONE; Feature4 #322 remains draft until coordinator resolves ZIP packaging and merges.
+
+
+## 2026-10-30 — Unified branch-green source handoff; source is NOT integrated DONE
+Five nonoverlapping technical source drafts have been batched for one final integration CI run: #686 F4-04 encoded duplicate parity (4/4 #40955296326), #690 F4-13/F4-15 staged input mutation guard (4/4 #40955734381), #695 F4-14 immutable CPU benchmark (4/4 #40961371565), #701 F4-10 tenant-safe pointer editing (4/4 #40961280016), and #705 F4-03 exact-head 15/30/60 evidence verifier (4/4 #40966895351). Combined branch `feat/feature4-batched-source-handoff-20261030` is intentionally made as one tree/commit from existing #322 parent. None are coordinator-merged or commercial accepted. F4-03 actual three same-head MP4s, F4-14 all duration CPU budgets and F4-10 manual accessibility still OPEN; #650, #249 and real approved F2/F3/F5/F7 outputs remain external. Original draft PRs become trace evidence only, not five changes to apply twice. No GPU, paid AI, hosted actions, PROD or WineShopPOS.
+
+### 2026-11-17 — original F4-04 #723 decoded frame integrity preservation
+- Source-only: exact 9216-byte grayscale decode guard and four malformed buffer regressions ported into `feature4_edited_export_qa.py` and tests. Original #723 historical tracker notes archived in [checkpoint](feature4/ORIGINAL_723_PROVENANCE_20261117.md); latest parent #322 retains stronger per-download rights/lease check from original. #779 source needs rebasing/reconciliation, F4-04/F4-15 still IN PROGRESS.
+
+### 2026-11-17 — #753 contiguous full-minute scene window proof
+- Original F4-02 #753 finite, positive contiguous 12-scene 60s window validation and four regression tests were reconciled into the latest v3 continuous-black-scan source. Original tracker/handoff preserved verbatim in [note](feature4/ORIGINAL_753_PROVENANCE_20261117.md). Source-only IN PROGRESS; actual private 60s release/CI/main acceptance separate.
+
+### 2026-11-17 — original #784 native clip drag cancellation regression
+- Ported the independent F4-10 #784 cancelled-drag fence and Playwright regression into the current consolidated source; retains newer bounded frame seek, caption drag lease/draft checks. Original SHA + tracker lines preserved in [note](feature4/ORIGINAL_784_PROVENANCE_20261117.md). Source-only F4-10 IN PROGRESS until CI and accepted current-main integration.
+
+### 2026-11-17 — original #745/#773 encoded split/reorder QA
+- Integrated #745 frozen moving-clip source (3/17s) and #773 near-cut scene family (5/13/15/21s) checks and two targeted regressions on surviving #779, preserving duplicate-op and source SHA. Details and original HEADs: [handoff](feature4/ORIGINAL_745_773_PROVENANCE_20261117.md). F4-04 IN PROGRESS pending full exact-head CI and accepted current-main source integration.
+
+### 2026-11-17 — original F4-04 #735 complete duplicate project regression recovered
+- Ported original JS duplicate→Python compiler→HyperFrames negative/positive project test (adapted to current operation name), retaining source-level 0/0 inpoints, one music SFX and explicit OWNER_REJECTED; current #779 already actually renders duplicate in CPU smoke. Details: [source note](feature4/ORIGINAL_735_PROVENANCE_20261117.md). Source-only F4-04 IN PROGRESS, parent/main merge + exact-head CI pending.
+
+### 2026-11-17 — F4-06 original #830 fully preserved in source consolidation #779
+- Copy original #830 fixed bounded four-channel audio source contract, complete compile/renderer tests and source handoffs onto #779 as **exact Git blobs**. Audio mix source 0.20–1, music 0–1, voiceover 0.20–1, SFX 0–0.50 and 0.01 quantization, deny unknown/inert/nonfinite/unlicensed track; trusted renderer writes corresponding fixed `data-volume` and keeps existing music-under-narration/source ducking. Independent JS duplicate, encoded motion/boundary and tenant/rights protections on other paths untouched. Original #830 remains source-only until final CI/current-parent integration, F4-06/F4-07 IN PROGRESS.
~~~~

### video-engine/FEATURE4_ACCELERATED_BATCH_HANDOFF_20261030.md
~~~~diff
@@ -0,0 +1,27 @@
+# Feature4 accelerated source batch handoff — 2026-10-30
+
+**IN PROGRESS — source-only proposed single-review bundle.** One coherent Git commit combines **five** previously green but unmerged, nonoverlapping Feature4 draft-PR batches (#686, #690, #695, #701, #705) into `feat/feature4-batched-source-handoff-20261030`, based exactly on existing Feature4 parent SHA `e32a8da61a6272666d757b6c51b0ec2576d7602f`. CI must validate this combined tree. Do **not** mark DONE merely because an individual draft had 4/4.
+
+| Original draft | Tasks advanced (not closed) | Exact branch push CI |
+| --- | --- | --- |
+| #686 | F4-04 mock 30s actual encoded duplicated-replay parity | #40955296326, 4/4 |
+| #690 | F4-13/F4-15 staged private input SHA and worker mutation denial | #40955734381, 4/4 |
+| #695 | F4-14 immutable 30s local CPU benchmark SHA receipt | #40961371565, 4/4 after import repair |
+| #701 | F4-10 React timeline stale-drag cross-tenant/approval denial | #40961280016, 4/4 |
+| #705 | F4-03 exact-head actual 15/30/60 MP4 evidence verifier | #40966895351, 4/4 |
+
+## Throughput changes for the next batches
+
+- Instead of five separate coordinator integration/merge trains, review this **one combined draft** with original source commits and exact proofs attached, and run normal four-job CI once at the final combined head.
+- New work on independent F4-01/F4-02/F4-05/F4-07/F4-11/F4-12 can proceed on separate nonoverlapping source branches, but must not overwrite these same files. **Global maximum 10 is a concurrency ceiling, not 10 agents currently running**; there is no installed coding executor or atomic claims.
+- Do targeted security/parity tests when touched, especially source-media rights, SHA/tenant/approval/race invariants; batch slower full FFmpeg/Playwright/Supabase 4-job CI at meaningful review boundaries. Do **not** defer all testing until task end or disable protected workflows. GitHub default branch-push CI still automatically triggers on pushes; batching files in one tree/commit minimizes redundant runs without changing coordinator-owned workflows.
+- Reuse verified versioned F2 creative, F3 private rights metadata, F5 bounded motion receipt, F7 edit instructions and deterministic approved mock fixtures only as **technical interface test inputs**. Never represent these as actual human-approved music, garment-matched Wan video, real voice, or released retailer media.
+- Keep details and task IDs in the original ledger plus feature handoff. Coordinator alone reviews, reconciles main, merges, issues accepted status receipts and checks **fresh** main 4/4.
+
+## Unresolved exact release dependencies
+
+- F4-03 needs **three actual 15/30/60 same-code encoded outputs**, not just the checker; F4-10 manual mobile/a11y; F4-14 full three-length CPU/RSS budgets; F4-13/F4-15 hosted signed worker and rights need separate acceptance.
+- F4-16/17: Feature2 independently approved script, audio licensing and real spoken-word timed cues; F4-18: Feature3 actual rights-authorized product/model originals; F4-19: Feature5 authorized real model motion (GPU remains OFF); F4-20: Feature7 human-reviewed edit instruction; F4-21: complete source/owner integration and signoff.
+- F4-22/#650 is coordinator-owned Functions ZIP package; F4-23 coordinator review/main integration; F4-24..28 coordinator signed auth/lease/output/worker integration; F4-29/#249 Azure HTTP 503 owner; F4-30 coordinator signed DEV E2E; F4-31 owner commercial content approval.
+
+**No GPU, charged model/coding executor, PROD, hosted SQL, WineShopPOS, user-facing samples or unreviewed owner approval.**
~~~~

### video-engine/FEATURE4_AUDIO_GAIN_HANDOFF_20261030.md
~~~~diff
@@ -0,0 +1,13 @@
+# F4-06 — bounded independent audio gains (2026-10-30)
+
+**IN PROGRESS; Feature4 source only**, stacked on draft #828. No user-facing control is enabled and no output is commercial-ready.
+
+## New trusted source shape
+`creative_reel_v1` and `rg_video_v2` now optionally accept `audio_mix` containing at most four reviewed channel names: `source` (original video audio, [0.20,1]), `music` (licensed bed, [0,1]), `voiceover` (licensed full-length narration, [0.20,1]) and `sfx` (licensed 2-second effect, [0,0.50]). A finite real number with 0.01-step precision is required. Boolean, NaN/Infinity, injected CSS/filtergraphs, missing authorized tracks or unrecognized keys fail closed. Existing defaults remain source 1, music 0.55, voiceover 1 and SFX 0.25.
+
+Trusted Python compiler writes matching existing HyperFrames `data-volume` on the four existing track families with fixed per-channel gain. Under original video audio or narration, music is automatically capped to 0.12 to preserve dialogue audibility. Independent gains have **no bus automation or per-word/adaptive ducking**. Only an authoritative coordinator/backend approved snapshot may provide this map; never accept a browser draft gain as authority.
+
+## Evidence
+Source-level compiler tests verify the actual emitted HyperFrames track index + per-track volume and no regression to existing default attributes. Cross-feature source tests verify trusted request -> plan -> HTML media route with an actual offline synthetic H264/AAC video fixture. Negatives refuse unsupported/inert channel gains, nonfinite/string/bool/out-of-bounds values, false production authorization. CI four-job exact-head branch required; actual *decoded final AAC output* of each optional channel and signed owner gain selection remains separately unverified. Original 31-task ledger updated.
+
+**Dependency/acceptance:** Real media rights and F2 approved narration/music remains separate; F4-07 human audio mix/ducking listening QA and F4-06 editor gain UI still disabled; source-specific PR requires coordinator-approved main integration and **fresh main four-job CI**. #650 protected package and #249 Azure 503 remain coordinator. No GPU, paid AI, production cloud, signed downloads, user-facing samples or WineShopPOS.
~~~~

### video-engine/FEATURE4_CONTINUOUS_BLACK_SCAN_HANDOFF_20261030.md
~~~~diff
@@ -0,0 +1,18 @@
+# Feature #4 F4-11 — continuous black-hold scan handoff (2026-10-30)
+
+**IN PROGRESS, not integrated DONE.** Branch `feat/feature4-continuous-black-qa-20261030` stacks on consolidated draft #779. This work is source-only, no real retailer media, paid model, GPU or production cloud.
+
+## What changed
+The existing 15/30/60 real H264/AAC sampled scene QA checked five interior points per shot and could miss an unwanted 0.8-second fully black hole BETWEEN points. New FFmpeg `blackdetect` performs one bounded **continuous full-timeline video decode** at a conservative 0.65s nearly-all-black threshold, rejecting >=threshold holds even if all five scene spot checks pass. The emitted v3 proof records the full scan, threshold and zero findings, while explicitly NOT certifying subthreshold flash absence, legibility, rights or human-quality approval. The 60s source-to-receipt verifier now requires v3 full-scan evidence and denies fabricated approval, missing fields, noninteger booleans, changed threshold or detected holds.
+
+New 15s actual FFmpeg synthetic regression encodes a real 0.8s black hold hidden between previous five sample times. Existing encoded red/blue/green fixture verifies no false rejection, and 60s receipt negatives test fail-closed omission/forgery.
+
+## Acceptance and remaining gates
+Run full four-job exact-head branch CI, coordinator-reviewed integration to main and fresh main 4/4. Real **updated** 60s full-HD garment/motion/outro source and actual reviewer approval remain F4-01/F4-11/F4-12 separate gates. This technical control neither proves every isolated black frame nor transforms synthetic media into a commercial render.
+
+Ownership: Feature4 files only. Do not modify workflows, shared coordinator docs, signed auth, Azure, WineShopPOS, or launch GPU.
+
+## CI failure and actual corrective action (bounded first repair)
+
+- [Branch CI #41052416541](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41052416541) at `ae68b1f57f0166446e404e18ad4eba71aff39570`: 3/4 PASS, FFmpeg media 239/240 tests PASS, new real encoded gap regression FAILED closed with `Incomplete black-frame scan evidence`. Root cause was **over-escaped Python raw regex**: the pattern contained two backslashes before `d` and `s`, so FFmpeg `black_start:1.6 ...` numeric log never matched. No security/media acceptance gates were weakened.
+- Fixed regex to single-backslash Python raw digit/whitespace expressions and added an explicit numeric FFmpeg log parser unit test. New exact-head four-job CI required; do not count F4-11 as verified until green. Attempts: initial #1 failed, repaired #2 pending.
~~~~

### video-engine/FEATURE4_CPU_3PROFILE_MATRIX_HANDOFF_20261030.md
~~~~diff
@@ -0,0 +1,11 @@
+# Feature4 F4-14 15/30/60 CPU evidence matrix — 2026-10-30
+
+**IN PROGRESS.** This is a source-only contract improvement, not completion of F4-14.
+
+The new `video-engine/feature4_cpu_matrix.py` checks exactly three **existing actual private MP4s** and three existing separate HyperFrames CPU receipts generated from the **same declared Git checkout**. It calls F4-03's real ffprobe and immutable original-byte SHA checks, then rejects incorrect source SHA, mismatched receipt sha/length/duration, missing stats, invalid timing/RSS sampling, rights-claim escalation, cloud/GPU or commercial approval flags. Source receipts are bounded, no-follow JSON and report output is fresh/private. Returns an honest local observed envelope with max wall time and sampled RSS; it does not set a spending budget or cloud capacity.
+
+F4-14's original `benchmark_render.py` now includes `source_commit_claim` directly in the local receipt, but that SHA is **not CI-signed provenance**. A technical matrix never becomes an approved cloud memory budget or a commercial video. Three actual 15/30/60 same-head encoded files **and** genuine associated measured reports are still required. Tests use synthetic bytes with a **mocked** ffprobe and explicitly cannot establish actual 15/30/60 encoding, producer rights, or performance budgets.
+
+**Dependency gates:** F4-03 same-head encoded media; F4-01 genuine updated 60s native render; F4-22 coordinator package issue #650; F4-29 Azure HTTP 503 #249; F4-30 hosted DEV E2E. Coordinator reviews/merges after exact-head 4/4 and verifies fresh main 4/4. Do not merge stacked drafts separately or mark F4-14 DONE before scope acceptance.
+
+No GPU, charged models, cloud deployments, SQL, WineShopPOS, user-facing samples or approval bypass.
~~~~

### video-engine/FEATURE4_CPU_BENCHMARK_HANDOFF_20261029.md
~~~~diff
@@ -0,0 +1,15 @@
+# Feature #4 F4-14 — offline CPU budget/output evidence handoff (2026-10-29)
+
+**Status:** IN PROGRESS, never integrated DONE without coordinator-reviewed merge into `main` and fresh four-job main CI. Branch `feat/feature4-cpu-benchmark-proof-20261029` is isolated from F4-04 duplicate parity and F4-13/F4-15 worker staging integrity.
+
+## Source-only change
+
+The existing mandatory 30-second Full-HD synthetic HyperFrames `benchmark_render.py` now binds its **actual encoded file bytes** to the CPU/RSS/wall-clock JSON report through a SHA-256 of a stable no-follow, regular-file descriptor, validates local file identity after hashing, and refuses existing target or report paths rather than silently overwriting another task's evidence. No extra render or paid inference is added. Tests verify full SHA, symlink/missing/truncated file denials and existing destination refusal without launching browser/render processes.
+
+This is an improvement of the existing *local sampled lower-bound* CPU/RSS evidence: it does not create or certify a 15/30/60 cross-profile budget matrix, Azure cold start, Azure cost, cloud memory, human visual quality, or permitted commercial media. Benchmarks still explicitly set `azure_runtime_memory_verified=false` and `commercial_visual_quality_accepted=false`.
+
+## Acceptance and dependencies
+
+Run targeted `python3 -m unittest tests.media.test_feature4_hyperframes_benchmark -v` and standard four-job CI at branch boundary. Coordinator may merge source after separate review; fresh main 4/4 required to mark accepted slice. F4-14 remains IN PROGRESS until genuine 15/30/60 comparable measured envelope is approved; F4-22 ISSUE-650 packaging, F4-29 ISSUE-249 reliability and F4-30 signed DEV E2E remain coordinator/external tasks.
+
+No GPU, Azure/PROD, hosted SQL, customer media or WineShopPOS.
~~~~

### video-engine/FEATURE4_EXPORT_MATRIX_HANDOFF_20261030.md
~~~~diff
@@ -0,0 +1,15 @@
+# Feature #4 F4-03 — Same-code 15/30/60 local export matrix handoff (2026-10-30)
+
+**Task F4-03 is IN PROGRESS, not DONE.** Branch `feat/feature4-export-matrix-receipt-20261030` is isolated from #686, #690, #695 and #701, all based on draft Feature4 #322 SHA `e32a8da61a6272666d757b6c51b0ec2576d7602f`.
+
+## Independent work
+New `feature4_export_matrix.py` is an offline **evidence verifier, not a renderer**. When provided three existing local trusted CPU MP4s for 15, 30, 60 seconds, it refuses duplicate/missing profiles, stale declared checkout SHA, malformed or traversing names, symlinks, oversized outputs, corrupt/unsupported H264/AAC codecs, wrong 1080×1920 yuv420p 24fps/duration and mismatched or changed original-byte SHA. It produces an exclusive new JSON source-only receipt with explicit release/human/Azure flags **false**. Does not download media or run any AI/GPU/inference/extra video renders.
+
+The existing branch and prior 60s evidence are from **different code heads**. Therefore this checker must **not** report accepted same-code matrix until genuine three matching artifacts are assembled by the coordinator using the source from **one exact commit**, actual byte manifests and real ffprobe checks. The `source_commit_claim` is declared local evidence; `code_commit_attested_by_ci=false` deliberately prevents treating an untrusted manifest as signed GitHub Actions provenance.
+
+## Acceptance
+- Source unit/negative coverage via `python3 -m unittest discover -s tests/media -p 'test_feature4_export_matrix.py'`.
+- Full 4-job CI on final branch; coordinator review and integration into `main`, then fresh 4/4 main CI.
+- F4-03 remains IN PROGRESS pending matching actual 15/30/60 MP4s at the same code SHA and independent human visual/copyright approval. No user-facing example Reel or synthetic clip output generated by this task.
+
+No paid GPU/models, live DEV/PROD deployment, WineShopPOS, shared contracts, or coordinator task-progress mutations.
~~~~

### video-engine/FEATURE4_HANDOFF.md
~~~~diff
@@ -158,3 +158,7 @@ Coordinator's one atomic `create_feature4_intent` must supply frozen `snapshot`
 ## 2026-10-28 — F4-16 professional open-source editor code adoption
 
 Selected actual pinned MIT [Timeline Studio](https://github.com/MartinDelophy/ai-video-editor/tree/e1091feccca3be8832b507eb7e17c9e55eb2233a); source adaptation and file map [here](FEATURE4_TIMELINE_STUDIO_ADOPTION.md). Reused original timeline/clip/undo/redo/zoom/split/caption code instead of adding a second video renderer. User-facing React timeline contains scene, caption, licensed music and voice/SFX tracks, playhead/zoom, split/trim/reorder and undo/redo. Unsupported independent effects/gain are disabled. Feature2 creative package preview is strictly review-locked and not a server approval. New F2-to-F5 handoff is source-only and explicitly cannot run paid model inference. Original upstream's own CI at pinned commit passed lint, typecheck, build; original app was not locally launched. Current exact-head CI and future hosted/real licensed media QA must be observed separately.
+
+## 2026-10-29 F4-04 duplicate renderer parity handoff
+
+Stacked Feature4-only branch `feat/feature4-encoded-duplicate-parity-20261029` adds separately encoded 30s/540p synthetic duplicate of the genuine Timeline Studio JS action through the **same** trusted Python compiler and HyperFrames renderer, with SHA-linked four-point FFmpeg pixel-restart check and negative regressions. Split/reorder remains an independent unchanged regression. This is technical-only mock evidence; 31-task registry F4-04 remains IN PROGRESS until accepted coordinator main merge/postmerge CI, and private retailer quality/rights/live UI remain blocked. The coordinator, not this branch, owns shared docs, #650 packaging, Azure #249 and hosted integration. No paid service, GPU, PROD or WineShopPOS.
~~~~

### video-engine/FEATURE4_POINTER_LIFECYCLE_HANDOFF_20261029.md
~~~~diff
@@ -0,0 +1,15 @@
+# Feature4 F4-10 timeline pointer lifecycle handoff — 2026-10-29
+
+**Status:** IN PROGRESS, not integrated DONE. Branch: `feat/feature4-drag-tenant-fence-20261029` (separate from F4-04, F4-13/F4-15, F4-14 branches, all based on existing #322 head `e32a8da61a6272666d757b6c51b0ec2576d7602f`).
+
+## Exact source change
+
+The existing modified MIT Timeline Studio caption-boundary resize registered a global pointer-up callback that could outlive the selected shop, approved-direction lock, or original draft. We now cancel an outstanding resize on draft/tenant/approval updates and unmount; require the original primary pointer ID and left button; remove listeners on pointercancel and completion; reject any completion if the live draft/approval differs from the pointer-down snapshot. This stops stale client edits and overlapping listeners, without claiming backend authorization: the trusted compiler still controls tenant/rights.
+
+Actual React/Playwright fixture asserts no `onChange` after a synthetic tenant switch, an approval lock introduced during drag, or pointercancel then late release. Existing legal split/resize logic and no-freeform-FX contract are unchanged. Fixture is mocked, no hosted sign-in, actual customer media or real encoded-frame equivalence.
+
+## Verification / release
+
+Run existing Playwright timeline suite (and full four-job CI at batch boundary); coordinator reviews/merges to latest main with fresh postmerge 4/4 before counting any accepted task. F4-10 requires additional manual touch, accessibility and signed DEV acceptance and therefore remains IN PROGRESS after this source hardening.
+
+No paid GPU/AI, PROD, hosted migrations, WineShopPOS or user-facing media.
~~~~

### video-engine/FEATURE4_STAGING_INTEGRITY_HANDOFF_20261029.md
~~~~diff
@@ -0,0 +1,19 @@
+# Feature4 staged-byte integrity handoff — 2026-10-29
+
+**Task IDs:** F4-13 (private input integrity), F4-15 (worker failure/race negative tests). Both remain **IN PROGRESS**, not integrated DONE.
+
+**Owned branch:** `feat/feature4-stage-input-integrity-20261029`, forked at Feature4 draft #322 SHA `e32a8da61a6272666d757b6c51b0ec2576d7602f`. Does not alter the other isolated F4-04 duplicate-parity branch.
+
+## Source-only change
+
+The existing authenticated worker's downloaded, reviewed private media staging files are now SHA-256 and stable-fstat checked using no-follow regular-file opens. The worker compares each original before and after CPU rendering, refusing changed, appended, replaced or symlink-swapped inputs **before private output upload and claim finalization**. The existing per-claim total staged-byte budget, tenant authorization, lease fence and one-charge coordinator RPC remain unchanged.
+
+Existing injected renderer tests now cover three negative mutation classes (same-run overwrites, appends and symlink swaps) and require no media upload or completion, plus permanent input-error receipt. The tests remain deliberately fake renderer and synthetic source fixtures, NOT genuine Azure/Supabase JWT/RLS, commercial original-byte grant verification, source identity, licensing, rights approval or live retry success.
+
+## Verification and integration
+
+- Required tests: `python3 -m unittest tests.media.test_feature4_worker_handoff -v` or the repository's `video-engine/ci.sh`; at batch boundary require 4/4 branch and PR checks.
+- Coordinator must review and integrate into main with **fresh 4/4 main CI** before marking either F4 task DONE. Update original 31-item task ledger and `coordination/task_progress.json` only through coordinator after accepted integration.
+- Other blockers: F4-22/ISSUE-650 coordinator packaging, F4-29/ISSUE-249 Azure HTTP, F4-30 real two-tenant signed DEV E2E. These do not invalidate this independent source work.
+
+**Safety:** No GPU, paid inference, hosted SQL, PROD, customer media, new services or WineShopPOS.
~~~~

### video-engine/FEATURE4_TIMELINE_STUDIO_ADOPTION.md
~~~~diff
@@ -148,3 +148,6 @@ edit controls despite working seek. Commits `4f8c260f`, `ca281aac`,
 `a552dfa8`. Browser/source CI at exact head required before claiming
 verified. This is not a true frame-accurate decoded preview or mobile human
 usability approval; real hosted signed-media preview remains a separate gate.
+
+## 2026-10-30 — Server-only F4-06 bounded audio channel levels; UI control still disabled
+A new **optional trusted** `creative_reel_v1.audio_mix` scalar map is lowered through the existing reviewed source contract to native HyperFrames data-volume for source-video sound, music bed, licensed narration and 2s SFX. Bounded linear gains, original music-under-voice ducking safety cap and rights checks remain mandatory; default render mix is unchanged. The adopted Timeline Studio **still disables** browser gain automation and arbitrary per-clip envelopes: do not enable controls before an authenticated, shop-scoped reviewed change set and actual audio render/FFmpeg decoding prove the same gain. No new source audio, licensing, F2 speech alignment or voice synthesis is inferred. Detailed contract/negatives in `FEATURE4_AUDIO_GAIN_HANDOFF_20261030.md`.
~~~~

### video-engine/creative_contract.py
~~~~diff
@@ -11,7 +11,10 @@
 from uuid import UUID
 
 from feature4_caption_track import checked_caption_cues
-from professional import VideoPlanError, compile_composition, validate
+from professional import (
+    VideoPlanError, compile_composition, validate, checked_audio_mix,
+    SUPPORTED_ANIMATIONS, SUPPORTED_TRANSITIONS,
+)
 
 CONTRACT_VERSION = "creative_reel_v1"
 UUID_PATTERN = re.compile(r"^[0-9a-fA-F-]{36}$")
@@ -22,8 +25,9 @@
            "retailer": {"image", "poster", "video", "logo", "audio"},
            "stock": {"image", "video", "audio"}}
 PRESETS = {"streetwear", "cinematic", "festival"}
-ANIMATIONS = {"subtle_zoom", "fade", "slide", "pop", "glow"}
-TRANSITIONS = {"fade", "slide", "cut"}
+# Reuse the actual trusted HyperFrames compiler allowlists: no UI/backend drift.
+ANIMATIONS = SUPPORTED_ANIMATIONS
+TRANSITIONS = SUPPORTED_TRANSITIONS
 
 
 class CreativeContractError(VideoPlanError):
@@ -90,7 +94,7 @@ def render_inputs(request, media_manifest, *, allow_synthetic_test=False):
     require_fields(request, {
         "version", "shop_id", "campaign_id", "video_job_id", "idempotency_key",
         "script", "brand", "scenes", "template", "duration_seconds", "output",
-        "music_asset_id", "music_source", "voiceover_asset_id", "voiceover_source", "beat_grid", "edit_plan",
+        "music_asset_id", "music_source", "voiceover_asset_id", "voiceover_source", "audio_mix", "beat_grid", "edit_plan",
         "allow_image_fallback", "mode",
     }, {"version", "shop_id", "campaign_id", "video_job_id", "idempotency_key",
         "script", "brand", "scenes", "template", "duration_seconds", "output"}, "reel request")
@@ -223,6 +227,15 @@ def render_inputs(request, media_manifest, *, allow_synthetic_test=False):
         if scene.get("mute_source") is not None:
             base["mute_source"] = scene["mute_source"]
         lowered.append(base)
+    mix = checked_audio_mix(
+        request.get("audio_mix"), has_music=sound_id is not None,
+        has_voice=voice_id is not None,
+        has_source=any(
+            x.get("asset_id") is not None
+            and media_manifest["assets"][x["asset_id"]]["kind"] == "video"
+            and not x.get("mute_source", False) for x in lowered),
+        has_sfx=any(x.get("sfx_asset_id") for x in lowered),
+    )
     if logo_id:
         used_ids.add(logo_id)
     if sound_id:
@@ -257,7 +270,8 @@ def render_inputs(request, media_manifest, *, allow_synthetic_test=False):
                                 if "secondary_color" in brand else {})},
                    "logo_asset_id": logo_id,
                    "music_asset_id": sound_id,
-                   "voiceover_asset_id": voice_id}
+                   "voiceover_asset_id": voice_id,
+                   **({"audio_mix": mix} if mix else {})}
     if request.get("beat_grid") is not None:
         composition["beats"] = copy.deepcopy(request["beat_grid"])
     if captions is not None:
~~~~

### video-engine/demo_feature4_edited_reel.py
~~~~diff
@@ -20,7 +20,7 @@
 sys.path.insert(0, str(ROOT / "tests" / "media"))
 sys.path.insert(0, str(ROOT / "video-engine"))
 from test_feature4_cross_feature import CreativeReelTests  # noqa: E402
-from test_feature4_editor_to_render_contract import edited_draft  # noqa: E402
+from test_feature4_editor_to_render_contract import edited_draft, duplicated_draft  # noqa: E402
 from test_feature4_intent_compiler import pair  # noqa: E402
 from feature4_intent_compiler import compile_approved_storyboard  # noqa: E402
 from creative_contract import compile_creative_reel  # noqa: E402
@@ -43,15 +43,24 @@ def _run_ffmpeg(*args):
 }
 
 
-def make_edited_project(destination: Path, *, width: int = 540) -> dict:
+def make_edited_project(destination: Path, *, width: int = 540, operation: str = "split_reorder") -> dict:
     if width not in (540, 1080):
         raise ValueError("Only reviewed private portrait dimensions supported")
     if destination.exists() and any(destination.iterdir()):
         raise ValueError("Refusing to replace an existing project/media directory")
+    if operation not in ("split_reorder", "duplicate"):
+        raise ValueError("Unsupported editor operation")
     original, trusted = pair()
-    draft = edited_draft()
-    if draft["scenes"][0]["sfx_asset_id"] != "musicowned":
+    draft = edited_draft() if operation == "split_reorder" else duplicated_draft()
+    source_scene = 0 if operation == "split_reorder" else 1
+    if draft["scenes"][source_scene].get("sfx_asset_id") != "musicowned":
         raise ValueError("Expected approved source-audio edit fixture")
+    if operation == "duplicate":
+        if (len(draft["scenes"]) != 4 or
+                [scene["duration"] for scene in draft["scenes"]] != [10, 5, 5, 10] or
+                any(draft["scenes"][i].get("trim_start", 0) != 0 for i in (1, 2)) or
+                "sfx_asset_id" in draft["scenes"][2]):
+            raise ValueError("Untrusted duplicate did not preserve restart/SFX contract")
     draft["output"].update(width=width, height=width * 16 // 9)
     bundle = compile_approved_storyboard(draft, trusted)
     fixture = CreativeReelTests(methodName="test_diwali_30s_brand_logo_motion_poster_exact_offer")
@@ -86,13 +95,20 @@ def make_edited_project(destination: Path, *, width: int = 540) -> dict:
         page = (compiled / "index.html").read_text(encoding="utf8")
         # Hard fail if the editor's real SFX/clip source trims or exact offer
         # would be dropped by the renderer. Matches real generated HTML.
+        # Split/reorder plays at source inpoints 0 and 4; duplication must
+        # restart the same source twice from inpoint 0. The final encoded
+        # duplicate parity check independently samples the actual pixels.
+        inpoints_ok = (('data-media-start="4"' in page and
+                        'data-media-start="0"' in page)
+                       if operation == "split_reorder" else
+                       'data-media-start="4"' not in page and
+                       page.count('data-media-start="0"') >= 2)
         if (page.count('class="footage clip"') != 2 or
                 page.count('id="sfx') != 1 or
-                'data-media-start="4"' not in page or
-                'data-media-start="0"' not in page or
+                not inpoints_ok or
                 '20% OFF' not in page or 'Visit Our Store' not in page or
-                'id="intro-logo"' in page or  # video-led: no face-covering center logo
-                'id="brand-logo"' not in page or  # small corner brand is retained
+                (operation == "split_reorder" and 'id="intro-logo"' in page) or
+                'id="brand-logo"' not in page or
                 "90% OFF" in page):
             raise AssertionError("Actual edited HyperFrames composition diverged from approved timeline")
         audit = bundle["lineage"]
@@ -103,7 +119,8 @@ def make_edited_project(destination: Path, *, width: int = 540) -> dict:
             "project": str(compiled), "seconds": 30, "width": width,
             "scenes": len(draft["scenes"]), "asset_ids": sorted(generated),
             "video_clip_count": 2, "approved_sfx_count": 1,
-            "source_video_inpoints_seconds": [0, 4],
+            "source_video_inpoints_seconds": [0, 4] if operation == "split_reorder" else [0, 0],
+            "editor_operation": operation,
             "approved_offer": "20% OFF", "real_ai_motion": False,
             "commercial_fashion_realism_accepted": False,
             **OWNER_VISUAL_VERDICT,
@@ -116,8 +133,10 @@ def main():
     parser = argparse.ArgumentParser(description=__doc__)
     parser.add_argument("project")
     parser.add_argument("--width", type=int, default=540, choices=(540, 1080))
+    parser.add_argument("--operation", choices=("split_reorder", "duplicate"),
+                        default="split_reorder")
     args = parser.parse_args()
-    print(json.dumps(make_edited_project(Path(args.project), width=args.width)))
+    print(json.dumps(make_edited_project(Path(args.project), width=args.width, operation=args.operation)))
 
 
 if __name__ == "__main__":
~~~~

### video-engine/feature4/ORIGINAL_723_PROVENANCE_20261117.md
~~~~diff
@@ -0,0 +1,14 @@
+# Original #723 F4-04 proof preservation — 2026-11-17
+
+- Original head: `e71a4e401e6634120f3a4f5e85571b4f807b88f8`. Original change contains fail-closed exact 72x128 grayscale buffer length/type validation plus four negative malformed frame regressions, now ported to this surviving #779 source branch without changing existing split/reorder/duplicate semantics.
+- Original #723 worker per-download authorization/lease protection was already recovered in newer CURRENT Feature4 parent #322, and per-download negative tests retained there. Do not restore the older #723 worker over newer staged SHA/inode rights checks.
+- Historical original tracker notes preserved verbatim below; original PR/source remains available after any unmerged closure.
+- This is source integration, **F4-04/F4-15 IN PROGRESS** not accepted main/hosted DONE; #779 still conflicts with newer #322 and cannot bulk merge. Exact-head 4/4 and safe source reconciliation are required.
+- GPU/paid inference/PROD/WineShopPOS untouched.
+
+> ## 2026-10-30 — F4-04 decoded frame integrity, stacked review PR #723
+> 
+> - Existing draft PR #322 at `e32a8da61a6272666d757b6c51b0ec2576d7602f` was verified as **DRAFT/UNMERGED**. The prior exact-head PR workflow #40937402426 failed; no green merged-base acceptance is claimed. Canonical `coordination/task_progress.json` has zero reviewed DONE events.
+> - Feature4-owned stacked [PR #723](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/723) hardens `feature4_edited_export_qa._luma_delta`: strict 72x128 grayscale byte-length and type validation prevents silent `zip` truncation of malformed decoded frames. Added four negative cases (short, long, non-byte and empty frames) in `tests/media/test_feature4_edited_export_qa.py`.
+> - **Status F4-04: IN PROGRESS / SOURCE CHANGE PROPOSED, NOT DONE.** No test result is asserted until exact-head CI or a reproducible targeted run finishes. Existing 30s fixture remains an illustrated MOCK technical regression, not commercial product/garment/voice approval. Duplicate-clip encoded parity, actual human visual review and full renderer equivalence remain open.
+> - Coordinator task-status proposal (not an authoritative shared event): `{task_id: F4-04, proposed_status: IN_PROGRESS, evidence_pr: 723, source_only: true, accepted_integrated_done: false}`. Coordinator must review and write `coordination/task_progress.json` only after accepted integration and fresh main 4/4 CI.
~~~~

### video-engine/feature4/ORIGINAL_735_PROVENANCE_20261117.md
~~~~diff
@@ -0,0 +1,12 @@
+# Feature4 F4-04 original #735 duplicate editor project contract — 2026-11-17
+
+- Original PR #735 head `8f80480f9d6d27cb781d6389a423ee843a67e8d3` had independent real JS duplicate → trusted Python compiler → HyperFrames project regression `tests/media/test_feature4_duplicate_project.py`, absent from surviving #779.
+- Restored its single real-project assertion with minimal adaptation to **current** approved API: `make_edited_project(operation="duplicate")` and `editor_operation`. The test still checks two 0-second original video inpoints, exactly two media clips and one approved source-audio, HTML track composition, bad offer suppression, and explicit OWNER_REJECTED/false publication/false AI claims.
+- Current #779 code already physically encodes and QA-checks the independent 30s duplicate path in `hyperframes/ci-smoke.sh`, **stronger than original #735 opt-in** path, and current `feature4_edited_export_qa.py` supports `operation="duplicate"` with distinct encoded replay proof.
+- Source-only; current #779 has stale parent conflicts and still needs source CI/current parent integration/hosted acceptance; original F4-04 IN PROGRESS. No GPU, paid provider, cloud/PROD/WineShopPOS changes.
+
+## Preserved original tracker notes
+> ## 2026-10-30 — F4-04 duplicate-editor encoded QA source (stacked PR #735)
+> - Source-only extension of the existing real Timeline Studio JS `studioDuplicate` → trusted Python compiler → HyperFrames fixture generator, with separate `--edit-mode duplicate` and a fail-closed two-timestamp-per-scene decoded pixel comparison. Frozen/replayed, wrong-duration and mutated-input negative unit tests added. This is not a second generated AI video or approved retailer media.
+> - **Execution gate:** `FEATURE4_DUPLICATE_PARITY_CI=1 bash video-engine/hyperframes/ci-smoke.sh` is required to render and inspect the new actual encoded duplicate MP4. The default 4-job CI runs the new Python tests but deliberately does **not** spend extra CPU encoding time on the opt-in video. Do not mark F4-04 integrated DONE from source or unit tests alone.
+> - Dedicated feature-owned branch `feat/feature4-duplicate-encoded-qa-20261030`, stacked draft [PR #735](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/735) onto existing Feature4 draft PR #322. Coordinator must review and merge to main, then verify fresh main 4/4. The current external ZIP #650 and real approved-media gates remain unchanged. No GPU, paid model, PROD, Supabase SQL or WineShopPOS changes.
~~~~

### video-engine/feature4/ORIGINAL_745_773_PROVENANCE_20261117.md
~~~~diff
@@ -0,0 +1,16 @@
+# Feature4 F4-04 original #745/#773 trace — 2026-11-17
+
+- Original #745 HEAD `bd9088ebe8c401441e0a27e66f85e648ed8d24d7`: 3/17-second intra-clip moving-source encoded probes and frozen negative cases.
+- Original #773 HEAD `31dd9d72e8b059eaa92005a596cad7aa7acdac6c`: 5/13/15/21-second near-cut decoded scene-family comparisons, rejecting early/missing/delayed segments.
+- Both distinct QA requirements and regression tests have been ported to surviving #779 F4-04 split/reorder path. Duplicate-operation remains independently 4-frame and unchanged. Source SHA is verified **after all** the extra decoded frames, and the original stricter exact grayscale length/type test from #723 remains active.
+- The positive proof reports separate motion/boundary metrics and explicitly `commercial_release_eligible=false`. No hosted video/human product signoff/actual frame-exact trim proof. Original task F4-04 remains IN PROGRESS, not main/hosted DONE. Full exact-head CI / video integration with current parent #322 pending. No paid GPU/Azure/PROD/WineShopPOS changes.
+
+## Original #745 tracker notes
+> ## 2026-10-30 — F4-04 frozen-clip regression (source-only, awaiting CI)
+> - Dedicated source branch `feat/feature4-encoded-edit-motion-qa-20261030` adds two actual FFmpeg decoded interior video samples at 3s and 17s to the existing 2/7/16/24s encoded parity gate. The QA now fails closed if either supposed moving clip is frozen, even when four different scene-family images could otherwise pass. Adds negative unit tests for first/second/both frozen clips and explicit technical-only deltas in the SHA-linked receipt.
+> - No new render, network fetch, GPU, model inference, cloud deployment or sample publication is required. Existing 30s media CI already exercises this validator. Exact-head CI and review remain necessary; do **not** mark integrated DONE. Coordinator owns main merge, shared task-status events and postmerge 4/4 checks. Separate issue #650 Python ZIP member guard remains coordinator-owned; do not bypass it.
+
+## Original #773 tracker notes
+> ## 2026-10-30 — F4-04 encoded near-cut parity (separate reviewed staging branch)
+> - The existing 30s/540p FFmpeg-decoded edited output proof now samples 5, 13, 15 and 21 seconds in addition to 2, 7, 16 and 24 seconds. It rejects late product-photo entry, early photo exit, late trimmed-video entry and late offer entry, using conservative relative luma scene-family checks. It still **does not** establish exact trim frame, fade duration, product identity or commercial visual approval.
+> - Regression tests add four boundary-mutation cases and preserve source SHA, symlink, replay, scene-order, duration and immutable-media negatives. The existing synthetic illustrated fixture remains OWNER_REJECTED; no new user-facing sample was made.
~~~~

### video-engine/feature4/ORIGINAL_753_PROVENANCE_20261117.md
~~~~diff
@@ -0,0 +1,15 @@
+# Source preservation: original F4-02 #753 — 2026-11-17
+
+Original PR head: `eeec8c363627b1085cfff33dcc62d85a57973800`. Source was F4-02 v2 minute visibility receipts; surviving #779 currently requires *v3* full-reel continuous near-black scan. Only the missing **contiguous positive finite 12-window coverage** guard was ported, together with original four fixture tests adapted for v3 required fields. Never restore the older v2 schema over v3. Original distinct tracker/handoff text follows.
+
+## Original tracker excerpt
+> ## 2026-10-30 — F4-02 additional negative coverage (source proposal)
+> A dedicated stacked branch proposes a fail-closed `feature4_minute_quality_receipt.validate_visibility_evidence` contiguous-window check and deterministic negative tests. It prevents a 60-second QA report when both provenance and visibility JSON consistently skip or overlap time, or contain nonfinite/zero-length scene windows. **F4-02 remains IN PROGRESS** until exact-head CI, the actual updated private 60s media+SHA+report chain, coordinator integration and acceptance. F4-01 and F4-12 remain unverified for the new native encoded minute; no production approval is implied. Shared blocker #650 remains with coordinator.
+
+## Original handoff excerpt
+> ## 2026-10-30 — F4-02 full-minute visibility QA integrity (proposed, not integrated)
+> - Dedicated review branch `fix/feature4-visibility-contiguous-windows-20261030` based on Feature4 PR #322 head `e32a8da61a6272666d757b6c51b0ec2576d7602f`. New guard in `feature4_minute_quality_receipt.py` requires 12 finite, positive, contiguous scene windows spanning exactly 60 seconds before a technical-only receipt can pass; matching forged provenance and sample JSON may not omit or overlap time.
+> - Added `tests/media/test_feature4_visibility_window_integrity.py` for contiguous positive, gapped/overlapping forged JSON, incomplete last window, NaN/infinite/nonpositive duration, and unexpected metadata. This is deterministic mocked JSON regression only, **not** a newly rendered 60s video or approved product media.
+> - Integration and QA pending: targeted Python/uv and exact-head four-job CI, coordinator review into #322/main, a new private native 60s encoded render and actual human visual acceptance. The existing Python ZIP >120 failure is coordinator-owned issue #650; no guard relaxation, GPU/PROD/paid inference, hosted SQL, or WineShopPOS changes.
+
+Still **F4-02 IN PROGRESS**. No actual approved private 60s render, complete human visual acceptance, legal rights, main merge or PROD. CPU/mock-only; GPU/paid/cloud/WineShopPOS untouched.
~~~~

### video-engine/feature4/ORIGINAL_784_PROVENANCE_20261117.md
~~~~diff
@@ -0,0 +1,10 @@
+# Feature4 F4-10 #784 original cancelled-drag preservation — 2026-11-17
+
+Original head `55832723c784bc08694ea73d4a9cd6ba72452c65` (stale DRAFT). Source-only guard clears `dragFrom` on `dragend`, rejects unrelated/external drops, invalid old indices and locked approvedDirection, preventing a cancelled clip drag from silently reordering the next render. Original Playwright browser DragEvent regression was ported with the existing newer fixture and guard. Newer bounded playhead seek and pointer-resize tenant fencing were *not* overwritten.
+
+> ## 2026-10-30 — F4-10 cancelled native drag safety (review pending)
+> - Dedicated stacked branch `fix/feature4-cancelled-drag-reorder-20261030-run3` against draft PR #322 head `e32a8da61a6272666d757b6c51b0ec2576d7602f` proposes clearing clip drag state on `dragend`, rejecting unrelated/external drops, and rejecting synthetic drag start while an approved direction is locked. Previously a cancelled drag left `dragFrom.current` stale and a later drop could unexpectedly reorder the draft.
+> - Added Playwright negative regression using actual browser `DragEvent` and render-submission ordering; **tests/CI not yet verified at this checkpoint**. No approval, production media, live deployment, paid GPU or shared coordinator files touched.
+> - This is a F4-10 mobile/browser safety subtask, **not** full task completion. Await exact-head CI and coordinator review; retain 0 integrated DONE unless accepted on main with 4/4.
+
+Not main/hosted DONE. Original F4-10 remains IN PROGRESS; #779 must be reconciled into current #322 with exact-head four-job CI, real signed DEV identity and review. GPU/paid/cloud/PROD/WineShopPOS OFF.
~~~~

### video-engine/feature4/ORIGINAL_808_816_PROVENANCE_20261117.md
~~~~diff
@@ -0,0 +1,43 @@
+# Feature4 #808/#816 historical source notes — preserved on #779 (2026-11-17)
+
+**ARCHIVE ONLY — does not merge source into main, run a live 60s render, or accept tasks.** Original #808 F4-11 continuous black-hold and #816 F4-14 CPU three-profile evidence are source-in-progress drafts stacked on obsolete parent refs. Their core code/test source is preserved unchanged in surviving OPEN source consolidation PR #779: #808 5/5 code/test/handoff paths identical Git blobs (its tracker differs); #816 4/4 code/test/profile handoff paths identical Git blobs (tracker and CPU benchmark handoff differ). This archive preserves missing historical lines without reverting newer source or claiming quality/commercial acceptance.
+
+### Original #808: `video-engine/FEATURE4_31_TASK_PARALLEL_TRACKER_20261029.md`
+- Original head: `81023702673f48730d85e4b33fae26936e8b30cd`
+- Original Git blob: `39a9ecf11255579b6a7447238f59ec15e4e2351a`
+- Surviving tracker Git blob before archive: `30a6b8b2fb0973cf13bad4766b0133b4069a8549`
+- Unretained original lines (3, quoted verbatim):
+
+> ## 2026-10-30 — F4-11 independent continuous full-video black hold QA (draft #808)
+> - After consolidated source batch draft #779, F4-11 adds one FFmpeg continuous decode scan of the actual encoded 15/30/60s video, denying near-black holds of at least 0.65s that all five sampled interior frames can miss. The v3 60s SHA-linked source receipt requires this scan and explicitly disclaims shorter flashes, lettering/garment identity/rights and human approval; exact test-only 15s synthetic black-gap regression encodes a real 0.8s hidden hold. PR #808 is **draft, not merged**, dependency unchanged.
+> - First exact-head media CI #41052416541 caught an over-escaped raw regular expression while all other jobs passed; corrected parser and negative regression test in this follow-up source repair. Main integration/actual updated 60s technical and human acceptance still pending; F4-11 remains IN PROGRESS.
+
+### Original #816: `video-engine/FEATURE4_31_TASK_PARALLEL_TRACKER_20261029.md`
+- Original head: `d01e3c716b4f651809d645684c921c6f0413c343`
+- Original Git blob: `c8bfbf92538923e11dfe27174240fdfc230cdaa7`
+- Surviving tracker Git blob before archive: `30a6b8b2fb0973cf13bad4766b0133b4069a8549`
+- Unretained original lines (7, quoted verbatim):
+
+> ## 2026-10-30 — F4-11 independent continuous full-video black hold QA (draft #808)
+> - After consolidated source batch draft #779, F4-11 adds one FFmpeg continuous decode scan of the actual encoded 15/30/60s video, denying near-black holds of at least 0.65s that all five sampled interior frames can miss. The v3 60s SHA-linked source receipt requires this scan and explicitly disclaims shorter flashes, lettering/garment identity/rights and human approval; exact test-only 15s synthetic black-gap regression encodes a real 0.8s hidden hold. PR #808 is **draft, not merged**, dependency unchanged.
+> - First exact-head media CI #41052416541 caught an over-escaped raw regular expression while all other jobs passed; corrected parser and negative regression test in this follow-up source repair. Main integration/actual updated 60s technical and human acceptance still pending; F4-11 remains IN PROGRESS.
+> ## 2026-10-30 F4-14 three-length CPU evidence aggregator (NEW source, CI pending)
+> Draft stack on F4-11 #808, based on exact 4/4 head `81023702673f48730d85e4b33fae26936e8b30cd`. The new `feature4_cpu_matrix.py` requires three **real** 15/30/60 original 1080×1920/24fps H264/AAC MP4 files and their corresponding independently measured `benchmark_render.py` receipts. It reuses F4-03's stable hash / actual ffprobe verification, rejects swapped media, wrong duration, forged benchmark SHA/bytes, missing or altered Git checkout claim, false Azure/cloud/commercial flags, non-finite/missing timing/RSS data, path traversal and symlinked JSON. No media render is executed by this aggregator; unit tests use explicit fake probe, not real GPU/quality evidence.
+> `benchmark_render.py` now embeds a **declared local Git SHA**, not an independently signed Actions attestation. The matrix aggregates source-only 15/30/60 sampled CPU/RSS observations and marks `cloud_budget_accepted=false`, `code_commit_attested_by_ci=false`, `human_visual_approval=false`. It **does not** claim a matrix actually ran: required three same-code real encoded outputs and measured reports do not yet exist together. F4-14 remains IN PROGRESS; later opt-in full 60s CPU run is required, never automatically trigger repeated lengthy GPU/CPU or public samples.
+> CI and coordinator review/main merge/fresh main 4/4 must be verified before an accepted source task. No Azure Functions/PROD, priced AI, SQL, WineShopPOS.
+
+### Original #816: `video-engine/FEATURE4_CPU_BENCHMARK_HANDOFF_20261029.md`
+- Original head: `d01e3c716b4f651809d645684c921c6f0413c343`
+- Original Git blob: `c171b0fbd341c6610b165c42fd7007dd1e0c85eb`
+- Surviving tracker Git blob before archive: `6e4040b0977b579dce4bd25a8fcc242bad729548`
+- Unretained original lines (4, quoted verbatim):
+
+> ## 2026-10-30 F4-14 three-length CPU evidence aggregator (NEW source, CI pending)
+> Draft stack on F4-11 #808, based on exact 4/4 head `81023702673f48730d85e4b33fae26936e8b30cd`. The new `feature4_cpu_matrix.py` requires three **real** 15/30/60 original 1080×1920/24fps H264/AAC MP4 files and their corresponding independently measured `benchmark_render.py` receipts. It reuses F4-03's stable hash / actual ffprobe verification, rejects swapped media, wrong duration, forged benchmark SHA/bytes, missing or altered Git checkout claim, false Azure/cloud/commercial flags, non-finite/missing timing/RSS data, path traversal and symlinked JSON. No media render is executed by this aggregator; unit tests use explicit fake probe, not real GPU/quality evidence.
+> `benchmark_render.py` now embeds a **declared local Git SHA**, not an independently signed Actions attestation. The matrix aggregates source-only 15/30/60 sampled CPU/RSS observations and marks `cloud_budget_accepted=false`, `code_commit_attested_by_ci=false`, `human_visual_approval=false`. It **does not** claim a matrix actually ran: required three same-code real encoded outputs and measured reports do not yet exist together. F4-14 remains IN PROGRESS; later opt-in full 60s CPU run is required, never automatically trigger repeated lengthy GPU/CPU or public samples.
+> CI and coordinator review/main merge/fresh main 4/4 must be verified before an accepted source task. No Azure Functions/PROD, priced AI, SQL, WineShopPOS.
+
+## Next
+- Independently test and reconcile #779 into the current F4 parent #322, preserving its newer lease/rights/security implementation and F4-05/11/15 work.
+- Do NOT close #808/#816 until original source/negative tests, these preserved notes, review/CI and surviving references are checked; do not mark original F4-11/F4-14 DONE by PR closure.
+- Paid AI, GPU, Azure/SQL/PROD and WineShopPOS remain untouched.
~~~~

### video-engine/feature4/ORIGINAL_830_PROVENANCE_20261117.md
~~~~diff
@@ -0,0 +1,6 @@
+# Feature4 F4-06 original audio gain integration checkpoint — 2026-11-17
+
+- Original #830 head `a86884dd1d676719b9000515dec0cdfe4df06ffb` stacked on old #828 contains a narrowly bounded four-channel gain contract, renderer wiring, trusted cross-feature source lowering, and negative tests for inert, missing, unknown, NaN, float-step, string and bool controls.
+- Source-backed directly into surviving #779 as **six original unchanged Git file blobs** (Python 4 source/tests and two handoffs); no whole old-parent merge, no JS UI gain control enabled.
+- Audio output fixed `data-volume` limits and preexisting music ducking remain required. This source-only integration does not establish actual decoded final AAC gain parity, hosted tenant authorization, audio listening quality, music license, publication signoff, main merge or original F4-06/F4-07 task DONE.
+- Follow-up: re-validate #779 exact-head source tests and selectively reconcile into newer main-targeted F4 parent #322 while preserving its footage transitions, lease and all-asset rights checks. GPU/paid/PROD/WineShopPOS OFF.
~~~~

### video-engine/feature4/RUN_CHECKPOINT_F4_07.md
~~~~diff
@@ -0,0 +1,44 @@
+# Feature4 F4-07 source-only checkpoint — 2026-10-30
+
+- **Task:** F4-07 actual audio fades/ducking and final QA. This PR is a *partial security/reliability hardening*, not the full task or an accepted output.
+- **PR:** #845, draft, stacked onto Feature4 parent draft #322 (`feat/feature4-professional-video-studio`). Pre-checkpoint head `e45a9bc833584bb85f74c0993cf17ac9e9454a89`.
+- **Changes:** `video-engine/feature4_audio_master.py` now checks a new private JSON proof path before running local FFmpeg and creates the receipt exclusively; `tests/media/test_feature4_audio_master.py` checks existing proof causes no mastering and rejects symlink parent/non-JSON destinations.
+- **Verification:** Python 4/4 isolated *source-equivalent* preflight tests passed in temporary local copy. These are not full repository tests. Exact-checkout tests, FFmpeg regression and 4-job exact-head CI are **not verified**; inspect after this checkpoint commit.
+- **Why:** Prior CLI ran mastering and created private output before discovering an existing proof path, leaving an unreceipted output. New preflight denies that known unsafe case. Concurrent proof creation after preflight still requires error/cleanup review; do not claim fully atomic output/report transaction.
+- **Next:** F4-07: inspect audio-master report-write failure/cleanup semantics and real fade/ducking test coverage without introducing unsupported UI gain automation. Alternative independent F4-09: test currently disabled unsupported controls and history correctness.
+- **Ownership:** Feature4-owned code/test/handoff only. Coordinator controls shared task status, PR merge, fresh main CI, hosted validation and commercial release. F2 licensed voice/audio remains required. GPU OFF; no paid model, PROD, Azure deployment, SQL or WineShopPOS changes.
+
+## Continuation — receipt failure atomicity hardening (2026-10-30)
+
+- **Task:** F4-07, partial source-only reliability fix. No voice/music license or final mix quality acceptance.
+- **Existing stacked PR:** #845, base `feat/feature4-professional-video-studio` (draft parent #322). No new PR or duplicate work.
+- **Code/test commits before checkpoint:** `0720a49d6cbc7e9d60f7309c051eb1b88d6f2343`, `30f4efcf4cf027fa5bf8a8b634519054cd06a8be`, `49189f7bae3c00f3f967377e6e498555769df00f`, `b816782c3b8578f63203e31f40add544e5517390`.
+- **Changed files:** `video-engine/feature4_audio_master.py`, `tests/media/test_feature4_audio_master.py`. If an exclusive JSON receipt write fails after MP4 mastering, the CLI now removes only a matching unchanged output SHA; it also removes a partially written receipt only if the same inode created by this process still exists. Replaced/different output is not deleted. Negative tests inject proof-open failure, post-master output replacement, and partial receipt-write failure.
+- **Verification:** Changes committed through connected GitHub and source reread; exact checkout targeted Python tests **not run** in this execution (GitHub source unavailable to local test runner). GitHub PR-triggered workflow lookup at pre-checkpoint head `b816782c3b8578f63203e31f40add544e5517390` returned no runs, and combined statuses returned none; **full 4/4 CI not verified**. Recheck exact new head after this checkpoint push; never mark PR-ready/integrated without checks.
+- **Remaining F4-07:** actual licensed narration/music, multiple realistic duck/fade profiles, source-authorized commercial signoff, and exact-head CI. The new failure-path tests are mocked, not real MP4 QA.
+- **NEXT:** F4-09 independent UI history/disabled-control negative-path regression, or F4-06 renderer-backed multi-track levels only after actual semantics verified. Do not duplicate open PR #838 F4-08 or other owned PRs. Coordinator owns canonical task status, review/merge, and fresh main 4/4.
+- **Cost/security:** GPU OFF, no cloud/PROD/SQL writes, no WineShopPOS or customer media.
+
+## Next-task ownership reconciliation
+
+- Rechecked candidate **F4-09**: existing open PR **#769** already implements bounded history; do not create a competing branch.
+- Rechecked candidate **F4-06**: existing open PRs **#830** (independent gain contract) and **#739** (truthful fixed-gain preview); do not duplicate those implementations.
+- F4-05 already has PRs #711/#822; F4-15 has multiple in-flight branches. The next run should first inspect the freshest exact heads and focus on **F4-07 exact-checkout tests/CI and receipt failure semantics** or another truly unclaimed scoped task. No atomic worktree lease was claimed.
+- **Checkpoint commit context:** code/test head `b816782c3b8578f63203e31f40add544e5517390`; previous checkpoint commit `5bee81aab0e4e26e76d3a72b0ef3ceb4bdb6d558`. Recheck the final head after this update.
+
+## Continuation — private proof confidentiality and durability (2026-10-30)
+
+- **Task:** F4-07, partial security/reliability hardening only; real audio fades/ducking and final QA remain incomplete.
+- **PR/branch:** Draft #845, `feat/feature4-f4-07-proof-preflight-20261030`, stacked on draft #322; no merge or task DONE claimed.
+- **Code commits:** `06ca86b6fe778f2b5bf64b941e4dbe7a13fc0aea`, `b60bf4215e8203493485b61507e89ef789623454`. **Tests commit:** `118d925337e772d959c95e63c20008fcc7b135da`.
+- **Changed:** `video-engine/feature4_audio_master.py` uses atomic `os.open(O_CREAT|O_EXCL|O_NOFOLLOW, mode=0600)` for private proof receipts, rejects symlinked ancestors, flushes and fsyncs receipt before reporting success. This prevents permissive-umask disclosure and nested symlink traversal; failure continues to use existing receipt/output cleanup.
+- **Tests added/updated:** `tests/media/test_feature4_audio_master.py` now patches the secure report opener for injected errors and checks owner-only 0600 permissions under umask 000, plus nested symlink-parent rejection.
+- **Verification:** Three isolated **source-equivalent** local Python checks passed (0600 mode, no-clobber, nested symlink denial). Exact repository tests **not run**: this runtime cannot resolve GitHub for local checkout. At pre-checkpoint head `b60bf4215e8203493485b61507e89ef789623454`, GitHub PR-triggered workflow lookup returned **0 runs**, combined status **0**; exact-head 4/4 CI **not verified**. Source-equivalent checks are not full CI.
+- **Remaining:** Verify full repository tests and 4/4 exact-head CI, assess actual multi-track fade/duck behavior with licensed audio, commercial reviewer signoff, and coordinator integration. No new live media, user sample, paid model, GPU, PROD, SQL or WineShopPOS.
+- **NEXT:** F4-07 exact-checkout targeted `python -m unittest tests/media/test_feature4_audio_master.py` (adjust module invocation to repository convention) and required 4-job CI. If still CI-blocked, inspect F4-09 existing PR #769 or F4-06 #830/#739 for nonoverlapping tests rather than duplicating their work. Coordinator owns review, main merge and task receipt.
+- **Final head:** checkpoint commit will advance branch beyond the pre-checkpoint code SHA; reread PR #845 head before claiming CI.
+
+### Additional fail-closed regression (same run)
+
+- Commit `9175f746fe20d0796898204326bccdeaddeed9a5` adds a mocked `os.fsync` failure regression. Expected behavior: CLI exits code 2 and removes only its own private proof and matching output; no success is reported. This test is **committed but not executed in exact repository checkout**. It supplements, not replaces, the three local source-equivalent checks.
+- NEXT remains exact-head repository test/4-job CI verification followed by F4-07 actual licensed fade/ducking acceptance. No verified task DONE.
~~~~

### video-engine/feature4/RUN_CHECKPOINT_INTEGRATION.md
~~~~diff
@@ -0,0 +1,124 @@
+# Feature #4 integration checkpoint — 2026-10-30
+
+## Current batch and ownership
+- Integration candidate: PR #779, branch `feat/feature4-batched-source-handoff-20261030`, stacked on Feature #4 parent PR #322 (`feat/feature4-professional-video-studio`).
+- Pre-integration #779 head: `ab1a123821219c196c4357b25429f51eff5e689c`.
+- Source donor: PR #845, head `304e7236eb7183f668ed629dda8822b2292d67b0`, same parent PR #322. The PR comparison confirmed a shared parent and exactly three donor-only paths, with no overlap in #779's previous changed paths.
+- This checkpoint is **not** a coordinator merge or an accepted task completion.
+
+## Integration performed
+- F4-07: copied the exact reviewed donor blob `579de71b057a86e944cf1d81426207c96fc29581` into `video-engine/feature4_audio_master.py` in batch PR #779, commit `949fbb3c2e6f7be7c1e08a885d1bd28786dfa736`.
+- F4-07: copied the exact donor test blob `eb9e39f005ce35e18ad19cafb7a0804769f35167` into `tests/media/test_feature4_audio_master.py` in batch PR #779, commit `97cd09f235fde12f72e1bf3f15e30c1e3dacd0c5`.
+- The source and tests already existed in PR #845; no new feature behavior was invented. Its original checkpoint `video-engine/feature4/RUN_CHECKPOINT_F4_07.md` remains in PR #845 as donor trace evidence; do not double-merge donor PR.
+- Existing #779 batch F4-03/04/10/13/14/15 remains intact. Its original tracker and handoff remain source snapshots; coordinator must reconcile their acceptance evidence.
+
+## Verification and gates
+- **Verified:** GitHub donor and recipient file blob SHA equality after the two copies; PR #779 head advanced to `97cd09f235fde12f72e1bf3f15e30c1e3dacd0c5` before this checkpoint.
+- **Not verified:** executable test run on combined checkout, exact-head four-job CI, merge-ref CI, signed hosted DEV, commercial rights/music acceptance, and fresh postmerge main CI. Earlier donor claims of isolated tests are not substituted for combined-head CI.
+- **Task state:** F4-07 remains in progress; the original 31-task registry snapshot shows 0 source-complete, 16 blocked and 0 integrated. This batch is **not PR-ready** until mandatory CI and coordinator review.
+- **No spend:** GPU, paid models, PROD, SQL migrations and WineShopPOS untouched; no media samples created.
+
+## Next eligible integration actions
+1. Verify PR #779 new exact head and full four-job CI. Diagnose actual failing job logs, fix owned batch source only, and rerun checks as permitted; never infer pass from missing runs.
+2. Coordinator to review #779 relative to parent #322 and reconcile stacked branches / issue #650 packaging before any main merge. Review rights and integration boundaries; do not merge automatically.
+3. Compare existing F4 batches #828 and #779 plus F4-07 donor #845 for compatible changes. Preserve original PR evidence and avoid double-merge. If CI is blocked by external owner #650/#249, work on a different independently reviewable batch.
+
+
+## Integration continuation — F4-08 source reconciliation, 2026-10-30
+
+- **PR #779** remains OPEN/DRAFT, stacked on **PR #322** (`feat/feature4-professional-video-studio`), not on `main`. Exact observed batch code head before this checkpoint: `027adec234691779ab508d8781926f8a5b8f7c3b`; current PR head after this checkpoint must be re-read from GitHub.
+- **Donor PR #838** (F4-08 finite frame seeking), donor head `74bc376af78c55c2e3fc1fb93ede681c603594ac`, was reconciled into the *existing* batch rather than opening a new micro-PR.
+- Reused byte-identical donor files `frontend/src/features/video/frame-seek.mjs` (blob `195e6e53041635dc4ad120eda76af506857120fd`) and `tests/frontend/feature4-frame-seek.test.mjs` (blob `7de58dcfc7be031afd74ebdd2a409b058dd617ef`).
+- **Conflict resolution:** `frontend/src/features/video/TimelineStudioSurface.jsx` overlaps existing F4-10 tenant/pointer fences in #779. Did **not** replace the entire component with donor version. Instead integrated five bounded seek edits (import, invalid-input guard, normalized seek, caption click, scene midpoint click) while retaining F4-10 `pendingResize` cancellation and live approval checks. Integrated component blob `04c9d76fdf6e602522628aa035a63b4100750dc3`. Source commits `c7072319`, `1c01bee6`, `027adec2`.
+- **Targeted test:** `node --test tests/frontend/feature4-frame-seek.test.mjs` on a source-equivalent isolated Node v22.16.0 copy: **4 passed, 0 failed**. This is **not** a full PR checkout, Playwright, decoded-media parity, nor 4-job CI. GitHub donor/recipient blob SHAs were independently verified equal for the pure helper and test.
+- **Exact-head CI:** GitHub commit workflow lookup returned no PR-triggered runs for `027adec2`; push-triggered run visibility is not established by that lookup. Treat 4/4 as **NOT VERIFIED**, not passed or failed. No merge, no integrated DONE, no production rights/hosted approval.
+- **Task state:** F4-08 remains IN PROGRESS until full acceptance and coordinator integration. Central registry snapshot remains source-complete 0/31, blocked 16/31, integrated 0/31; tested and PR-ready per-task counts remain unverified.
+- **NEXT:** inspect exact PR #779 head and actual *push* CI on that SHA; resolve failures without bypassing required jobs. Run F4-10 pointer-lifecycle regressions against the combined branch; then reconcile #828 and other existing F4 stacks only after file-overlap review. Coordinator owns #650 packaging, main merge and fresh postmerge 4/4. Do not separately merge donor #838 without checking for duplicate code.
+- No GPU, paid models, PROD, hosted SQL, customer samples or WineShopPOS changes.
+
+
+## Integration continuation — F4-11 encoded motion integrity, 2026-10-31
+
+- **Existing batch:** PR #779 (OPEN/DRAFT), branch `feat/feature4-batched-source-handoff-20261030`, stacked on PR #322 / `feat/feature4-professional-video-studio`, **not** on `main`. Pre-checkpoint code head `c0dccccf05349f34d3291b76b32eeb647711f8a6`; this checkpoint commit advances head, so re-read PR before any exact-head CI claim.
+- **Donor:** existing F4-05/F4-11/F4-15 consolidation PR #828, head `ca103ce851c567d67198040a5a41738ea98e8395`. The branches diverge (4 ahead, 7 behind relative to #779); do **not** fast-forward/merge the entire donor stack. Selected only the self-contained F4-11 encoded-motion source/test pair; the unchanged module import `feature4_private_preview` is already present on recipient.
+- **Actual integration commits:** `d34b4d2058f84d96a99fdbe9d562ad77a55aa492` replaces `video-engine/feature4_encoded_motion_qa.py`; `c0dccccf05349f34d3291b76b32eeb647711f8a6` replaces `tests/media/test_feature4_encoded_motion_qa.py`. GitHub recipient blob SHAs were checked against donor: source `2d8c96b80ac94f2c9099401442d28f5b174bbc86`, test `3c45f3b5af2e5a9ec7bac769bd8d602699df03be`, **both exact matches**.
+- **Source behavior reused, not newly invented:** fail closed on source inode/path swap and bytes changed during actual FFmpeg frame probes; reject nonfinite configuration and cross-scene sampling; add existing encoded-media race negative tests. This is a technical source control, **not** a commercial visual/rights approval or finished 60-second quality proof.
+- **Verification:** GitHub source/test blob equality **VERIFIED**. Combined-checkout `python3 -m unittest tests.media.test_feature4_encoded_motion_qa -v` **NOT RUN** (no local GitHub network checkout); combined exact-head four-job CI **NOT VERIFIED**. PR-head workflow lookup currently returns no PR-triggered runs, which does not prove absence of push-triggered runs. Parent PR #322 had an earlier failed Python job in Actions run `40937402426` (4 failed package/rollback tests, 913 passed), owned by coordinator Issue #650; **not** attributed to this F4-11 change and **not** bypassed.
+- **Acceptance:** F4-11 stays IN PROGRESS; coordinator must verify combined CI, reconcile #322/#779 stack to main and require fresh postmerge main 4/4 before integrated DONE. Central snapshot: 0/31 source-complete, 16/31 blocked, 0/31 integrated; tested and PR-ready not verified. No GPU, paid inference, Azure, PROD, hosted SQL, samples or WineShopPOS.
+- **NEXT:** F4-11 combined exact-head CI and targeted encoded-motion regression; then review #828's remaining F4-05 CSS/effects and F4-15 lease-race source for compatible, nonduplicative integration into #779 (check overlap with `feature4_worker_handoff.py` and prior #779 F4-15). Coordinator owns Issue #650 package and #249 Azure 503; keep unrelated work independent.
+
+
+## Integration CI repair — audio proof syntax, 2026-10-31
+
+- **Owner/batch:** Feature #4, PR #779 (OPEN/DRAFT), branch `feat/feature4-batched-source-handoff-20261030`, based on parent PR #322 / `feat/feature4-professional-video-studio` (NOT main).
+- **Failure verified:** PR #779 push run [41114095979](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41114095979) on head `02c325df97fe9137da4447f61a0925af5e9ccde9`: FFmpeg codecs + renderer FAILED; frontend, Python/uv and Supabase jobs PASSED. FFmpeg job 124264186849 showed `SyntaxError: unexpected character after line continuation character` at `video-engine/feature4_audio_master.py:149`, preventing `test_feature4_audio_master` import (238 discovered tests; one import error).
+- **Actual repair:** commit `eba79514695a765afd700033145f9c377df191bc` in this same batch replaces the accidentally embedded literal `\\n` between two clauses of `_private_report_path` with a real source newline. No change to proof-path rejection behavior, permissions or security guards; existing import/test coverage exercises the syntax. Changed file: `video-engine/feature4_audio_master.py`.
+- **Verification:** failed CI log and exact source line inspected in GitHub. A new exact-head four-job CI pass is **NOT YET VERIFIED**; no local Python/FFmpeg run claimed. This checkpoint commit advances PR head again; check the new SHA before citing CI.
+- **NEXT integration gate:** wait for/inspect latest PR #779 exact-head 4/4 CI; fix any further concrete failures, then reconcile only compatible F4-05/F4-15 source from existing donor PR #828 (do not wholesale merge overlapping worker-handoff source). Coordinator must review parent PR #322/main ancestry, issue #650 packaging and #249 live DEV separately before main integration; no DONE yet.
+- **Progress evidence:** central F4 snapshot source-complete 0/31 and blocked 16/31; reviewed integrated DONE 0/31; tested and PR-ready on combined batch remain unverified. GPU, paid models, PROD, hosted SQL and samples OFF.
+
+
+## Integration CI repair — partial receipt-write regression, 2026-10-31
+
+- **Owner / existing batch:** Feature #4 PR #779, branch `feat/feature4-batched-source-handoff-20261030`, stacked on draft PR #322; this does not target `main` directly.
+- **Verified failing exact-head CI:** [Part 1 run #41122872783](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41122872783) on head `e8bad29174fbac65d8f60a4a50d5f384a586533f`: frontend, Python/uv and Supabase passed; FFmpeg media job failed (1 error among 246 tests). Failing test `test_partial_proof_write_failure_removes_owned_receipt_and_output` in `tests/media/test_feature4_audio_master.py` raised `KeyError: source_audio_mean_db` from the success print instead of injecting the intended proof write failure.
+- **Root cause:** existing regression mock only injected its simulated partial write when `_open_private_report` was called with a legacy positional `'x'` mode. Current production `_open_private_report(proof)` uses `os.open(..., O_CREAT | O_EXCL, 0o600)` and takes no positional mode, so the failure injection was silently skipped. This was a test-mock mismatch, not evidence that real proof cleanup failed.
+- **Actual owned test change:** commit `43028189c626ee9c1c28a4f32f77a1e04b8f743f`, file `tests/media/test_feature4_audio_master.py`, makes the fake opener inject the partial write failure whenever the selected proof path is opened. Existing assertions then require the partial private receipt and matching output to be removed. No production mastering/rights/tenant code was changed and no additional PR opened.
+- **Verification:** GitHub failed job log, production opener signature and modified test source inspected. Local test execution **NOT RUN**; the new exact-head four-job CI **PENDING / NOT VERIFIED**. This checkpoint commit advances the head again; verify actual PR SHA and push-run before calling it tested or PR-ready.
+- **NEXT:** inspect PR #779 new exact-head push CI, specifically `test_partial_proof_write_failure_removes_owned_receipt_and_output` and all four required jobs. If green, reconcile remaining compatible F4-05/F4-15 source from PR #828 without overwriting existing worker safety fences; coordinator then reviews #322 parent/main ancestry and Issue #650 before merge. Do not claim integrated DONE before reviewed merge and fresh main 4/4.
+- **Counts:** original Feature4 registry snapshot source-complete 0/31, blocked 16/31; reviewed integrated DONE 0/31; per-task tested and PR-ready still not verified. GPU OFF; no paid inference, PROD, hosted SQL, samples or WineShopPOS.
+
+
+## Integration continuation — F4-05 reviewed CSS effect parity, 2026-10-31
+
+- **Existing batch:** [PR #779](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/779), branch `feat/feature4-batched-source-handoff-20261030`, stacked on parent [PR #322](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322), not on main. Source integration head before this checkpoint: `168c2fb4ca8b74ff8d6f7eef148c541a56037fb3`. Re-read PR head after this checkpoint commit.
+- **Donor:** existing consolidated [PR #828](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/828), head `ca103ce851c567d67198040a5a41738ea98e8395`. Reused its *already written* F4-05 code and offline regression, not a new feature or PR. Donor stack is divergent; do not wholesale merge it.
+- **Actual source commits in this same batch:** `79f9c161640171d81abf6d13a2e2243f936a6518` (`video-engine/professional.py`), `46994f275f12a499ae5dbb820b22ce60c4e91bf9` (`video-engine/creative_contract.py`), and `168c2fb4ca8b74ff8d6f7eef148c541a56037fb3` (`tests/media/test_feature4_professional.py`).
+- **Verified GitHub donor/recipient blob equality:** `professional.py` `a52c2737f825f6f3b7ea193943626f004029f7a2`; `creative_contract.py` `80c395881be9ae3f37e782638889ae9b0bd5c0eb`; `test_feature4_professional.py` `88c6be8c6e188776e220517ee28467a8f19c5c1c`. These three files were not previously changed in #779; prior F4-07/08/10/11/13/14/15 changes remain intact.
+- **Scope:** shared allowlists for five approved animation presets and three transitions, actual deterministic CSS keyframe selectors, and offline compiler regressions. CSS source parity does **not** prove decoded MP4 effects or manual UI acceptance.
+- **CI:** Prior [run #41130847025](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41130847025) had all four jobs successful, but **does not cover this newly changed head**. GitHub commit workflow lookup and combined-status endpoint returned no exact-head evidence for `168c2fb4`; this lookup filters to PR-triggered runs and may miss branch-push CI. Current combined 4/4 is **NOT VERIFIED**. No local tests were executed in this run. Do not mark PR-ready or tested based on donor or previous-head CI.
+- **Counts:** coordinator registry snapshot F4 source-complete **0/31**, blocked **16/31**, in progress **15/31**; tested **not verified**, PR-ready **not verified**, integrated DONE **0/31**. No coordinator-reviewed task receipts.
+- **NEXT F4-15 integration gate:** compare PR #828 `video-engine/feature4_worker_handoff.py` and `tests/media/test_feature4_worker_handoff.py` against #779's existing F4-13/F4-15 source and preserve staged-SHA and lease fences; reconcile only compatible donor changes. Verify exact latest #779 push CI (all four jobs), then request coordinator review of stacked #322/#779 and #650 packaging. #249 signed DEV reliability and human commercial rights remain separate owner gates. No double-merge of donor #828.
+- **Safety:** GPU OFF, no paid inference, cloud spend, PROD, hosted SQL, WineShopPOS or samples.
+
+
+## Integration continuation — F4-15 staged SHA and lease-race reconciliation, 2026-10-31
+
+- **PR/branch:** [#779](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/779), `feat/feature4-batched-source-handoff-20261030`, stacked on parent #322. Source code head before checkpoint: `69f205bc058f3d05f85886c82ce4884afdd562d0`; re-read head for CI.
+- **Existing donor:** [PR #828](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/828), head `ca103ce851c567d67198040a5a41738ea98e8395`. Inspected source line-level comparison before copying: donor worker changes are **16 added / 2 replaced lines** over #779 and donor test changes are **70 added / 0 removed lines**. Therefore recipient F4-13/F4-15 original fingerprint and post-render guards were retained, not overwritten.
+- **Owned source integration:** `82ade3f455c631814b86716aef69b6da3f7184a4` updated `video-engine/feature4_worker_handoff.py`; `69f205bc058f3d05f85886c82ce4884afdd562d0` updated `tests/media/test_feature4_worker_handoff.py`. Recipient/donor blobs verified identical: `72d6bcb7270a8bf315e972333e0b9cb1a2947817` and `5959eade94e2cb6e3f01141e4bb58d1c23cc6c72`.
+- **Scope:** reject empty/oversized and same-content swapped inode staged files; deny private download on stale preflight lease; deny CPU render when lease/rights revoked after staging. Added donor's existing negative tests; **no new worker API, deployment, rights approval, or billing changes**.
+- **Verification:** GitHub donor/recipient source equality and line-level preservation verified. No local tests executed. Prior [Actions #41130847025](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41130847025) had 4/4 successful jobs on an **earlier** head, not this combined head. Exact-head four-job CI and merge-ref CI **NOT VERIFIED**. Do not claim tested, PR-ready, or integrated DONE from donor CI or old head.
+- **Registry:** source-complete 0/31 snapshot, blocked 16/31 snapshot, tested not verified, PR-ready not verified, integrated DONE 0/31 (empty coordinator-reviewed receipt log).
+- **NEXT integration gate:** inspect latest #779 exact-head push CI for all four jobs; diagnose/fix concrete regressions in F4-05/F4-15 if present. Coordinator must review #779/#322 stack and reconcile main / #650 packaging; #249 hosted 503 and production rights remain separate owners. Do **not** double-merge #828 or the original donor PRs. GPU OFF; no paid model, cloud spend, PROD, SQL, WineShopPOS or samples.
+
+
+## Integration continuation — F4-11 continuous encoded black-hold QA (2026-10-31)
+
+- **Integration target:** existing OPEN/DRAFT PR #779, branch `feat/feature4-batched-source-handoff-20261030`, stacked on draft parent #322; pre-integration head `28da476ce5b5b8b7a8926aca3da5858378e93414` and base `e32a8da61a6272666d757b6c51b0ec2576d7602f`. No main merge.
+- **Donor:** existing PR #808, exact head `81023702673f48730d85e4b33fae26936e8b30cd`, based on earlier #779 `ab1a123821219c196c4357b25429f51eff5e689c`. Donor [Actions #41052945105](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41052945105) reported 4/4 SUCCESS at donor head, **not** proof for this newly combined batch.
+- **Pre-copy conflict check:** four recipient code/test blobs were byte-identical to the donor's base `ab1a1238`; none was modified by later #779 integration. Copied only existing F4-11 source/tests and donor handoff, **not** donor's stale 31-task shared ledger snapshot. Paths:
+  `video-engine/feature4_scene_visibility.py` (donor blob `c4e1ba05858f26feba1b4572a8852084eea9e7c0`);
+  `video-engine/feature4_minute_quality_receipt.py` (`d25685efd028a7c3c4017eee149cf79f558a6050`);
+  `tests/media/test_feature4_scene_visibility.py` (`0d8cc50dc15eb7732f02cb65384de8ef2880e50b`);
+  `tests/media/test_feature4_scene_visibility_receipt.py` (`cb5f2b78ecfaecc2f7971c8cbe10eed1f2bb4e4b`);
+  `video-engine/FEATURE4_CONTINUOUS_BLACK_SCAN_HANDOFF_20261030.md` (`78e07970d137a2f09e40c633ab21002168feb191`).
+- **Scope:** F4-11 continuous FFmpeg blackdetect full-timeline scan and v3 visibility proof; existing encoded 0.8s hidden black-gap negative regression, no commercial/rights/visual approval.
+- **Verification:** GitHub source/base blob comparison VERIFIED; donor 4/4 from its own exact head VERIFIED via PR #808 evidence. New batch combined-head tests/CI **NOT RUN / NOT VERIFIED** at checkpoint creation. Previous #779 head `28da476ce5b5b8b7a8926aca3da5858378e93414` passed [Actions #41137311270](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41137311270) 4/4, but that is **pre-integration** and cannot be reused as new-head proof. Re-read current #779 SHA and GitHub Actions run before claiming tested/PR-ready.
+- **Review blocker:** parent #322 diverged from main at `140a9f86170132d7c482a183b843788aa09b3b5a` (229 ahead / 308 behind at inspection); coordinator owns main reconciliation, #650 protected Functions ZIP, PR merge-reference checks, merge and fresh main 4/4. #249 signed Azure 503 and customer media/rights/human acceptance remain separately blocked. No worker merge or shared canonical docs edits.
+- **Five-stage snapshot:** F4 source-complete 0/31 (registry, not absence of coding); tested per-task **not verified** on new combined head; PR-ready **not verified**; integrated DONE 0/31; blocked 16/31 (registry).
+- **NEXT integration gate:** inspect exact-head #779 four-job CI after this commit, fix any concrete owned failures; then review existing stacked PR #816 F4-14 CPU 15/30/60 matrix against current batch (overlapping `hyperframes/benchmark_render.py` requires semantic reconciliation). Avoid double-merging donor #808. Coordinator must review parent #322 and release packaging before main integration.
+- GPU OFF; no paid inference, cloud deployment, PROD, hosted SQL, WineShopPOS or samples.
+
+
+## Integration continuation — F4-14 three-profile CPU matrix donor reconciliation (2026-10-31)
+
+- **Existing batch / ancestry:** PR #779, `feat/feature4-batched-source-handoff-20261030`, OPEN/DRAFT and mergeable, stacked on parent PR #322 `feat/feature4-professional-video-studio` at base SHA `e32a8da61a6272666d757b6c51b0ec2576d7602f`; not a direct main PR. Current main observed `7404b46e2aeda2707dd7793a4bae36295390d039`. Do not merge #779 or #322 as Feature4 worker.
+- **Verified previous gate:** exact prior batch SHA `eb609c509afb315e13efbb83934f031c7b861a48` passed 4/4 push CI [#41149431861](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41149431861) (frontend, Supabase, FFmpeg, Python all successful). This green result does **not** apply to newly changed head.
+- **Source donor:** existing F4-14 stacked PR #816 head `d01e3c716b4f651809d645684c921c6f0413c343`, whose branch diverges from #779 (3 ahead / 22 behind). Did **not** merge donor stack or overwrite overlapping F4-11 security/quality files. Instead selectively reused existing donor F4-14 implementation and tests in #779, preserving other batch edits.
+- **Actual owned commits:** `49b8a9f49a605226bd53922010513e2c8d6d65ef` added `video-engine/feature4_cpu_matrix.py`; `b9f35b679391bea9b1d4cc6bd162ddf13f327a1f` added `tests/media/test_feature4_cpu_matrix.py`; `924cbb9a3693215e02412ee81e31c81dc6f9c3d1` preserved `video-engine/FEATURE4_CPU_3PROFILE_MATRIX_HANDOFF_20261030.md`; `d61aa7e075b803c5e434b78ea2be5bced2ec88e6` inserted the donor's `source_commit_claim` into existing `video-engine/hyperframes/benchmark_render.py` without replacing unrelated code.
+- **Verification:** GitHub recipient blobs equal donor blobs for all four paths: CPU source `6e0dbe554f113ba6022fb9fa788abaf3e7e097ae`, test `d03ab1da9786cd17a097ead54eb774d5e9a9ff61`, handoff `5f2d75c10daadde77c16f7c005cb180e57ba26c6`, benchmark `69256391f5b6a81e4e0aa7c36f3225449efdd04f`. No executable test was run locally; donor tests use mocked ffprobe, **not** actual CPU measurement or a real encoded media qualification.
+- **CI gate:** push [#41155224113](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41155224113) was PENDING on code head `d61aa7e075b803c5e434b78ea2be5bced2ec88e6` when inspected. This checkpoint commit advances the PR head again; inspect the *new* exact-head push run and all four jobs before any tested/PR-ready claim. No new 15/30/60 genuine measured CPU receipts or Azure budget acceptance claimed.
+- **Status:** F4-14 source consolidated into batch; accepted integrated DONE remains **0/31** until coordinator review/merge and fresh main 4/4. Canonical snapshot remains source-complete 0/31 and blocked 16/31; tested/PR-ready per-task receipts not verified. Source implementation is not a registry completion.
+- **NEXT task ID / integration gate:** F4-14 verify current exact-head 4/4, investigate failing jobs if any, and reconcile any remaining overlap in PR #816's ledger/benchmark handoff without double-merging; then hand off #779/#322 ancestry and Issue #650 packaging to coordinator. Independent F4-03 receipt review can proceed while CI is pending. Azure Issue #249 live 503 and real 15/30/60 CPU budget are external gates, not excuses to stop offline work.
+- GPU OFF, no paid inference, cloud spend, PROD, SQL, customer samples or WineShopPOS.
~~~~

### video-engine/feature4_audio_master.py
~~~~diff
@@ -125,6 +125,33 @@ def master_private_audio(source: Path, target: Path, *, expected_seconds: int):
             partial.unlink(missing_ok=True)
 
 
+def _open_private_report(proof: Path):
+    """Atomically create a private, no-clobber receipt with owner-only permissions.
+
+    Path.open('x') defaults to 0666 before umask and can expose private media
+    metadata to other local users. Never chmod after creation: that leaks briefly.
+    """
+    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
+    if hasattr(os, "O_NOFOLLOW"):
+        flags |= os.O_NOFOLLOW
+    fd = os.open(proof, flags, 0o600)
+    try:
+        return os.fdopen(fd, "w", encoding="utf-8")
+    except BaseException:
+        os.close(fd)
+        raise
+
+
+def _private_report_path(path: Path):
+    """Reject unusable proof destinations before touching authorized media."""
+    path = Path(path)
+    if (path.suffix.lower() != ".json" or path.is_symlink() or path.exists() or
+            not path.parent.is_dir() or
+            any(parent.is_symlink() for parent in (path.parent, *path.parent.parents))):
+        raise AudioMasterError("Proof report must be a new private JSON file")
+    return path
+
+
 def main():
     ap=argparse.ArgumentParser(description=__doc__)
     ap.add_argument("--source",required=True)
@@ -133,12 +160,41 @@ def main():
     ap.add_argument("--report",required=True)
     args=ap.parse_args()
     try:
+        # Check proof destination before expensive mastering, then use exclusive
+        # creation so a concurrent receipt cannot be overwritten.
+        proof=_private_report_path(Path(args.report))
         report=master_private_audio(Path(args.source),Path(args.output),
                                     expected_seconds=args.duration)
-        proof=Path(args.report)
-        if proof.is_symlink() or proof.exists() or not proof.parent.is_dir():
-            raise AudioMasterError("Proof report must be new and private")
-        proof.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
+        proof_identity=None
+        try:
+            with _open_private_report(proof) as stream:
+                st=os.fstat(stream.fileno())
+                proof_identity=(st.st_dev,st.st_ino)
+                stream.write(json.dumps(report,indent=2)+"\n")
+                stream.flush()
+                os.fsync(stream.fileno())  # Do not announce success before proof bytes are durable.
+        except OSError as exc:
+            # Remove an incomplete receipt only when it is still our own
+            # exclusive file, not a symlink or a replacement by another writer.
+            if proof_identity is not None:
+                try:
+                    st=proof.lstat()
+                    if (not proof.is_symlink() and
+                            (st.st_dev,st.st_ino)==proof_identity):
+                        proof.unlink()
+                except OSError:
+                    pass
+            # An exclusively created MP4 is not usable without its matching
+            # private proof. Remove only our exact output bytes; never delete
+            # a symlink or a different file that appeared after mastering.
+            target=Path(args.output)
+            try:
+                if (target.is_file() and not target.is_symlink() and
+                        hashlib.sha256(target.read_bytes()).hexdigest()==report["master_sha256"]):
+                    target.unlink()
+            except OSError:
+                pass  # Leave uncertain bytes for operator reconciliation.
+            raise AudioMasterError("Proof report could not be committed privately; output invalid") from exc
         print(json.dumps({"status":report["status"],
                           "source_mean_db":report["source_audio_mean_db"],
                           "mastered_mean_db":report["mastered_audio_mean_db"]}))
~~~~

### video-engine/feature4_cpu_matrix.py
~~~~diff
@@ -0,0 +1,172 @@
+#!/usr/bin/env python3
+"""Offline F4-14 aggregate: immutable actual 15/30/60 MP4s + CPU receipts.
+
+NO render, GPU, Azure, upload, credentials or customer approval is performed.
+A claimed Git checkout SHA is NOT authenticated GitHub Actions provenance.
+"""
+from __future__ import annotations
+
+import argparse
+import json
+import math
+import os
+from pathlib import Path
+import re
+import stat
+import subprocess
+
+from feature4_export_matrix import MatrixEvidenceError, verify_export_matrix
+
+HEAD_RX = re.compile(r"^[0-9a-f]{40}$")
+KINDS = (15, 30, 60)
+MAX_REPORT_BYTES = 64 * 1024
+
+
+class CpuMatrixError(ValueError):
+    pass
+
+
+def _read_report(path):
+    try:
+        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
+        with os.fdopen(fd, "rb") as stream:
+            before = os.fstat(stream.fileno())
+            if not stat.S_ISREG(before.st_mode) or not 20 <= before.st_size <= MAX_REPORT_BYTES:
+                raise CpuMatrixError("Missing or unsafe bounded CPU receipt")
+            data = stream.read(MAX_REPORT_BYTES + 1)
+            after = os.fstat(stream.fileno())
+            current = os.lstat(path)
+            if (len(data) != before.st_size or
+                    (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) !=
+                    (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) or
+                    not stat.S_ISREG(current.st_mode) or
+                    (current.st_dev, current.st_ino, current.st_size) !=
+                    (after.st_dev, after.st_ino, after.st_size)):
+                raise CpuMatrixError("CPU receipt changed or was replaced")
+            obj = json.loads(data.decode("utf-8"))
+            if type(obj) is not dict:
+                raise CpuMatrixError("CPU receipt must be one JSON object")
+            return obj
+    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
+        raise CpuMatrixError("CPU receipt unavailable, unsafe or malformed") from exc
+
+
+def _positive_number(value):
+    return type(value) in (int, float) and math.isfinite(value) and value > 0
+
+
+def aggregate_cpu_matrix(manifest, root, *, expected_head):
+    """Review three recorded local benchmarks; do not synthesize media or rates."""
+    if type(expected_head) is not str or not HEAD_RX.fullmatch(expected_head):
+        raise CpuMatrixError("Expected one exact git checkout SHA")
+    if (type(manifest) is not dict or set(manifest) != {"schema", "source_commit", "renders"}
+            or manifest["schema"] != "feature4_cpu_matrix_inputs_v1"
+            or manifest["source_commit"] != expected_head):
+        raise CpuMatrixError("Unexpected or cross-commit CPU matrix inputs")
+    rows = manifest["renders"]
+    if type(rows) is not list or len(rows) != 3:
+        raise CpuMatrixError("Three source-linked 15/30/60 receipts required")
+    media_rows = []
+    receipts = {}
+    occupied = set()
+    for row in rows:
+        if type(row) is not dict or set(row) != {"seconds", "path", "sha256", "benchmark"}:
+            raise CpuMatrixError("Invalid CPU matrix input row")
+        duration = row["seconds"]
+        if type(duration) is not int or duration not in KINDS or duration in receipts:
+            raise CpuMatrixError("Missing or repeated duration")
+        report_name = row["benchmark"]
+        if (type(report_name) is not str or len(report_name) > 120 or
+                not report_name.endswith(".json") or report_name in ("", ".", "..")
+                or "/" in report_name or "\\" in report_name or
+                report_name == row["path"] or report_name in occupied):
+            raise CpuMatrixError("CPU receipts must be distinct local JSON basenames")
+        occupied.add(report_name)
+        media_rows.append({key: row[key] for key in ("seconds", "path", "sha256")})
+        receipts[duration] = report_name
+
+    root = Path(root)
+    if not root.is_dir() or root.is_symlink():
+        raise CpuMatrixError("Expected private existing media/benchmark directory")
+    try:
+        media = verify_export_matrix(
+            {"schema": "feature4_export_matrix_inputs_v1",
+             "source_commit": expected_head, "renders": media_rows},
+            root, expected_head=expected_head)
+    except MatrixEvidenceError as exc:
+        raise CpuMatrixError("Actual encoded MP4 profile / immutable SHA verification failed") from exc
+
+    results = []
+    for item in media["renders"]:
+        duration = item["seconds"]
+        receipt = _read_report(root / receipts[duration])
+        if (receipt.get("kind") != "OFFLINE_SYNTHETIC_HYPERFRAMES_CPU_BENCHMARK_NOT_AZURE"
+                or receipt.get("source_commit_claim") != expected_head
+                or receipt.get("output_sha256") != item["sha256"]
+                or receipt.get("output_bytes") != item["bytes"]
+                or receipt.get("output_hash_type") != "SHA256_STABLE_LOCAL_REGULAR_FILE_ONLY"
+                or receipt.get("duration_seconds") != duration
+                or (receipt.get("width"), receipt.get("height"), receipt.get("fps")) !=
+                   (1080, 1920, 24)
+                or receipt.get("cloud_or_gpu_inference") is not False
+                or receipt.get("measured_on_azure_functions") is not False
+                or receipt.get("commercial_visual_quality_accepted") is not False
+                or receipt.get("azure_runtime_memory_verified") is not False
+                or receipt.get("azure_cost_inr") is not None
+                or not _positive_number(receipt.get("wall_seconds"))
+                or not _positive_number(receipt.get("max_sampled_process_tree_rss_bytes"))
+                or not _positive_number(receipt.get("max_sampled_cpu_seconds_lower_bound"))
+                or not _positive_number(receipt.get("sampling_interval_seconds"))
+                or type(receipt.get("samples")) is not int or receipt["samples"] < 1
+                or type(receipt.get("max_observed_process_count")) is not int
+                or receipt["max_observed_process_count"] < 1):
+            raise CpuMatrixError("Benchmark receipt does not match exact encoded profile, source or safe cost scope")
+        results.append({
+            "seconds": duration, "original_mp4_sha256": item["sha256"],
+            "original_mp4_bytes": item["bytes"],
+            "wall_seconds": receipt["wall_seconds"],
+            "sampled_peak_rss_bytes_lower_bound": receipt["max_sampled_process_tree_rss_bytes"],
+            "sampled_cpu_seconds_lower_bound": receipt["max_sampled_cpu_seconds_lower_bound"],
+            "sample_count": receipt["samples"],
+        })
+    results.sort(key=lambda item: item["seconds"])
+    return {
+        "schema": "feature4_cpu_15_30_60_offline_observations_v1",
+        "status": "THREE_ENCODED_LENGTHS_CPU_OBSERVED_NOT_CLOUD_QUALIFIED",
+        "source_commit_claim": expected_head,
+        "code_commit_attested_by_ci": False,
+        "renders": results,
+        "max_measured_wall_seconds": max(x["wall_seconds"] for x in results),
+        "max_sampled_rss_bytes_lower_bound": max(
+            x["sampled_peak_rss_bytes_lower_bound"] for x in results),
+        "cloud_budget_accepted": False,
+        "actual_azure_memory_verified": False,
+        "commercial_release_eligible": False,
+        "human_visual_approval": False,
+        "missing_short_peak_and_child_memory_risk": True,
+    }
+
+
+def main():
+    parser = argparse.ArgumentParser(description=__doc__)
+    parser.add_argument("--manifest", required=True)
+    parser.add_argument("--source-root", required=True)
+    parser.add_argument("--report", required=True)
+    args = parser.parse_args()
+    manifest_path, output = Path(args.manifest), Path(args.report)
+    if (output.exists() or output.is_symlink() or output.suffix.lower() != ".json"
+            or not output.parent.is_dir() or output.parent.is_symlink()):
+        raise CpuMatrixError("CPU matrix output must be fresh, private and local")
+    inputs = _read_report(manifest_path)
+    head = subprocess.check_output(
+        ["git", "rev-parse", "--verify", "HEAD"],
+        cwd=Path(__file__).resolve().parents[1], text=True, timeout=5).strip()
+    result = aggregate_cpu_matrix(inputs, args.source_root, expected_head=head)
+    with output.open("x", encoding="utf-8") as out:
+        json.dump(result, out, indent=2)
+        out.write("\n")
+    print(result["status"] + " — NOT cloud or retailer approval")
+
+
+if __name__ == "__main__":
+    main()
~~~~

### video-engine/feature4_edited_export_qa.py
~~~~diff
@@ -45,11 +45,22 @@ def _frame(path, at):
 
 
 def _luma_delta(a, b):
+    # Decode always requests an exact 72x128 grayscale frame. Never allow
+    # implicit zip truncation or non-byte buffers to fake editor parity.
+    if (not isinstance(a, bytes) or not isinstance(b, bytes)
+            or len(a) != 72 * 128 or len(b) != 72 * 128):
+        raise EditorExportProofError("Malformed encoded editor grayscale frame")
     return sum(abs(x-y) for x, y in zip(a, b)) / len(a)
 
 
-def verify_mock_editor_output(source: Path):
-    """Audit actual encoded 540p 30s TEST edit scene families; never human art QA."""
+def verify_mock_editor_output(source: Path, *, operation: str = "split_reorder"):
+    """Decode actual 30s test pixels for split/reorder OR duplicate semantics.
+
+    This is a fixture-specific signal, never frame-accurate source identity,
+    human visual approval, product-motion fidelity or commercial acceptance.
+    """
+    if operation not in ("split_reorder", "duplicate"):
+        raise EditorExportProofError("Unknown approved mock editor operation")
     source = Path(source)
     try:
         metadata = inspect_mp4(source, max_size=80*1024*1024)
@@ -59,13 +70,23 @@ def verify_mock_editor_output(source: Path):
             or abs(metadata["seconds"] - 30) > .45):
         raise EditorExportProofError("Expected verified 30s 540p editor export")
     source_digest = _sha(source)
-    # Source storyboard generated by actual Timeline Studio JS editor:
-    # video 0..4, photo 4..14, trimmed same video 14..20,
-    # different product/offer photo 20..30. Interior-only samples.
-    at = (2.0, 7.0, 16.0, 24.0)
-    first_video, first_photo, trimmed_video, offer_photo = [
-        _frame(source, time) for time in at
-    ]
+    # Actual JS storyboards:
+    # split_reorder: video 0..4, photo 4..14, trimmed video 14..20, offer 20..30
+    # duplicate: photo 0..10, source video 10..15, SAME source restart
+    # 15..20, offer 20..30. Compare at the same position in each replay.
+    at = ((2.0, 7.0, 16.0, 24.0) if operation == "split_reorder"
+          else (2.0, 11.5, 16.5, 25.0))
+    frames = [_frame(source, time) for time in at]
+    # Original F4-04 #745 (3/17s intra-clip motion) and #773 (5/13/15/21s
+    # near-cut scene-family parity); the independent duplicate path stays 4 frames.
+    motion_frames = boundary_frames = ()
+    if operation == "split_reorder":
+        motion_frames = tuple(_frame(source, t) for t in (3.0, 17.0))
+        boundary_frames = tuple(_frame(source, t) for t in (5.0, 13.0, 15.0, 21.0))
+    if operation == "split_reorder":
+        first_video, first_photo, trimmed_video, offer_photo = frames
+    else:
+        first_photo, first_video, trimmed_video, offer_photo = frames
     if _sha(source) != source_digest:
         raise EditorExportProofError("Encoded MP4 changed during export QA sampling")
     video_pair = _luma_delta(first_video, trimmed_video)
@@ -80,16 +101,42 @@ def verify_mock_editor_output(source: Path):
     # The two video segments share footage, but the second is nonidentical
     # due to its reviewed 4s media in-point, not an exact identical replay.
     # Both product-photo scenes must remain distinct from each other and video.
-    if not (2.0 < video_pair < .65 * cross and
-            photo_pair >= 10.0 and cross >= 12.0):
+    if operation == "split_reorder":
+        moving_first, moving_trimmed = motion_frames
+        early_photo, late_photo, early_trimmed_video, early_offer = boundary_frames
+        motion_first = _luma_delta(first_video, moving_first)
+        motion_trimmed = _luma_delta(trimmed_video, moving_trimmed)
+        boundary_photo_delta = max(_luma_delta(early_photo, first_photo),
+                                   _luma_delta(late_photo, first_photo))
+        boundary_offer_delta = _luma_delta(early_offer, offer_photo)
+        boundary_video_separation = min(
+            _luma_delta(early_trimmed_video, first_photo),
+            _luma_delta(early_trimmed_video, offer_photo))
+        # Fixture-only technical heuristics; not real human media approval.
+        accepted = (2.0 < video_pair < .65 * cross
+                    and motion_first >= .25 and motion_trimmed >= .25
+                    and boundary_photo_delta < .65 * photo_pair
+                    and boundary_offer_delta < .65 * photo_pair
+                    and boundary_video_separation >= .65 * cross)
+    else:
+        # Same 5s source frames restart at 15s: the two video segments
+        # must encode similar pixels, not advance to source t=5..10.
+        # Allow minor renderer/seek noise, but reject reordered photos.
+        accepted = video_pair <= 8.0
+    if not (accepted and photo_pair >= 10.0 and cross >= 12.0):
         raise EditorExportProofError(
             "Actual encoded editor order/inpoint or image distinction regressed")
-    return {
-        "schema": "feature4_edited_30s_pixel_parity_v1",
-        "status": "ENCODED_MOCK_EDITOR_ORDER_TECHNICALLY_VERIFIED",
+    report = {
+        "schema": ("feature4_edited_30s_pixel_parity_v1" if operation == "split_reorder"
+                   else "feature4_duplicated_30s_pixel_parity_v1"),
+        "status": ("ENCODED_MOCK_EDITOR_ORDER_TECHNICALLY_VERIFIED"
+                   if operation == "split_reorder"
+                   else "ENCODED_MOCK_VIDEO_RESTART_TECHNICALLY_VERIFIED"),
+        "editor_operation": operation,
         "source_sha256": source_digest,
         "profile": "30s/540x960/H264/AAC",
-        "timeline_starts_seconds": [0, 4, 14, 20],
+        "timeline_starts_seconds": ([0, 4, 14, 20] if operation == "split_reorder"
+                                    else [0, 10, 15, 20]),
         "pixel_times_seconds": list(at),
         "repeated_source_video_delta": round(video_pair, 3),
         "different_photo_scene_delta": round(photo_pair, 3),
@@ -99,18 +146,33 @@ def verify_mock_editor_output(source: Path):
         "stock_model_product_match_verified": False,
         "commercial_release_eligible": False,
     }
+    if operation == "split_reorder":
+        report.update({
+            "first_video_encoded_motion_delta": round(motion_first, 3),
+            "trimmed_video_encoded_motion_delta": round(motion_trimmed, 3),
+            "encoded_motion_threshold": .25,
+            "boundary_probe_times_seconds": [5.0, 13.0, 15.0, 21.0],
+            "boundary_photo_max_delta": round(boundary_photo_delta, 3),
+            "boundary_offer_delta": round(boundary_offer_delta, 3),
+            "boundary_video_min_separation": round(boundary_video_separation, 3),
+            "boundary_scene_family_verified": True,
+            "exact_transition_frame_verified": False,
+        })
+    return report
 
 
 def main():
     cli = argparse.ArgumentParser(description=__doc__)
     cli.add_argument("--source", required=True)
     cli.add_argument("--report", required=True)
+    cli.add_argument("--operation", choices=("split_reorder", "duplicate"),
+                     default="split_reorder")
     args = cli.parse_args()
     report = Path(args.report)
     if (report.is_symlink() or report.exists() or report.suffix.lower() != ".json"
             or not report.parent.is_dir() or report.parent.is_symlink()):
         raise EditorExportProofError("Private QA output must be new JSON")
-    evidence = verify_mock_editor_output(Path(args.source))
+    evidence = verify_mock_editor_output(Path(args.source), operation=args.operation)
     with report.open("x", encoding="utf-8") as f:
         json.dump(evidence, f, indent=2)
         f.write("\n")
~~~~

### video-engine/feature4_encoded_motion_qa.py
~~~~diff
@@ -10,6 +10,8 @@
 import hashlib
 import json
 import math
+import os
+import stat
 from pathlib import Path
 import subprocess
 
@@ -36,6 +38,38 @@ def _frame(path: Path, sec: float):
     return data
 
 
+def _stable_source(path):
+    """Bind encoded bytes AND local pathname/inode before and after decoding.
+
+    A SHA of the final path alone would miss a same-content atomic swap during
+    inspection. No-follow FD + pre/post fstat/lstat guards fail closed on such
+    local races. Does not independently prove remote storage custody.
+    """
+    path = Path(path)
+    try:
+        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
+        with os.fdopen(fd, "rb") as src:
+            before = os.fstat(src.fileno())
+            if not stat.S_ISREG(before.st_mode) or not 1024 < before.st_size <= 80*1024*1024:
+                raise MotionProofError("Unsafe or oversized original video source")
+            digest = hashlib.sha256()
+            for chunk in iter(lambda: src.read(1024*1024), b""):
+                digest.update(chunk)
+            after = os.fstat(src.fileno())
+            current = os.lstat(path)
+            identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
+            if (identity != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
+                    or not stat.S_ISREG(current.st_mode)
+                    or identity != (current.st_dev, current.st_ino, current.st_size,
+                                    current.st_mtime_ns)):
+                raise MotionProofError("Encoded video source changed while hashing")
+            return identity, digest.hexdigest()
+    except MotionProofError:
+        raise
+    except OSError as exc:
+        raise MotionProofError("Unsafe or missing original video source") from exc
+
+
 def verify_moving_scenes(mp4: Path, *, seconds: int, scene_starts,
                          sample_offset=.8, separation=.7, threshold=5.0):
     """Measure mean absolute luma differences of reviewed moving scene windows.
@@ -50,20 +84,26 @@ def verify_moving_scenes(mp4: Path, *, seconds: int, scene_starts,
             any(type(s) not in (int,float) or not math.isfinite(s)
                 for s in scene_starts)):
         raise MotionProofError("Expected explicit trusted moving scene timecodes")
-    if (scene_starts != sorted(set(scene_starts)) or
+    if (type(sample_offset) not in (int,float) or not math.isfinite(sample_offset)
+            or not .5 <= sample_offset <= 1.2
+            or type(separation) not in (int,float) or not math.isfinite(separation)
+            or not .3 <= separation <= .9
+            or type(threshold) not in (int,float) or not math.isfinite(threshold)
+            or not 3 <= threshold <= 18):
+        raise MotionProofError("Unsafe motion verification configuration")
+    if (list(scene_starts) != sorted(set(scene_starts)) or
             any(s < 0 or s + sample_offset + separation >= seconds - .2
-                for s in scene_starts)):
+                for s in scene_starts) or
+            any(a + sample_offset + separation >= b - .05
+                for a,b in zip(scene_starts,scene_starts[1:]))):
         raise MotionProofError("Invalid or repeated moving-scene ranges")
-    if (type(sample_offset) not in (int,float) or not .5 <= sample_offset <= 1.2
-            or type(separation) not in (int,float) or not .3 <= separation <= .9
-            or type(threshold) not in (int,float) or not 3 <= threshold <= 18):
-        raise MotionProofError("Unsafe motion verification configuration")
     try:
         source = inspect_mp4(Path(mp4), max_size=80*1024*1024)
     except PreviewExportError as exc:
         raise MotionProofError("Rendered MP4 failed trusted codec/input preflight") from exc
     if abs(source["seconds"]-seconds) > .45:
         raise MotionProofError("Encoded video duration not as expected")
+    original_identity, original_sha = _stable_source(mp4)
     measured = []
     for start in scene_starts:
         a=_frame(Path(mp4),round(start+sample_offset,3))
@@ -73,10 +113,13 @@ def verify_moving_scenes(mp4: Path, *, seconds: int, scene_starts,
         if average < threshold:
             raise MotionProofError(
                 f"Expected moving scene near {start}s is frozen or insufficiently distinct")
+    final_identity, final_sha = _stable_source(mp4)
+    if (final_identity, final_sha) != (original_identity, original_sha):
+        raise MotionProofError("Encoded video source changed during motion sampling")
     return {
         "status":"MOVING_PIXELS_VERIFIED_NOT_CONTENT_APPROVAL",
         "duration_seconds":seconds,
-        "source_sha256":hashlib.sha256(Path(mp4).read_bytes()).hexdigest(),
+        "source_sha256":original_sha,
         "threshold_luma_difference":threshold,
         "checked_moving_scenes":measured,
         "garment_fidelity_verified":False,
~~~~

### video-engine/feature4_export_matrix.py
~~~~diff
@@ -0,0 +1,147 @@
+#!/usr/bin/env python3
+"""Feature4 F4-03: bind 15/30/60 ACTUAL local MP4 evidence on a single code head.
+
+No renderer/model/hosting runs here. This checks codec/shape/duration and exact
+file bytes; a self-declared source SHA is NOT an Actions attestation, rights
+grant, human visual acceptance, or proof that footage is customer-approved.
+"""
+from __future__ import annotations
+
+import argparse
+import hashlib
+import json
+import os
+import stat
+from pathlib import Path
+import re
+import subprocess
+
+from render_adapter import CreativeRenderError, verify_mp4
+
+SHA = re.compile(r"^[0-9a-f]{40}$")
+DIGEST = re.compile(r"^[0-9a-f]{64}$")
+SECONDS = (15, 30, 60)
+MAX_BYTES = 80 * 1024 * 1024
+
+
+class MatrixEvidenceError(ValueError):
+    pass
+
+
+def _stable_sha(path):
+    """Before/after stat and content check of bounded regular, non-symlink file."""
+    try:
+        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
+        with os.fdopen(fd, "rb") as stream:
+            before = os.fstat(stream.fileno())
+            if not stat.S_ISREG(before.st_mode):
+                raise MatrixEvidenceError("Missing or unsafe encoded MP4")
+            if not 1024 < before.st_size <= MAX_BYTES:
+                raise MatrixEvidenceError("Output is empty or beyond private reviewer cap")
+            digest = hashlib.sha256()
+            for part in iter(lambda: stream.read(1024 * 1024), b""):
+                digest.update(part)
+            after = os.fstat(stream.fileno())
+            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
+                    after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
+                raise MatrixEvidenceError("Encoded source mutated during hashing")
+            current = os.lstat(path)
+            if (not stat.S_ISREG(current.st_mode) or
+                    (current.st_dev, current.st_ino, current.st_size) !=
+                    (after.st_dev, after.st_ino, after.st_size)):
+                raise MatrixEvidenceError("Encoded source path replaced during hashing")
+            return before.st_size, digest.hexdigest()
+    except OSError as exc:
+        raise MatrixEvidenceError("Missing or unsafe encoded MP4") from exc
+
+
+def verify_export_matrix(manifest, source_root, *, expected_head):
+    if type(expected_head) is not str or not SHA.fullmatch(expected_head):
+        raise MatrixEvidenceError("Expected exact checkout commit SHA")
+    if type(manifest) is not dict or set(manifest) != {"schema", "source_commit", "renders"}:
+        raise MatrixEvidenceError("Unexpected export matrix manifest")
+    if (manifest["schema"] != "feature4_export_matrix_inputs_v1" or
+            manifest["source_commit"] != expected_head):
+        raise MatrixEvidenceError("Reels must claim this same exact checkout SHA")
+    rows = manifest["renders"]
+    if type(rows) is not list or len(rows) != 3:
+        raise MatrixEvidenceError("Exactly three actual 15/30/60 exports required")
+    root = Path(source_root)
+    if not root.is_dir() or root.is_symlink():
+        raise MatrixEvidenceError("Expected one existing private source directory")
+    verified = []
+    found = set()
+    seen_paths = set()
+    for row in rows:
+        if type(row) is not dict or set(row) != {"seconds", "path", "sha256"}:
+            raise MatrixEvidenceError("Unexpected export-row fields")
+        seconds, name, claimed_digest = row["seconds"], row["path"], row["sha256"]
+        if type(seconds) is not int or seconds not in SECONDS or seconds in found:
+            raise MatrixEvidenceError("Missing or duplicated export duration")
+        if (type(name) is not str or not name or len(name) > 120 or
+                name in (".", "..") or "/" in name or "\\" in name or
+                not name.endswith(".mp4") or name in seen_paths):
+            raise MatrixEvidenceError("Only distinct local MP4 basenames supported")
+        if type(claimed_digest) is not str or not DIGEST.fullmatch(claimed_digest):
+            raise MatrixEvidenceError("Missing immutable original media SHA")
+        path = root / name
+        size, actual = _stable_sha(path)
+        if actual != claimed_digest:
+            raise MatrixEvidenceError("Manifest original-byte SHA mismatch")
+        try:
+            probe = verify_mp4(path, duration=seconds, width=1080, height=1920, fps=24)
+        except CreativeRenderError as exc:
+            raise MatrixEvidenceError("Actual encoded 1080x1920 H264/AAC/24fps proof failed") from exc
+        if (type(probe) is not dict or type(probe.get("bytes")) is not int or
+                probe["bytes"] != size or _stable_sha(path) != (size, actual)):
+            raise MatrixEvidenceError("Encoded MP4 changed during verification")
+        found.add(seconds)
+        seen_paths.add(name)
+        verified.append({"seconds": seconds, "file_name": name,
+                         "bytes": size, "sha256": actual,
+                         "code_sha_claim": expected_head,
+                         "encoded_codec_check": "H264_AAC_YUV420P_1080X1920_24FPS"})
+    if found != set(SECONDS):
+        raise MatrixEvidenceError("15/30/60 profile coverage is incomplete")
+    return {
+        "schema": "feature4_15_30_60_local_export_matrix_v1",
+        "status": "ALL_THREE_LOCAL_ENCODED_PROFILES_TECHNICALLY_CHECKED",
+        "source_commit_claim": expected_head,
+        "code_commit_attested_by_ci": False,
+        "renders": sorted(verified, key=lambda r: r["seconds"]),
+        "scope": "PRIVATE_OFFLINE_SOURCE_VERIFICATION_ONLY",
+        "commercial_release_eligible": False,
+        "retailer_media_rights_verified": False,
+        "human_visual_approval": False,
+        "speech_alignment_verified": False,
+        "hosted_dev_e2e_verified": False,
+    }
+
+
+def main():
+    parser = argparse.ArgumentParser(description=__doc__)
+    parser.add_argument("--manifest", required=True)
+    parser.add_argument("--source-root", required=True)
+    parser.add_argument("--report", required=True)
+    args = parser.parse_args()
+    manifest_path = Path(args.manifest)
+    report = Path(args.report)
+    if (manifest_path.is_symlink() or not manifest_path.is_file() or
+            manifest_path.stat().st_size > 32_768):
+        raise MatrixEvidenceError("Only bounded private manifest files accepted")
+    if (report.exists() or report.is_symlink() or report.suffix != ".json" or
+            not report.parent.is_dir() or report.parent.is_symlink()):
+        raise MatrixEvidenceError("Report must be a new private JSON file")
+    expected_head = subprocess.check_output(
+        ["git", "rev-parse", "--verify", "HEAD"], text=True,
+        timeout=5, cwd=Path(__file__).resolve().parents[1]).strip()
+    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
+    evidence = verify_export_matrix(manifest, args.source_root, expected_head=expected_head)
+    with report.open("x", encoding="utf-8") as handle:
+        json.dump(evidence, handle, indent=2)
+        handle.write("\n")
+    print(evidence["status"] + " — NOT customer/hosted quality approval")
+
+
+if __name__ == "__main__":
+    main()
~~~~

### video-engine/feature4_minute_quality_receipt.py
~~~~diff
@@ -53,12 +53,17 @@ def validate_visibility_evidence(*, original, provenance, visibility_proof):
     v=_record(visibility_proof)
     windows=p.get("scene_windows")
     measured=v.get("checked_scenes")
-    if (v.get("schema")!="feature4_scene_visibility_v2"
+    if (v.get("schema")!="feature4_scene_visibility_v3"
             or v.get("status")!="SAMPLED_SCENES_NOT_BLANK_NOT_CONTENT_APPROVAL"
             or v.get("source_sha256")!=_sha(original)
             or v.get("seconds")!=60
             or v.get("checked_scene_count")!=12
             or v.get("sample_fractions")!=[.15,.30,.50,.70,.85]
+            or v.get("continuous_full_reel_black_scan") is not True
+            or v.get("continuous_black_hold_threshold_seconds")!=.65
+            or type(v.get("continuous_long_black_holds_count")) is not int
+            or v["continuous_long_black_holds_count"]!=0
+            or v.get("sub_threshold_blank_frames_certified_absent") is not False
             or v.get("short_blank_frames_excluded_by_sampling") is not False
             or v.get("sustained_near_black_count")!=0
             or v.get("commercial_release_eligible") is not False
@@ -67,6 +72,21 @@ def validate_visibility_evidence(*, original, provenance, visibility_proof):
             or not isinstance(windows,list) or len(windows)!=12
             or not isinstance(measured,list) or len(measured)!=12):
         raise MinuteProofError("60s visual scene evidence incomplete or overclaimed")
+    # A matched pair of provenance/visibility JSON cannot jointly omit or
+    # overlap part of the minute. Require finite positive contiguous windows.
+    cursor=0.0
+    for window in windows:
+        if (type(window) is not dict or set(window)!={"start","duration"}
+                or type(window["start"]) not in (int,float)
+                or type(window["duration"]) not in (int,float)
+                or not math.isfinite(window["start"])
+                or not math.isfinite(window["duration"])
+                or window["duration"]<=0
+                or abs(window["start"]-cursor)>.003):
+            raise MinuteProofError("60s visibility scene windows are not contiguous")
+        cursor=window["start"]+window["duration"]
+    if abs(cursor-60)>.003:
+        raise MinuteProofError("60s visibility scenes do not cover the full minute")
     for want,got in zip(windows,measured):
         if (type(want) is not dict or type(got) is not dict
                 or set(want)!={"start","duration"}
~~~~

### video-engine/feature4_scene_visibility.py
~~~~diff
@@ -10,6 +10,7 @@
 import hashlib
 import json
 import math
+import re
 from pathlib import Path
 import subprocess
 
@@ -46,9 +47,40 @@ def _sha(path:Path):
     return digest.hexdigest()
 
 
-# The scene's interior is sampled, not its transition edges. This is *not* a
-# continuous no-black-frame certification: an intervening flash may be missed.
+# Independent full-file decoder detects sustained black holds between sample
+# probes without claiming that every sub-second blank frame is impossible.
 INTERIOR_SAMPLE_FRACTIONS=(.15,.30,.50,.70,.85)
+BLACK_HOLD_MIN_SECONDS=.65
+_BLACK_HOLD_RX=re.compile(
+    r"black_start:(\d+(?:\.\d+)?)\s+black_end:(\d+(?:\.\d+)?)"
+    r"\s+black_duration:(\d+(?:\.\d+)?)"
+)
+
+
+def _continuous_black_holds(source, *, seconds):
+    """Scan all decoded video frames for >=.65s near-uniform black holds."""
+    try:
+        run=subprocess.run([
+            "ffmpeg","-nostdin","-hide_banner","-loglevel","info",
+            "-protocol_whitelist","file","-i",str(source),
+            "-map","0:v:0",
+            "-vf","blackdetect=d=0.65:pix_th=0.05:pic_th=0.98",
+            "-an","-f","null","-",
+        ],capture_output=True,text=True,check=True,timeout=160)
+    except (OSError,subprocess.SubprocessError) as exc:
+        raise VisibilityProofError("Continuous actual encoded black-frame scan failed") from exc
+    matches=list(_BLACK_HOLD_RX.finditer(run.stderr))
+    if run.stderr.count("black_start:")!=len(matches):
+        raise VisibilityProofError("Incomplete black-frame scan evidence")
+    holds=[]
+    for match in matches:
+        start,end,span=map(float,match.groups())
+        if (not all(math.isfinite(x) for x in (start,end,span))
+                or start<0 or end<=start or end>seconds+.5
+                or abs(end-start-span)>.08 or span<BLACK_HOLD_MIN_SECONDS-.09):
+            raise VisibilityProofError("Inconsistent continuous black-frame event")
+        holds.append((round(start,3),round(end,3),round(span,3)))
+    return holds
 
 
 def verify_scene_visibility(source:Path,*,seconds:int,scenes):
@@ -97,14 +129,21 @@ def verify_scene_visibility(source:Path,*,seconds:int,scenes):
                         "samples":samples,"sustained_near_black":blank})
         if blank:
             raise VisibilityProofError(f"Encoded scene at {start}s has a nearly entirely blank/black sample")
+    holds=_continuous_black_holds(source,seconds=seconds)
     if _sha(source)!=source_sha:
         raise VisibilityProofError("Encoded Reel bytes changed while scene frames were decoded")
-    return {"schema":"feature4_scene_visibility_v2",
+    if holds:
+        raise VisibilityProofError("Encoded Reel contains a sustained continuous black hold")
+    return {"schema":"feature4_scene_visibility_v3",
             "status":"SAMPLED_SCENES_NOT_BLANK_NOT_CONTENT_APPROVAL",
             "source_sha256":source_sha,
             "sample_fractions":list(INTERIOR_SAMPLE_FRACTIONS),
             "seconds":seconds,"checked_scene_count":len(scenes),
             "checked_scenes":checked,"sustained_near_black_count":0,
+            "continuous_full_reel_black_scan":True,
+            "continuous_black_hold_threshold_seconds":BLACK_HOLD_MIN_SECONDS,
+            "continuous_long_black_holds_count":0,
+            "sub_threshold_blank_frames_certified_absent":False,
             "short_blank_frames_excluded_by_sampling":False,
             "unexpected_overlay_absence_verified":False,
             "commercial_release_eligible":False,
~~~~

### video-engine/feature4_worker_handoff.py
~~~~diff
@@ -7,7 +7,10 @@
 """
 from __future__ import annotations
 
+import hashlib
 import math
+import os
+import stat
 import tempfile
 from pathlib import Path
 from uuid import UUID
@@ -39,6 +42,40 @@ class Feature4ClaimBusy(RuntimeError):
     """The job is claimed elsewhere; existing queue retry policy owns this."""
 
 
+def _staged_fingerprint(path):
+    """Hash only a stable regular file without following staged symlinks.
+
+    This prevents a renderer or another local actor from silently replacing
+    downloaded approved bytes during CPU work. It does not independently
+    prove a provider's remote object SHA or grant commercial rights.
+    """
+    try:
+        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
+        with os.fdopen(fd, "rb") as stream:
+            first = os.fstat(stream.fileno())
+            if not stat.S_ISREG(first.st_mode) or not 0 < first.st_size <= MAX_TOTAL_STAGED_BYTES:
+                raise Feature4HandoffError("Private staged asset must be nonempty bounded regular file")
+            digest = hashlib.sha256()
+            for block in iter(lambda: stream.read(1024 * 1024), b""):
+                digest.update(block)
+            last = os.fstat(stream.fileno())
+            if (first.st_dev, first.st_ino, first.st_size, first.st_mtime_ns) != (
+                    last.st_dev, last.st_ino, last.st_size, last.st_mtime_ns):
+                raise Feature4HandoffError("Private staged asset changed while hashing")
+            # An opened descriptor can still contain approved OLD bytes when
+            # the path was atomically replaced with a same-content new inode.
+            current = os.lstat(path)
+            if (not stat.S_ISREG(current.st_mode)
+                    or (last.st_dev, last.st_ino, last.st_size, last.st_mtime_ns) !=
+                       (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns)):
+                raise Feature4HandoffError("Private staged asset path changed while hashing")
+            return first.st_size, digest.hexdigest()
+    except Feature4HandoffError:
+        raise
+    except OSError as exc:
+        raise Feature4HandoffError("Private staged asset cannot be verified") from exc
+
+
 def _uuid(value, label):
     if type(value) is not str:
         raise Feature4HandoffError(label + " must be canonical UUID")
@@ -184,6 +221,9 @@ def process_feature4_render(job_id, admin, media, *, render_fn=run_compiled_reel
     if admin.render_authorized(claim) is not True:
         admin.render_failure(claim, "ACCESS_REVOKED", permanent=True)
         return "DENIED"
+    # Stale claims must never initiate private source download or CPU work.
+    if admin.feature4_claim_current(claim) is not True:
+        return "STALE"
     try:
         request, manifest, objects, audit = _bundle(claim, admin.load_feature4_bundle(claim))
         with tempfile.TemporaryDirectory(prefix="retailgrowth-f4-") as tmp:
@@ -193,16 +233,30 @@ def process_feature4_render(job_id, admin, media, *, render_fn=run_compiled_reel
             staging.mkdir()
             output.mkdir()
             staged_bytes = 0
+            staged_fingerprints = {}
             for asset_id, key in objects.items():
                 path = staging / manifest["assets"][asset_id]["path"]
                 media.download(claim["shop_id"], key, path)
                 if not path.is_file() or path.is_symlink():
                     raise Feature4HandoffError("Private media source was not staged safely")
-                staged_bytes += path.stat().st_size
+                fingerprint = _staged_fingerprint(path)
+                staged_bytes += fingerprint[0]
                 if staged_bytes > MAX_TOTAL_STAGED_BYTES:
                     raise Feature4HandoffError("Total staged media exceeds the private worker budget")
+                staged_fingerprints[asset_id] = fingerprint
+            # Lost lease or revoked rights during stage: prevent expensive CPU.
+            if (admin.render_authorized(claim) is not True
+                    or admin.feature4_claim_current(claim) is not True):
+                return "STALE"
             result = render_fn(request, manifest, staging, output)
             result_path, probe = _verified_render_result(result, output, claim, request, audit)
+            # The renderer must consume the exact approved staged originals.
+            # Reject late replacement, append/truncation and symlink swap before
+            # the worker uploads any private output or finalizes billing.
+            for asset_id, original in staged_fingerprints.items():
+                path = staging / manifest["assets"][asset_id]["path"]
+                if _staged_fingerprint(path) != original:
+                    raise Feature4HandoffError("Private staged media changed during render")
             if admin.render_authorized(claim) is not True or admin.feature4_claim_current(claim) is not True:
                 # Lease lost while expensive CPU work ran: never publish or bill.
                 return "STALE"
~~~~

### video-engine/hyperframes/benchmark_render.py
~~~~diff
@@ -8,11 +8,13 @@
 from __future__ import annotations
 
 import argparse
+import hashlib
 import json
 import os
 from pathlib import Path
 import platform
 import signal
+import stat
 import subprocess
 import tempfile
 import time
@@ -64,6 +66,37 @@ def sample_process_group(pgid, *, proc_root=Path("/proc")):
     return rss, ticks, len(active & records.keys())
 
 
+def verified_output_sha256(path):
+    """Hash exactly one stable regular render file, rejecting symlink swaps.
+
+    The hash binds a *local synthetic benchmark receipt* to the encoded bytes
+    actually left on disk; not cloud artifact custody or a rights approval.
+    """
+    try:
+        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
+        with os.fdopen(fd, "rb") as source:
+            before = os.fstat(source.fileno())
+            if not stat.S_ISREG(before.st_mode) or before.st_size < 1024:
+                raise ValueError("Expected nonempty regular encoded benchmark output")
+            digest = hashlib.sha256()
+            for block in iter(lambda: source.read(1024 * 1024), b""):
+                digest.update(block)
+            after = os.fstat(source.fileno())
+            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
+                    after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
+                raise ValueError("Benchmark output changed while hashing")
+            # The path itself must still refer to that file, not a late swap.
+            current = os.lstat(path)
+            if (not stat.S_ISREG(current.st_mode) or
+                    current.st_dev != after.st_dev or
+                    current.st_ino != after.st_ino or
+                    current.st_size != after.st_size):
+                raise ValueError("Benchmark output path changed")
+            return after.st_size, digest.hexdigest()
+    except OSError as exc:
+        raise ValueError("Benchmark output could not be safely hashed") from exc
+
+
 def benchmark(project, output, report, *, timeout_seconds=420, use_npm_node22=False,
               sampling_interval=0.2):
     if type(timeout_seconds) is not int or not 20 <= timeout_seconds <= 780:
@@ -78,6 +111,8 @@ def benchmark(project, output, report, *, timeout_seconds=420, use_npm_node22=Fa
         raise ValueError("Expected an existing approved local HyperFrames composition")
     if report.suffix != ".json" or report == output:
         raise ValueError("Expected separate JSON performance evidence file")
+    if output.exists() or output.is_symlink() or report.exists() or report.is_symlink():
+        raise ValueError("Benchmark output and report destinations must be new")
     command = (["npm", "exec", "--yes", "--package=node@22", "--", "node"] if use_npm_node22
                else ["node"]) + [str(NODE_SCRIPT), str(project), str(output)]
     started = time.monotonic()
@@ -116,6 +151,7 @@ def benchmark(project, output, report, *, timeout_seconds=420, use_npm_node22=Fa
         raise RuntimeError("Bounded local HyperFrames render exceeded timeout")
     if process.returncode != 0 or not output.is_file():
         raise RuntimeError("Local HyperFrames render failed; inspect restricted CI job output")
+    output_bytes, output_sha256 = verified_output_sha256(output)
     ticks_per_second = os.sysconf("SC_CLK_TCK")
     report_data = {
         "kind": "OFFLINE_SYNTHETIC_HYPERFRAMES_CPU_BENCHMARK_NOT_AZURE",
@@ -126,7 +162,13 @@ def benchmark(project, output, report, *, timeout_seconds=420, use_npm_node22=Fa
         "width": config["width"],
         "height": config["height"],
         "fps": config["fps"],
-        "output_bytes": output.stat().st_size,
+        "output_bytes": output_bytes,
+        "output_sha256": output_sha256,
+        # Declared current Git checkout, not a signed CI provenance attestation.
+        "source_commit_claim": subprocess.check_output(
+            ["git", "-C", str(ROOT.parents[1]), "rev-parse", "--verify", "HEAD"],
+            text=True, timeout=5).strip(),
+        "output_hash_type": "SHA256_STABLE_LOCAL_REGULAR_FILE_ONLY",
         "runtime_platform": platform.platform(),
         "cpu_count_visible": os.cpu_count(),
         "wall_seconds": round(time.monotonic() - started, 3),
@@ -152,7 +194,9 @@ def benchmark(project, output, report, *, timeout_seconds=420, use_npm_node22=Fa
         ).returncode == 0,
     }
     report.parent.mkdir(parents=True, exist_ok=True)
-    report.write_text(json.dumps(report_data, indent=2, sort_keys=True) + "\n")
+    # Keep the benchmark receipt from overwriting another job's proof.
+    with report.open("x", encoding="utf-8") as handle:
+        handle.write(json.dumps(report_data, indent=2, sort_keys=True) + "\n")
     print("PASS: source-only HyperFrames sampled benchmark", json.dumps({
         k: report_data[k] for k in (
             "duration_seconds", "width", "height", "wall_seconds",
~~~~

### video-engine/hyperframes/ci-smoke.sh
~~~~diff
@@ -113,6 +113,25 @@ python3 "$ROOT/video-engine/feature4_edited_export_qa.py" \
   --source "$EDITED_MP4" \
   --report "$ROOT/ci-artifacts/feature4-30s-editor-encoded-parity.json"
 
+# F4-04: duplicate is a DIFFERENT real editor action from split/reorder.
+# Reuse the same approved mock-only fixture and actual HyperFrames engine,
+# physically encode a second 30s 540p video and prove two 5s video scenes
+# restart the same source in-point. Never release synthetic footage to users.
+DUPLICATE_PROJECT="$TEMP/duplicate-30s-composition"
+DUPLICATE_MP4="$ROOT/ci-artifacts/feature4-30s-540p-actual-duplicate-mock.mp4"
+python3 "$ROOT/video-engine/demo_feature4_edited_reel.py" \
+  "$DUPLICATE_PROJECT" --width 540 --operation duplicate
+if (( NODE_MAJOR >= 22 )); then
+  timeout --signal=TERM --kill-after=10s 420s node \
+    "$ROOT/video-engine/hyperframes/render.mjs" "$DUPLICATE_PROJECT" "$DUPLICATE_MP4"
+else
+  timeout --signal=TERM --kill-after=10s 420s npm exec --yes \
+    --package=node@22 -- node "$ROOT/video-engine/hyperframes/render.mjs" \
+    "$DUPLICATE_PROJECT" "$DUPLICATE_MP4"
+fi
+python3 "$ROOT/video-engine/feature4_edited_export_qa.py" \
+  --source "$DUPLICATE_MP4" --operation duplicate \
+  --report "$ROOT/ci-artifacts/feature4-30s-duplicate-encoded-parity.json"
 
 # Once the first source benchmark is recorded, keep this as an opt-in gate to
 # avoid paying a 60s full-resolution encode on every unrelated branch change.
~~~~

### video-engine/professional.py
~~~~diff
@@ -24,6 +24,38 @@
 VERSION = "rg_video_v2"
 MODES = {"text", "image", "poster", "media", "music_sync"}
 TEMPLATES = {"streetwear", "cinematic", "festival"}
+# Single, fixed renderer-authorized vocabulary. Client/user CSS is never accepted.
+SUPPORTED_ANIMATIONS = frozenset({"subtle_zoom", "fade", "slide", "pop", "glow"})
+SUPPORTED_TRANSITIONS = frozenset({"fade", "slide", "cut"})
+# Four strictly bounded, server-reviewed channel gains. No arbitrary filters.
+AUDIO_GAIN_LIMITS = {
+    "source": (0.2, 1.0), "music": (0.0, 1.0),
+    "voiceover": (0.2, 1.0), "sfx": (0.0, 0.5),
+}
+
+
+def checked_audio_mix(value, *, has_music, has_voice, has_source, has_sfx):
+    """Deny unknown, inactive, unbounded or unapproved gain controls."""
+    if value is None:
+        return {}
+    if type(value) is not dict or set(value) - set(AUDIO_GAIN_LIMITS):
+        raise VideoPlanError("Unknown or unapproved audio mix controls")
+    available = {"source": has_source, "music": has_music,
+                 "voiceover": has_voice, "sfx": has_sfx}
+    levels = {}
+    for name, raw in value.items():
+        low, high = AUDIO_GAIN_LIMITS[name]
+        if (available[name] is not True or type(raw) not in (int, float)
+                or not math.isfinite(raw) or not low <= raw <= high
+                or abs(raw * 100 - round(raw * 100)) > 1e-7):
+            raise VideoPlanError("Audio mix requires present approved track and bounded 0.01 gain")
+        levels[name] = round(float(raw), 2)
+    return levels
+
+
+def _gain_text(gain):
+    return f"{gain:.2f}".rstrip("0").rstrip(".")
+
 UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,36}$")
 ASSET_ID = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")
 IMAGES = {".png", ".jpg", ".jpeg", ".webp"}
@@ -98,7 +130,7 @@ def checked_video(path):
 
 def validate(plan, manifest, asset_root, allow_test_media=False):
     fields(plan, {"version", "shop_id", "mode", "template", "duration_seconds", "output",
-                  "scenes", "cta", "music_asset_id", "voiceover_asset_id", "caption_cues", "beats", "brand", "logo_asset_id"},
+                  "scenes", "cta", "music_asset_id", "voiceover_asset_id", "audio_mix", "caption_cues", "beats", "brand", "logo_asset_id"},
            {"version", "shop_id", "mode", "template", "duration_seconds", "output", "scenes", "cta"}, "plan")
     fields(manifest, {"shop_id", "assets"}, {"shop_id", "assets"}, "manifest")
     if plan["version"] != VERSION or plan["shop_id"] != manifest["shop_id"] or not UUID.fullmatch(str(plan["shop_id"])):
@@ -150,9 +182,9 @@ def validate(plan, manifest, asset_root, allow_test_media=False):
         clean_text(scene["headline"], "approved headline", 110)
         if "offer" in scene:
             clean_text(scene["offer"], "approved offer", 70)
-        if scene.get("animation_preset", "subtle_zoom") not in ("subtle_zoom", "pop", "fade", "slide", "glow"):
+        if scene.get("animation_preset", "subtle_zoom") not in SUPPORTED_ANIMATIONS:
             raise VideoPlanError("Unknown approved animation preset")
-        if scene.get("transition", "fade") not in ("fade", "slide", "cut"):
+        if scene.get("transition", "fade") not in SUPPORTED_TRANSITIONS:
             raise VideoPlanError("Unknown reviewed transition")
         sfx_id = scene.get("sfx_asset_id")
         if sfx_id is not None:
@@ -259,6 +291,11 @@ def validate(plan, manifest, asset_root, allow_test_media=False):
         if b <= prev:
             raise VideoPlanError("Beats must be strictly ascending")
         prev = b
+    checked_audio_mix(
+        plan.get("audio_mix"), has_music=music_id is not None,
+        has_voice=voice_id is not None, has_source=source_audio,
+        has_sfx=any(s.get("sfx_asset_id") is not None for s in scenes),
+    )
     if plan["mode"] == "music_sync":
         if music_id is None or len(beats) < 2:
             raise VideoPlanError("Beat-sync requires rights-cleared music and beat timestamps")
@@ -303,6 +340,11 @@ def compile_composition(plan, manifest, asset_root, output_dir, allow_test_media
     if brand.get("primary_color"):
         accent = brand["primary_color"]
     k = html.escape(kicker)
+    mix = checked_audio_mix(
+        plan.get("audio_mix"), has_music=plan.get("music_asset_id") is not None,
+        has_voice=plan.get("voiceover_asset_id") is not None, has_source=source_audio,
+        has_sfx=any(s.get("sfx_asset_id") is not None for s in plan["scenes"]),
+    )
     components = []
     for i, scene in enumerate(plan["scenes"]):
         start, length = scene["start"], scene["duration"]
@@ -318,7 +360,7 @@ def compile_composition(plan, manifest, asset_root, output_dir, allow_test_media
                 media_markup = (
                     f'<video class="footage clip" id="video{i}" src="{src}" '
                     f'data-start="{start}" data-duration="{length}" data-media-start="{trim}" '
-                    f'data-track-index="0" data-volume="1" playsinline{original_audio}{mute}></video>'
+                    f'data-track-index="0" data-volume="{_gain_text(mix.get("source", 1.0))}" playsinline{original_audio}{mute}></video>'
                 )
             else:
                 media_markup = f'<img class="product-photo" src="{src}" alt="" decoding="sync">'
@@ -336,7 +378,7 @@ def compile_composition(plan, manifest, asset_root, output_dir, allow_test_media
             src = names[scene["sfx_asset_id"]]
             components.append(
                 f'<audio id="sfx{i}" src="{src}" data-start="{start}" '
-                f'data-duration="{min(2, length)}" data-track-index="6" data-volume="0.25"></audio>'
+                f'data-duration="{min(2, length)}" data-track-index="6" data-volume="{_gain_text(mix.get("sfx", .25))}"></audio>'
             )
         animation = scene.get("animation_preset", "subtle_zoom")
         transition = scene.get("transition", "fade")
@@ -431,9 +473,17 @@ def compile_composition(plan, manifest, asset_root, output_dir, allow_test_media
   font-weight:500;font-size:{width//12}px!important}}
 .role-outro .kicker{{margin:0 0 2%}}
 .role-outro .editorial-rule{{display:none}}
+.anim-subtle_zoom .glass{{animation:presetSubtleZoom var(--span) ease-in-out both}}
+.anim-fade .glass{{animation:presetFade var(--span) linear both}}
 .anim-pop .glass{{animation:promoPop var(--span) ease-in-out both}}
+.anim-glow .glass{{animation:presetGlow var(--span) ease-in-out both}}
 .anim-glow .offer{{text-shadow:0 0 15px {accent},0 0 30px {accent}75}}
+.anim-slide .glass{{animation:presetSlide var(--span) ease-out both}}
 .anim-slide .photo-wrap{{animation:editorialDrift var(--span) ease both}}
+@keyframes presetSubtleZoom{{0%{{opacity:.88;transform:scale(.975)}}18%{{opacity:1}}100%{{opacity:1;transform:scale(1.025)}}}}
+@keyframes presetFade{{0%{{opacity:0}}18%{{opacity:1}}100%{{opacity:1}}}}
+@keyframes presetSlide{{0%{{opacity:0;transform:translateY(7%)}}18%{{opacity:1;transform:translateY(0)}}100%{{opacity:1}}}}
+@keyframes presetGlow{{0%{{filter:drop-shadow(0 0 0 {accent}00)}}35%{{filter:drop-shadow(0 0 16px {accent}75)}}100%{{filter:drop-shadow(0 0 5px {accent}30)}}}}
 @keyframes editorialFade{{0%{{opacity:0}}7%{{opacity:1}}96%{{opacity:1}}100%{{opacity:.98}}}}
 @keyframes editorialSlide{{0%{{opacity:0;transform:translate3d(7%,0,0)}}14%{{opacity:1;transform:translate3d(0,0,0)}}100%{{opacity:1;transform:translate3d(0,0,0)}}}}
 @keyframes editorialDrift{{0%{{transform:scale(1.025) translate3d(-1%,1%,0)}}100%{{transform:scale(1.12) translate3d(1%,-1%,0)}}}}
@@ -487,13 +537,13 @@ def compile_composition(plan, manifest, asset_root, output_dir, allow_test_media
             f'data-start="{cue["start"]}" data-duration="{cue["duration"]}" '
             f'data-track-index="8"><span>{safe}</span></div>'
         )
-    # Narration is a full-length approved audio source, not 2-second SFX.
-    # Fix gain in the trusted renderer until an advanced audio-mix contract exists.
+    # Narration is an approved full-length audio source; fixed per-track gains
+    # do not imply arbitrary mix automation or actual speech QA.
     if plan.get("voiceover_asset_id") is not None:
         src = names[plan["voiceover_asset_id"]]
         components.append(
             f'<audio id="approved-voiceover" src="{src}" data-start="0" '
-            f'data-duration="{duration}" data-track-index="7" data-volume="1" '
+            f'data-duration="{duration}" data-track-index="7" data-volume="{_gain_text(mix.get("voiceover", 1.0))}" '
             f'data-fade-in="0.10" data-fade-out="0.16"></audio>'
         )
     # Duck ONLY the licensed bed beneath clips retaining their original sound.
@@ -504,7 +554,10 @@ def compile_composition(plan, manifest, asset_root, output_dir, allow_test_media
             aid = scene.get("asset_id")
             is_source_sound = bool(aid and ordered[aid][1] == "video"
                                    and not scene.get("mute_source", False))
-            gain = "0.12" if (is_source_sound or plan.get("voiceover_asset_id") is not None) else "0.55"
+            music_gain = mix.get("music", .55)
+            gain = _gain_text(min(music_gain, .12) if
+                              (is_source_sound or plan.get("voiceover_asset_id") is not None)
+                              else music_gain)
             start, length = scene["start"], scene["duration"]
             fade = min(0.12, length / 6)
             components.append(
@@ -514,7 +567,10 @@ def compile_composition(plan, manifest, asset_root, output_dir, allow_test_media
                 f'data-fade-in="{fade}" data-fade-out="{fade}"></audio>'
             )
     else:
-        gain = "0.15" if (source_audio or plan.get("voiceover_asset_id") is not None) else "0.55"
+        music_gain = mix.get("music", .55)
+        gain = _gain_text(min(music_gain, .15) if
+                          (source_audio or plan.get("voiceover_asset_id") is not None)
+                          else music_gain)
         components.append(
             f'<audio id="soundtrack" src="{soundtrack}" data-start="0" '
             f'data-duration="{duration}" data-track-index="5" data-volume="{gain}" '
~~~~
## Original #966 HEAD 9962da1764d54b199fc069e9cf0f02f911849327
https://github.com/saifsiddiqui59/RetailGrowthAI/pull/966/files

### docs/DECISIONS.md
~~~~diff
@@ -1125,3 +1125,37 @@ Owner direction to reuse original VoiceStudio code implemented with unchanged pi
 - Accept **source-only** recovery of old #767 private trace generation/scope fence into #960; no backend authorization implied. Accept compatible #796 Unicode/bidi control checks into newest main under #962, retaining valid Devanagari virama conjunct behavior and mock-only provider tests, **not** old signed CAS/editor approval. Separate reviewer/security approval remains needed for hosted tenant/JWT/RLS/VoiceStudio/F4/F7 changes, original F2-03/F2-12/F2-17 task status not automatically DONE.
 - Archive-only source preservation and source-level mock CI never grant rights for real media, commercial voice inference, paid provider, GPU, PROD or WineShopPOS.
 
+## 2026-11-15 — F4 stale PR cleanup only on exact consolidated source proof
+- Close redundant old feature-stacked draft PR objects only when every changed path is already preserved as an identical Git blob in an explicitly surviving open consolidation with its source/test/docs traceability. Verified #822 (5/5), #824 (3/3) and #827 (3/3) all reside unchanged in #828; each old PR closed **UNMERGED**. Never count closure or archiving as accepted product work.
+- Unique patches and unresolved semantic differences remain open until selectively integrated into current parent #322 and accepted by exact-head + fresh-main four-job tests and required review. The handoff is documented at `docs/integration/F4_STACKED_DRAFT_DEDUP_20261115.md`. No new architecture or hosted approval implied.
+
+## 2026-11-17 — F4 preserve stronger current-parent authorization during source consolidation
+- Prefer surgical imports to wholesale old-parent merges. F4-11 original stable-file source/tests may be copied exactly when unchanged. For F4-15 retain **both** per-download and pre/post bundle claim/rights guards while adding SHA/inode-stable staged source proofs; older #828 code alone omits some newer per-download checks. For F4-05 reuse renderer whitelist constants but retain newer footage-layer transition rendering absent from old source. Tests must cover both old and new guards. Record source as IN PROGRESS until exact-head CI plus main acceptance, never equate retired stacked PRs with task DONE.
+
+## 2026-11-17 — Multi-PR cleanup requires verifiable surviving source, not misleading DONE
+- User-directed integration sprint retired 12 additional obsolete F4 drafts #808, #816, #686, #690, #731, #701, #723, #753, #792, #784, #803, #799 **unmerged** after checking exact heads, original changed Git blobs, test migration and/or equivalent stronger current-parent protections. Each old PR received a current evidence comment, a named surviving branch (#779 or #322), original ID remaining work, and outstanding CI/hosted acceptance. PR closure is not a source/main merge, customer rights/license, real media, product feature DONE or approval waiver.
+- Do not restore old source wholesale where it regresses current F4: #723's decoded-frame guard ported alongside distinct encoded duplicate flow; #753 contiguous 60s checks ported into newer v3 black-scan receipt; #784 native cancelled clip drag fix ported without undoing bounded-frame seeking; #803 all-rendered-asset release rights and #799 anti-alias/no-op media proof exact original sources/tests can be safely retained on current #322 because latest source was no stronger except already compared compatibility. Others stay open if not proven duplicates.
+- Keep final exact-head 4/4 CI and fresh main 4/4 plus review/hosted acceptance separate before original task DONE. Feature #5 GPU OFF; paid/cloud/PROD/WineShopPOS unchanged.
+
+## 2026-11-17 — second batch of F4 stale DRAFT cleanup
+- Closed #745, #773, #735, #830, #850, #841, #837, #831, #839, #851, #835, #845 as UNMERGED PR objects only after original exact-head, ancestry/code/blob and test guard traceability. Surviving #779/#852 remain open; original F4 tasks stay IN PROGRESS and original PR object closure is not source/main acceptance.
+- Current parent now checks actual encoded output stable SHA/inode across renderer, guards after upload, requires exact tenant/job/lease output key, and rejects encoded traversal or noncanonical private inputs. No existing current-parent staged-source SHA/lease/tenant rights guard was removed. F4-06 reviewed four-channel gain work remains on #779 until compatible parent integration; no unapproved browser audio control enabled.
+
+## 2026-11-17 — F4 cross-snapshot integrity and source-preserving closure
+- The release/worker sha256 alone cannot detect `os.replace` with identical bytes between fingerprint reads. Return size and content SHA at original tuple indexes plus stable filesystem `st_dev/st_ino/st_mtime_ns`; retain no-follow FD identity validation before/during hashing. Preserve both staged **input** swap and private **output** same-byte atomic swap negative tests.
+- Persisted Feature7 reviewed edit approval must bind the entire canonical decision SHA, not only review ID. Import original #906 source/test SHA into current F4 parent instead of reimplementing a parallel feature or allowing browser-provided review evidence. Old drafts #715/#852/#906 may be retired unmerged only once code, tests and original notes are preserved. Still require real hosted DB/JWT/RLS approval and independent Feature7 affected-lead review; task not DONE by PR count reduction.
+- Preserve original #828 tracker history as docs-only provenance without changing running parent CI head. No F4 task status changed to accepted.
+
+## 2026-11-17 — Retire #828 only after exact parent four-job CI; preserve F2 one-shot gaps
+- An old Feature4 stacked source PR with 12 changed files may be retired unmerged when original code/tests/handoffs are proven preserved in a stronger current parent, missing original tracker lines archived and **exact current parent head four-job CI 4/4 SUCCESS**. This condition was met for #828 against current F4 #322 head `97e17c10`, run #44001722737. This does NOT complete original F4 task or authorize main merge, visual content/tenant rights or hosted release.
+- Old Feature2 #720/#684/#707 source-only duplicates were retired into #848 with verified original rights-safe test coverage and exact handoff artifacts. A **different** F2 retake #697 must stay OPEN: successor #848 omitted immutable one-shot `job_key` from trusted private writer data/receipt, potentially accepting a cross-job stored asset despite a verified claim. Do not close based on newer branch age or similar function names; affected lead must fix and prove security, then review. No lowering independent approval.
+
+## 2026-11-17 — Preserve old F4 preview and CPU proof without resetting newer protections
+- F4-08 #733 preview-scrub source-only change can retire unmerged after transplanting source/video-model test and original handoff into current #322; preserve stronger bounded playhead, tenant-private preview and pointer cancellation. Do not confuse muted source preview with final composited frame/render grant.
+- F4-14 source-only 15/30/60 CPU receipt aggregator and unit negatives can be copied exactly when required benchmark/export helpers are byte-identical in survivor and parent. It performs **no actual media encoding** and gives NO Azure cost authorization, spending cap, cloud benchmark, GPU or retailer visual approval.
+- Feature4 historical provenance can be archived verbatim (12 exact blobs) from #779, but do not merge stale/conflicted code or close #779 until remaining behaviors are individually verified. Historical F3 shared docs #873 can retire only after all 294 changed lines are preserved on review-gated #966; archived CI facts are **historical**, not current source acceptance.
+
+## 2026-11-17 — F4 parent retains stronger trust boundaries while recovering #779 media/audio controls
+- Import old #779's F4-07 strictly bounded, optional `audio_mix` as a TRUSTED private cross-feature contract only after track presence, finite 0.01 volume limits, tenant/rights checked upstream; disallow arbitrary FFmpeg filters and caller-provided grants. Preserve newer current parent footage-layer transitions and audio ducking. Require affected-lead independent review before main integration. F4-04 proof remains tied to externally supplied exact renderer SHA/inode despite added original motion/boundary probes; independent stronger duplicated-video QA is retained.
+- Native pointer-cancel/approval/tenant lifecycle controls and private audio mastering 0600/fsync+owned-inode cleanup are security boundaries; reject stale old branch variants and preserve deterministic negative regressions. Archive the four old #779 tracking/handoff blobs verbatim instead of replacing newer source-ledger/docs, which are not equivalent to reviewed/accepted work.
+- Do not claim original F4-02/04/07/10/14/15 DONE on source code or docs closure. Exact final branch 4/4, safe main integration, fresh main 4/4 and rights/hosted visual acceptance remain separate.
~~~~

### docs/NEXT_TASK.md
~~~~diff
@@ -1502,3 +1502,45 @@ Feature3 NEXT: verify main CI #41820799158, integrate reviewed 24-component sour
 4. For each missing old feature patch, inspect archived diff and latest same-module code, port only missing behavior into **reviewable current-main feature-owned changes**, keep existing newer sources, run exact-head four jobs and fresh main four jobs. Shared JWT/RLS/storage/F4/F7/Functions routes require independent affected-lead review. Do not turn disabled Kokoro/Azure-only voice drafts into active model calls: favor approved VoiceStudio CPU-only. Azure #249 and #650 remain OPEN.
 5. Continue other independent non-GPU Feature2 source jobs while private hosted test identities/licenses/editor rights are unavailable. No paid provider, Azure SQL/PROD, new GPU or WineShopPOS mutation.
 
+## 2026-11-15 — After F4 source-duplicate cleanup (#822/#824/#827)
+1. Keep surviving [#828](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/828) OPEN. Reconcile its 11 preserved original changed-file source/test/handoff blobs into current F4 parent [#322](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322) without overwriting newer code. The three exact-duplicate child PR objects are CLOSED UNMERGED, **not accepted DONE**.
+2. Inspect unique missing code in #735/#745/#753/#773/#784/#799/#803 and verify #808 semantically before any closure. Use [source dedup checkpoint](integration/F4_STACKED_DRAFT_DEDUP_20261115.md). No blanket closure of unported or unproven work.
+3. Run appropriate CPU/FFmpeg/UI negatives, four exact-head CI jobs, authorized review, and four independent fresh-main CI jobs for each eventual merge. Feature4 tasks remain IN PROGRESS pending evidence; GPU/paid AI/DEV/PROD/WineShopPOS unchanged.
+
+## 2026-11-17 — F4 next acceptance after preserving #828 unique source
+1. Check PR #322 exact final head CI for the F4-05/F4-11/F4-15 source hardening. Run/fix targeted CPU/FFmpeg negative tests if failed. Do not count cancelled or superseded heads as passing.
+2. Verify original #828 feature code/tests and four original handoff documents are preserved in the newer F4 parent with **additional** lease/rights and footage fixes; only then close superseded #828 with explicit evidence. Remaining F4 stale drafts #735/#745/#753/#773/#784/#799/#803/#808 require separate reconciliation, not blanket closure.
+3. Parent #322 is still DRAFT, not main accepted. Require eligible review, main-targeted PR exact-head 4/4 and fresh main 4/4 for any accepted task status. No GPU/provider/Azure/SQL/PROD/WineShopPOS activation.
+
+## 2026-11-17 — F4 post-12-draft retirement next integration steps
+1. Verify exact latest #322 parent head `3c29fec1718b4bf03ae29c54dedd52cc701ce2b2` passes four mandatory CI jobs; if its branch moves, verify the new head instead. Preserve all original/new negative tests and fix actual failing code rather than disabling them. Distinguish prior failed/cancelled runs from PASS.
+2. Reconcile #779 after the #723/#753/#784 fixes into **current** #322 without losing newer footage/pointer/tenant rights, F4-05 actual animation CSS, staged file SHA/inode and F4-13 all-media release gate. Run targeted frontend/Playwright & CPU QA; never bulk-merge conflicted old source. Keep #779 OPEN until current-branch proof.
+3. Reconcile #828 remaining source/tests/handoffs into #322 and only retire it after exact-head CI and source preservation evidence. Do not close outstanding unique #735/#745/#773/#733/#830 etc. based solely on titles or stale branch age. All F4 original task IDs remain IN PROGRESS until main integration + fresh main 4/4 and reviewed hosted acceptance.
+4. Keep #966 docs review, #551/#848 F2 source work, Azure #249 and #650 separately open. No GPU, paid inference, PROD, cloud deployment or WineShopPOS changes.
+
+## 2026-11-17 — F4 next after 24 stale source PR retirements
+1. Confirm exact latest #322 head 4d31fec8396759c5d9889c2b9960262490f8b428 CI #43999989563 all four required jobs. Fix actual source tests; do not label earlier run #43996971323 PASS because long FFmpeg harness was cancelled after its 733 Python media unit tests passed.
+2. Reconcile surviving #779 original F4-04 duplicate/encoded-cut/motion tests and F4-06/07 approved bounded audio source into CURRENT #322, retaining new encoded SHA/lease/canonical input and actual footage transitions. Review current #852 distinct F4-08/12/14 source; do not bulk-merge stale parent or discard existing rights fixes.
+3. Leave #828, #779, #852 OPEN until exact evidence confirms every unique source/test and final CI. Separate distinct #733/#906 reviews. Only accepted fresh-main 4/4 + authorized feature review may mark task DONE. No GPU/cloud/PROD/WineShopPOS.
+
+## 2026-11-17 — Follow-up after #715/#852/#906 source dedup
+1. Inspect current F4 parent #322 exact-final-head four-job CI at `97e17c10fd5ca2de2968e3adaa0b336d2979d5b2` (or newer if concurrently advanced); fix real failures without disabling tests. Previous FFmpeg run #44000451010 failed on same-byte atomic output swap; this source race is now addressed by binding size/SHA/device/inode/mtime. The missing staged source same-byte regression from #852 has also been restored.
+2. Verify source equivalence + original tests/handoffs on obsolete #828 and retire only after current-parent CI/source proof; continue F4 #779 safe reconciliation instead of old-parent bulk merge. Feature7 approval-digest code from old #715/#906 is in parent but **independent affected-lead review and trusted DB persistence remain outstanding**.
+3. Keep #966 independent docs review, #551/#848 F2, Issue #249, F3/F5/F7 queues separate; no false DONE credit or production/paid/GPU actions.
+
+## 2026-11-17 — Continuation after #828 exact CI pass and Feature2 dedup
+1. Proceed Feature4 source consolidation #779 vs current parent #322, keeping parent reviewed SHA/inode, full-media rights, editor decision digest and real CSS/footage protections. #828 is closed SOURCE-DUPLICATE after exact F4 parent 4/4; original task acceptance still needs eligible reviewed main merge and fresh main 4/4, plus real hosted/rights media conditions. Do not reopen/re-merge old #828 blobs wholesale.
+2. Feature2 #848 is still stacked on #551; run exact-final-head 4/4 after added #707 test functions, reconcile F2-02/F2-04/F2-29 without duplicate PR creation. Keep #697 OPEN until retake `job_key` bound to private pending writer and original negative tests restored; ensure correct server/tenant/plan and no rights/billing bypass. Keep #700 OPEN until after-store writer response contract reviewed. Never pretend synthetic signed fixture is real rights.
+3. Docs #966 remains review-gated despite its prior exact-head 4/4; run CI for this new checkpoint and require independent shared-doc review. No GPU/paid inference/hosted deployment/PROD/WineShopPOS.
+
+## 2026-11-17 — Follow-on sprint actual next actions after F4-08/F4-14 source recovery
+1. Check exact-head F4 parent #322 `3a09f6c29ee6db9bc15f61e3b18de38e53c76fb2` CI #44009262867 (all four mandatory jobs); repair any failures in owned code/tests before claiming source readiness. A cancelled run or old-head PASS is insufficient.
+2. Continue carefully reconciling **remaining differing** #779 F4 source/test paths into current #322. Preserve current rights, lease, staged SHA/inode, negative tests, bounded preview/drag and F4-13 all-media release checks. Do not close #779 until exact-source coverage, final CI, review and task traceability are verified.
+3. Independent F4-14: obtain actual 15/30/60 same-head private encoded MP4s and honest local CPU/RSS reports **only when an authorized bounded test run is available**, not from fake fixtures; never enable GPU or expensive services. F4-08 requires hosted, same-shop signed preview/seek and browser negatives. Both original tasks stay IN PROGRESS even if stale PRs retire.
+4. #873 historical docs preserved in #966 archive; require independent applicable shared-doc review and four-job exact final CI for #966 before merge. Do not mark F3-08/13 DONE from historical notes.
+
+## 2026-11-17 — Finish source reconciliation before retiring F4 #779
+1. Verify #322 final exact head `c2bc9ff9b47c46c9186a72b9faa86e894bebb1cd` four-job CI #44011387138; if moved, use newer head. Repair real failing CPU/media/frontend tests rather than removing security guard, especially F4-04 original decoded frame probes and F4-07 mixed-gain synthetic fixtures.
+2. Compare old #779 against current F4 parent for remaining *semantically distinct* audio-master/report negatives and any original source/export contract gaps, preserving the #779 original historic Git blobs now archived. Close old #779 **only after** exact-source/negative-test survival, latest CI 4/4 and review evidence. No old bulk merge over newer tenant/rights/preview paths.
+3. Keep F4-07 audio gain and F4-10 pointer edits source-only pending independent affected-lead review of cross-feature approved audio mix and signed DEV/browser tests; the F4-14 three-profile evidence checker does not establish real 15/30/60 CPU measurements. Parent DRAFT must meet main PR eligibility and fresh main 4/4 before accepted original task DONE.
+4. Keep docs #966 independently reviewed; no auto GPU, cloud activation, customer media signoff, paid inference or WineShopPOS modification.
~~~~

### docs/PROJECT_STATE.md
~~~~diff
@@ -1493,3 +1493,41 @@ Feature3 verified source-integration checkpoint:
 - New [#962](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/962) surgically ports original #796 invisible/bidi Unicode prompt-safety restrictions onto **current-main** `prompt_improver.py`, with new tests; legitimate Hindi virama conjuncts preserved, mock LLM only. Exact-head [CI #43713860334](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43713860334) **4/4 PASS**, merged `e9610ffd32e27b9c9dc02aac5770c0dec45fe080`; fresh main [CI #43714482943](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43714482943) **COMPLETED SUCCESS 4/4**. Original reviewed prompt CAS and stored script review are **NOT** integrated or accepted.
 - No Azure or Supabase deployment/migration, paid AI inference, model weights, GPU, PROD or WineShopPOS mutation. Feature2 38 original IDs remain unchanged.
 
+## 2026-11-15 — Integration Sprint Feature4 duplicate-source retirement
+- Exactly three older stacked Feature4 draft PRs [#822](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/822), [#824](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/824), [#827](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/827) were **closed UNMERGED** after all **11/11 changed-file Git blobs** were confirmed byte-identical to surviving open consolidated [#828](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/828). This is deduplication only, not main integration or Feature4 acceptance.
+- Eleven F4 drafts inspected; other eight kept open because unique source exists or exact dedup is unverified. [F4 parent #322](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322) remains DRAFT and #828 remains OPEN. See [F4 dedup checkpoint](integration/F4_STACKED_DRAFT_DEDUP_20261115.md) for original heads, code preservation, and next tasks. No tests, main code merge, GPU, DEV/PROD or WineShopPOS writes in this cleanup.
+
+## 2026-11-17 — F4 parent source hardening (pending final CI)
+- Parent [#322](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322) now contains selectively reconciled original F4-11 stable encoded MP4 original SHA/inode proof; F4-15 same-shop local staged-media SHA/inode integrity and pre-bundle claim freshness; and F4-05 editor/renderer effect vocabulary parity. Its newer footage-layer transitions and per-asset lease/rights checks were deliberately retained instead of copying older #828 wholesales. Original scoped handoffs are retained under `video-engine/feature4/INTEGRATION_SPRINT_F405_F411_F415_20261117.md` on the F4 branch. **Final current-head CI and independent main integration are not yet verified**, so F4-05/F4-11/F4-15 remain IN PROGRESS. Parent #322 and consolidated #828 still OPEN; no F4 task DONE or cloud/GPU/PROD/WineShopPOS action.
+
+## 2026-11-17 — F4 twelve more obsolete draft PRs retired unmerged with source preservation
+- **12 additional F4 stale DRAFT PRs CLOSED/UNMERGED:** #808, #816, #686, #690, #731, #701, #723, #753, #792, #784, #803, #799; live repository open PR count after closure **56** (snapshot only). This is review hygiene, **NOT** 12 completed tasks, not merged main code. All original F4-02/04/10/11/13/14/15/31 tasks remain IN PROGRESS.
+- Survivor F4 source consolidation [#779](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/779) head `27c3729c8d222b0c4450e509de7acfaf721ed019`: original #808 5/5 and #816 4/4 code/test/handoff Git blob matches, original historical notes archived; #686 exact 5/5 non-tracker blobs; #701 original Playwright E2E+fixture+handoff exact and safer bounded-frame seek supersedes old UI; #723 strict grayscale decode + negative tests ported; #753 continuous full-minute positive contiguous scene windows and original negatives ported into v3 QA; #784 cancelled-drag event fence and Playwright negative tests ported. Source branch #779 is still OPEN, stale/conflicting with stronger parent, not main-accepted.
+- Feature4 parent [#322](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322) current code checkpoint `3c29fec1718b4bf03ae29c54dedd52cc701ce2b2`: original #690 staged source integrity and all old test lines superseded by stronger SHA+inode guards, #731 late encoded-frame mutation regression ported, #792 dot-only/trailing-slash/ASCII-control storage key safety & negatives ported; #803 exact 3/3 original source/test/handoff Git blobs restored for all-rendered-media rights; #799 exact 3/3 source/test/handoff Git blobs restored for immutable render-stage path/SHA separation. Also preserves prior #828 F4-05/11/15 reconciliation and four source handoffs.
+- Parent #322 remains **DRAFT**, stacked [#828](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/828) remains OPEN pending exact final-head CI/source acceptance. No main merge, hosted DEV rights/visual acceptance, GPU/paid/cloud/PROD/WineShopPOS mutation. Shared docs [#966](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/966) review remains independent.
+
+## 2026-11-17 — additional twelve F4 stale drafts retired with original source preserved
+- This execution closed UNMERGED twelve F4 drafts: #745, #773, #735, #830, #850, #841, #837, #831, #839, #851, #835, #845, reducing live open PR count 56 to 44 at snapshot. With prior twelve F4 stale drafts retired in the adjacent batch, 24 F4 PR objects were retired, but NO original feature task was marked DONE or merged to main.
+- Surviving F4 source PR #779 at head c1d66e9b3903c45ae4cc9930ad1362a38b3f8843 contains original #745 and #773 in-video motion/near-cut negatives, original #735 compiled duplicate project test, six exact original #830 bounded four-channel audio gain source/test/handoff blobs, and #845 exact two audio-master source/test blobs plus now exact original handoff. Provenance recorded inside video-engine/feature4/ORIGINAL_*_PROVENANCE_20261117.md and RUN_CHECKPOINT_F4_07.md. PR #779 remains OPEN and conflicts with stronger parent.
+- Surviving F4 chain PR #852 head 7ce7dbfea81a9ee028d7378f7ad6f3889dfe5ac9 is verified descendant of #850/#841/#837/#831/#839/#851/#835: exact original code/test blob matches for #850 4/4, #841 3/3, #837 5/5, #831 3/3, #835 3/3 and stronger descendant guards with old negative tests for #839/#851; all original tracker nonblank lines retained. PR #852 remains OPEN.
+- Current F4 parent PR #322 head 4d31fec8396759c5d9889c2b9960262490f8b428: repaired two old SHA-negative fixtures in 2bbc2ab5; ported unique #828 post-staging lease regression in 23bf21e1; ported from #852 stable encoded output SHA/inode/size checks before and after private upload, exact shop/job/lease uploaded key, canonical tenant input paths, four targeted negative regressions and original handoffs at 4d31fec8. Stronger newer tenant source SHA/rights/lease checks retained. Run #43996971323 had 733/733 media unit tests PASS but FFmpeg full harness CANCELLED; NOT 4/4. New exact head CI #43999989563 IN PROGRESS at checkpoint. #322 remains DRAFT, #779/#852/#828 remain OPEN, original tasks remain IN PROGRESS. GPU/paid/provider/cloud/PROD/WineShopPOS unchanged.
+
+## 2026-11-17 — Additional duplicate PR retirements, F4 safety remediation
+- In continuation sprint, stale source-only drafts #715 (approved Feature7 edit digest), #852 (tenant object keys + same-byte inode source guard), and #906 (review digest consolidation) were each **CLOSED UNMERGED** after source preservation against a named surviving F4 parent/child; original F4-04/F4-13/F4-15/F4-20 remain IN PROGRESS. Current open PR count 42 at this checkpoint (live snapshot only; concurrent workers may change it).
+- Current parent #322 source head `97e17c10fd5ca2de2968e3adaa0b336d2979d5b2`: exact original #906 reviewed Feature7 decision digest source+tests integrated, original #715 provenance and current #906 handoff retained; #852 original same-byte source inode-replacement regression ported. Encoded output upload SHA/device/inode/mtime fingerprint repaired at `fc9788bc` after a prior FFmpeg CI failure; exact latest parent four-job CI pending, not asserted passed. Parent #322 remains DRAFT; no main merge.
+- Original #828 historical tracker-only lines now preserved in `docs/integration/F4_828_ORIGINAL_TRACKER_PROVENANCE_20261117.md` on this docs PR. #828 and #779 remain OPEN pending verified source reconciliation/CI. No GPU/paid/cloud/PROD/WineShopPOS mutation.
+
+## 2026-11-17 — #828 retired after exact 4/4, F2 three duplicate drafts preserved
+- Current Feature4 parent [#322](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322) source head `97e17c10fd5ca2de2968e3adaa0b336d2979d5b2` exact [Part1 run #44001722737](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44001722737) **4/4 SUCCESS** (Python, frontend, Supabase, FFmpeg). Obsolete F4 stacked DRAFT #828 head `ca103ce85` CLOSED UNMERGED: 5/12 changed file Git blobs exact current parent (including four original handoffs); remaining source/test semantics ported into stronger current code with every original test method retained; original 16 historical tracker lines archived in `docs/integration/F4_828_ORIGINAL_TRACKER_PROVENANCE_20261117.md`. Feature4 original tasks still IN PROGRESS; #322 remains DRAFT/unmerged and does not attest commercial/hosted acceptance.
+- Obsolete Feature2 stacked drafts #720, #684, #707 also CLOSED UNMERGED after recovered source/negatives and exact original handoffs into survivor [#848](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/848) head `a35a1f171819564bfb3ed00806e4a87545a8a043`. #720 original MP3 dual-private receipt superseded by stronger two UUIDs, SHA and atomic pair registration; #684 original Unicode tests retained with NFKC and rights-safe audio; #707 all five previously missing parametrized Unicode/RSS spoof tests imported and source handoff archived. F2-02/F2-04/F2-29 IN PROGRESS; #848 stacked on #551, not main accepted. **DO NOT close #697:** newer F2 retake source still lacks original one-shot job-key in private writer envelope and receipt (identified, owner notified on #848). **#700** likewise still requires review of mandatory post-store pending-rights fields. No GPU/paid/cloud/PROD/WineShopPOS changes.
+
+## 2026-11-17 — Subsequent integration checkpoint: 36 open, F4-08/F4-14 source and F3 docs retired
+- Live 36 open PRs at checkpoint (count is not a number of completed tasks). Original obsolete F4-08 draft #733 CLOSED UNMERGED after its source-preview-playhead helper, mapped authorized source seek and regression were reconciled into newer F4 parent [#322](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322) commit `8b1b9fb014f412474b8adfa63e74f9063786f978`. Original source handoff copied verbatim; UI still uses current tenant-authorized preview and bounded frame seek. F4-08 IN PROGRESS.
+- F4-14 offline no-GPU existing-15/30/60-CPU-receipt checker and tests copied from surviving OPEN [#779](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/779) into parent #322 as three exact blobs in `0d24c7e772cfbdab49a0e56edf1fb0b62928332b`. This does NOT run real three-duration media or establish cloud performance acceptance; F4-14 IN PROGRESS.
+- Parent #322 `3a09f6c29ee6db9bc15f61e3b18de38e53c76fb2` additionally preserves 12 exact former-#779 feature handoff/provenance Git blobs and an adapted synthetic duplicate-project regression test. #779 still OPEN/conflicting: many current-parent source differences require semantic review, not a bulk merge. Exact-parent CI #44009262867 pending.
+- Historical F3 docs PR #873 CLOSED UNMERGED after preserving 294 added original lines in `docs/integration/ARCHIVED_F3_PR873_20261117.md` on review-gated #966. This is an archive, not a new F3 acceptance event. #966 independently review-gated. GPU/paid AI/Azure/SQL/PROD/WineShopPOS unchanged.
+
+## 2026-11-17 — F4 consolidated source QA hardening after source-only #779 recovery
+- Feature4 parent [#322](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322) source checkpoint `c2bc9ff9b47c46c9186a72b9faa86e894bebb1cd`: selectively reconciled #779 F4-07 optional strictly bounded four-channel music/voice/SFX/source `audio_mix` with reviewed track-presence/finite/0.01 precision checks, deterministic ducking + four existing test regressions. Preserved newer footage-layer transitions and current creative contract authorization. Also restored F4-04 3s/17s moving-video and 5/13/15/21s near-cut negative pixel probes while retaining externally pinned SHA+inode source proof and separate duplicate video verifier. Two extra copy/no-op and malformed-grayscale negatives are not commercial content signoff.
+- Integrated F4-10 revoked/other-tenant pointer cancel lifetime guards and native cancelled-drag Playwright regression into current Timeline UI, preserving the authorized muted source jog and audio display. Private 60s audio mastering now includes 0600 exclusive no-follow **fsync-before-success** local proof, owned-inode-only partial cleanup, symlinked-ancestor rejection and replacement-race guard for unreceipted masters, with four offline regressions. Four original #779 tracker/handoff blobs preserved byte-identically under `video-engine/feature4/archive/pr779_*` with mapping `ARCHIVED_779_SOURCE_TRACKER_20261117.md`.
+- Parent #322 remains DRAFT; the latest exact-head four-job CI on `c2bc9ff9` **pending**, so **no F4 task DONE**. Stacked source #779 stays OPEN pending full parity/review + exact head CI; no main merge, real approved video, rights grant, GPU/paid services/PROD/WineShopPOS change. Shared docs PR #966 separately requires eligible independent review.
~~~~

### docs/WORK_LOG.md
~~~~diff
@@ -910,3 +910,45 @@ Work completed: #859 merged & postmerge 4/4, #866 merged (postmerge running), #8
 - [#962](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/962): surgical current-main port of #796 Unicode/invisible/bidi prompt control checks plus new negative tests and Hindi conjunct positive fixture, no model execution. Exact PR [#43713860334](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43713860334) **4/4 PASS**; merged `e9610ffd32e27b9c9dc02aac5770c0dec45fe080`; fresh main [#43714482943](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/43714482943) **COMPLETED SUCCESS 4/4**. Old signed prompt CAS not ported.
 - Original #551 has 171 changed paths, previously 58 exact main blobs / 105 absent / 8 different, and stacked #848 has 82 changed filenames (66 absent, 16 different at earlier checkpoint); these are **file counts**, not feature completion. Recompare against moving main before next batch. GPU/provider/paid AI, Azure/SQL, PROD and WineShopPOS unchanged by this run.
 
+## 2026-11-15 — Integration Sprint: F4 precise stale-draft source retirement
+- Reviewed first ten stale F4 drafts #735/#745/#753/#773/#784/#799/#803/#808/#822/#824, plus #827. Compared original changed paths, source snippets and active parent #322/batch #779/consolidation #828 Git blobs. Found several unique still-unported code paths; left eight drafts OPEN and did not force older file versions over newer current code.
+- Before closure, confirmed that F4 #822 exact head `1ba7949c` all 5/5 changed blobs, #824 head `3dd46820` all 3/3, and #827 head `b1a5058c` all 3/3 match surviving #828 head `ca103ce8`. Posted evidence comments on all three and #828, reverified all four heads, and closed only #822/#824/#827 **unmerged**. #828 and #322 remain open; no tests or main code merge claimed.
+- Added durable [F4 source dedup evidence](integration/F4_STACKED_DRAFT_DEDUP_20261115.md). Further source/security/rights integration and exact-head/main CI are pending. No GPU/paid model, Azure/SQL/PROD or WineShopPOS mutation.
+
+## 2026-11-17 — F4-05/F4-11/F4-15 code reconciliation into live parent #322
+- Verified exact #828 and current parent source/test blobs and compared functional differences before editing. Ported F4-11 original stable MP4 source/tests exactly (`e0bc41b4`, `70762243`); F4-15 staged SHA/inode/no-follow fingerprint and three targeted negative tests **while preserving stronger current per-download rights/lease tests** (`e69cb722`, `f486099a`); F4-05 shared renderer/editor allowlist and two parity/rejection tests while preserving newer footage transitions (`c1b415cb`, `da8870a0`, `31be150d`). Added F4-15 pre-bundle lease check + test (`0e634f8d`, `25d60c99`).
+- Four original #828 source handoff documents copied into parent, tracker and feature-owned integration checkpoint recorded in single CAS commit `713a2d98`, followed by F4-15 preflight checkpoint. F4 parent still DRAFT and #828 still OPEN pending final exact-head CI; source-only never treated as main/hosted DONE. No paid model, GPU, Azure/SQL/PROD or WineShopPOS change.
+
+## 2026-11-17 — 12 F4 source-preserving DRAFT PR retirements + current code fixes
+- Inspected live GitHub open queue (68 initially), current AGENTS/current four canonical docs and active feature self-merge policy, exact PR changed files/current heads, source/test SHA and branch ancestry. Verified and CLOSED UNMERGED twelve obsolete F4 drafts: #808, #816, #686, #690, #731, #701, #723, #753, #792, #784, #803, #799, leaving 56 OPEN (live snapshot). Per-PR evidence comments retained. These are **not** twelve accepted feature tasks.
+- Surviving [#779](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/779): original #808/#816 code+tests exact; #686 five exact non-tracker SHA; #701 original 3 exact blobs plus equivalent stronger bounded seek; #723 ported grayscale frame validation/4 malformed frame negatives at `0e0075e60e22a8b997f38b8c38966c92592ecdf1`; #753 ported finite contiguous full-minute windows and v3-compatible original tests at `703b9d540802ed005d355b1b7c1eababe89e74a6`; #784 ported cancelled native drag source + actual Playwright negative at `27c3729c8d222b0c4450e509de7acfaf721ed019`. Historical original SHA/provenance handoffs stored under `video-engine/feature4/ORIGINAL_*_PROVENANCE_20261117.md`.
+- Current F4 parent [#322](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322): #690/#731/#792 source/negative integration `022a3b4e0adb60242e277dd88112170bdee04617`; #803 all-rendered-media rights original exact 3/3 source+tests+handoff blobs `b590e8196ee10f3888ab6779f1ea3d664e76b162`; #799 alias/hardlink/unchanged SHA stage proof original exact 3/3 blobs `3c29fec1718b4bf03ae29c54dedd52cc701ce2b2`. All source/task handoffs and F4 tracker updated; no original F4 task marked DONE or any source directly merged to main. Current F4 parent exact-head CI still pending at checkpoint; do not inherit earlier cancelled/pass runs.
+- Docs review PR #966 remains OPEN. No GPU, paid AI, cloud deployment, Azure/SQL/PROD, WineShopPOS changes.
+
+## 2026-11-17 — twelve further F4 draft retirements and code fixes
+- Verified original heads, surviving exact Git file blobs and documented newer protections, then CLOSED UNMERGED #745, #773, #735, #830, #850, #841, #837, #831, #839, #851, #835, #845, taking queue 56 -> 44 open. #745/#773 encoded moving-clip and cut-boundary negatives ported into #779 in commits e3b43a4f/aaebd185/18438451/c80809fc; #735 real duplicate project test port f67b0ac6; original #830 six exact bounded audio source/tests/handoffs port a5c7d639; #845 two exact master source/test Git blobs and original handoff copied verbatim commit c1d66e9b. Retired #850/#841/#837/#831/#839/#851/#835 on proof of direct ancestry and unchanged source or preserved stronger guard in #852 (head 7ce7dbfe).
+- F4 parent #322: repaired the two old malformed-media fixtures exposed by stricter #799 no-op hash guard (2bbc2ab5), ported last original #828 pre-render claim-loss regression (23bf21e1); latest run #43996971323 completed CANCELLED after 733/733 media unit tests passed and many video renders, so 4/4 not verified. Ported source-superset render_adapter.py and tests from #852, plus current-compatible worker encoded output SHA/inode, changed-during-upload, canonical private key, exact authorized return key, four additional negative cases; parent source commit 4d31fec8, final CI #43999989563 pending. All original F4 tasks IN PROGRESS; parent DRAFT; surviving #779/#852/#828 OPEN. No paid, GPU, cloud, PROD or WineShopPOS actions.
+
+## 2026-11-17 — Continuation sprint 5: F4 original #715/#852/#906 safely retired
+- Rechecked live GitHub queue after 12 earlier closures: 44 open at initial check; three further original stacked Feature4 DRAFT PRs #715/#852/#906 closed **unmerged** after evidence comments and surgical source/test preservation. 42 open at last queue check (other chats may create/close PRs concurrently). Original task IDs remain IN PROGRESS.
+- #715 `dbae534f` source/test exact in surviving #906; archived original tracker/Azure handoff under `video-engine/feature4/ORIGINAL_715_PROVENANCE_20261117.md` on #906 commit `6f3ebd3c`. #852 `7ce7dbfe` originals contained distinct same-byte **staged input** inode replacement regression, copied into current parent #322 at `3a8b80b4`; original two handoff blobs identical in parent, tracker lines archived. #906 `6f3ebd3c` had exact source blob `efd57f56`, tests `937dee49`, both original doc handoffs copied into current parent at commit `97e17c10`; #906 then closed unmerged.
+- Diagnosed prior parent CI #44000451010: 3/4 PASS, FFmpeg 1/738 failure due same-byte atomic **output** replacement escaping SHA-only fingerprint check. Fixed helper to include device/inode/mtime without changing SHA/size indexes in `fc9788bc`; targeted regression retained. Latest exact-final-head CI not yet verified. Archived #828 16 missing historical tracker lines in `docs/integration/F4_828_ORIGINAL_TRACKER_PROVENANCE_20261117.md`. No main merge, no GPU, cloud, PROD or WineShopPOS mutation.
+
+## 2026-11-17 — Continuation sprint 6: F4 #828 full exact-CI source retirement; F2 #720/#684/#707 dedup
+- Verified F4 #322 exact head `97e17c10fd5ca2de2968e3adaa0b336d2979d5b2`, [Actions #44001722737](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44001722737) **Python/frontend/Supabase/FFmpeg 4/4 successful**. Compared 12 #828 paths: five old Git blobs exact against current parent, every original affected test method retained; remaining source has stronger authorization, checked original SHA + inode across source and upload, effect CSS and footage transitions. Historic 16 tracker-only lines preserved in current docs PR. Commented evidence and closed obsolete #828 DRAFT UNMERGED. #322 remains draft/not main DONE.
+- Feature2 #720 original dual-private MP3/WAV writer receipt handoff copied into #848, source superseded by stronger `atomic_pair_registered`, `derived_wav_private`, distinct UUIDs and SHA tests; closed #720 unmerged. #684 old editorial + MP3 test lines preserved in #848, exact original handoffs copied and closed unmerged. #707 five unique original Unicode NFKC/bidi/Hindi joiner/offer SKU/RSS spoof regression functions appended verbatim into `ai-agents/tests/test_feature2_editorial_basis.py` on #848 at `a35a1f171819564bfb3ed00806e4a87545a8a043`, exact handoff preserved, old PR closed unmerged. F2 head CI still needs verification; original F2 tasks not DONE. Found #697 F2 retake missing persisted `job_key` gap; left OPEN and commented on #848 (comment #6936163658).
+- Live PR count after #828 retirement **38 open** (snapshot can vary due parallel feature schedules). All source changes remain on respective existing feature branches, docs on separate PR #966. No main merge, GPU, paid, Azure/SQL/PROD or WineShopPOS.
+
+## 2026-11-17 — Continue 4 Sprint Status Recovery across actively changing branches
+- Refetched 44→38→36 live open PR queue; concurrent leads had closed #715/#906/#828 while their source/traceability was retained. Did not duplicate those closures or overwrite moving branch heads.
+- Committed F4-08 #733 authorized muted source-video frame jog `8b1b9fb0` (model helper, Node negative test, Timeline and VideoStudio wiring, original handoff, task tracker); closed #733 UNMERGED after exact-head comment. Feature owner source-only; parent #322 remains DRAFT.
+- Ported F4-14 exact source/tests/handoff Git blobs from #779 into #322 at `0d24c7e7`; checked `feature4_export_matrix.py` and `hyperframes/benchmark_render.py` dependencies were exact SHA matches. No real three-profile encoded/CPU test claimed.
+- Verified 13 missing #779 file paths versus current parent; copied 12 old handoff/provenance blobs by exact Git SHA and adapted old duplicate project regression from prior `operation` argument to newer `edit_mode` in commit `3a09f6c2`. Current final parent [CI #44009262867](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44009262867) pending at checkpoint; 21 differing source/test paths remain in OPEN #779.
+- Preserved 294 original added historical lines across five files of stale F3 PR #873 as `docs/integration/ARCHIVED_F3_PR873_20261117.md` on docs PR #966 (commit `d2ab2af9`), then closed #873 UNMERGED with evidence comment. This is archival only; docs review still required. No original Feature3/4 task marked DONE. No GPU/paid models, Azure/SQL/PROD, WineShopPOS modifications.
+
+## 2026-11-17 — Follow-up F4 #779 source synthesis and negative gate recovery
+- Committed current F4 parent #322 `0305a958f3b0602ba023274924058ea0b51a0e4d`: old #779 approved audio_mix four-channel bounds/track-preset semantics, composer track gains + scene duck, creative contract propagation and 4 original unit negatives; no newer footage transition overwritten.
+- Committed `f56455b75c7f360f73b9dbe9d5358bcb97217a43`: strict decoded grayscale buffer type/size guard compatible with 72×128 split and 72×96 duplicate verifier, added F4-04 original 3s/17s moving pixels and 5/13/15/21s near-cut probes with 3 old negative methods; retained independently pinned SHA/inode and original duplicate verifier.
+- Committed `add33908721faffba106b362f10897295980277e`: old F4-10 current-draft and approval-cancel-aware caption resize, immutable pointer-id release, native dragend cleanup, original Playwright harness + two negative tests; kept newer source preview jog, bounded frame seeking, audio UI.
+- Committed `d14fe47bc8062eda212b0f94820402a6ad79ac73`: audio mastering private proof fsync+owner-only replacement-safe cleanup, ancestor symlink rejection, safe master output replacement checking with 4 new tests. Historical #779 tracked files restored as four original Git blobs under F4 archive in `c2bc9ff9b47c46c9186a72b9faa86e894bebb1cd`.
+- **Current exact-head CI #44011387138 pending**, shared docs review #966 still OPEN. Original task statuses IN PROGRESS, no main/hosted accepted DONE; GPU/paid Azure/SQL/PROD/WineShopPOS untouched.
~~~~

### docs/integration/ARCHIVED_F3_PR873_20261117.md
~~~~diff
@@ -0,0 +1,315 @@
+# Historical F3 PR #873 source/CI checkpoint — archived on 2026-11-17
+
+This is a **verbatim archive of added historical lines** from the now-stale main-targeted Feature3 documentation PR [#873](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/873), original head `8cdbe41dab9e8a1f5c2c60003bb2de7ede099ce9`, created while independent review was still missing. It is NOT a current status report; GitHub source commits and CI results should be reverified before any claim about current Feature3 readiness. Current canonical docs and Feature3 original task ledger take precedence. The historical F3-13 / F3-08 source integration facts, security-review exceptions, hosted 0/33 caveat, and future work are preserved here so closing the obsolete doc PR does not erase them. **No task DONE or independent approval is asserted by this archive.**
+
+## Original added text: `docs/DECISIONS.md`
+
+
+
+## 2026-11-05 — Feature3 offline CPU draft export remains non-authoritative
+- Source decision implemented by PR #872: asynchronous `canvas.toBlob()` and local `File.text()` results must be scoped to the same mounted tenant/day, current edit and authorized media-map identity; stale responses are ignored, and concurrent export encodes are refused. Explicit own-property checks prevent inherited JavaScript keys from being mistaken for v2 formats or authorized private images. These are browser/CPU safety fences, **not** live server authorization, licensed provenance, a signed download route or permission to publish.
+- [Feature3 PR #872](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/872) merged into main as `b1509e24557530ce99e412d10213139893f30df3`; its exact final source head `5bf630b194c8df2fe34c284fc6a14426f677089a` passed [PR CI #41902676515](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41902676515) **4/4**, and [fresh main CI #41903466197](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41903466197) **4/4**.
+- Security-review caveat: zero independent GitHub reviews were submitted on #872 before merge, so source integration is verified but review acceptance is not. Require explicit review evidence separately. No new shared v1/v2 API/schema contract, GPU approval, hosted action or billing decision.
+
+## 2026-11-05 — Feature3 private PNG and cross-shop queue trust fences
+
+- Browser draft restore/save must resolve image-map grants with **own properties only**, not inherited `constructor`, `toString`, `__proto__` or other prototype fields. Loaded finite image dimensions are a UI precondition; original private media rights and RLS remain independently server verified (source PR #877, main `96bf834a`).
+- The private PNG HTTP adapter rejects malformed IHDR dimensions, illegal color/bit depth, unexpected PNG compression/filter/interlace or illegal chunk naming even with self-consistent CRC/SHA; negative tests must target *actually forbidden* dimensions, not permitted small image sizes (source PR #876, main `8c412e0`).
+- A Queue server-assigned **nil** GUID or a **repeated message GUID across two sends** is not an accepted delivery receipt for distinct dispatches. On an uncertain ACK stop before the next SQL confirmation/retry; offline two-shop failure injection is acceptable development evidence but never genuine provider financial/delivery proof (source PR #878, main `f21a9de7`).
+- All three source PRs passed exact final-head four-job CI and fresh main four-job CI. Owner-authorized source integration does not fabricate independent privacy/security review, live tenant approvals or hosted acceptance. Maintain GPU/paid services OFF and WineShopPOS untouched.
+
+## 2026-11-06 — F3-09 unknown write and strict private history boundaries
+
+- A failed/untrusted acknowledgement **after** an attempted v2 poster POST is an UNKNOWN commit outcome, not permission to send the same POST again. In-memory guard synchronously denies double writes and retains an uncertainty latch until a successful same-shop/day/API authenticated history read **plus an explicit user selection** of existing DRAFT or deliberate new document, with duplicate warning. Local validation errors before POST do not latch; old tenant/session callbacks cannot release the current gate. Source integrated #881.
+- Signed v2 draft-history lists must be strongly validated before React caches them: exact row/response keys, tenant/campaign/day, unique UUID, version/revision, document schema and shop binding, canonical digest syntax and review status. Never grant publication/media rights from browser status text. APPROVED/REJECTED are rendered as read-only **server statuses**, and only DRAFT is editable. Source integrated #882.
+- Immutable server document digest *syntax* is checked by browser; this is not proof of cryptographic equality to PostgreSQL JSON canonical hashing, commercial rights or independently reviewed permissions. GPU and paid AI remain OFF. No hosted SQL, PROD or WineShopPOS changes. Feature-owned merges passed 4/4 PR-head and fresh-main CI, including targeted recovery from a transient 54322 bind conflict on main run #42264379502.
+
+## 2026-11-06 — Feature3 single generated-output surface and read-only review snapshot
+
+- The optional v2 draft workspace must not mint legacy expiring Storage signed URLs just to display generated-job details. There is one authenticated Feature3GeneratedHistory surface; its separate current-rights private PNG reader remains default-OFF pending actual reviewed provider and route. Legacy API methods remain backwards-compatible without being used by the v2 draft UX.
+- Read-only review inspection of signed saved DRAFT/APPROVED/REJECTED rows is client-only, current tenant/campaign/day/API-scoped, schema-bounded and image-grant fenced. It withholds media bytes, remote URLs and private image source strings; it is not an accurate server-rendered final poster, copyright approval, publishing permission or signed role evidence. Inspected state clears on history reload and tenant/session changes.
+- PR #883 final head 183ee28f exact CI #42270219850 4/4; main merge e9a7d1d2 fresh CI #42270848090 4/4. This is a source component, with independent release/security rights review and hosted acceptance separate. No GPU, paid models, global auth changes, hosted SQL, PROD or WineShopPOS.
+
+## 2026-11-06 — Feature3 model preview Blob revocation ownership
+
+- Browser-side private generated/model preview lifecycle must retain ownership of each Blob URL until successful revoke, including if revoke throws; partial cleanup removes successfully revoked handles and preserves failures for a retry. Before cleanup or a new signed model GET, hide prior decoded private media from the current view. Deny new model loads while previous cleanup remains pending; use a synchronous one-flight read token before React state paints.
+- Source PR #884 exact head 08c5769e CI #42272456836 4/4, merged main e3a65d0d, fresh CI #42272979340 4/4. This is fixture-tested F3-10/F3-13 code; no claim of hosted revocation, licensed media, independent security approval or production availability. GPU, paid AI, hosted SQL, PROD and WineShopPOS untouched.
+
+## 2026-11-06 — F3-08 PNG covert payload and authoritative identity requirements
+
+- A whole-file SHA/PNG CRC plus decodable pixels is insufficient to authorize private output when the PNG's IDAT contains extra bytes after zlib EOF, a second compressed stream, or surplus decompressed scanlines. The private binary adapter must validate exact noninterlaced/Adam7 filtered scanline size and complete bounded zlib termination, while preserving opaque errors and the existing size threshold. This protects against hidden bytes inside otherwise well-formed private images. Source proposal #879, head `41fecbaf5d`, exact CI #42284441065 4/4, independent security review pending.
+- A trusted current-rights provider row must supply canonical **exact Python string** shop/job/asset UUIDs; arbitrary equality-overloaded object values do not prove identity. Source proposal #880, head `e98752d3bf`, exact CI #42284306824 4/4, independent rights/security review pending. Neither proposal supplies legal rights, JWT/RLS runtime validation or a mounted endpoint. GPU, hosted SQL, PROD and WineShopPOS remain OFF/unchanged.
+
+## 2026-11-08 — No duplicated private PNG parser at the Feature3 route
+
+- Reuse the existing `Feature3PrivateBinaryHTTP` for immutable SHA, generated-output receipt identity, PNG structure and HTTP headers. Keep the new route's exact-string shop/job scope check as defense against arbitrary equality objects; separately harden the canonical adapter itself so direct callers cannot be tricked. Preserve opaque denial responses, fresh rights/JWT reads, no signed Storage URLs, default-OFF route and no production authorization inferred from synthetic fixtures.
+- **2026-11-08 F3-08 source continuation (2026-11-07 UTC GitHub commits):** Existing [#880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880) head `918bbc14cef8bd6a9077ce766560d8fb8c8a4c3b` now delegates its GET-only private PNG HTTP response to the previously existing `Feature3PrivateBinaryHTTP` instead of maintaining a weaker parallel PNG parser. A scoped exact-string shop/job receipt boundary blocks equality-overloaded forged identifiers. Synthetic HTTP/route tests were updated to the complete private receipt, immutable SHA and opaque malformed-internal 503 semantics. The first refactor test run #42410099605 exposed 14 regressions, including a real 200-on-spoofed-scope defect; follow-up code/test repair was committed and [CI #42410323345](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42410323345) started. Concurrent existing [#879](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/879), head `60251cf930bb6131bad9e11f0713ca80ba50b12b`, adds exact-string shop/job checks and adversarial forged-equality tests to the underlying canonical binary adapter; [CI #42410451925](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42410451925) started. **At this documentation checkpoint, exact FINAL-head all-four CI results are not yet certified; verify both before source integration.** These PRs do not mount an Azure endpoint or supply real rights/JWT. Both remain sensitive and require independent security review; no new original task, merged DONE or hosted acceptance. Prior DEV_CODE_DONE 4/33 and hosted 0/33 unchanged. No GPU, paid inference, hosted database, PROD or WineShopPOS mutations.
+
+## 2026-11-08 — F3-08 canonical cache policy interoperability, no relaxation
+
+2026-11-08 F3-08 private PNG source correction: Existing [#880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880) head `7d7f885a5a26a57ae99cffee1a661b9c448f2331` fixes a real response-contract break introduced by its earlier header-hardening change. The Azure adapter had required `Cache-Control: no-store, private` but the trusted `Feature3PrivateBinaryHTTP` actually returns the equally private `no-store, private, max-age=0`; the mismatch caused **valid 256x256 synthetic PNG reads to return HTTP 503**. Prior exact-head [CI #42505722622](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42505722622) failed Python 1 test (1197 passed; other three jobs passed). The fix permits exactly the two established no-store/private variants with an exact Python string check; rejects public/cacheable or overloaded-equality policy values and strips backend response metadata from the Azure reply. Added positive strict-header, negative caching/equality spoof and end-to-end synthetic PNG header tests without disabling security tests. Latest exact-head [CI #42507466950](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42507466950) **4/4 SUCCESS** (Python/uv, FFmpeg, Supabase isolation, frontend/Chromium). Source only: no Azure route mounted, no live JWT/RLS, current rights backend/provider, real private download, GPU/provider spend, hosted SQL, PROD or WineShopPOS change. Existing canonical security PR #879 remains unmerged, and both sensitive source PRs and shared docs require independent GitHub review; original Feature3 DEV_CODE_DONE baseline **4/33**, fully hosted **0/33** unchanged.
+Decision: Keep both legacy `no-store, private` and canonical `no-store, private, max-age=0` as the only accepted downstream successful cache-policy values. Preserve response-level no-store/no-cache/Vary/Security headers and never pass through untrusted backend headers or signed URLs.
+
+## 2026-11-08 — Test source auth, private bytes and rights revocation together
+
+- Continued original F3-08 in existing source [PR #880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880): commit `6b8e8f86e670db8e0ffce4fd113d31cbf8c36c57` adds `tests/api/test_feature3_private_png_route_composed_two_shop.py`. Tests construct real in-process `handle_private_png_request` + `build_private_png_reader_factory` + `Feature3RevocablePNGReader`, with two isolated synthetic retailer JWTs/RLS rows, private PNG bytes, backend rights callback and authenticated Storage transport. Four tests cover (1) both shops getting only their own valid bytes and no leaked private headers, (2) foreign token denial before rights/Storage, (3) rights revoked during byte IO denying the returned PNG, and (4) JWT expiry during the read denying returned bytes and then recovery. All fake/local: **not** two live DEV identities, live JWT/RLS or a deployed route.
+- Python/uv [CI #42508181511](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42508181511) completed **1204 tests + 1152 subtests SUCCESS** on this head at the documentation checkpoint; **the other three jobs were still running and must be reverified before any 4/4 claim or source integration**. Prior source CI #42507466950 was 4/4 green on `7d7f885a` (cache-header fix), superseded by this new test-head.
+- PR #879 (canonical private binary) and PR #880 (route/rights) remain sensitive, unmerged and without real independent security review; docs #873 needs independent shared-document review too. Never classify test fixture as an accepted commercial license, hosted rights/JWT or Feature3 DONE. Original DEV_CODE_DONE baseline **4/33**, hosted **0/33** unchanged. GPU/paid model calls, hosted SQL, PROD and WineShopPOS untouched.
+
+## 2026-11-09 — F3-08 denial vs backend outage status contract
+
+Explicit failed rights/membership authorization remains opaque 404; rights transport failures are opaque 503 from the HTTP boundary. Malformed HTTP Authorization CR/LF is a bad framing request (400), while structurally invalid bearer credentials remain 401. Do not expose diagnostic exception text or private bytes in any denied response. **2026-11-09 F3-08 source repair, [PR #880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880) head `e9612a8ec30746a5e8a332545e7c0fa7621973bd`:** Prior updated source head `7fbe7b7d81d4302e9f75894768775a4aa3f0ffa8` [CI #42568255441](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42568255441) had **7 failing Python cases, 1253 passing tests and 1301 passing subtests**, with the other three jobs successful. Two root causes: new rights transport outage handling correctly preserved `TimeoutError` for opaque HTTP 503 but a legacy reader unit test still expected an explicit-access-denial exception (404), and a new early bearer parser classified CR/LF injection as 401 instead of the established 400 framing rejection. The new source change re-establishes early 400 for CR/LF before GET-body or backend access, updates the low-level outage assertion to match transport-vs-denial semantics, and adds full two-shop route-to-reader rights-outage negative tests for failures before and after Storage IO. The separate existing rights-outage test imports the fixture under a private alias. Latest [Actions #42570838025](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42570838025) **Python/uv PASSED: 1256 tests + 1308 subtests**; complete all-four final-head CI still requires verification at this document-writing checkpoint. This is source-only, with **NO** independently reviewed live rights provider or verified hosted JWT/RLS, no approved commercial media or activated private byte route; PRs #879/#880 and shared docs #873 remain unmerged/review-gated. Original F3-08 is **IN PROGRESS**, historic DEV_CODE_DONE **4/33**, fully hosted **0/33**. GPU/paid inference, hosted DB, PROD, WineShopPOS untouched.
+
+## Original added text: `docs/NEXT_TASK.md`
+
+
+
+## 2026-11-05 — Next Feature3 work after merged F3-13 CPU privacy source
+- [Feature3 PR #872](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/872) merged into main as `b1509e24557530ce99e412d10213139893f30df3`; its exact final source head `5bf630b194c8df2fe34c284fc6a14426f677089a` passed [PR CI #41902676515](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41902676515) **4/4**, and [fresh main CI #41903466197](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41903466197) **4/4**.
+1. Obtain and record a **genuine independent affected-lead/human privacy review** for the already-merged PR #872; GitHub review count was zero at merge. Review the exact diff for tenant/day scopes, inherited media maps, delayed PNG Blob and JSON callbacks. Never invent an approval or change an acceptance status without evidence.
+2. Continue original F3-09/F3-13 source fixtures and non-GPU UI/review integration where independent of unavailable hosted endpoints; use existing 33-package ledger to avoid repeat work. Preserve merged F3-13 code and targeted tests.
+3. Track #325/#471 real authenticated no-URL binary mount and #249 Azure 503 as hosted acceptance gates. Perform real signed DEV and commercial-rights tests only after their actual approved credentials/services exist; do not substitute synthetic fixtures for those claims.
+4. Keep F3-13 source-partial and original Feature3 **0/33 fully hosted accepted**; no user-provider/GPU/SQL/PROD/WineShopPOS actions authorized by this checkpoint.
+
+## 2026-11-05 — Feature3 next coding tasks after owner-authorized source merges
+
+- Do NOT reimplement PRs #876/#877/#878: F3-08 strict PNG dimensions, F3-09 private image-map own-key save/reopen protection, F3-05 nil/duplicate Queue message GUID and two-shop ambiguous ACK failure tests are present on verified main `f21a9de7e3a2ae2ee4a58db6f7fbe95265a99cf6`, fresh [CI #41981648369](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41981648369) **4/4**.
+- Continue genuine F3-08 code gap: mount the authenticated no-URL private PNG byte response only after service-owned current output rights authority, JWT/RLS checks and safe default-OFF rollout are wired. Existing `feature3_private_binary_http.py` alone is NOT a mounted Azure route. Do not enable an unsafe placeholder or reuse expiring signed URLs as proof of revocation.
+- Continue F3-09 offline/hosted save–reopen–review composition and F3-05 durable queue ACK/unknown-outcome reconciliation, using synthetic two-shop media and failure injection without paid GPU or customer accounts. Fixture-only successful tests may close a **DEV_CODE_DONE milestone** after verified main 4/4 but cannot fabricate live signed DEV or actual Azure ACK.
+- Current DEV-code snapshot **4 DONE / 8 in progress / 21 historically dependent**. Original hosted acceptance **0/33**. Unreviewed shared docs PR #873 retains independent review requirement; duplicate PR #874 was closed without merge. Do not ask owner to provide customer images or manually validate synthetic outputs.
+
+## 2026-11-06 — Feature3 next after two verified F3-09 code merges
+
+- Do **not** rebuild [#881](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/881) ambiguous draft POST write guard or [#882](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/882) strict tenant-bound versioned history/read-only status UI. Both are merged to latest main `d390e6552a6b19d1ba24978ce50c8eb656d5913f` and backed by final-head + fresh-main 4/4 evidence. Source handoffs under `frontend/src/features/creative/FEATURE3_F3_09_*_20261106.md`.
+- Next **coding**, GPU-OFF: finish F3-09 genuine offline reviewer/preview integration and F3-08 secure no-URL binary authentication/rights composition using mock two-shop and synthetic media. F3-08 [PR #879](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/879) mounts only fail-closed disabled route and [#880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880) proposes current-rights adapter; treat as security-sensitive independent-review candidates, never enable with fake rights or mere environment flag. Preserve their existing code and tests; avoid parallel conflict/duplicate PRs.
+- Keep F3 DEV 4 complete / 8 source in progress / 21 historically dependent until **full individual offline-code acceptance** evidence, and 0 fully hosted verified. Do not demand real retailer media/test accounts from user. Do not modify global auth/RLS, paid provider, hosted SQL, PROD or WineShopPOS without explicit permitted review.
+- Source main CI #42264379502 failed disposable Supabase Docker port 54322 on first attempt; targeted failed-job rerun passed, **attempt 2 = four successful jobs**. Do not label transient infrastructure startup as an application regression.
+
+## 2026-11-06 — Feature3 next GPU-free coding after F3-09 PR #883
+
+- Do not duplicate merged [PR #883](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/883): v2 private draft review now uses read-only offline metadata with two-shop/media denial tests; duplicate signed Storage download UI removed while separate authenticated history/private binary preview path stays fail-closed. Exact head CI #42270219850 4/4, main e9a7d1d2 main CI #42270848090 4/4.
+- Next F3-09 coding: finish authenticated v2 API mounting/review acceptance under shared interface owners, and reviewer UX persistence with synthetic two-shop fixtures. Next independent F3-10: verify same-shop private model Blob revocation and cleanup failure recovery, including same-tick repeated loads. F3-08 [#879](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/879) and [#880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880) remain security-sensitive and independently review-gated; never activate private bytes using mock authorization.
+- Fixture-based source can advance without retailer image accounts or GPU. Do not claim hosted completed, independent rights approval or real Azure ACK from mock tests. Baseline 4/33 development done, 8 in progress, 21 historically dependent, hosted 0/33; original task registry unchanged.
+
+## 2026-11-06 — Feature3 next tasks after verified F3-10 Blob cleanup merge
+
+- Do not repeat [PR #884](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/884) model Blob revocation ledger and same-tick GET gating: final-head CI #42272456836 4/4, merged main e3a65d0d, fresh main CI #42272979340 4/4. Synthetic tests cover failed/retried URL revoke, hidden private state and distinct session reads.
+- Continue F3-08 private binary backend integration only under reviewed current-rights authority, using existing [#879](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/879) and [#880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880) branches without duplicating source. Independent security review required for actual route activation. Continue F3-09 offline review/preview and F3-10 signed-hosted revocation negative tests when safe disposable tenant accounts are available; no customer imagery required for source work.
+- Original DEV_CODE_DONE 4/33; eight original source tasks still in progress and 21 historically dependent. Hosted fully accepted 0/33. Do not bypass review, enable GPU, mutate hosted SQL/PROD or WineShopPOS.
+
+## 2026-11-06 — F3-08 source-ready PR review and integration queue
+
+1. Independently review existing [#879](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/879) `41fecbaf5d` / [CI #42284441065](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42284441065) **4/4**, including PNG IDAT single-stream, exact filtered scanlines and 1-bit fixture; separately review existing [#880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880) `e98752d3bf` / [CI #42284306824](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42284306824) **4/4**, including exact canonical authority identity types. No duplicate F3-08 source PR/task.
+2. Verify fresh main compatibility and security/rights reviewer on **actual diffs** before any merge, then require four fresh postmerge CI jobs before a reviewed source receipt. Both PRs are currently open, not independently reviewed. F3-08 registered private download still default-OFF; do not use a mock rights adapter as an Azure service authorization.
+3. Continue other CPU-only independent F3 coding with synthetic fixtures. Original 4/33 DEV_CODE_DONE and 0/33 hosted accepted remain unchanged; no GPU or cloud mutations.
+
+## 2026-11-08 — Next F3-08 merge/test gate after canonical response consolidation
+
+- Verify exact final heads and all four jobs of #879/#880, inspect changed paths and latest main; #879 canonical binary identity correction should integrate before #880's dependent adapter to avoid weaker source behavior on a stale base. Actual independent current-rights/security review remains required. After eligible merges verify fresh main four-job CI and update only evidence-backed source task receipts, not hosted status.
+- **2026-11-08 F3-08 source continuation (2026-11-07 UTC GitHub commits):** Existing [#880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880) head `918bbc14cef8bd6a9077ce766560d8fb8c8a4c3b` now delegates its GET-only private PNG HTTP response to the previously existing `Feature3PrivateBinaryHTTP` instead of maintaining a weaker parallel PNG parser. A scoped exact-string shop/job receipt boundary blocks equality-overloaded forged identifiers. Synthetic HTTP/route tests were updated to the complete private receipt, immutable SHA and opaque malformed-internal 503 semantics. The first refactor test run #42410099605 exposed 14 regressions, including a real 200-on-spoofed-scope defect; follow-up code/test repair was committed and [CI #42410323345](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42410323345) started. Concurrent existing [#879](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/879), head `60251cf930bb6131bad9e11f0713ca80ba50b12b`, adds exact-string shop/job checks and adversarial forged-equality tests to the underlying canonical binary adapter; [CI #42410451925](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42410451925) started. **At this documentation checkpoint, exact FINAL-head all-four CI results are not yet certified; verify both before source integration.** These PRs do not mount an Azure endpoint or supply real rights/JWT. Both remain sensitive and require independent security review; no new original task, merged DONE or hosted acceptance. Prior DEV_CODE_DONE 4/33 and hosted 0/33 unchanged. No GPU, paid inference, hosted database, PROD or WineShopPOS mutations.
+
+## 2026-11-08 — Next: review and integrate existing F3-08 security source
+
+2026-11-08 F3-08 private PNG source correction: Existing [#880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880) head `7d7f885a5a26a57ae99cffee1a661b9c448f2331` fixes a real response-contract break introduced by its earlier header-hardening change. The Azure adapter had required `Cache-Control: no-store, private` but the trusted `Feature3PrivateBinaryHTTP` actually returns the equally private `no-store, private, max-age=0`; the mismatch caused **valid 256x256 synthetic PNG reads to return HTTP 503**. Prior exact-head [CI #42505722622](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42505722622) failed Python 1 test (1197 passed; other three jobs passed). The fix permits exactly the two established no-store/private variants with an exact Python string check; rejects public/cacheable or overloaded-equality policy values and strips backend response metadata from the Azure reply. Added positive strict-header, negative caching/equality spoof and end-to-end synthetic PNG header tests without disabling security tests. Latest exact-head [CI #42507466950](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42507466950) **4/4 SUCCESS** (Python/uv, FFmpeg, Supabase isolation, frontend/Chromium). Source only: no Azure route mounted, no live JWT/RLS, current rights backend/provider, real private download, GPU/provider spend, hosted SQL, PROD or WineShopPOS change. Existing canonical security PR #879 remains unmerged, and both sensitive source PRs and shared docs require independent GitHub review; original Feature3 DEV_CODE_DONE baseline **4/33**, fully hosted **0/33** unchanged.
+Next: obtain actual independent security review for #879 and #880, inspect compatibility with current main and integrate safely (canonical #879 before dependent #880); verify fresh main 4/4 CI and only then record evidence-backed original task progress. Review docs in #873 separately. Source fixture test accounts do not attest to genuine hosted authorization.
+
+## 2026-11-08 — Follow up on tested F3-08 synthetic two-shop route pipeline
+
+- Continued original F3-08 in existing source [PR #880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880): commit `6b8e8f86e670db8e0ffce4fd113d31cbf8c36c57` adds `tests/api/test_feature3_private_png_route_composed_two_shop.py`. Tests construct real in-process `handle_private_png_request` + `build_private_png_reader_factory` + `Feature3RevocablePNGReader`, with two isolated synthetic retailer JWTs/RLS rows, private PNG bytes, backend rights callback and authenticated Storage transport. Four tests cover (1) both shops getting only their own valid bytes and no leaked private headers, (2) foreign token denial before rights/Storage, (3) rights revoked during byte IO denying the returned PNG, and (4) JWT expiry during the read denying returned bytes and then recovery. All fake/local: **not** two live DEV identities, live JWT/RLS or a deployed route.
+- Python/uv [CI #42508181511](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42508181511) completed **1204 tests + 1152 subtests SUCCESS** on this head at the documentation checkpoint; **the other three jobs were still running and must be reverified before any 4/4 claim or source integration**. Prior source CI #42507466950 was 4/4 green on `7d7f885a` (cache-header fix), superseded by this new test-head.
+- PR #879 (canonical private binary) and PR #880 (route/rights) remain sensitive, unmerged and without real independent security review; docs #873 needs independent shared-document review too. Never classify test fixture as an accepted commercial license, hosted rights/JWT or Feature3 DONE. Original DEV_CODE_DONE baseline **4/33**, hosted **0/33** unchanged. GPU/paid model calls, hosted SQL, PROD and WineShopPOS untouched.
+
+## 2026-11-09 — Next F3-08 steps
+
+**2026-11-09 F3-08 source repair, [PR #880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880) head `e9612a8ec30746a5e8a332545e7c0fa7621973bd`:** Prior updated source head `7fbe7b7d81d4302e9f75894768775a4aa3f0ffa8` [CI #42568255441](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42568255441) had **7 failing Python cases, 1253 passing tests and 1301 passing subtests**, with the other three jobs successful. Two root causes: new rights transport outage handling correctly preserved `TimeoutError` for opaque HTTP 503 but a legacy reader unit test still expected an explicit-access-denial exception (404), and a new early bearer parser classified CR/LF injection as 401 instead of the established 400 framing rejection. The new source change re-establishes early 400 for CR/LF before GET-body or backend access, updates the low-level outage assertion to match transport-vs-denial semantics, and adds full two-shop route-to-reader rights-outage negative tests for failures before and after Storage IO. The separate existing rights-outage test imports the fixture under a private alias. Latest [Actions #42570838025](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42570838025) **Python/uv PASSED: 1256 tests + 1308 subtests**; complete all-four final-head CI still requires verification at this document-writing checkpoint. This is source-only, with **NO** independently reviewed live rights provider or verified hosted JWT/RLS, no approved commercial media or activated private byte route; PRs #879/#880 and shared docs #873 remain unmerged/review-gated. Original F3-08 is **IN PROGRESS**, historic DEV_CODE_DONE **4/33**, fully hosted **0/33**. GPU/paid inference, hosted DB, PROD, WineShopPOS untouched.
+
+Verify latest #880 exact-head 4/4 CI. Obtain independent security review of canonical PNG adapter #879 and dependent #880; merge in that order only when permitted, run fresh main 4/4, then add reviewed original task status evidence. Review docs PR #873 independently. A hosted rights-provider integration is still unverified; do not promote synthetic grants or enable GPU/paid providers.
+
+## Original added text: `docs/PROJECT_STATE.md`
+
+
+
+## 2026-11-05 — Feature3 F3-13 CPU privacy source integrated; hosted completion unchanged
+- [Feature3 PR #872](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/872) merged into main as `b1509e24557530ce99e412d10213139893f30df3`; its exact final source head `5bf630b194c8df2fe34c284fc6a14426f677089a` passed [PR CI #41902676515](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41902676515) **4/4**, and [fresh main CI #41903466197](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41903466197) **4/4**.
+- The offline CPU editor now suppresses pending PNG Blob downloads after unmount/tenant-day/edit/media-map changes, rejects duplicate encodes and stale JSON imports, validates own format/colour types and rejects inherited private-image map entries. Deterministic Chromium and Node tests were included in the green jobs. No real remote private media, customer rights, GPU, paid image inference or hosted deployment tested.
+- **Provenance limitation:** PR #872 had **zero submitted independent GitHub reviews**, despite sensitive private-image/tenant changes. Owner-account merge and CI are recorded accurately, **not** described as independently reviewed. A follow-up affected-lead/human review of the merged diff remains open under `docs/FEATURE_SELF_MERGE_POLICY_20261031.md`.
+- Original **F3-13 remains SOURCE PARTIAL**, not fully accepted task DONE. Feature3 **0/33 hosted-accepted**; no task-manager DONE status fabricated. Azure #249, authenticated mounted private PNG endpoint (#471/#325), true signed role/RLS tests, real licensed images and paid GPU/provider approval remain separately gated. No WineShopPOS, PROD, hosted SQL or billable GPU mutation.
+
+## 2026-11-05 — Feature3 F3-05/F3-08/F3-09 source hardening merged, no GPU
+
+- Owner-authorized development-code baseline [PR #875](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/875) is merged: **4/33 DEV_CODE_DONE** original IDs F3-01/02/03/13, **8/33 source in progress**, 21 older dependent classifications. These are development-only categories; **0/33 independently verified hosted acceptance**.
+- F3-08 private PNG IHDR boundary [PR #876](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/876) merged to main `8c412e0dfd3b95a8ba5371f6667903a6b3b1ef52`: final-head [CI #41978514108](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41978514108) 4/4, fresh main [CI #41979596428](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41979596428) 4/4. Two initially failing oversized-pixel test cases were corrected to genuinely exceed the 16,777,216 pixel cap.
+- F3-09 current private-draft image-map own-property fence [PR #877](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/877) merged to main `96bf834a97ed2b5742748f5699b1cce8dec32c75`: final-head [CI #41979220126](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41979220126) 4/4, fresh main [CI #41980044471](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41980044471) 4/4. Reopen/save require current own-key private image entry and valid decoded dimensions; inherited prototype entries denied.
+- F3-05/F3-13 two-shop queue receipt/ACK fail-closed [PR #878](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/878) merged to main `f21a9de7e3a2ae2ee4a58db6f7fbe95265a99cf6`: final-head [CI #41981164567](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41981164567) 4/4, fresh main [CI #41981648369](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41981648369) 4/4. Nil or repeated Queue message GUIDs fail closed before unsafe SQL ACK; mock two-shop dispatch failure injections preserve one-shot boundaries.
+- These are integrated *source components* of still-open packages, not proof of live Azure queue, real signed two-shop verification, mounted private PNG endpoint or approved commercial content. No independent GitHub reviewer was recorded for these source merges. Release-security review, authenticated endpoint and hosted acceptance remain separate, not reasons to delay unrelated fixture-based coding. No paid GPU/AI, hosted SQL, PROD or WineShopPOS operations.
+
+## 2026-11-06 — Feature3 F3-09 reliable private draft persistence and review-state source integrations
+
+- [PR #881](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/881) merged to main `d1e2db42502ac6538d4cfe7e8c3373a62c355a13`. Its final-head [CI #42262450211](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42262450211) 4/4; fresh main [CI #42263039678](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42263039678) 4/4. The browser's ambiguous v2 poster POST now synchronously latches uncertain state; no new POST without fresh private signed history and an explicit user decision. Shop/day/JWT-provider rotation and local-before-POST errors are separately fenced.
+- [PR #882](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/882) merged to main `d390e6552a6b19d1ba24978ce50c8eb656d5913f`. Its final-head [CI #42263765934](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42263765934) 4/4; fresh main [CI #42264379502](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42264379502) 4/4 **on failed-job retry attempt 2**. Initial main Supabase job failed to start disposable Docker on occupied local port 54322, not a test assertion; only the failing job was retried and passed. Strict same-shop v2 draft history now rejects malformed/duplicate/injected records and displays DRAFT/APPROVED/REJECTED as read-only statuses without publication authority.
+- Both are source components of original F3-09/F3-13; **F3-09 remains DEV in progress**, not the complete hosted save/reopen/reviewer workflow. Existing baseline **4/33 DEV_CODE_DONE**, **8/33 in progress**, **21/33 historical dependent**; **0/33 independently verified hosted acceptance**. No GPU, paid inference, hosted migrations, PROD or WineShopPOS operations. These feature-owned merges have no recorded independent GitHub security review; that review remains separate for release and sensitive shared interfaces.
+
+## 2026-11-06 — Feature3 F3-09/F3-20 saved-review inspector + no signed-link source integration
+
+- [PR #883](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/883) merged to main e9a7d1d2ea1ff08258a58bd17a99b9d32d9233f5. Its exact final head 183ee28fb9eb0f0449a2f8fd0efd72f9a1d2bea4 passed [CI #42270219850](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42270219850) all four jobs; fresh main [CI #42270848090](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42270848090) passed four of four jobs.
+- The optional v2 private *draft* workspace no longer offers the duplicate 60-second signed Storage download CTA. The authenticated host's existing Feature3GeneratedHistory remains the single read-only job/history and, when independently enabled, no-URL private binary preview surface. The legacy signed-download API method remains source-compatible, but is not invoked by the v2 draft workspace.
+- The v2 workspace now offers an isolated read-only inspector for saved DRAFT/APPROVED/REJECTED document layouts. It validates current shop/campaign/day/source records and own-key private image grants, withholds image pixels/URLs and renders only bounded metadata. The read-only status cannot authorize publication. Inspection clears before a new history fetch and on account/day/API changes.
+- Original F3-09 and F3-20 gain accepted development source slices, NOT original-package DEV_CODE_DONE or hosted acceptance: existing development baseline remains 4/33 complete, 8 source-in-progress and 21 historically dependent; hosted 0/33. F3-08 security-sensitive PRs #879/#880 and this canonical docs PR #873 still await actual independent review. No paid GPU/model, hosted migrations, PROD or WineShopPOS changes.
+
+## 2026-11-06 — Feature3 F3-10 private model-preview Blob cleanup source accepted
+
+- [PR #884](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/884), exact final head 08c5769eebbc3d011149ef812b3e8bb8aba7fb6f, passed [four-job CI #42272456836](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42272456836); merged to main e3a65d0d477665edee955ac3440b657ac71b6165. Fresh [main CI #42272979340](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42272979340) passed all four jobs.
+- F3-10/13 private model preview uses an owned browser Blob URL cleanup ledger: failed revocations retain URL handles for explicit recovery, successfully revoked handles are removed, current preview state is hidden before cleanup, and repeated same-tick private-model GETs are gated synchronously. Cross-tenant/session late completions are fenced; all tests use synthetic private media and mock URL methods.
+- Source component integrated, NOT full original F3-10 DEV_CODE_DONE or hosted Blob/revocation acceptance. Previous 4/33 DEV_CODE_DONE baseline remains unchanged, 8 source-in-progress and 21 historically dependent; hosted 0/33. No independent GitHub review recorded for #884; independent release-security verification remains separate. No live GPU/paid AI, hosted database or PROD/WineShopPOS changes.
+
+## 2026-11-06 — Feature3 F3-08 dual source hardening checked, independently review-gated
+
+- Existing [PR #879](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/879), final source head `41fecbaf5dde455a2152acdcfb1278196ed3fd25`, passed exact-head [CI #42284441065](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42284441065) 4/4. Source PNG HTTP adapter now checks bounded exact filtered scanlines (including Adam7), complete single zlib stream, no extra compressed/decompressed covert data; synthetic malformed IDAT denials and valid PNG-mode recovery. Earlier Python run failed on a too-small blank 1-bit fixture; deterministic nonblank 1-bit fixture corrected without relaxing production size bound.
+- Existing [PR #880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880), final source head `e98752d3bffd06b56af14d010891c9addb82a543`, passed exact-head [CI #42284306824](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42284306824) 4/4. Current backend output-rights adapter now requires exact `str` UUID identities rather than accepting objects with overloaded equality; adversarial adapter regression added. No live trusted rights service is mounted.
+- Both are **open PRs**, neither source slice merged or independently approved at this checkpoint. Existing 4/33 original DEV_CODE_DONE and 0/33 fully hosted accepted remain unchanged. Actual signed two-shop JWT/RLS rights, mounted private binary route, Azure #249 and independently reviewed customer media remain separate. GPU/paid models, hosted DB, PROD and WineShopPOS untouched.
+
+## 2026-11-08 — Feature3 F3-08 canonical private PNG response consolidation
+
+- **2026-11-08 F3-08 source continuation (2026-11-07 UTC GitHub commits):** Existing [#880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880) head `918bbc14cef8bd6a9077ce766560d8fb8c8a4c3b` now delegates its GET-only private PNG HTTP response to the previously existing `Feature3PrivateBinaryHTTP` instead of maintaining a weaker parallel PNG parser. A scoped exact-string shop/job receipt boundary blocks equality-overloaded forged identifiers. Synthetic HTTP/route tests were updated to the complete private receipt, immutable SHA and opaque malformed-internal 503 semantics. The first refactor test run #42410099605 exposed 14 regressions, including a real 200-on-spoofed-scope defect; follow-up code/test repair was committed and [CI #42410323345](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42410323345) started. Concurrent existing [#879](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/879), head `60251cf930bb6131bad9e11f0713ca80ba50b12b`, adds exact-string shop/job checks and adversarial forged-equality tests to the underlying canonical binary adapter; [CI #42410451925](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42410451925) started. **At this documentation checkpoint, exact FINAL-head all-four CI results are not yet certified; verify both before source integration.** These PRs do not mount an Azure endpoint or supply real rights/JWT. Both remain sensitive and require independent security review; no new original task, merged DONE or hosted acceptance. Prior DEV_CODE_DONE 4/33 and hosted 0/33 unchanged. No GPU, paid inference, hosted database, PROD or WineShopPOS mutations.
+
+## 2026-11-08 — Feature3 F3-08 valid private PNG recovery with strict cache policy
+
+2026-11-08 F3-08 private PNG source correction: Existing [#880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880) head `7d7f885a5a26a57ae99cffee1a661b9c448f2331` fixes a real response-contract break introduced by its earlier header-hardening change. The Azure adapter had required `Cache-Control: no-store, private` but the trusted `Feature3PrivateBinaryHTTP` actually returns the equally private `no-store, private, max-age=0`; the mismatch caused **valid 256x256 synthetic PNG reads to return HTTP 503**. Prior exact-head [CI #42505722622](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42505722622) failed Python 1 test (1197 passed; other three jobs passed). The fix permits exactly the two established no-store/private variants with an exact Python string check; rejects public/cacheable or overloaded-equality policy values and strips backend response metadata from the Azure reply. Added positive strict-header, negative caching/equality spoof and end-to-end synthetic PNG header tests without disabling security tests. Latest exact-head [CI #42507466950](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42507466950) **4/4 SUCCESS** (Python/uv, FFmpeg, Supabase isolation, frontend/Chromium). Source only: no Azure route mounted, no live JWT/RLS, current rights backend/provider, real private download, GPU/provider spend, hosted SQL, PROD or WineShopPOS change. Existing canonical security PR #879 remains unmerged, and both sensitive source PRs and shared docs require independent GitHub review; original Feature3 DEV_CODE_DONE baseline **4/33**, fully hosted **0/33** unchanged.
+
+## 2026-11-08 — F3-08 two-shop route composition and post-byte revocation regression
+
+- Continued original F3-08 in existing source [PR #880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880): commit `6b8e8f86e670db8e0ffce4fd113d31cbf8c36c57` adds `tests/api/test_feature3_private_png_route_composed_two_shop.py`. Tests construct real in-process `handle_private_png_request` + `build_private_png_reader_factory` + `Feature3RevocablePNGReader`, with two isolated synthetic retailer JWTs/RLS rows, private PNG bytes, backend rights callback and authenticated Storage transport. Four tests cover (1) both shops getting only their own valid bytes and no leaked private headers, (2) foreign token denial before rights/Storage, (3) rights revoked during byte IO denying the returned PNG, and (4) JWT expiry during the read denying returned bytes and then recovery. All fake/local: **not** two live DEV identities, live JWT/RLS or a deployed route.
+- Python/uv [CI #42508181511](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42508181511) completed **1204 tests + 1152 subtests SUCCESS** on this head at the documentation checkpoint; **the other three jobs were still running and must be reverified before any 4/4 claim or source integration**. Prior source CI #42507466950 was 4/4 green on `7d7f885a` (cache-header fix), superseded by this new test-head.
+- PR #879 (canonical private binary) and PR #880 (route/rights) remain sensitive, unmerged and without real independent security review; docs #873 needs independent shared-document review too. Never classify test fixture as an accepted commercial license, hosted rights/JWT or Feature3 DONE. Original DEV_CODE_DONE baseline **4/33**, hosted **0/33** unchanged. GPU/paid model calls, hosted SQL, PROD and WineShopPOS untouched.
+
+## 2026-11-09 — Feature3 F3-08 rights-outage and header-framing repair
+
+**2026-11-09 F3-08 source repair, [PR #880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880) head `e9612a8ec30746a5e8a332545e7c0fa7621973bd`:** Prior updated source head `7fbe7b7d81d4302e9f75894768775a4aa3f0ffa8` [CI #42568255441](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42568255441) had **7 failing Python cases, 1253 passing tests and 1301 passing subtests**, with the other three jobs successful. Two root causes: new rights transport outage handling correctly preserved `TimeoutError` for opaque HTTP 503 but a legacy reader unit test still expected an explicit-access-denial exception (404), and a new early bearer parser classified CR/LF injection as 401 instead of the established 400 framing rejection. The new source change re-establishes early 400 for CR/LF before GET-body or backend access, updates the low-level outage assertion to match transport-vs-denial semantics, and adds full two-shop route-to-reader rights-outage negative tests for failures before and after Storage IO. The separate existing rights-outage test imports the fixture under a private alias. Latest [Actions #42570838025](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42570838025) **Python/uv PASSED: 1256 tests + 1308 subtests**; complete all-four final-head CI still requires verification at this document-writing checkpoint. This is source-only, with **NO** independently reviewed live rights provider or verified hosted JWT/RLS, no approved commercial media or activated private byte route; PRs #879/#880 and shared docs #873 remain unmerged/review-gated. Original F3-08 is **IN PROGRESS**, historic DEV_CODE_DONE **4/33**, fully hosted **0/33**. GPU/paid inference, hosted DB, PROD, WineShopPOS untouched.
+
+## Original added text: `docs/WORK_LOG.md`
+
+
+
+## 2026-11-05 — Feature3 F3-13 real GitHub code/CI checkpoint
+- Read canonical startup and feature instructions, examined original 33-package ledger, current main, #858/#860/#870 and unresolved #249/#325/#471 dependencies. Reused existing Feature3 source, no restart.
+- Implemented and tested scoped F3-13 async PNG cancel/single-flight, late local JSON import rejection, strict poster format/color own-type validation and inherited private image-map denial in [PR #872](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/872), with Node + mocked real Chromium regressions and feature-owned handoff/ledger updates. Initial old-head Playwright test failed because required prompt was blank; fixture repaired and re-tested, not bypassed.
+- [Feature3 PR #872](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/872) merged into main as `b1509e24557530ce99e412d10213139893f30df3`; its exact final source head `5bf630b194c8df2fe34c284fc6a14426f677089a` passed [PR CI #41902676515](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41902676515) **4/4**, and [fresh main CI #41903466197](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41903466197) **4/4**.
+- Independent code review **not submitted** (zero GitHub reviews at merge); do not mark the original F3-13 complete without real acceptance/review. Source is main-integrated; hosted F3 still **0/33 DONE**. No Azure/SQL mutation, GPU, paid models, PROD or WineShopPOS.
+
+## 2026-11-05 — Feature3 three-PR code-first integration batch
+
+- Resumed at main `837943de`. Diagnosed #876 Python CI #41975033875 (two false oversized-image assertions). Changed two fixture mutations to actual over-limit 8192×8192/4096×8192 IHDR values. Final PR head `3b322565` [#41978514108](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41978514108) 4/4; [PR #876](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/876) merged `8c412e0`; fresh main [#41979596428](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41979596428) 4/4.
+- Implemented F3-09/F3-13 shared private image-map own-key validation on both secure draft reopen/save, positive/inherited/malformed pixel metadata Node regressions in [PR #877](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/877). Final head `906c260` [#41979220126](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41979220126) 4/4; merged `96bf834`; fresh main [#41980044471](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41980044471) 4/4.
+- Implemented F3-05/F3-13 nil/duplicate Queue message GUID denial and mock cross-tenant two-shop ACK failure tests in [PR #878](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/878). Final head `7776cda` [#41981164567](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41981164567) 4/4; merged `f21a9de7`; fresh main [#41981648369](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41981648369) 4/4.
+- Closed duplicate documentation PR #874 unmerged, retained fuller #873 for review and appended the source integration receipts. Historical 33-package hosted acceptance unchanged 0; owner-authorized DEV_CODE_DONE count remains 4/33. No genuine live worker/queue ACK, signed Auth Admin accounts, commercial rights, paid GPU, hosted SQL, PROD or WineShopPOS were claimed/used. No independent GitHub reviews were submitted for these feature-source merges; keep release review distinct.
+
+## 2026-11-06 — Feature3 F3-09 dual code-first source batch
+
+- Read live GitHub main, mandatory AGENTS/docs/feature ledger and feature-owned PR #879/#880 review gates; chose a disjoint F3-09 frontend-only gap to avoid duplicating their security-sensitive backend work.
+- [PR #881](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/881) adds `feature3-draft-write-guard.mjs`, integrates strict browser POST-replay denial and an explicit successful private-history/reopen-or-new recovery flow into `Feature3SecureDraftWorkspace.jsx`, plus synthetic same-tick/foreign-shop/session rotation tests. Head `34411a09`, CI [#42262450211](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42262450211) 4/4; merged `d1e2db42502ac6538d4cfe7e8c3373a62c355a13`; fresh main [#42263039678](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42263039678) 4/4.
+- [PR #882](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/882) requires full tenant-safe versioned/private history identity, SHA syntax and design-schema validation; rejects duplicate/foreign/malformed rows and shows read-only reviewer statuses. Head `75cb0329`, CI [#42263765934](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42263765934) 4/4; merged `d390e6552a6b19d1ba24978ce50c8eb656d5913f`.
+- Fresh main [CI #42264379502](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42264379502) attempt 1 failed Supabase setup on Docker host port 54322 occupied. Inspected exact job logs: no SQL/tenant assertion failure. Used GitHub targeted failed-job rerun, attempt 2 succeeded; together with Python, frontend Chromium and FFmpeg, **four jobs passed on final main**.
+- Both source PRs used feature-owned paths; no independent GitHub reviewer was present (do not claim independent sensitive/release review). Canonical docs recorded through separate review-gated PR #873. Existing original F3-09 remains dev in progress, 4 of 33 original dev milestones are DONE, hosted 0/33. No GPU/paid AI, hosted SQL, PROD, resource mutation, real customer licensing claims or WineShopPOS touch.
+
+## 2026-11-06 — Feature3 F3-09/F3-20 source inspector and signed-link consolidation
+
+- Verified current main d390e655 and open security/backend PRs #879/#880 and shared docs PR #873. Chose a disjoint feature-owned CPU-only UI task: the v2 draft workspace duplicated generated-job history and exposed a 60-second signed Storage download while Feature3PosterHost already mounted scoped private job history/no-URL preview behind independent gates.
+- Authored [PR #883](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/883): removed legacy signed-download CTA and duplicate generated handlers from Feature3SecureDraftWorkspace, added the F3-09 read-only review inspector and immutable safe metadata snapshot, and updated signed-link/workspace source tests plus new two-shop and forged-image tests. Does not touch the backend F3-08 security PRs.
+- Initial PR head d720533 test run #42269924094 exposed one obsolete pendingJobs source-test assertion after removing the handler; corrected in follow-up head 183ee28fb9eb0f0449a2f8fd0efd72f9a1d2bea4. Final-head [CI #42270219850](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42270219850) 4/4. Merged to main e9a7d1d2ea1ff08258a58bd17a99b9d32d9233f5; fresh [CI #42270848090](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42270848090) 4/4.
+- Source-only accepted F3-09/F3-20 slices, original DEV milestones remain 4/33 DONE and hosted 0/33. This PR has zero recorded independent GitHub reviews; do not claim independent sensitive/release approval. No GPU, AI spend, hosted SQL, PROD or WineShopPOS modifications. Canonical docs remain subject to independent review via PR #873.
+
+## 2026-11-06 — Feature3 F3-10 private preview URL lifecycle and same-tick rights reads
+
+- Found source bug in Feature3PosterHost: revoke could throw before old approved model pixels were hidden, a partial revoke could leave inaccurate cleanup ownership, and React busy state was not a synchronous private model GET lease.
+- Implemented [PR #884](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/884), head 08c5769eebbc3d011149ef812b3e8bb8aba7fb6f. Feature-owned code: URL ownership ledger that retains failed handles and drops successful ones, hide-before-cleanup ordering, same-tick model GET guard, stale-session cleanup and source/mocked positive/negative regressions. No root/router or global auth edits.
+- Final head [CI #42272456836](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42272456836) all four jobs success; squash merged main e3a65d0d477665edee955ac3440b657ac71b6165; fresh [main CI #42272979340](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42272979340) all four jobs success.
+- This completes an original F3-10/F3-13 source slice, but neither entire F3-10 DEV_CODE_DONE nor hosted rights/revocation release. No independent GitHub review present; release review kept separate. No GPU/paid models, cloud mutation/hosted migration, PROD or WineShopPOS.
+
+## 2026-11-06 — F3-08 no-URL private PNG source continuation, two existing PRs
+
+- On existing PR #879, reproduced locally with synthetic Pillow PNG that a valid decoded 256px image can retain extra hidden bytes after its zlib stream inside CRC-valid IDAT, with a self-consistent forged source SHA. Implemented strict complete bounded zlib/scanline validation and synthetic denied trailer/second-stream/excess-filtered-pixels/truncation variants, valid PNG formats and cross-shop denial in `tests/api/test_feature3_private_binary_idat_payload.py`. An initial exact-head Python CI run caught that blank 1-bit test PNG was below the existing 100-byte minimum: changed **only the test fixture** to deterministic patterned pixels, re-ran full CI. Final head `41fecbaf5dde455a2152acdcfb1278196ed3fd25`, [run #42284441065](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42284441065) 4/4 SUCCESS. Scoped handoff: `azure-functions/campaign-api/FEATURE3_F308_IDAT_INTEGRITY_HANDOFF_20261106.md`.
+- In parallel on existing PR #880, hardened fresh backend rights row against equality-spoofed returned shop/job/asset identities: canonical exact-str required, not arbitrary object equality. Added negative/recovery regressions, final head `e98752d3bffd06b56af14d010891c9addb82a543`, [run #42284306824](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42284306824) 4/4 SUCCESS.
+- Neither PR has an actual independent rights/security GitHub review or postmerge main CI yet; both remain **open/source tested**. No source package DONE or hosted completion is claimed. Existing original 4/33 DEV_CODE_DONE baseline and 0/33 hosted accepted remain unchanged. No paid GPU/image/model inference, real user media, hosted JWT/RLS/SQL writes, PROD or WineShopPOS.
+
+## 2026-11-08 — F3-08 concrete source changes and CI-derived repair
+
+- **2026-11-08 F3-08 source continuation (2026-11-07 UTC GitHub commits):** Existing [#880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880) head `918bbc14cef8bd6a9077ce766560d8fb8c8a4c3b` now delegates its GET-only private PNG HTTP response to the previously existing `Feature3PrivateBinaryHTTP` instead of maintaining a weaker parallel PNG parser. A scoped exact-string shop/job receipt boundary blocks equality-overloaded forged identifiers. Synthetic HTTP/route tests were updated to the complete private receipt, immutable SHA and opaque malformed-internal 503 semantics. The first refactor test run #42410099605 exposed 14 regressions, including a real 200-on-spoofed-scope defect; follow-up code/test repair was committed and [CI #42410323345](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42410323345) started. Concurrent existing [#879](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/879), head `60251cf930bb6131bad9e11f0713ca80ba50b12b`, adds exact-string shop/job checks and adversarial forged-equality tests to the underlying canonical binary adapter; [CI #42410451925](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42410451925) started. **At this documentation checkpoint, exact FINAL-head all-four CI results are not yet certified; verify both before source integration.** These PRs do not mount an Azure endpoint or supply real rights/JWT. Both remain sensitive and require independent security review; no new original task, merged DONE or hosted acceptance. Prior DEV_CODE_DONE 4/33 and hosted 0/33 unchanged. No GPU, paid inference, hosted database, PROD or WineShopPOS mutations.
+
+## 2026-11-08 — F3-08 source bug repaired, exact-head CI 4/4
+
+2026-11-08 F3-08 private PNG source correction: Existing [#880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880) head `7d7f885a5a26a57ae99cffee1a661b9c448f2331` fixes a real response-contract break introduced by its earlier header-hardening change. The Azure adapter had required `Cache-Control: no-store, private` but the trusted `Feature3PrivateBinaryHTTP` actually returns the equally private `no-store, private, max-age=0`; the mismatch caused **valid 256x256 synthetic PNG reads to return HTTP 503**. Prior exact-head [CI #42505722622](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42505722622) failed Python 1 test (1197 passed; other three jobs passed). The fix permits exactly the two established no-store/private variants with an exact Python string check; rejects public/cacheable or overloaded-equality policy values and strips backend response metadata from the Azure reply. Added positive strict-header, negative caching/equality spoof and end-to-end synthetic PNG header tests without disabling security tests. Latest exact-head [CI #42507466950](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42507466950) **4/4 SUCCESS** (Python/uv, FFmpeg, Supabase isolation, frontend/Chromium). Source only: no Azure route mounted, no live JWT/RLS, current rights backend/provider, real private download, GPU/provider spend, hosted SQL, PROD or WineShopPOS change. Existing canonical security PR #879 remains unmerged, and both sensitive source PRs and shared docs require independent GitHub review; original Feature3 DEV_CODE_DONE baseline **4/33**, fully hosted **0/33** unchanged.
+Observed regression independently in CI run #42505722622, fixed same F3-08 PR instead of creating a duplicate task or disabling a test.
+
+## 2026-11-08 — F3-08 new multi-tenant route test commit
+
+- Continued original F3-08 in existing source [PR #880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880): commit `6b8e8f86e670db8e0ffce4fd113d31cbf8c36c57` adds `tests/api/test_feature3_private_png_route_composed_two_shop.py`. Tests construct real in-process `handle_private_png_request` + `build_private_png_reader_factory` + `Feature3RevocablePNGReader`, with two isolated synthetic retailer JWTs/RLS rows, private PNG bytes, backend rights callback and authenticated Storage transport. Four tests cover (1) both shops getting only their own valid bytes and no leaked private headers, (2) foreign token denial before rights/Storage, (3) rights revoked during byte IO denying the returned PNG, and (4) JWT expiry during the read denying returned bytes and then recovery. All fake/local: **not** two live DEV identities, live JWT/RLS or a deployed route.
+- Python/uv [CI #42508181511](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42508181511) completed **1204 tests + 1152 subtests SUCCESS** on this head at the documentation checkpoint; **the other three jobs were still running and must be reverified before any 4/4 claim or source integration**. Prior source CI #42507466950 was 4/4 green on `7d7f885a` (cache-header fix), superseded by this new test-head.
+- PR #879 (canonical private binary) and PR #880 (route/rights) remain sensitive, unmerged and without real independent security review; docs #873 needs independent shared-document review too. Never classify test fixture as an accepted commercial license, hosted rights/JWT or Feature3 DONE. Original DEV_CODE_DONE baseline **4/33**, hosted **0/33** unchanged. GPU/paid model calls, hosted SQL, PROD and WineShopPOS untouched.
+
+## 2026-11-09 — F3-08 failed first test, repaired code and updated regression
+
+**2026-11-09 F3-08 source repair, [PR #880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880) head `e9612a8ec30746a5e8a332545e7c0fa7621973bd`:** Prior updated source head `7fbe7b7d81d4302e9f75894768775a4aa3f0ffa8` [CI #42568255441](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42568255441) had **7 failing Python cases, 1253 passing tests and 1301 passing subtests**, with the other three jobs successful. Two root causes: new rights transport outage handling correctly preserved `TimeoutError` for opaque HTTP 503 but a legacy reader unit test still expected an explicit-access-denial exception (404), and a new early bearer parser classified CR/LF injection as 401 instead of the established 400 framing rejection. The new source change re-establishes early 400 for CR/LF before GET-body or backend access, updates the low-level outage assertion to match transport-vs-denial semantics, and adds full two-shop route-to-reader rights-outage negative tests for failures before and after Storage IO. The separate existing rights-outage test imports the fixture under a private alias. Latest [Actions #42570838025](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42570838025) **Python/uv PASSED: 1256 tests + 1308 subtests**; complete all-four final-head CI still requires verification at this document-writing checkpoint. This is source-only, with **NO** independently reviewed live rights provider or verified hosted JWT/RLS, no approved commercial media or activated private byte route; PRs #879/#880 and shared docs #873 remain unmerged/review-gated. Original F3-08 is **IN PROGRESS**, historic DEV_CODE_DONE **4/33**, fully hosted **0/33**. GPU/paid inference, hosted DB, PROD, WineShopPOS untouched.
+
+## Original added text: `docs/feature3/FEATURE3_33_PACKAGE_STATUS_20261029.md`
+
+
+
+## 2026-11-05 — F3-13 scoped CPU fixes integrated, original package remains PARTIAL
+- [Feature3 PR #872](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/872) merged into main as `b1509e24557530ce99e412d10213139893f30df3`; its exact final source head `5bf630b194c8df2fe34c284fc6a14426f677089a` passed [PR CI #41902676515](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41902676515) **4/4**, and [fresh main CI #41903466197](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/41903466197) **4/4**.
+- Verified local Chromium/Node code tests cover delayed PNG completion after editor unmount, single-flight, stale JSON import after another edit, inherited private-image map key denial and strict v2 format/colour validation. These are **additional source components on an existing original F3-13 task**, not new original packages or real image/rights acceptance.
+- **Audit flag:** no independent GitHub reviews were present on #872 at merge. Follow-up affected-lead/human private-media/tenant review remains required; do not assert independently reviewed safety. The F3-13 task continues **SOURCE PARTIAL**, not original DONE; **0/33 fully hosted accepted**, GPU OFF, cloud rights/real JWT/route unverified, WineShopPOS untouched. Source task-progress records must not overstate the independent review gate.
+
+## 2026-11-05 — Development-code milestone overlay and three verified source merges
+
+- Owner-authorized DEV code-only overlay [#875](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/875) records **4/33 DEV_CODE_DONE** (F3-01/02/03/13) based on exact merged source, tests and main CI, leaving **8 source-in-progress** (F3-05..12) and **21 previously classified dependent** under the older combined hosted ledger. The baseline categories at the top of this historical ledger remain recorded for comparison. **0/33 hosted/full-release accepted**.
+- [#876](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/876) F3-08 source component: validated PNG IHDR/pixel budget; exact PR CI #41978514108 4/4; merged `8c412e0`; main CI #41979596428 4/4. No authenticated private byte route mounted.
+- [#877](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/877) F3-09/F3-13 source component: own-property image-map grant and pixel-size fence for save/reopen; exact PR CI #41979220126 4/4; merged `96bf834`; main CI #41980044471 4/4. No live signed v2 design review approval.
+- [#878](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/878) F3-05/F3-13 source component: nil/repeated Azure Queue GUID denial and two-shop mock negative tests; exact PR CI #41981164567 4/4; merged `f21a9de7`; main CI #41981648369 4/4. No live Azure ACK/inference/financial reconciliation.
+- All three source-owned PRs were merged on user authorization after full four-job CI; no independent GitHub reviews were submitted, so do not claim security/rights independent review. Synthetic evidence closes tested source slices, not hosted queue/tenant/revocation/commercial acceptance; CPU/GPU payment gates remain OFF. Duplicate canonical-doc PR #874 closed unmerged; #873 requires separate shared-document review.
+
+## 2026-11-06 — F3-09 two accepted source components; original packages unchanged
+
+- Ambiguous draft save read-before-retry enforcement in [#881](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/881), head `34411a09` exact CI #42262450211 **4/4**, merged main `d1e2db4`, fresh main CI #42263039678 **4/4**. Actual source test proves unknown POST locks subsequent saves until signed history read plus deliberate user choice; no replay on a failed/409 response.
+- Exact tenant/schema/hash-format private history validation and DRAFT/APPROVED/REJECTED read-only UI in [#882](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/882), head `75cb0329` exact CI #42263765934 **4/4**, merged main `d390e65`. Fresh main CI #42264379502 **4/4 on retry attempt 2** (attempt 1 failed transient Docker port 54322 bind during Supabase startup; rerun of failing job passed). Not a real reviewer decision, public approval, valid commercial rights or hosted output.
+- Both source components extend F3-09 and F3-13. **Do not increment original task DONE based on the source slices:** DEV_CODE_DONE = 4/33 (F3-01/F3-02/F3-03/F3-13), F3-09 remains among 8 source-in-progress, 21 historically dependent, hosted verified 0/33. Further reviewer, output preview, mounted binary route and live permissions acceptance remain separate. Test images/shops can drive continued GPU-free coding; no user customer image/account required for fixtures.
+- Feature #3 source merges had no separately submitted independent reviewer; preserve this evidence caveat. Shared docs PR #873 itself remains review-gated; no GPU/paid models, hosted SQL, PROD or WineShopPOS were changed.
+
+## 2026-11-06 — F3-09/F3-20 private read-only inspection, one generated history surface
+
+- [Feature3 PR #883](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/883) final head 183ee28fb9eb0f0449a2f8fd0efd72f9a1d2bea4 passed exact [CI #42270219850](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42270219850) 4/4. Squash merge main e9a7d1d2ea1ff08258a58bd17a99b9d32d9233f5 passed fresh [CI #42270848090](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42270848090) 4/4.
+- Separate source component of F3-09/F3-20: saved signed draft DRAFT/APPROVED/REJECTED layouts inspectable read-only using current tenant/day/API-scoped and registered-image-only metadata, with no remote image src/signed Storage URL or publishing grant. Duplicated 60-second signed generated download removed from v2 draft panel; authenticated host retains single gated no-URL history/preview. Server rights provider and hosted v2 route remain unverified; binary endpoint cannot be enabled by this UI.
+- No original full development package was closed by this source slice. DEV_CODE_DONE still 4/33, source in progress 8, historical dependent 21, independently verified hosted 0/33. No paid AI/GPU, actual authorized DEV identity or commercial-rights evidence claimed, and no independent GitHub security review recorded. Open #879/#880 and shared docs #873 remain review-gated.
+
+## 2026-11-06 — F3-10 model-preview Blob cleanup + F3-13 regression integrated
+
+- [PR #884](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/884) exact final head 08c5769eebbc3d011149ef812b3e8bb8aba7fb6f, [CI #42272456836](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42272456836) 4/4, merged main e3a65d0d477665edee955ac3440b657ac71b6165 and fresh [CI #42272979340](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42272979340) 4/4.
+- Accepted source behavior: browser private-model Blob ledger retains failed URL revocations for bounded later retry; hides decoded private pixels before attempting revoke, blocks duplicate same-tick rights-scoped reads, and prevents stale cross-shop response display. Tests are synthetic and mock URL revocation, not real DEV hosted rights/revocation evidence.
+- Source slice F3-10/F3-13, not a new work package or whole-parent acceptance. Original DEV_CODE_DONE 4/33, source in-progress 8, historically dependent 21, hosted 0/33. Independent security review was not submitted for this feature-owned source PR; open F3-08 #879/#880 and shared-doc #873 still need respective independent review. No GPU, paid AI or production mutation.
+
+## 2026-11-06 — F3-08 / F3-13 current dual code-source PR checkpoint
+
+- **F3-08 private binary PNG integrity:** open [#879](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/879) final source `41fecbaf5dde455a2152acdcfb1278196ed3fd25`, exact 4/4 [CI #42284441065](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42284441065); valid CRC/SHA no longer permits trailing zlib IDAT covert payload, concatenated streams or excess decompressed filtered bytes. Tests include positive RGBA/indexed/16-bit/1-bit modes, cross-shop denials, malformed CRC-self-consistent data. First CI failure was only blank 1-bit test image falling below preexisting 100-byte minimum; patterned synthetic fixture passed.
+- **F3-08 current backend output rights:** open [#880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880) final source `e98752d3bffd06b56af14d010891c9addb82a543`, exact 4/4 [CI #42284306824](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42284306824); grants now require canonical exact-str shop/job/asset IDs rather than equality-spoofed objects. Synthetic backend tests only; live rights provider is not mounted.
+- Both remain source **IN PROGRESS**, lacking independent security/rights review, main integration and fresh main CI. No new original task ID; DEV_CODE_DONE remains 4/33, 8 source in progress, 21 historical dependent, hosted accepted 0/33. Separate hosted JWT/RLS, approved customer media, Azure #249, licensed model/GPU approval unaffected. No GPU, paid model, hosted DB/PROD or WineShopPOS change.
+
+## 2026-11-08 — F3-08 private PNG parser deduplication and scoped identity guard
+
+- **2026-11-08 F3-08 source continuation (2026-11-07 UTC GitHub commits):** Existing [#880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880) head `918bbc14cef8bd6a9077ce766560d8fb8c8a4c3b` now delegates its GET-only private PNG HTTP response to the previously existing `Feature3PrivateBinaryHTTP` instead of maintaining a weaker parallel PNG parser. A scoped exact-string shop/job receipt boundary blocks equality-overloaded forged identifiers. Synthetic HTTP/route tests were updated to the complete private receipt, immutable SHA and opaque malformed-internal 503 semantics. The first refactor test run #42410099605 exposed 14 regressions, including a real 200-on-spoofed-scope defect; follow-up code/test repair was committed and [CI #42410323345](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42410323345) started. Concurrent existing [#879](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/879), head `60251cf930bb6131bad9e11f0713ca80ba50b12b`, adds exact-string shop/job checks and adversarial forged-equality tests to the underlying canonical binary adapter; [CI #42410451925](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42410451925) started. **At this documentation checkpoint, exact FINAL-head all-four CI results are not yet certified; verify both before source integration.** These PRs do not mount an Azure endpoint or supply real rights/JWT. Both remain sensitive and require independent security review; no new original task, merged DONE or hosted acceptance. Prior DEV_CODE_DONE 4/33 and hosted 0/33 unchanged. No GPU, paid inference, hosted database, PROD or WineShopPOS mutations.
+
+## 2026-11-08 — F3-08 private PNG route header correction (source only)
+
+2026-11-08 F3-08 private PNG source correction: Existing [#880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880) head `7d7f885a5a26a57ae99cffee1a661b9c448f2331` fixes a real response-contract break introduced by its earlier header-hardening change. The Azure adapter had required `Cache-Control: no-store, private` but the trusted `Feature3PrivateBinaryHTTP` actually returns the equally private `no-store, private, max-age=0`; the mismatch caused **valid 256x256 synthetic PNG reads to return HTTP 503**. Prior exact-head [CI #42505722622](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42505722622) failed Python 1 test (1197 passed; other three jobs passed). The fix permits exactly the two established no-store/private variants with an exact Python string check; rejects public/cacheable or overloaded-equality policy values and strips backend response metadata from the Azure reply. Added positive strict-header, negative caching/equality spoof and end-to-end synthetic PNG header tests without disabling security tests. Latest exact-head [CI #42507466950](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42507466950) **4/4 SUCCESS** (Python/uv, FFmpeg, Supabase isolation, frontend/Chromium). Source only: no Azure route mounted, no live JWT/RLS, current rights backend/provider, real private download, GPU/provider spend, hosted SQL, PROD or WineShopPOS change. Existing canonical security PR #879 remains unmerged, and both sensitive source PRs and shared docs require independent GitHub review; original Feature3 DEV_CODE_DONE baseline **4/33**, fully hosted **0/33** unchanged.
+Original task F3-08 remains source in progress; no additional 33-task acceptance receipt until approved merge and fresh main 4/4.
+
+## 2026-11-08 — F3-08 offline route-to-private-byte negative tests
+
+- Continued original F3-08 in existing source [PR #880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880): commit `6b8e8f86e670db8e0ffce4fd113d31cbf8c36c57` adds `tests/api/test_feature3_private_png_route_composed_two_shop.py`. Tests construct real in-process `handle_private_png_request` + `build_private_png_reader_factory` + `Feature3RevocablePNGReader`, with two isolated synthetic retailer JWTs/RLS rows, private PNG bytes, backend rights callback and authenticated Storage transport. Four tests cover (1) both shops getting only their own valid bytes and no leaked private headers, (2) foreign token denial before rights/Storage, (3) rights revoked during byte IO denying the returned PNG, and (4) JWT expiry during the read denying returned bytes and then recovery. All fake/local: **not** two live DEV identities, live JWT/RLS or a deployed route.
+- Python/uv [CI #42508181511](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42508181511) completed **1204 tests + 1152 subtests SUCCESS** on this head at the documentation checkpoint; **the other three jobs were still running and must be reverified before any 4/4 claim or source integration**. Prior source CI #42507466950 was 4/4 green on `7d7f885a` (cache-header fix), superseded by this new test-head.
+- PR #879 (canonical private binary) and PR #880 (route/rights) remain sensitive, unmerged and without real independent security review; docs #873 needs independent shared-document review too. Never classify test fixture as an accepted commercial license, hosted rights/JWT or Feature3 DONE. Original DEV_CODE_DONE baseline **4/33**, hosted **0/33** unchanged. GPU/paid model calls, hosted SQL, PROD and WineShopPOS untouched.
+
+## 2026-11-09 — F3-08 rights transport exception and CRLF framing hardening
+
+**2026-11-09 F3-08 source repair, [PR #880](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/880) head `e9612a8ec30746a5e8a332545e7c0fa7621973bd`:** Prior updated source head `7fbe7b7d81d4302e9f75894768775a4aa3f0ffa8` [CI #42568255441](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42568255441) had **7 failing Python cases, 1253 passing tests and 1301 passing subtests**, with the other three jobs successful. Two root causes: new rights transport outage handling correctly preserved `TimeoutError` for opaque HTTP 503 but a legacy reader unit test still expected an explicit-access-denial exception (404), and a new early bearer parser classified CR/LF injection as 401 instead of the established 400 framing rejection. The new source change re-establishes early 400 for CR/LF before GET-body or backend access, updates the low-level outage assertion to match transport-vs-denial semantics, and adds full two-shop route-to-reader rights-outage negative tests for failures before and after Storage IO. The separate existing rights-outage test imports the fixture under a private alias. Latest [Actions #42570838025](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/42570838025) **Python/uv PASSED: 1256 tests + 1308 subtests**; complete all-four final-head CI still requires verification at this document-writing checkpoint. This is source-only, with **NO** independently reviewed live rights provider or verified hosted JWT/RLS, no approved commercial media or activated private byte route; PRs #879/#880 and shared docs #873 remain unmerged/review-gated. Original F3-08 is **IN PROGRESS**, historic DEV_CODE_DONE **4/33**, fully hosted **0/33**. GPU/paid inference, hosted DB, PROD, WineShopPOS untouched.
+
+
+No GPU/paid model, Azure/SQL/PROD, or WineShopPOS changes.
~~~~

### docs/integration/F4_828_ORIGINAL_TRACKER_PROVENANCE_20261117.md
~~~~diff
@@ -0,0 +1,30 @@
+# Original Feature4 source-draft #828 tracker history — 2026-11-17
+
+Original source-draft #828 was OPEN at archival inspection head `ca103ce851c567d67198040a5a41738ea98e8395` and is now **CLOSED UNMERGED** (verified 2026-11-17). Its original run/task tracker included 16 historical nonblank lines absent from newer current parent #322. These are preserved verbatim below, **not** treated as 16 unfinished tasks. Four original source handoff markdown Git blobs and encoded motion source blob match current Feature4 parent exactly; original tests/motion/worker/editor contracts have been selectively imported or replaced with stronger current safety checks. Exact-parent CI, verified source preservation review and independent main integration are separate; no current feature is DONE by retiring stale branches.
+
+## Historical lines from original F4 tracker (exact source text)
+
+> ## 2026-10-29 — F4-04 independent encoded duplication parity batch
+> - Task **F4-04** remains IN PROGRESS until coordinator-reviewed integration and fresh main 4/4 CI. Stacked branch `feat/feature4-encoded-duplicate-parity-20261029` is isolated from coordinator/shared files and based on Feature4 #322 head `e32a8da61a6272666d757b6c51b0ec2576d7602f`.
+> - Reuses exact pinned Timeline Studio JS `studioDuplicate` via `duplicated_draft()`; trusted Python `compile_approved_storyboard` and the existing HyperFrames real 30s 540p H264/AAC CPU media job now physically encode both split/reorder and **separate 10/5/5/10 duplicate** actions. The real decoder checks two encoded replay positions 11.5s and 16.5s, distinct photo segments and source SHA; tests reject advanced replay, forged photo pairs, unexpected operations and missing proof. No GPU, paid inference, PROD, customer or WineShopPOS media.
+> - This is a deterministic **OWNER-REJECTED synthetic fixture**, not real retailer footage, commercial quality, or exact original-frame matching. Remain explicit `commercial_release_eligible=false`; source and QA are only complete after final branch/stack PR full four-job CI. Source-implemented is not integrated DONE; Feature4 #322 remains draft until coordinator resolves ZIP packaging and merges.
+> ## 2026-10-30 — Unified branch-green source handoff; source is NOT integrated DONE
+> Five nonoverlapping technical source drafts have been batched for one final integration CI run: #686 F4-04 encoded duplicate parity (4/4 #40955296326), #690 F4-13/F4-15 staged input mutation guard (4/4 #40955734381), #695 F4-14 immutable CPU benchmark (4/4 #40961371565), #701 F4-10 tenant-safe pointer editing (4/4 #40961280016), and #705 F4-03 exact-head 15/30/60 evidence verifier (4/4 #40966895351). Combined branch `feat/feature4-batched-source-handoff-20261030` is intentionally made as one tree/commit from existing #322 parent. None are coordinator-merged or commercial accepted. F4-03 actual three same-head MP4s, F4-14 all duration CPU budgets and F4-10 manual accessibility still OPEN; #650, #249 and real approved F2/F3/F5/F7 outputs remain external. Original draft PRs become trace evidence only, not five changes to apply twice. No GPU, paid AI, hosted actions, PROD or WineShopPOS.
+> ## 2026-10-30 — F4-11 independent continuous full-video black hold QA (draft #808)
+> - After consolidated source batch draft #779, F4-11 adds one FFmpeg continuous decode scan of the actual encoded 15/30/60s video, denying near-black holds of at least 0.65s that all five sampled interior frames can miss. The v3 60s SHA-linked source receipt requires this scan and explicitly disclaims shorter flashes, lettering/garment identity/rights and human approval; exact test-only 15s synthetic black-gap regression encodes a real 0.8s hidden hold. PR #808 is **draft, not merged**, dependency unchanged.
+> - First exact-head media CI #41052416541 caught an over-escaped raw regular expression while all other jobs passed; corrected parser and negative regression test in this follow-up source repair. Main integration/actual updated 60s technical and human acceptance still pending; F4-11 remains IN PROGRESS.
+> ## 2026-10-30 F4-14 three-length CPU evidence aggregator (NEW source, CI pending)
+> Draft stack on F4-11 #808, based on exact 4/4 head `81023702673f48730d85e4b33fae26936e8b30cd`. The new `feature4_cpu_matrix.py` requires three **real** 15/30/60 original 1080×1920/24fps H264/AAC MP4 files and their corresponding independently measured `benchmark_render.py` receipts. It reuses F4-03's stable hash / actual ffprobe verification, rejects swapped media, wrong duration, forged benchmark SHA/bytes, missing or altered Git checkout claim, false Azure/cloud/commercial flags, non-finite/missing timing/RSS data, path traversal and symlinked JSON. No media render is executed by this aggregator; unit tests use explicit fake probe, not real GPU/quality evidence.
+> `benchmark_render.py` now embeds a **declared local Git SHA**, not an independently signed Actions attestation. The matrix aggregates source-only 15/30/60 sampled CPU/RSS observations and marks `cloud_budget_accepted=false`, `code_commit_attested_by_ci=false`, `human_visual_approval=false`. It **does not** claim a matrix actually ran: required three same-code real encoded outputs and measured reports do not yet exist together. F4-14 remains IN PROGRESS; later opt-in full 60s CPU run is required, never automatically trigger repeated lengthy GPU/CPU or public samples.
+> CI and coordinator review/main merge/fresh main 4/4 must be verified before an accepted source task. No Azure Functions/PROD, priced AI, SQL, WineShopPOS.
+> ## 2026-10-30 — F4-05 animation/transition renderer CSS parity repair (draft pending)
+> - Verified trusted Python writer accepts animations `subtle_zoom/fade/slide/pop/glow` and transitions `fade/slide/cut`. Before this patch, **`anim-fade` and text-only `anim-subtle_zoom` were accepted but had no distinct matched CSS effects**, and `anim-glow` without an offer had no visible glow. Repaired the actual HyperFrames HTML/CSS compiler so all five modes act visibly on the glass layer, including text-only scenes. Client-to-compiler allowlists now import the single trusted renderer vocabulary; unexpected CSS/effects fail closed.
+> - Added offline tests for every approved enum and exact compiled stylesheet-keyframe selector, and rejects unsupported effect/preset injection. **Source-only parity, NOT actual decoded animation-frame QA**. Exact new-head four-job CI, coordinator-owned main integration and postmerge 4/4 required; F4-05 remains IN PROGRESS pending encoded visual/pixel review and UI/device QA. No paid inference, customer media or GPU.
+
+Original tracker Git SHA: `25ab70cda527de35793d8241f9ad5534d76453e2`. Current parent tracker Git SHA as reviewed: `ba599ecbdbc3d36ce78de72f298b1b870cb4b3b4`. Source original PR #828: https://github.com/saifsiddiqui59/RetailGrowthAI/pull/828
+
+GPU and paid models OFF; no Azure/PROD/SQL/WineShopPOS actions.
+
+## Current preservation boundary (2026-11-17 recheck)
+
+The exact historical #828 source head remains GitHub-readable after unmerged closure. Current F4 parent [#322](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322) has integrated or replaced its effect/motion/worker source while retaining this verbatim original task-history appendix in the reviewable #966 docs PR. This is **not** acceptance on main: parent is draft, the earlier media CI run #44011387138 failed a mock exhaustion regression, and the newer run #44012074650 cancelled during encoded rendering. A correct final-head 4/4, independent review and postmerge main 4/4 are required; keep underlying original tasks open.
~~~~

### docs/integration/F4_STACKED_DRAFT_DEDUP_20261115.md
~~~~diff
@@ -0,0 +1,44 @@
+# Feature4 stacked draft reconciliation — 2026-11-15
+
+This is an Integration Sprint bookkeeping checkpoint, **not release acceptance**. The source of truth is the GitHub PRs and exact commit blobs; feature #4 development still lives in #322 and owned source branches. No source code was merged, no tests run in this cleanup, and no GPU/provider/DEV/PROD/WineShopPOS mutation was made.
+
+## Exact Git-blob duplicate findings
+
+| Closed PR | Verified exact head | Changed files | Surviving source PR | Verification |
+|---|---|---:|---|---|
+| #822 (F4-05 effect parity) | `1ba7949c2666691a6442e007053bd1a2c58512d3` | 5 | #828 `ca103ce851c567d67198040a5a41738ea98e8395` | All 5/5 changed paths have identical Git blob SHA in #828 |
+| #824 (F4-15 lease/staged inode) | `3dd468202a781f331391ff1172ba4f5cbc60384b` | 3 | #828 (same head) | All 3/3 changed paths have identical Git blob SHA in #828 |
+| #827 (F4-11 encoded motion identity) | `b1a5058c853b8087788982311c12f2576323877d` | 3 | #828 (same head) | All 3/3 changed paths have identical Git blob SHA in #828 |
+
+All three PR objects were closed **UNMERGED** with durable per-PR evidence comments. At the original 2026-11-15 checkpoint, surviving #828 was OPEN and targeted the F4 CPU profile branch; its exact original 11 source/test/handoff blobs were preserved. **Live recheck on 2026-11-17: #828 is CLOSED UNMERGED**; the current #322 F4 parent contains reconciled source and an additional original-tracker provenance archive, but this is still not main integration. Closing child PRs did **not** add their code to main or mark F4-05/F4-11/F4-15 DONE.
+
+## Older drafts reviewed and deliberately kept open
+
+- #735 — duplicate-encoded QA: candidate `feature4_edited_export_qa.py` has different SHA from both current #322 and older batch #779; unique mock decoder function present in #735 but absent in #322.
+- #745 — encoded motion probe: changed QA logic not in #322, needs controlled additive port/testing.
+- #753 — full-minute contiguous visibility receipt: unique requirement absent from #322 version, keep source/test.
+- #773 — near-cut boundary probes: unique QA logic absent from #322 version.
+- #784 — cancelled drag fencing: JSX differs from #322 and older #779; needs current UI event reconciliation.
+- #799 — original-stage receipt identity: source/test/handoff differ or are absent on #779.
+- #803 — auxiliary media rights denial: source/test/handoff differ or are absent on #779.
+- #808 — 60s continuous black-scan receipt: changed paths identified; **full semantic dedup NOT proven**.
+- #822 and #824 — included in the ten-first review set; closed as above.
+- #827 — additionally inspected and closed, bringing the reviewed set to eleven unique PRs.
+
+Current original [F4 parent #322](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322) is still DRAFT and cannot be treated as main-integrated. Avoid wholesale merging old ancestors or silently replacing newer security/tenant contracts. Existing [batch #779](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/779) while historical [consolidation #828](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/828) was closed unmerged after reconciliation into the *still-open* F4 parent. Neither state means DONE.
+
+## Follow-up / bounded acceptance
+
+1. Feature4 owner checks the already-reconciled #828 source and retained unique older changes against the **latest** #322 and newest main, preserving all surviving negative tests and original provenance without reopening #828. Preserve current tests and the new missing protections.
+2. Run targeted CPU/FFmpeg/UI negative tests, then verify required exact-final-head 4/4 CI on eligible main-targeted PRs. Review sensitive rights, storage/auth, and cross-feature paths independently.
+3. After safe non-draft PR merge, separately verify fresh exact-main 4/4 before any original task DONE receipt. Only then update canonical completion counters.
+4. Do not restore old branches merely to reduce the open count. GPU OFF, paid AI OFF, no cloud deployment, PROD or WineShopPOS modifications.
+
+Reference: PR comments on #822, #824, #827 and the preserved parent #828.
+
+## Live CI and review recheck — 2026-11-17
+
+- Parent [#322](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/322) currently has source head `b9525a9ea3d5e5aee351edf89a3c011c2314ed2e`, still **DRAFT** with zero independent reviews. Earlier exact source commit `c2bc9ff9b47c46c9186a72b9faa86e894bebb1cd` failed FFmpeg job in [run #44011387138](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44011387138) because the inode-swap regression mock exhausted its frame `side_effect` and raised `StopIteration`. The later parent commit adds a 4-line correction in `video-engine/feature4_edited_export_qa.py`, but its [run #44012074650](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44012074650) had three successful jobs and **cancelled** FFmpeg rendering near the existing job time budget: **not 4/4 accepted**.
+- Separate [#967](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/967) proposes a 15→25-minute FFmpeg workflow cap and passed exact-head [run #44000894199](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44000894199) **4/4**. It remains OPEN and requires independent shared-workflow review; a green workflow-change PR does not retroactively pass #322's media job.
+- [#779](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/779) remains OPEN/DRAFT and historically stacked; current #322 holds newer reconciled versions of shared source. **Do not merge #779 wholesale, mark F4 task DONE or retire it solely on this bookkeeping evidence**; require full source/negative-test parity and safe review.
+- This docs PR [#966](https://github.com/saifsiddiqui59/RetailGrowthAI/pull/966) previously passed exact-head [run #44011542854](https://github.com/saifsiddiqui59/RetailGrowthAI/actions/runs/44011542854) 4/4, **before this follow-up docs correction**. Recheck final exact-head four-job CI and independent canonical-doc review before any merge. No GPU, paid models, hosted mutation, PROD or WineShopPOS actions.
~~~~

## Unfinished conditions remain
Continue exact original F4 task IDs, parent #322 and private JWT/RLS, rights, visual editorial source/acceptance; do not use archive alone to mark DONE. No model inference, GPU, paid API, hosted Azure, PROD or WineShopPOS.