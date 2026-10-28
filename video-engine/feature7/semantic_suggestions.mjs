/**
 * CPU-only AutoBroll retake grouping and verified-owned B-roll guidance.
 *
 * Directly adapts the one-best-per-beat / original-permutation intention of
 * upstream andriidrok1/autobroll scripts/arrange-clips.mjs (MIT), without
 * Gemini, a second editor, or unreviewed deletions. Ranks text FLUENCY
 * PROXIES only; a transcript cannot measure acting, image, or audio quality.
 */
import {EditValidationError} from './autobroll_semantics.mjs';
const ensure=(condition,message)=>{if(!condition) throw new EditValidationError(message);};
const TOKEN=/[\p{L}\p{N}]+/gu;
function normalizeWords(words) {
  ensure(Array.isArray(words) && words.length<=3000,'Invalid transcript');
  let previousEnd=-1;
  return words.flatMap(w=>{
    ensure(w && typeof w.word==='string' && w.word.length<=80 &&
      Number.isInteger(w.startMs) && Number.isInteger(w.endMs) &&
      w.startMs>=0 && w.startMs>=previousEnd-50 &&
      w.endMs>w.startMs && w.endMs<=600000,
      'Invalid source-relative transcript/word alignment');
    previousEnd=w.endMs;
    return w.word.toLocaleLowerCase('en').match(TOKEN)??[];
  });
}
const jaccard=(a,b)=> {
  const sa=new Set(a),sb=new Set(b);
  const intersection=[...sa].filter(w=>sb.has(w)).length;
  const union=new Set([...sa,...sb]).size;
  return union===0?0:intersection/union;
};
const overlapCount=(a,b)=>{
  const aSet=new Set(a),bSet=new Set(b);
  return [...aSet].filter(x=>bSet.has(x)).length;
};
function nearSameSpokenBeat(a,b){
  // Partial retakes may stop halfway through the same line. Never group on
  // generic two-word phrases or one shared product term alone.
  if(a.length<3 || b.length<3)return false;
  const common=overlapCount(a,b);
  const containment=common/Math.min(new Set(a).size,new Set(b).size);
  return (common>=3 && (jaccard(a,b)>=.72 || containment>=.8));
}
function takeQualityProxy(t) {
  const words=t.words;
  const tokens=t.tokens;
  const unique=new Set(tokens).size;
  const repeatedPairs=new Map();
  let repeatedPhraseCount=0;
  for(let i=0;i<tokens.length-1;i++){
    const pair=tokens[i]+' '+tokens[i+1];
    const found=repeatedPairs.get(pair)??0;
    if(found>0)repeatedPhraseCount++;
    repeatedPairs.set(pair,found+1);
  }
  let longGaps=0;
  for(let i=1;i<words.length;i++)if(words[i].startMs-words[i-1].endMs>600)longGaps++;
  const fillerCount=tokens.filter(x=>['um','uh','erm','ah'].includes(x)).length;
  const completeSentence=words.length>0 && /[.!?]["']?$/.test(words.at(-1).word);
  // Coverage of distinct words rewards completed delivery without rewarding
  // false starts/repeating phrases. Heuristic score != real ASR confidence.
  const score=+(unique*2 + Math.min(tokens.length,30)*.2 +
    (completeSentence?2:0) - repeatedPhraseCount*4 -
    longGaps*1.5 - fillerCount*2).toFixed(3);
  return {score,distinct_word_count:unique,long_pause_count:longGaps,
    repeated_phrase_count:repeatedPhraseCount,filler_count:fillerCount,
    ends_in_sentence_punctuation:completeSentence,
    score_basis:'TRANSCRIPT_HEURISTIC_NOT_VISUAL_OR_AUDIO_QUALITY'};
}

export function suggestRetakeSelections({shop_id,footage}={}) {
  ensure(typeof shop_id==='string' && /^[\w-]{1,120}$/.test(shop_id) &&
    Array.isArray(footage) && footage.length<=12,
    'Invalid retake scope');
  const scenes=new Set(),assets=new Set();
  const items=footage.map((f,i)=>{
    ensure(f && f.shop_id===shop_id && Number.isInteger(f.scene_index) &&
      f.scene_index>=0 && f.scene_index<12 &&
      !scenes.has(f.scene_index) &&
      typeof f.asset_id==='string' && /^[\w-]{1,120}$/.test(f.asset_id) &&
      !assets.has(f.asset_id),
      'Invalid, duplicated or foreign retake source');
    scenes.add(f.scene_index);assets.add(f.asset_id);
    const tokens=normalizeWords(f.words);
    return {...f,original_index:i,tokens};
  });
  const used=new Set();
  const recommendations=[];
  for(let i=0;i<items.length;i++){
    if(used.has(i) || items[i].tokens.length<3)continue;
    const group=[items[i]];used.add(i);
    for(let j=i+1;j<items.length;j++){
      if(used.has(j) || !nearSameSpokenBeat(items[i].tokens,items[j].tokens))continue;
      group.push(items[j]);used.add(j);
    }
    if(group.length<2)continue;
    const ranking=group.map(g=>({
      source_scene_index:g.scene_index,asset_id:g.asset_id,
      ...takeQualityProxy(g)
    })).sort((a,b)=>b.score-a.score ||
      a.source_scene_index-b.source_scene_index);
    recommendations.push({
      source_scene_indices:group.map(g=>g.scene_index),
      recommended_source_scene_index:ranking[0].source_scene_index,
      ranking,reason:'similar_verified_transcript_possible_retake',
      human_review_required:true,discarded_scene_ids:[],
      output_executable_by_feature4:false,
      original_order_preserved:true,
      selection_not_based_on_visual_quality:true,
      actual_cpu_asr_model_inference_proven:false
    });
  }
  return recommendations;
}

export function suggestOwnedCutaways({shop_id,words,approved_assets,max_cues=3}={}) {
  ensure(typeof shop_id==='string' && shop_id.length>0 &&
    Array.isArray(words) && words.length<=3000 &&
    Array.isArray(approved_assets) && approved_assets.length<=30 &&
    Number.isInteger(max_cues) && max_cues>=0 && max_cues<=12,
    'Invalid cutaway suggestion request');
  const used=new Set();
  const cues=[];
  for(const asset of approved_assets){
    ensure(asset && asset.shop_id===shop_id &&
      asset.source==='retailer_upload' && asset.issued_by==='trusted_server' &&
      asset.rights_status==='APPROVED' && asset.active===true &&
      ['image','video'].includes(asset.media_type) &&
      typeof asset.asset_id==='string' && /^[\w-]{1,100}$/.test(asset.asset_id) &&
      Array.isArray(asset.keywords) && asset.keywords.length<=12 &&
      asset.keywords.every(x=>typeof x==='string' && x.length<=50),
      'Unapproved or foreign suggested cutaway');
  }
  for(let i=0;i<words.length && cues.length<max_cues;i++){
    const w=words[i];
    ensure(w && typeof w.word==='string' &&
      Number.isInteger(w.startMs) && Number.isInteger(w.endMs) &&
      w.endMs>w.startMs,'Invalid word anchor');
    const token=normalizeWords([w])[0];
    if(!token || used.has(token))continue;
    const asset=approved_assets.find(a=>a.keywords.some(k=>
      k.toLocaleLowerCase('en')===token));
    if(!asset)continue;
    // Strictly within the current spoken-word span, so Feature4 can later
    // anchor to the user's clip. Time is proposed, not an inserted overlay.
    const end=Math.min(words.length-1,i+3);
    cues.push({
      asset_id:asset.asset_id,startIdx:i,endIdx:end,
      source_start_ms:w.startMs,source_end_ms:words[end].endMs,
      mode:'inset',reason:'approved_asset_keyword_match',
      human_review_required:true,output_executable_by_feature4:false
    });
    used.add(token);
    // Sparse cues: do not overwhelm actual human speech with stock.
    i+=3;
  }
  return cues;
}
