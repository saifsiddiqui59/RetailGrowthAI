import test from 'node:test'
import assert from 'node:assert/strict'
import { studioRanges, studioSplit, studioReorder, studioTrimPair, studioSourceTrim, studioValidatedDraft } from '../../frontend/src/features/video/timeline-studio-bridge.mjs'
import { inspectCreativeDirection } from '../../frontend/src/features/video/creative-direction-adapter.mjs'
import { createEditorHistory, pushEditorHistory, undoEditorHistory, redoEditorHistory } from '../../frontend/src/features/video/vendor/editorHistoryCore.mjs'
import { packTimedSegmentsIntoLanes, materializeCaptionTimings, getVisualSegmentTimeline } from '../../frontend/src/features/video/vendor/timeline.js'
import { getTimelineRulerTicks, getTimelineAutoFitZoom } from '../../frontend/src/features/video/vendor/timelineScale.js'
import { makeVideoDraft, validateVideoDraft } from '../../frontend/src/features/video/video-model.mjs'

const SHOP='11111111-1111-4111-8111-111111111111'
const OTHER='22222222-2222-4222-8222-222222222222'
const assets=[
 {id:'photo1',kind:'image',shop_id:SHOP,authorized:true,name:'Reviewed kurti'},
 {id:'motion1',kind:'video',shop_id:SHOP,authorized:true,name:'Mocked Feature5 motion'},
 {id:'poster1',kind:'poster',shop_id:SHOP,authorized:true,name:'Reviewed poster'},
 {id:'forbidden',kind:'video',shop_id:OTHER,authorized:true},
 {id:'revoked',kind:'video',shop_id:SHOP,authorized:false},
]
const music=[{id:'licensed_music',kind:'audio',authorized:true,shop_id:SHOP}]
function draft(){
 const d=makeVideoDraft({shopId:SHOP,mode:'media',duration:30,mediaAssets:assets})
 d.scenes[0].asset_id='photo1'
 d.scenes[1].asset_id='motion1'
 d.scenes[2].asset_id='poster1'
 d.scenes[1].headline='Approved model movement'
 d.scenes[1].offer='20% OFF'
 d.music_asset_id='licensed_music'
 return d
}

test('real upstream timeline geometry, caption lanes and zoom work on approved ad',()=>{
 const d=draft()
 assert.deepEqual(studioRanges(d).map(s=>[s.start,s.end]),[[0,10],[10,20],[20,30]])
 assert.equal(getVisualSegmentTimeline(d.scenes).at(-1).end,30)
 const zoom=getTimelineAutoFitZoom(30)
 const ticks=getTimelineRulerTicks(30,zoom,0,30)
 assert.ok(ticks.some(t=>t.isMajor))
 const captions=materializeCaptionTimings(d.scenes.map(s=>({text:s.headline,start:s.start,end:s.start+s.duration})),30)
 assert.deepEqual(captions.map(s=>s.start),[0,10,20])
 assert.equal(packTimedSegmentsIntoLanes(captions.map((s,i)=>({...s,id:'caption'+i,duration:s.end-s.start}))).length,1)
})

test('Timeline Studio real upstream splitter preserves exact retailer offer and sound source',()=>{
 const d=draft()
 const out=studioSplit(d,1,4,assets)
 assert.equal(out.scenes.length,4)
 assert.deepEqual(out.scenes.map(s=>s.start),[0,10,14,20])
 assert.deepEqual(out.scenes.map(s=>s.duration),[10,4,6,10])
 assert.equal(out.scenes[1].offer,'20% OFF')
 assert.equal(out.scenes[2].offer,'20% OFF')
 assert.equal(out.scenes[1].asset_id,'motion1')
 assert.equal(out.scenes[2].asset_id,'motion1')
 assert.equal(out.scenes[2].trim_start,4)
 assert.equal(out.scenes[2].headline,'Approved model movement')
 assert.deepEqual(validateVideoDraft(out,assets,music),[])
 assert.deepEqual(d.scenes.map(s=>s.duration),[10,10,10],'original draft stays immutable')
})

