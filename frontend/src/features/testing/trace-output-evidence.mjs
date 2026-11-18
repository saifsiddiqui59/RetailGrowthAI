// Browser-observed completion contracts for human review eligibility.
// A job acknowledgement is NOT a finished media/copy output. These checks
// deliberately support only existing real F2 planner and Part1 F4 FFmpeg
// paths; unintegrated poster/motion/editor runtime stays unrated/NOT_RUN.
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const uuid=value=>typeof value==='string'&&UUID.test(value)
export function isObservedCompletedOutput(event){
 if(!event||event.status!=='PASS'||!event.details||typeof event.details!=='object')return false
 const d=event.details
 if(event.feature==='F2'){
   if(event.action==='prompt-improvement')return typeof d.improved_prompt==='string'&&
     d.improved_prompt.trim().length>=10&&d.provider_mode==='deterministic'
   if(event.action==='campaign-planning')return d.generated_days===7&&
     uuid(d.campaign_id)&&uuid(d.first_day_id)
 }
 if(event.feature==='F4'&&event.action==='ffmpeg-result'){
   return d.status==='SUCCEEDED'&&uuid(d.render_job_id)&&uuid(d.output_asset_id)
 }
 return false
}
export function hasObservedCompletedOutput(events,feature,beforeSeq=Infinity){
 return Array.isArray(events)&&events.some(e=>
   e?.feature===feature&&Number.isInteger(e.event_seq)&&e.event_seq>0&&
   e.event_seq<beforeSeq&&isObservedCompletedOutput(e))
}
