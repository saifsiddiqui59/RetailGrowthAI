/*
 * Feature #7: tenant-fenced, review-only uploaded-footage semantic suggestions.
 * Adapted from AutoBroll (Andrii Drok, MIT), pinned upstream main
 * tree 4aef3afb099c866bd2977c184f9912ba57318f77:
 *   scripts/trim-silence.mjs (speech runs and pause pads)
 *   scripts/captions-multiclip.mjs (phrase-aware caption grouping)
 *   scripts/broll-multiclip.mjs (word-index B-roll anchors)
 *   src/captions.ts (source-relative caption anchoring)
 * Changes: pure functions, no file/network calls, no Gemini/Pexels/WhisperX
 * execution, strict trusted same-shop uploaded media grants, no Remotion.
 * See AUTOBROLL_MIT_LICENSE.txt and HANDOFF.md.
 */
import {sha256Hex} from './sha256_sync.mjs';

const GAP_THRESH = 600; // AutoBroll: gap larger than 600ms creates a cut
const LEAD_PAD = 0.1;
const TRAIL_PAD = 0.3;
const INNER_PAD = 0.08;
const MIN_LEN = 0.35;
const MAX_WORDS = 5;
const GAP_MS = 450;
const DEFAULT_TOP = 58;
const GLUE = new Set([
  'a','an','the','of','to','and','or','but','in','on','at','for','with',
  'from','by','is','was','are','were','be','been','that','this','it','its',
  'as','so','my','your','i','we','you','they','he','she','has','have',
  'had','will',"it's",'about','into',
]);
const PUNCT_ONLY = /^[.,!?;:()\-—]+$/;
const SENT_END = /[.!?]$/;
const CLAUSE_END = /[,;:]$/;
const ASSET_ID = /^[a-zA-Z0-9_-]{1,100}$/;
const MAX_SCENES = 12;

export class EditValidationError extends Error {}

function requireThat(ok, msg) {
  if (!ok) throw new EditValidationError(msg);
}
function finite(value, min, max) {
  return typeof value === 'number' && Number.isFinite(value) && value >= min && value <= max;
}
function identity(value, label) {
  requireThat(typeof value === 'string' && ASSET_ID.test(value), 'Invalid ' + label);
  return value;
}
// A deterministic *hint*: Feature4 must recompute the hash in Python using
// draft_fingerprint before binding it to a persisted approval snapshot.
function sortJSON(value) {
  if (Array.isArray(value)) return value.map(sortJSON);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.keys(value).sort().map(k => [k, sortJSON(value[k])]));
  }
  return value;
}
export function draftHashHint(draft) {
  return sha256Hex(JSON.stringify(sortJSON(draft)));
}

// AutoBroll scripts/trim-silence.mjs, translated from its standalone CLI to
// an importable function using already-verified source-relative word timestamps.
export function speechRuns(words, durationSec) {
  requireThat(finite(durationSec, 0.5, 3600), 'Invalid source duration');
  if (!words.length) return [];
  const runs = [];
  let runStart = words[0].startMs;
  for (let k = 0; k < words.length; k++) {
    const gapNext = words[k + 1] ? words[k + 1].startMs - words[k].endMs : Infinity;
    if (gapNext > GAP_THRESH) {
      runs.push([runStart, words[k].endMs]);
      if (words[k + 1]) runStart = words[k + 1].startMs;
    }
  }
  return runs.map(([a,b],idx) => {
    const lead = idx === 0 ? LEAD_PAD : INNER_PAD;
    const trail = idx === runs.length - 1 ? TRAIL_PAD : INNER_PAD;
    return {inSec:Math.max(0,a/1000-lead),outSec:Math.min(durationSec,b/1000+trail)};
  }).filter(s => s.outSec-s.inSec >= MIN_LEN);
}

function validWords(words, durationSec) {
  requireThat(Array.isArray(words) && words.length <= 3000, 'Invalid word transcript');
  let previousStart = -1;
  return words.map(w => {
    requireThat(w && typeof w === 'object' && typeof w.word === 'string' &&
      w.word.length > 0 && w.word.length <= 80 &&
      Number.isInteger(w.startMs) && Number.isInteger(w.endMs) &&
      w.startMs >= previousStart && w.startMs >= 0 &&
      w.endMs > w.startMs && w.endMs <= durationSec*1000 + 1,
      'Invalid or unordered transcript timecodes');
    previousStart = w.startMs;
    return {word:w.word,startMs:w.startMs,endMs:w.endMs};
  });
}

function bestContiguousWindow(words, durationSec, neededSec, runs) {
  const maxStart = Math.max(0,durationSec-neededSec);
  // Scan source word boundaries and AutoBroll speech-run boundaries. Prefer
  // preserving more *complete* words; do not change Feature4 scene duration.
  const candidates = new Set([0,maxStart]);
  runs.forEach(r => candidates.add(Math.min(maxStart,Math.max(0,r.inSec))));
  words.forEach(w => candidates.add(Math.min(maxStart,Math.max(0,w.startMs/1000-0.08))));
  let best = {start:0,score:-1};
  for (const start of candidates) {
    const end = start+neededSec;
    const score = words.reduce((n,w) => n + (w.startMs >= start*1000 &&
      w.endMs <= end*1000 ? 1 : 0),0);
    if (score > best.score || (score === best.score && start < best.start)) best={start,score};
  }
  return +best.start.toFixed(3);
}

