import test from 'node:test'
import assert from 'node:assert/strict'
import { studioRanges, studioSplit, studioDuplicate, studioReorder, studioTrimPair, studioSourceTrim, studioValidatedDraft } from '../../frontend/src/features/video/timeline-studio-bridge.mjs'
import { inspectCreativeDirection, checkedPreviewCaptionCues } from '../../frontend/src/features/video/creative-direction-adapter.mjs'
import { createEditorHistory, pushEditorHistory, undoEditorHistory, redoEditorHistory } from '../../frontend/src/features/video/vendor/editorHistoryCore.mjs'
import { packTimedSegmentsIntoLanes, materializeCaptionTimings, getVisualSegmentTimeline } from '../../frontend/src/features/video/vendor/timeline.js'
import { getTimelineRulerTicks, getTimelineAutoFitZoom } from '../../frontend/src/features/video/vendor/timelineScale.js'
import { makeVideoDraft, compatibleMedia, validateVideoDraft, sourceClipPlaybackWindow } from '../../frontend/src/features/video/video-model.mjs'

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

test('scene sound effect is licensed and tenant-scoped, and remains a 2s SFX not voiceover',()=>{
 const d=draft()
 const withSfx={...d,scenes:d.scenes.map((s,i)=>i===1?{...s,sfx_asset_id:'licensed_music'}:s)}
 assert.deepEqual(validateVideoDraft(withSfx,assets,music),[])
 assert.equal(studioValidatedDraft(withSfx,assets,music).scenes[1].sfx_asset_id,'licensed_music')
 const other=[{...music[0],shop_id:OTHER}]
 assert.match(validateVideoDraft(withSfx,assets,other).join(';'),/same-shop licensed audio effect/)
 assert.throws(()=>studioValidatedDraft(withSfx,assets,other),/Foreign, unlicensed or revoked/)
})

test('full-Reel narration is a separate approved, tenant-owned source and not scene SFX',()=>{
 const d=draft()
 const voiced={...d,voiceover_asset_id:'licensed_music'}
 assert.deepEqual(validateVideoDraft(voiced,assets,music),[])
 assert.equal(studioValidatedDraft(voiced,assets,music).voiceover_asset_id,'licensed_music')
 const other=[{...music[0],shop_id:OTHER}]
 assert.match(validateVideoDraft(voiced,assets,other).join(';'),/same-shop full-Reel/)
 assert.throws(()=>studioValidatedDraft(voiced,assets,other),/Foreign, unlicensed or revoked/)
})

test('authoritative shop matching is required for product, poster, music and output validation',()=>{
 const d=draft()
 const media=[...assets,{id:'foreign',kind:'image',authorized:true,shop_id:OTHER}]
 assert.equal(compatibleMedia('media',media,SHOP).some(a=>a.id==='foreign'),false)
 const initial=makeVideoDraft({shopId:SHOP,mode:'media',duration:30,mediaAssets:[media.at(-1),...assets]})
 assert.notEqual(initial.scenes[0].asset_id,'foreign')
 const foreignAsset={...d,scenes:d.scenes.map((s,i)=>i===0?{...s,asset_id:'foreign'}:s)}
 assert.match(validateVideoDraft(foreignAsset,media,music).join(';'),/same-shop media/)
 const foreignPoster={...d,scenes:d.scenes.map((s,i)=>i===1?{...s,poster_overlay_asset_id:'foreign_poster'}:s)}
 const posters=[...media,{id:'foreign_poster',kind:'poster',authorized:true,shop_id:OTHER}]
 assert.match(validateVideoDraft(foreignPoster,posters,music).join(';'),/promotional poster/)
 const foreignMusic={...d,music_asset_id:'licensed_music'}
 assert.match(validateVideoDraft(foreignMusic,assets,[{...music[0],shop_id:OTHER}]).join(';'),/rights-cleared music/)
})
test('front-end refuses unsupported video edits and source-duration overruns before submission',()=>{
 const d=draft(), measured=assets.map(a=>a.id==='motion1'?{...a,duration_seconds:10}:a)
 const forged={...d,scenes:d.scenes.map((s,i)=>i===1?{...s,trim_start:2}:s)}
 assert.match(validateVideoDraft(forged,measured,music).join(';'),/verified video source duration/)
 const imageTrim={...d,scenes:d.scenes.map((s,i)=>i===0?{...s,trim_start:3}:s)}
 assert.match(validateVideoDraft(imageTrim,measured,music).join(';'),/invalid approved video trim/)
 const wrongMute={...d,scenes:d.scenes.map((s,i)=>i===0?{...s,mute_source:true}:s)}
 assert.match(validateVideoDraft(wrongMute,measured,music).join(';'),/source audio mute/)
 const shortVoice={...d,voiceover_asset_id:'licensed_music'}
 assert.match(validateVideoDraft(shortVoice,assets,[{...music[0],duration_seconds:8}]).join(';'),/does not cover/)
})

