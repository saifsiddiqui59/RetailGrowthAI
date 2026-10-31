/**
 * Low-cost semantic *suggestions* for existing uploaded speech and approved
 * uploaded cutaways. Adapts AutoBroll's arrange-clips / broll-multiclip
 * intention without importing Gemini, Pexels, a renderer or ad scriptwriting.
 *
 * These are review-only and never remove a take or publish an asset.
 */
import {EditValidationError} from './autobroll_semantics.mjs';
const ensure=(condition,message)=>{if(!condition) throw new EditValidationError(message);};
const TOKEN=/[\p{L}\p{N}]+/gu;
function normalizeWords(words) {
  ensure(Array.isArray(words) && words.length<=3000,'Invalid transcript');
  return words.flatMap(w=>{
    ensure(w && typeof w.word==='string' && w.word.length<=80,'Invalid word');
    return w.word.toLocaleLowerCase('en').match(TOKEN)??[];
  });
}
const jaccard=(a,b)=> {
  const sa=new Set(a),sb=new Set(b);
  const intersection=[...sa].filter(w=>sb.has(w)).length;
  const union=new Set([...sa,...sb]).size;
  return union===0?0:intersection/union;
};
function takeScore(t) {
  const words=t.words;
  const speech=words.length;
  const finalPunctuation=words.some(w=>/[.!?]$/.test(w.word)) ? 1:0;
  let gaps=0;
  for(let k=1;k<words.length;k++) {
    if(words[k].startMs-words[k-1].endMs>600)gaps++;
  }
  return +(speech*1.5+finalPunctuation-gaps*.3).toFixed(3);
}

export function suggestRetakeSelections({shop_id,footage}={}) {
  ensure(typeof shop_id==='string' && shop_id.length>0 &&
    Array.isArray(footage) && footage.length<=12,
    'Invalid retake scope');
  const items=footage.map((f,i)=>{
    ensure(f && f.shop_id===shop_id && Number.isInteger(f.scene_index) &&
      Array.isArray(f.words) && typeof f.asset_id==='string' &&
      f.words.length<=3000,'Invalid retake tenant/source');
    return {...f,original_index:i,tokens:normalizeWords(f.words)};
  });
  const used=new Set();
  const recommendations=[];
  for(let i=0;i<items.length;i++){
    if(used.has(i) || items[i].tokens.length<2)continue;
    const group=[items[i]];used.add(i);
    for(let j=i+1;j<items.length;j++){
      if(used.has(j) || items[j].tokens.length<2)continue;
      const overlap=jaccard(items[i].tokens,items[j].tokens);
      if(overlap>=0.72){group.push(items[j]);used.add(j);}
    }
    if(group.length<2)continue;
    const ranked=group.map(g=>({
      source_scene_index:g.scene_index,asset_id:g.asset_id,
      score:takeScore(g)
    })).sort((a,b)=>b.score-a.score ||
      a.source_scene_index-b.source_scene_index);
    recommendations.push({
      source_scene_indices:group.map(g=>g.scene_index),
      recommended_source_scene_index:ranked[0].source_scene_index,
      ranking:ranked,reason:'similar_existing_spoken_take',
      human_review_required:true,discarded_scene_ids:[],
      output_executable_by_feature4:false
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
