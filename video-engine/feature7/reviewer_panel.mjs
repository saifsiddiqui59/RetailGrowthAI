/**
 * Feature #7 embeddable reviewer controls, not a second video editor.
 * Mount inside an authenticated Feature4 workspace after media rights checks.
 * Media blob URLs are provided ONLY by trusted host, separate from proposals.
 * The callback is NOT approval; the backend must persist verified human action.
 */
import {createReviewSession,adjustTrimStart,proposeReviewDecision}
  from './review_actions.mjs';

const isObjectURL=x=>typeof x==='string'&&x.startsWith('blob:')&&!/[\u0000-\u001f]/.test(x);

export function mountFeature7ReviewPanel({
  target,draft,proposal,media_evidence,reviewer_view,
  trusted_media_object_urls={},onReviewRequest
}={}){
  if(!target||typeof target.replaceChildren!=='function'||
    typeof onReviewRequest!=='function')
    throw new Error('Trusted review container and request callback required');
  let session=createReviewSession({draft,proposal,media_evidence,reviewer_view});
  const doc=target.ownerDocument;
  if(!doc||typeof doc.createElement!=='function')
    throw new Error('DOM document unavailable');
  const el=(tag,txt,cls)=>{
    const n=doc.createElement(tag);
    if(txt!==undefined&&txt!==null)n.textContent=String(txt);
    if(cls)n.className=cls;
    return n;
  };
  const root=el('section',null,'rgai-f7-review');
  root.setAttribute('aria-label','Feature 7 media editing review');
  const heading=el('h2','Review AI video edits');
  const info=el('p','Review only. This screen cannot publish or render a video.');
  const feedback=el('p','Original footage and speech audio are preserved.','rgai-f7-feedback');
  feedback.setAttribute('aria-live','polite');
  const select=el('select');
  select.setAttribute('aria-label','Choose uploaded source scene');
  session.scenes.forEach(edit=>{
    const original=session.source_scenes[edit.source_scene_index];
    const option=el('option','Scene '+(edit.source_scene_index+1)+' - '+original.asset_id);
    option.value=String(edit.source_scene_index);
    select.appendChild(option);
  });
  const video=el('video');
  video.controls=true;
  video.preload='metadata';
  video.setAttribute('playsinline','');
  video.setAttribute('referrerpolicy','no-referrer');
  video.setAttribute('aria-label','Approved private footage preview');
  const placeholder=el('p','Video preview requires an authorized private media blob from the workspace.');
  const trimLabel=el('label','Source trim start (seconds)');
  const trim=el('input');
  trim.type='range';
  trim.min='0';
  trim.step='0.001';
  trim.setAttribute('aria-label','Adjust video trim start');
  const trimReadout=el('output');
  const captions=el('div',null,'rgai-f7-caption-review');
  const qa=el('div',null,'rgai-f7-quality-review');
  const confirmLabel=el('label','I have reviewed the selected clip and original speech audio.');
  const confirm=el('input');
  confirm.type='checkbox';
  confirmLabel.prepend(confirm);
  const approve=el('button','Request human approval');
  approve.type='button';
  const reject=el('button','Reject AI suggestion');
  reject.type='button';
  const warning=el('p','Caption overlays, B-roll and multi-cut changes are suggestions only. Final renderer integration is pending.');
  const update=()=>{
    const index=Number(select.value);
    const selected=session.scenes.find(item=>item.source_scene_index===index);
    if(!selected)throw Error('Missing selected scene');
    const assetId=session.source_scenes[index].asset_id;
    const trusted=trusted_media_object_urls[assetId];
    video.removeAttribute('src');
    if(isObjectURL(trusted)){
      video.src=trusted;video.hidden=false;placeholder.hidden=true;
    }else{
      video.hidden=true;placeholder.hidden=false;
    }
    const max=session.media_evidence[index].source_duration_seconds-selected.duration;
    trim.max=String(Math.max(0,max));
    trim.value=String(selected.trim_start);
    trimReadout.textContent=selected.trim_start.toFixed(3)+' of '+max.toFixed(3)+' seconds';
    trim.disabled=!session.can_request_approval;
    confirm.disabled=!session.can_request_approval;
    approve.disabled=!session.can_request_approval;
    reject.disabled=!session.can_request_approval;
    const pages=session.captions_advisory
      .filter(c=>c.source_scene_index===index).slice(0,40)
      .map(c=>c.words?.map(w=>w.text).join(' ')??'').filter(Boolean);
    captions.replaceChildren(el('h3','Suggested captions'),
      el('p',pages.join(' | ')||'No captions supplied'));
    const visual=session.media_evidence[index].visual_activity;
    const black=visual?.black_intervals?.length??0;
    const freeze=visual?.freeze_intervals?.length??0;
    qa.replaceChildren(el('h3','Read-only footage quality'),
      el('p',black+' black intervals; '+freeze+' potentially still intervals. Check manually.'));
  };
  select.addEventListener('change',()=>{confirm.checked=false;update();});
  trim.addEventListener('input',()=>{
    try{
      session=adjustTrimStart(session,Number(select.value),Number(trim.value));
      confirm.checked=false;update();
      feedback.textContent='Trim updated locally, not yet saved or approved.';
    }catch(e){feedback.textContent='Trim denied: '+e.message;update();}
  });
  const dispatch=action=>{
    try{
      const packet=proposeReviewDecision(session,{
        action,confirmed:confirm.checked});
      const result=onReviewRequest(packet);
      feedback.textContent='Request forwarded to trusted host. Approval is not confirmed.';
      if(result&&typeof result.then==='function')
        result.catch(()=>{feedback.textContent='Request failed. No approval was recorded.';});
    }catch(e){feedback.textContent='Review action denied: '+e.message;}
  };
  approve.addEventListener('click',()=>dispatch('REQUEST_APPROVAL'));
  reject.addEventListener('click',()=>dispatch('REJECT_PROPOSAL'));
  root.append(heading,info,select,video,placeholder,trimLabel,trim,
    trimReadout,captions,qa,confirmLabel,approve,reject,warning,feedback);
  target.replaceChildren(root);
  select.value=String(session.scenes[0].source_scene_index);
  update();
  return Object.freeze({
    destroy(){video.removeAttribute('src');target.replaceChildren();},
    getReviewSnapshot(){return {
      shop_id:session.shop_id,campaign_id:session.campaign_id,
      scenes:session.scenes.map(s=>({...s})),approved:false,renderable:false
    };}
  });
}
