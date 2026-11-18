// Human QA aggregation only; never an AI judge or trusted backend proof.
import {QUALITY_RUBRICS,acceptedDimension} from './quality-rubrics.mjs'
import {isObservedCompletedOutput} from './trace-output-evidence.mjs'
const validScore = x => Number.isInteger(x) && x >= 1 && x <= 5

export function inspectHumanQuality(events) {
  const ordered=Array.isArray(events)?events.filter(e=>e&&typeof e==='object'&&
    Number.isInteger(e.event_seq)&&e.event_seq>0).sort((a,b)=>a.event_seq-b.event_seq):[]
  const scores={}
  const outputSeen=new Set()
  for(const event of ordered){
    if(!Object.prototype.hasOwnProperty.call(QUALITY_RUBRICS,event.feature))continue
    if(isObservedCompletedOutput(event)){outputSeen.add(event.feature);continue}
    if(event.status!=='QUALITY_REVIEW'||!outputSeen.has(event.feature)||!validScore(event.details?.score))continue
    const id=event.details?.dimension===undefined?'overall':event.details.dimension
    if(!acceptedDimension(event.feature,id))continue
    const key=event.feature+':'+id
    if(!scores[key])scores[key]={
      feature:event.feature,dimension:id,score_sum:0,
      latest_score:null,sample_count:0,
    }
    scores[key].score_sum+=event.details.score
    scores[key].sample_count++
    scores[key].latest_score=event.details.score
  }
  return Object.values(scores).map(s=>({
    feature:s.feature,dimension:s.dimension,
    latest_score:s.latest_score,sample_count:s.sample_count,
    mean_score:Math.round(s.score_sum*10/s.sample_count)/10,
    source:'human_reviewer_only',
  }))
}

export function compareHumanQualityAspects(current,baseline){
  const a=inspectHumanQuality(current),b=inspectHumanQuality(baseline)
  return a.map(item=>{
    const previous=b.find(x=>x.feature===item.feature&&x.dimension===item.dimension)
    return {
      ...item,baseline_latest_score:previous?.latest_score??null,
      change:previous===undefined?null:item.latest_score-previous.latest_score,
      comparable:previous!==undefined,
      comparison_basis:'same_feature_and_human_quality_aspect_only',
    }
  })
}