test('split after a source trim keeps playback offsets, not fake footage generation',()=>{
 const trimmed=studioSourceTrim(draft(),1,3.25,assets)
 const split=studioSplit(trimmed,1,3,assets)
 assert.equal(split.scenes[1].trim_start,3.25)
 assert.equal(split.scenes[2].trim_start,6.25)
 assert.deepEqual(validateVideoDraft(split,assets,music),[])
})
test('reorder/retime independent tracks and maintain exact 30s backend contract',()=>{
 let d=draft()
 d=studioReorder(d,0,2)
 assert.deepEqual(d.scenes.map(s=>s.asset_id),['motion1','poster1','photo1'])
 d=studioTrimPair(d,0,2.5)
 assert.deepEqual(d.scenes.map(s=>s.duration),[12.5,7.5,10])
 assert.deepEqual(d.scenes.map(s=>s.start),[0,12.5,20])
 assert.deepEqual(validateVideoDraft(d,assets,music),[])
 assert.throws(()=>studioTrimPair(d,0,100),/at least/)
 assert.throws(()=>studioReorder(d,0,3),/Invalid/)
})
test('denies foreign, revoked, nonexistent media and invalid split without silent fallback',()=>{
 const d=draft()
 assert.throws(()=>studioSplit(d,1,.1,assets),/Split/)
 assert.throws(()=>studioSplit(d,1,10,assets),/Split/)
 const foreign={...d,scenes:d.scenes.map((s,i)=>i===1?{...s,asset_id:'forbidden'}:s)}
 assert.throws(()=>studioSplit(foreign,1,3,assets),/unapproved/)
 const revoked={...d,scenes:d.scenes.map((s,i)=>i===1?{...s,asset_id:'revoked'}:s)}
 assert.throws(()=>studioSplit(revoked,1,3,assets),/unapproved/)
 assert.throws(()=>studioSourceTrim(d,0,2,assets),/Source trim/)
 assert.throws(()=>studioSourceTrim(d,1,-3,assets),/Source trim/)
 assert.throws(()=>studioValidatedDraft({...d,cta:''},assets,music),/CTA/)
})
test('upstream undo/redo clears redo after new action and resets project state',()=>{
 const a=draft(), b=studioReorder(a,0,1)
 const first=createEditorHistory(a)
 const second=pushEditorHistory(first,b)
 assert.equal(second.current.scenes[0].asset_id,'motion1')
 const undo=undoEditorHistory(second)
 assert.equal(undo.changed,true)
 assert.equal(undo.value.scenes[0].asset_id,'photo1')
 const redo=redoEditorHistory(undo.history)
 assert.equal(redo.value.scenes[0].asset_id,'motion1')
 assert.equal(pushEditorHistory(undo.history,a).future.length,0)
 assert.equal(undoEditorHistory(first).changed,false)
})
function direction(){
 const d=draft()
 return {version:'creative_direction_v1',source_feature:'feature2',approved:true,
 shop_id:SHOP,campaign_id:'campaign1',approval_id:'approval1',review_hash:'a'.repeat(64),
 template:'cinematic',duration_seconds:30,cta:d.cta,music_asset_id:d.music_asset_id,
 scenes:d.scenes.map(s=>({duration:s.duration,asset_id:s.asset_id,headline:s.headline,
 animation_preset:s.animation_preset,transition:s.transition,...(s.offer?{offer:s.offer}:{})})),
 motion_direction_v1: {prompts:['Photoreal adult wearing identical approved kurti']}
 }
}
test('creative_direction_v1 is read-only renderer-safe bridge; preserves approved copy',()=>{
 const original=direction(), unchanged=structuredClone(original)
 const {draft:plan,readOnly,reviewHash}=inspectCreativeDirection(original,{shopId:SHOP,mediaAssets:assets,musicAssets:music})
 assert.equal(readOnly,true)
 assert.equal(reviewHash,'a'.repeat(64))
 assert.equal(plan.version,'rg_video_v2')
 assert.equal(plan.scenes[1].headline,'Approved model movement')
 assert.equal(plan.scenes[1].offer,'20% OFF')
 assert.equal(plan.cta,'Visit our store')
 assert.deepEqual(original,unchanged)
 assert.deepEqual(validateVideoDraft(plan,assets,music),[])
})
test('rejects mismatched/revoked creative approval and unsupported transitions',()=>{
 const good=direction()
 for(const modify of [
 d=>d.shop_id=OTHER,d=>d.approved=false,d=>d.version='creative_direction_v2',
 d=>d.scenes[1].asset_id='forbidden',d=>d.scenes[1].asset_id='revoked',
 d=>d.scenes[1].transition='wipe',d=>d.scenes[1].animation_preset='ai_weird',
 d=>d.scenes[1].headline='fake promotional line'.repeat(20),
 d=>d.duration_seconds=60,d=>d.music_asset_id='stolen',
 d=>d.review_hash='',d=>d.cta='',
 ]){const v=structuredClone(good);modify(v);assert.throws(()=>inspectCreativeDirection(v,{shopId:SHOP,mediaAssets:assets,musicAssets:music}))}
})