// Adapted from AutoBroll scripts/captions-multiclip.mjs buildCaptions.
// Captions stay relative to source asset, *not* timeline, until Feature4 places
// and trims the reviewed scenes. No "accent" is invented by this deterministic step.
export function buildCaptions(words, clipId) {
  const pages = [];
  let cur = [];
  let skipParen = false;
  const flush = () => {
    if (cur.length) {
      pages.push({clipId,words:cur,start:cur[0].startMs,end:cur[cur.length-1].endMs});
      cur=[];
    }
  };
  words.forEach((w,i)=>{
    if (w.word === '(') {skipParen=true;flush();return;}
    if (w.word === ')') {skipParen=false;return;}
    if (skipParen || PUNCT_ONLY.test(w.word)) return;
    const display=w.word.replace(/[.,;:]+$/g,'').replace(/^[.,;:]+/g,'');
    if (!display) return;
    cur.push({text:display,startMs:w.startMs,endMs:w.endMs,accent:false});
    const lastGlue=GLUE.has(display.toLowerCase());
    const next=words[i+1];
    const gapAfter=next && next.startMs-w.endMs>GAP_MS;
    if (SENT_END.test(w.word)) flush();
    else if (!lastGlue && (cur.length>=MAX_WORDS || gapAfter || CLAUSE_END.test(w.word))) flush();
    else if (cur.length>=MAX_WORDS+2) flush();
  });
  flush();
  for (let k=pages.length-1;k>0;k--) {
    const p=pages[k],prev=pages[k-1];
    if(p.words.length===1 && p.start-prev.end<350 && prev.words.length<=MAX_WORDS) {
      prev.words.push(...p.words);prev.end=p.end;pages.splice(k,1);
    }
  }
  return pages.map((p,i)=>({
    id:clipId+'_caption_'+i,clipId:p.clipId,words:p.words,
    startMs:p.start,endMs:p.end,topPct:DEFAULT_TOP
  }));
}

function authorizedGrant(grant, shopId, id, kind) {
  requireThat(grant && grant.asset_id===id && grant.shop_id===shopId &&
    grant.issued_by==='trusted_server' && grant.source==='retailer_upload' &&
    grant.rights_status==='APPROVED' && grant.active===true &&
    grant.media_type===kind, 'Missing authorized same-shop uploaded asset');
}
function assertProposalInput(input) {
  requireThat(input && typeof input==='object' && !Array.isArray(input),'Invalid request');
  const {shop_id, campaign_id, draft, footage, grants} = input;
  identity(shop_id,'shop_id');identity(campaign_id,'campaign_id');
  requireThat(draft && draft.shop_id===shop_id && draft.campaign_id===campaign_id &&
    [15,30,60].includes(draft.duration_seconds) && Array.isArray(draft.scenes) &&
    draft.scenes.length>=1 && draft.scenes.length<=MAX_SCENES,'Invalid Feature4 storyboard');
  requireThat(Array.isArray(footage) && footage.length===draft.scenes.length &&
    Array.isArray(grants) && grants.length<=40,'Invalid private footage manifest');
  return {shop_id,campaign_id,draft,footage,grants};
}