test('signed source video preview plays only the exact renderer trim window',()=>{
 const scene={duration:6,trim_start:2.5}
 const source={kind:'video',authorized:true,duration_seconds:9}
 assert.deepEqual(sourceClipPlaybackWindow(scene,source),{start:2.5,end:8.5})
 assert.equal(sourceClipPlaybackWindow(scene,{kind:'image',authorized:true}),null)
 assert.throws(()=>sourceClipPlaybackWindow({...scene,trim_start:3.5},source),/exceeds verified/)
 assert.throws(()=>sourceClipPlaybackWindow({...scene,trim_start:-1},source),/invalid verified/)
 assert.throws(()=>sourceClipPlaybackWindow({...scene,trim_start:NaN},source),/invalid verified/)
})

test('approved F2 clip trims, source mute and poster layers survive read-only handoff unchanged',()=>{
 const d=direction(), original=structuredClone(d)
 d.scenes[1].trim_start=2
 d.scenes[1].mute_source=true
 d.scenes[1].poster_overlay_asset_id='poster1'
 const approved=structuredClone(d)
 const result=inspectCreativeDirection(d,{shopId:SHOP,mediaAssets:assets,musicAssets:music})
 assert.equal(result.readOnly,true)
 assert.equal(result.draft.scenes[1].trim_start,2)
 assert.equal(result.draft.scenes[1].mute_source,true)
 assert.equal(result.draft.scenes[1].poster_overlay_asset_id,'poster1')
 assert.deepEqual(d,approved)
 assert.equal(original.scenes[1].trim_start,undefined)
 for(const mutate of [
   v=>v.scenes[1].trim_start=-1,
   v=>v.scenes[1].trim_start=Infinity,
   v=>v.scenes[0].trim_start=2,
   v=>v.scenes[1].mute_source='true',
   v=>v.scenes[1].poster_overlay_asset_id='motion1',
   v=>v.scenes[1].poster_overlay_asset_id='foreign',
 ]) {
   const forged=structuredClone(d)
   mutate(forged)
   assert.throws(()=>inspectCreativeDirection(forged,{shopId:SHOP,mediaAssets:assets,musicAssets:music}),
     /Feature #2 scene/)
 }
})

test('splitting a scene never duplicates or truncates its approved timed SFX',()=>{
 const d=draft()
 const audio={...d,scenes:d.scenes.map((s,i)=>i===1?{...s,sfx_asset_id:'licensed_music'}:s)}
 const split=studioSplit(audio,1,3,assets)
 assert.equal(split.scenes[1].sfx_asset_id,'licensed_music')
 assert.equal(split.scenes[2].sfx_asset_id,undefined)
 assert.equal(split.scenes[1].duration,3)
 assert.deepEqual(validateVideoDraft(split,assets,music),[])
 assert.throws(()=>studioSplit(audio,1,1,assets),/cut through the approved 2-second/)
 assert.deepEqual(audio.scenes[1].duration,10)
})

test('Feature2 approved timed subtitles display as immutable transcript instead of scene headings',()=>{
 const d=direction()
 d.voiceover_asset_id='licensed_music'
 d.script={source_feature:'feature2',approved:true,approval_id:'approval1',
  transcript:[{start:.5,duration:2,text:'Approved voice cue'},
  {start:20,duration:2,text:'Visit our store'}]}
 const unchanged=structuredClone(d)
 const result=inspectCreativeDirection(d,{shopId:SHOP,mediaAssets:assets,musicAssets:music})
 assert.equal(result.captionCues.length,2)
 assert.equal(result.captionCues[1].start,20)
 assert.deepEqual(d,unchanged)
 assert.equal(result.draft.scenes.length,3)
 for(const change of [
  q=>q.script.transcript[1].start=1,
  q=>q.script.transcript[0].text='<script>',
  q=>q.script.approved=false,
  q=>q.script.approval_id='another',
  q=>q.voiceover_asset_id=null,
 ]) {
  const candidate=structuredClone(d)
  change(candidate)
  assert.throws(()=>inspectCreativeDirection(candidate,{shopId:SHOP,mediaAssets:assets,musicAssets:music}))
 }
 assert.throws(()=>checkedPreviewCaptionCues([{start:0,duration:35,text:'bad'}],30))
})

test('approved F2 subtitle millisecond timecodes match backend without silent rounding',()=>{
  const cues=[{start:0.5,duration:1.25,text:'Silk & craft'},
    {start:1.75,duration:0.5,text:'Visit our store'}]
  assert.deepEqual(checkedPreviewCaptionCues(cues,30),cues)
  for (const invalid of [
    [{start:0.5004,duration:1.25,text:'Submillisecond start'}],
    [{start:0.5,duration:1.2504,text:'Submillisecond duration'}],
    [cues[0],{start:1.749,duration:0.5,text:'One millisecond overlap'}],
    [{start:29.801,duration:0.2,text:'Beyond 30s Reel'}],
  ]) {
    assert.throws(()=>checkedPreviewCaptionCues(invalid,30),/unsafe or overlapping/)
  }
})

test('timeline boundary changes never silently shorten or extend approved 2s scene SFX',()=>{
  const original=draft()
  const withEffect={...original,scenes:original.scenes.map((scene,index)=>
    index===1?{...scene,sfx_asset_id:'licensed_music'}:scene)}
  assert.throws(()=>studioTrimPair(withEffect,0,8.5,assets),/sound-effect duration/)
  assert.throws(()=>studioTrimPair(withEffect,1,-8.5,assets),/sound-effect duration/)
  const safe=studioTrimPair(withEffect,0,2,assets)
  assert.equal(safe.scenes[1].duration,8)
  assert.equal(safe.scenes[1].sfx_asset_id,'licensed_music')
  assert.deepEqual(validateVideoDraft(safe,assets,music),[])
  assert.equal(withEffect.scenes[1].duration,10)
})

test('extending left-hand video boundary cannot exceed verified private source duration',()=>{
  const original=draft()
  const measured=assets.map(a=>a.id==='motion1'?{...a,duration_seconds:10}:a)
  assert.throws(()=>studioTrimPair(original,1,1,measured),/verified source video duration/)
  assert.equal(original.scenes[1].duration,10)
  // Decreasing the selected video scene remains permitted and is source-safe.
  const safe=studioTrimPair(original,1,-1,measured)
  assert.equal(safe.scenes[1].duration,9)
  assert.deepEqual(validateVideoDraft(safe,measured,music),[])
})

test('real MIT OpenReel frame controls parse and step at 24/30fps with strict invalid input',async()=>{
  const {formatFrameTimecode,parseFrameTimecode}=await import('../../frontend/src/features/video/vendor/openreel/frame-timecode.mjs')
  const {stepEditingFrame,normalizeEditingFrameRate}=await import('../../frontend/src/features/video/vendor/openreel/editing-frame-rate.mjs')
  assert.equal(formatFrameTimecode(1.5,24),'00:00:01:12')
  assert.equal(formatFrameTimecode(1.5,30),'00:00:01:15')
  assert.equal(parseFrameTimecode('00:00:02:12',24),2.5)
  assert.equal(parseFrameTimecode('01:02:12',24),62.5)
  assert.equal(parseFrameTimecode('0.04',24),1/24)
  assert.equal(stepEditingFrame(0,1,30),1/30)
  assert.equal(stepEditingFrame(1/30,-1,30),0)
  assert.equal(normalizeEditingFrameRate(0),30)
  for(const invalid of ['','oops','-1','00:00:60:00','00:00:00:30','Infinity'])
    assert.equal(parseFrameTimecode(invalid,30),null)
})

test('OpenReel real track item selection identifies only authorized scenes and splittable interiors',async()=>{
  const {getTimelineItemRanges,getTimelineTrackSelection,getSplittableTimelineItemIds}
    = await import('../../frontend/src/features/video/vendor/openreel/timeline-item-actions.mjs')
  const plan=draft()
  const project={timeline:{tracks:[{id:'video',clips:plan.scenes.map((scene,i)=>({
    id:'scene-'+i,startTime:scene.start,duration:scene.duration}))}]}}
  const items=getTimelineItemRanges(project)
  assert.deepEqual(items.map(x=>x.startTime),[0,10,20])
  assert.deepEqual(getTimelineTrackSelection(project,'video').map(x=>x.id),['scene-0','scene-1','scene-2'])
  assert.deepEqual(getSplittableTimelineItemIds(project,['scene-1'],14),['scene-1'])
  assert.deepEqual(getSplittableTimelineItemIds(project,['scene-1'],10),[])
  assert.deepEqual(getSplittableTimelineItemIds(project,['scene-1'],20),[])
  assert.deepEqual(getSplittableTimelineItemIds(project,['forged-scene'],14),[])
})

test('OpenReel actual ClipManager snap finds cut/grid boundaries without modifying source',async()=>{
 const {OpenReelClipSnapper}
   =await import('../../frontend/src/features/video/vendor/openreel/clip-snap.mjs')
 const timeline={tracks:[{id:'video',clips:[
   {id:'scene-0',startTime:0,duration:3.5},
   {id:'scene-1',startTime:3.5,duration:6.5}
 ]}]}
 const original=structuredClone(timeline)
 const snapper=new OpenReelClipSnapper({snapThreshold:8,gridSize:1})
 const hit=snapper.snapToGrid(3.46,timeline,'video',100)
 assert.equal(hit.didSnap,true)
 assert.equal(hit.snappedTime,3.5)
 assert.equal(hit.snapTarget,'clip-end')
 assert.equal(snapper.snapToGrid(1.02,timeline,'video',100).snappedTime,1)
 assert.equal(snapper.snapToGrid(2.29,timeline,'video',100).didSnap,false)
 assert.deepEqual(timeline,original)
 const off=new OpenReelClipSnapper({snapToGridEnabled:false})
 assert.equal(off.snapToGrid(3.46,timeline,'video',100).snappedTime,3.46)
})


test('duplicate visual clip replays authorized in-point in-place with exact 30s duration',()=>{
 const original=draft()
 const doubled=studioDuplicate(original,1,assets)
 assert.equal(original.scenes.length,3)
 assert.equal(doubled.scenes.length,4)
 assert.deepEqual(doubled.scenes.map(s=>s.duration),[10,5,5,10])
 assert.equal(doubled.scenes[1].asset_id,'motion1')
 assert.equal(doubled.scenes[2].asset_id,'motion1')
 assert.equal(doubled.scenes[1].trim_start||0,0)
 assert.equal(doubled.scenes[2].trim_start,0) // Replay, not fake extra footage.
 assert.equal(doubled.scenes[1].offer,'20% OFF')
 assert.equal(doubled.scenes[2].offer,'20% OFF')
 assert.equal(doubled.scenes.reduce((n,s)=>n+s.duration,0),30)
 assert.deepEqual(validateVideoDraft(doubled,assets,music),[])
 assert.deepEqual(studioRanges(doubled).map(s=>s.end),[10,15,20,30])
 const retimed={...original,scenes:original.scenes.map((s,i)=>i===1?{...s,trim_start:2}:s)}
 const repeat=studioDuplicate(retimed,1,assets)
 assert.equal(repeat.scenes[2].trim_start,2)
})

test('duplicate cannot import foreign source, repeat SFX or change total Reel duration',()=>{
 const base=draft()
 assert.throws(()=>studioDuplicate(base,99,assets),/Duplication/)
 const foreign={...base,scenes:base.scenes.map((s,i)=>i===1?{...s,asset_id:'forbidden'}:s)}
 assert.throws(()=>studioDuplicate(foreign,1,assets),/foreign or unapproved/)
 const approvedSfx={...base,scenes:base.scenes.map((s,i)=>i===1?{...s,sfx_asset_id:'licensed_music'}:s)}
 const duplicated=studioDuplicate(approvedSfx,1,assets)
 assert.equal(duplicated.scenes[1].sfx_asset_id,'licensed_music')
 assert.equal(duplicated.scenes[2].sfx_asset_id,undefined)
 assert.deepEqual(validateVideoDraft(duplicated,assets,music),[])
 const shortFx={...base,scenes:base.scenes.map((s,i)=>i===1?{...s,duration:3,sfx_asset_id:'licensed_music'}:s)}
 assert.throws(()=>studioDuplicate(shortFx,1,assets),/truncate an approved/)
 const limited={...base,scenes:Array.from({length:12},(_,i)=>({...base.scenes[0],duration:2.5}))}
 assert.throws(()=>studioDuplicate(limited,1,assets),/fewer than 12/)
})
