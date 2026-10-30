/**
 * Feature #7 embeddable reviewer controls, not a second video editor.
 * Mount inside an authenticated Feature4 workspace after media rights checks.
 * Media blob URLs are provided ONLY by trusted host, separate from proposals.
 * The callback is NOT approval; the backend must persist verified human action.
 */
import {createReviewSession,adjustTrimStart,proposeReviewDecision}
  from './review_actions.mjs';
import {createCaptionCorrectionSession,editCaptionCorrection,
  requestCaptionCorrectionReview} from './caption_corrections.mjs';

const isObjectURL=x=>typeof x==='string'&&x.startsWith('blob:')&&!/[\u0000-\u001f]/.test(x);

export function mountFeature7ReviewPanel({
  target,draft,proposal,media_evidence,reviewer_view,
  trusted_media_object_urls={},onReviewRequest,
  caption_correction_input=null,onCaptionReviewRequest
}={}){
  if(!target||typeof target.replaceChildren!=='function'||
    typeof onReviewRequest!=='function')
    throw new Error('Trusted review container and request callback required');
  let session=createReviewSession({draft,proposal,media_evidence,reviewer_view});
  let reviewSubmissionPending=false;
  let reviewRequestEpoch=0;
  let captionRequestEpoch=0;
  let disposed=false;
  if(caption_correction_input!==null&&
    typeof onCaptionReviewRequest!=='function')
    throw new Error('Trusted caption correction callback required');
  let captionSession=caption_correction_input===null?null:
    createCaptionCorrectionSession({
      ...caption_correction_input,reviewer_view
    });
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
    if(isObjectURL(trusted)){
      if(video.src!==trusted)video.src=trusted;
      video.currentTime=selected.trim_start;
      video.hidden=false;placeholder.hidden=true;
    }else{
      video.removeAttribute('src');
      video.hidden=true;placeholder.hidden=false;
    }
    const max=session.media_evidence[index].source_duration_seconds-selected.duration;
    trim.max=String(Math.max(0,max));
    trim.value=String(selected.trim_start);
    trimReadout.textContent=selected.trim_start.toFixed(3)+' of '+max.toFixed(3)+' seconds';
    trim.disabled=!session.can_request_approval;
    confirm.disabled=!session.can_request_approval;
    approve.disabled=!session.can_request_approval||reviewSubmissionPending;
    reject.disabled=!session.can_request_approval||reviewSubmissionPending;
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
  select.addEventListener('change',()=>{
    // Changing the visible scene does not change a pending review packet.
    confirm.checked=false;update();
  });
  trim.addEventListener('input',()=>{
    try{
      const index=Number(select.value);
      const previous=session.scenes.find(s=>s.source_scene_index===index)?.trim_start;
      const next=adjustTrimStart(session,index,Number(trim.value));
      const current=next.scenes.find(s=>s.source_scene_index===index)?.trim_start;
      session=next;
      if(previous!==current){reviewRequestEpoch++;reviewSubmissionPending=false;}
      confirm.checked=false;update();
      feedback.textContent='Trim updated locally, not yet saved or approved.';
    }catch(e){feedback.textContent='Trim denied: '+e.message;update();}
  });
  const dispatch=action=>{
    if(reviewSubmissionPending){
      feedback.textContent='This review request was already forwarded. Edit the clip before requesting again.';
      return;
    }
    try{
      const packet=proposeReviewDecision(session,{
        action,confirmed:confirm.checked});
      const epoch=++reviewRequestEpoch;
      reviewSubmissionPending=true;
      update();
      const result=onReviewRequest(packet);
      if(result===false)throw Error('Trusted host rejected review request');
      feedback.textContent='Request forwarded to trusted host. Approval is not confirmed.';
      if(result&&typeof result.then==='function')
        Promise.resolve(result).then(accepted=>{
          if(accepted===false)throw Error('Trusted host rejected review request');
        }).catch(()=>{
          if(disposed||epoch!==reviewRequestEpoch)return;
          reviewSubmissionPending=false;update();
          feedback.textContent='Request failed. No approval was recorded.';
        });
    }catch(e){
      reviewSubmissionPending=false;update();
      feedback.textContent='Review action denied: '+e.message;
    }
  };
  approve.addEventListener('click',()=>dispatch('REQUEST_APPROVAL'));
  reject.addEventListener('click',()=>dispatch('REJECT_PROPOSAL'));
  // Optional review-only, word-time-preserving human captions. This extends
  // the existing F7 reviewer; it is NOT a separate timeline editor.
  let captionUI=null;
  let captionSubmissionPending=false;
  if(captionSession){
    const field=el('fieldset',null,'rgai-f7-caption-correction');
    const legend=el('legend','Correct recognized caption text');
    const help=el('p','Text only. Cue timing and original spoken audio cannot be changed here.');
    const cueSelect=el('select');
    cueSelect.setAttribute('aria-label','Caption to correct');
    for(const c of captionSession.cues){
      const option=el('option',
        'Cue '+(c.index+1)+' — '+(c.start_ms/1000).toFixed(2)+' seconds');
      option.value=String(c.index);
      cueSelect.appendChild(option);
    }
    const editor=el('textarea');
    editor.setAttribute('aria-label','Corrected caption text');
    editor.maxLength=90;
    editor.rows=2;
    const save=el('button','Save caption suggestion');
    save.type='button';
    const verified=el('input');
    verified.type='checkbox';
    const verifiedLabel=el('label','I checked the corrected words against the actual speaker.');
    verifiedLabel.prepend(verified);
    const send=el('button','Request caption correction review');
    send.type='button';
    const feedbackCaptions=el('p',
      'Caption corrections are unsaved, unapproved suggestions.');
    feedbackCaptions.setAttribute('aria-live','polite');
    const updateCaptionEditor=()=>{
      const i=Number(cueSelect.value);
      const original=captionSession.cues[i];
      const change=captionSession.corrections.find(c=>c.cue_index===i);
      editor.value=change?.corrected_text??original.text;
      editor.disabled=!captionSession.can_propose;
      save.disabled=!captionSession.can_propose;
      verified.disabled=!captionSession.can_propose;
      send.disabled=!captionSession.can_propose||
        !captionSession.corrections.length||captionSubmissionPending;
    };
    cueSelect.addEventListener('change',()=>{
      // A cue switch is not a new correction; retain its one-shot lock.
      verified.checked=false;updateCaptionEditor();
    });
    save.addEventListener('click',()=>{
      try{
        const next=editCaptionCorrection(
          captionSession,Number(cueSelect.value),editor.value);
        if(JSON.stringify(next.corrections)!==JSON.stringify(captionSession.corrections)){
          captionRequestEpoch++;captionSubmissionPending=false;
        }
        captionSession=next;
        verified.checked=false;updateCaptionEditor();
        feedbackCaptions.textContent='Caption change proposed locally. Still unapproved.';
      }catch(e){feedbackCaptions.textContent='Correction denied: '+e.message;}
    });
    send.addEventListener('click',()=>{
      if(captionSubmissionPending){
        feedbackCaptions.textContent='Correction was already forwarded. Modify it before resubmitting.';
        return;
      }
      try{
        const request=requestCaptionCorrectionReview(captionSession,{
          confirmed:verified.checked
        });
        const epoch=++captionRequestEpoch;
        captionSubmissionPending=true;
        updateCaptionEditor();
        const result=onCaptionReviewRequest(request);
        if(result===false)throw Error('Trusted host rejected caption review');
        feedbackCaptions.textContent=
          'Correction request forwarded to trusted host. Approval not confirmed.';
        if(result&&typeof result.then==='function')
          Promise.resolve(result).then(accepted=>{
            if(accepted===false)throw Error('Trusted host rejected caption review');
          }).catch(()=>{
            if(disposed||epoch!==captionRequestEpoch)return;
            captionSubmissionPending=false;updateCaptionEditor();
            feedbackCaptions.textContent='Caption request failed. No approval was recorded.';
          });
      }catch(e){
        captionSubmissionPending=false;updateCaptionEditor();
        feedbackCaptions.textContent='Caption request denied: '+e.message;
      }
    });
    field.append(legend,help,cueSelect,editor,save,verifiedLabel,send,
      feedbackCaptions);
    captionUI={field,updateCaptionEditor,cueSelect};
    cueSelect.value='0';updateCaptionEditor();
  }
  root.append(heading,info,select,video,placeholder,trimLabel,trim,
    trimReadout,captions,qa,confirmLabel,approve,reject,warning,feedback);
  if(captionUI)root.appendChild(captionUI.field);
  target.replaceChildren(root);
  select.value=String(session.scenes[0].source_scene_index);
  update();
  return Object.freeze({
    destroy(){
      disposed=true;reviewRequestEpoch++;captionRequestEpoch++;
      video.removeAttribute('src');target.replaceChildren();
    },
    getReviewSnapshot(){return {
      shop_id:session.shop_id,campaign_id:session.campaign_id,
      scenes:session.scenes.map(s=>({...s})),
      caption_correction_count:captionSession?.corrections.length??0,
      approved:false,renderable:false
    };}
  });
}