export function proposeUploadedFootageEdits(input) {
  const {shop_id,campaign_id,draft,footage,grants}=assertProposalInput(input);
  const grantMap=new Map();
  for(const g of grants) {
    identity(g?.asset_id,'grant asset_id');
    requireThat(!grantMap.has(g.asset_id),'Duplicate asset grant');
    grantMap.set(g.asset_id,g);
  }
  const byIndex=new Map();
  for(const item of footage) {
    requireThat(item && Number.isInteger(item.scene_index) &&
      item.scene_index>=0 && item.scene_index<draft.scenes.length &&
      !byIndex.has(item.scene_index),'Duplicate or invalid footage scene');
    byIndex.set(item.scene_index,item);
  }
  const proposedEdits=[];
  const captions=[];
  const brollSuggestions=[];
  const cutSuggestions=[];
  let sourceOffset=0;
  for(let i=0;i<draft.scenes.length;i++) {
    const scene=draft.scenes[i],item=byIndex.get(i);
    requireThat(item && scene && scene.asset_id===item.asset_id &&
      scene.asset_type==='video' && scene.source_feature==='retailer',
      'Feature7 accepts retailer-uploaded video scenes only');
    identity(item.asset_id,'footage asset_id');
    authorizedGrant(grantMap.get(item.asset_id),shop_id,item.asset_id,'video');
    requireThat(finite(scene.duration,0.5,60) && finite(item.source_duration_seconds,0.5,3600) &&
      item.source_duration_seconds>=scene.duration &&
      typeof item.has_audio==='boolean' && item.has_audio === grantMap.get(item.asset_id).has_audio,
      'Invalid media duration or audio metadata');
    const words=validWords(item.words,item.source_duration_seconds);
    // Reject transcript spoofing by requiring server-issued transcription evidence.
    requireThat(item.transcription_status==='verified_server' &&
      typeof item.transcript_sha256==='string' &&
      /^[a-f0-9]{64}$/.test(item.transcript_sha256),
      'Verified server transcript required');
    const runs=speechRuns(words,item.source_duration_seconds);
    const trimStart=bestContiguousWindow(words,item.source_duration_seconds,scene.duration,runs);
    // "mute_source" false preserves original input audio. Only the reviewer may
    // propose a future mute via Feature4's explicit approval; we never do it.
    proposedEdits.push({
      source_scene_index:i,duration:scene.duration,trim_start:trimStart,
      mute_source:false
    });
    cutSuggestions.push({
      source_scene_index:i,asset_id:item.asset_id,speech_runs:runs,
      long_pause_count:Math.max(0,runs.length-1),
      recommended_trim_start:trimStart,
      jump_cuts_executable_by_feature4:false
    });
    // Keep source-relative captions. Feature4's current edit_execution does not
    // accept caption overlays, so these are a separate *advisory* handoff.
    const sourceCaptions=buildCaptions(words,item.asset_id);
    captions.push(...sourceCaptions.filter(c=>c.endMs>trimStart*1000 &&
      c.startMs<(trimStart+scene.duration)*1000).map(c=>({
        ...c,source_scene_index:i,
        timeline_start_ms:Math.round(sourceOffset*1000+Math.max(0,c.startMs-trimStart*1000)),
        timeline_end_ms:Math.round(sourceOffset*1000+Math.min(scene.duration*1000,c.endMs-trimStart*1000))
      })));
    const candidates=item.broll_candidates??[];
    requireThat(Array.isArray(candidates) && candidates.length<=12,'Too many B-roll cues');
    for(const cue of candidates) {
      requireThat(cue && Number.isInteger(cue.startIdx) && Number.isInteger(cue.endIdx) &&
        cue.startIdx>=0 && cue.endIdx>=cue.startIdx && cue.endIdx<words.length &&
        ['inset','top','fullscreen'].includes(cue.mode) &&
        typeof cue.assetId==='string','Invalid B-roll anchor');
      identity(cue.assetId,'B-roll asset ID');
      const g=grantMap.get(cue.assetId);
      requireThat(g && ['video','image'].includes(g.media_type),'Unknown B-roll asset');
      authorizedGrant(g,shop_id,cue.assetId,g.media_type);
      // AutoBroll broll-multiclip.mjs source-anchored word-index mapping,
      // adapted to asset IDs and no Pexels URL downloading.
      const startMs=words[cue.startIdx].startMs,endMs=words[cue.endIdx].endMs;
      requireThat(startMs>=trimStart*1000 && endMs<=(trimStart+scene.duration)*1000 &&
        endMs>startMs,'B-roll cue outside selected speech');
      brollSuggestions.push({
        asset_id:cue.assetId,source_scene_index:i,source_start_ms:startMs,
        source_end_ms:endMs,mode:cue.mode,
        timeline_start_ms:Math.round(sourceOffset*1000+startMs-trimStart*1000),
        review_required:true,feature4_insertion_supported:false
      });
    }
    sourceOffset+=scene.duration;
  }
  requireThat(Math.abs(sourceOffset-draft.duration_seconds)<0.001,
    'Storyboard timeline must fill approved duration');
  // This is intentionally NOT a Feature4 approved edit: only the coordinator
  // can store approval, recompute draft_fingerprint and load same-tenant snapshot.
  return {
    version:'feature7_uploaded_footage_v1',source_feature:'feature7',
    shop_id,campaign_id,draft_sha256_hint:draftHashHint(draft),
    review_status:'NEEDS_REVIEW',renderable:false,approved:false,
    timeline_version:'creative_reel_v1',scenes:proposedEdits,
    captions_advisory:captions,broll_advisory:brollSuggestions,
    silence_advisory:cutSuggestions,
    audio_policy:'PRESERVE_SOURCE',network_calls:0,model_calls:0,
    warnings:['Verify visual cuts, caption words and speech intelligibility before approval.',
      'Feature4 edit_execution currently supports only one contiguous trim per original scene; captions, multi-jump-cuts and B-roll inserts require a separately approved Feature4 extension.']
  };
}

// CLI for isolated offline fixtures. No external media paths, credentials or renderer.
// stdin JSON -> stdout review-only JSON. Do not pass through an HTTP route.
// Browser import is allowed; CLI-only Node globals must not be dereferenced.
if (typeof process !== 'undefined' && process.argv?.[1] &&
    import.meta.url === new URL('file://' + process.argv[1]).href) {
  let body='';
  for await (const chunk of process.stdin) {
    body+=chunk;
    if(body.length>1024*1024) throw new EditValidationError('Input too large');
  }
  try {process.stdout.write(JSON.stringify(proposeUploadedFootageEdits(JSON.parse(body)))+'\n');}
  catch(e) {console.error(e.message);process.exitCode=1;}
}