test('security: cross-tenant poster overlay and soundtrack are rejected independently',()=>{
 const d=draft()
 const forged=structuredClone(d)
 forged.scenes[0].poster_overlay_asset_id='foreign_overlay'
 const all=[...assets,{id:'foreign_overlay',kind:'poster',shop_id:OTHER,authorized:true}]
 assert.throws(()=>studioValidatedDraft(forged,all,music),/Foreign, unlicensed or revoked/)
 const revoked={...d, music_asset_id:'licensed_music'}
 assert.throws(()=>studioValidatedDraft(revoked,assets,[{...music[0],authorized:false}]),/Foreign, unlicensed or revoked/)
})
test('video source bounds reject trim beyond verified duration, including after split',()=>{
 const d=draft()
 const measured=assets.map(a=>a.id==='motion1'?{...a,duration_seconds:11}:a)
 assert.throws(()=>studioSourceTrim(d,1,2,measured),/verified source length/)
 const ok=studioSourceTrim(d,1,1,measured)
 assert.deepEqual(validateVideoDraft(ok,assets,music),[])
 assert.throws(()=>studioValidatedDraft({...d,scenes:d.scenes.map((s,i)=>
  i===1?{...s,trim_start:3}:s)},measured,music),/verified source length/)
 const trimmed=studioSplit(ok,1,4,measured)
 assert.equal(trimmed.scenes[2].trim_start,5)
 assert.deepEqual(validateVideoDraft(trimmed,assets,music),[])
})
test('video right-hand boundary trim never rewinds or silently replays source footage',()=>{
 const d=draft()
 const modified={...d,scenes:d.scenes.map((s,i)=>i===1?{...s,trim_start:4}:s)}
 const moved=studioTrimPair(modified,0,2)
 assert.equal(moved.scenes[1].trim_start,6)
 assert.equal(moved.scenes[1].duration,8)
 assert.deepEqual(validateVideoDraft(moved,assets,music),[])
 assert.throws(()=>studioTrimPair(modified,0,-5),/before its source begins/)
})

test('moving the first image/video boundary never replays untrimmed motion clips',()=>{
  const d=draft()
  const changed=studioTrimPair(d,0,2,assets)
  assert.equal(changed.scenes[1].duration,8)
  assert.equal(changed.scenes[1].trim_start,2)
  assert.throws(()=>studioTrimPair(d,0,-2,assets),/before its source begins/)
  const measured=assets.map(a=>a.id==='motion1'?{...a,duration_seconds:9}:a)
  assert.throws(()=>studioValidatedDraft(changed,measured,music),/verified source length/)
})
