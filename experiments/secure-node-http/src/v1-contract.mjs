/**
 * Dependency-free validator aligned to Python ai_agents.schemas.v1.
 * Strict canonical UUID, valid ISO date, IANA zone, continuous 30s storyboard.
 * Validation never establishes media rights or authorization.
 */
import { canonicalUuid } from "./security.mjs";
export class ContractDenied extends TypeError {
  constructor() {super("INVALID_REQUEST");}
}
const obj=x=>x!==null && typeof x==="object" && !Array.isArray(x) &&
  Object.getPrototypeOf(x)===Object.prototype;
const exact=(o,keys)=>obj(o)&&Object.keys(o).length===keys.length &&
  keys.every(k=>Object.prototype.hasOwnProperty.call(o,k));
const text=(v,max)=>typeof v==="string" && v.trim().length>0 && v.length<=max;
const iso=v=>{
  if(typeof v!=="string" || !/^\d{4}-\d\d-\d\d$/.test(v))return false;
  const d=new Date(v+"T00:00:00Z");
  return !Number.isNaN(d.getTime()) && d.toISOString().slice(0,10)===v;
};
const uuid=v=>{ try { return canonicalUuid(v); } catch {throw new ContractDenied();} };
const bad=()=>{throw new ContractDenied();};
const dateMS=s=>Date.parse(s+"T00:00:00Z");
export function validateCampaignBrief(v) {
  if(!obj(v) || !Object.keys(v).every(k=>[
    "shop_id","brief","duration_days","start_date","timezone",
    "language","platforms","media_asset_ids","offer",
  ].includes(k)))bad();
  const shop_id=uuid(v.shop_id);
  if(!text(v.brief,1500) || !Number.isInteger(v.duration_days) ||
      v.duration_days<1 || v.duration_days>7 || !iso(v.start_date) ||
      !text(v.timezone,80) || !text(v.language,20) || v.language!=="en-IN" ||
      !Array.isArray(v.platforms) || v.platforms.length!==2 ||
      new Set(v.platforms).size!==2 ||
      !v.platforms.includes("linkedin") || !v.platforms.includes("instagram") ||
      !Array.isArray(v.media_asset_ids) || v.media_asset_ids.length<1 ||
      v.media_asset_ids.length>21)bad();
  try {new Intl.DateTimeFormat("en-US",{timeZone:v.timezone});}
  catch {bad();}
  const ids=v.media_asset_ids.map(uuid);
  if(new Set(ids).size!==ids.length)bad();
  let offer=null;
  if(v.offer!==undefined && v.offer!==null) {
    if(!exact(v.offer,["description","valid_until"]) ||
        !text(v.offer.description,180) || !iso(v.offer.valid_until) ||
        v.offer.valid_until<v.start_date)bad();
    offer={description:v.offer.description.trim(),valid_until:v.offer.valid_until};
  }
  return {
    shop_id,brief:v.brief.trim(),duration_days:v.duration_days,
    start_date:v.start_date,timezone:v.timezone,language:"en-IN",
    platforms:[...v.platforms],media_asset_ids:ids,offer,
  };
}

export function validateCampaign(c) {
  if(!exact(c,["id","shop_id","status","days"]))bad();
  const cid=uuid(c.id),shop=uuid(c.shop_id);
  if(!["DRAFT","PLANNING","FAILED"].includes(c.status)||
      !Array.isArray(c.days)||c.days.length<1||c.days.length>7)bad();
  const seen=new Set(),topics=new Set();
  let first=null;
  for(let n=0;n<c.days.length;n++){
    const d=c.days[n];
    if(!exact(d,["id","campaign_id","shop_id","day_index","scheduled_date",
      "topic","linkedin","instagram","review_status"]))bad();
    const did=uuid(d.id);
    if(seen.has(did) || uuid(d.campaign_id)!==cid || uuid(d.shop_id)!==shop ||
        !Number.isInteger(d.day_index)||d.day_index!==n+1 ||
        !iso(d.scheduled_date)||d.review_status!=="DRAFT"||
        !text(d.topic,140))bad();
    seen.add(did);
    if(first===null)first=dateMS(d.scheduled_date);
    if(dateMS(d.scheduled_date)!==first+n*86400000)bad();
    const folded=d.topic.trim().toLowerCase();
    if(topics.has(folded))bad();
    topics.add(folded);
    const linkedin=d.linkedin,instagram=d.instagram;
    if(!exact(linkedin,["post_text","hashtags"]) ||
        !text(linkedin.post_text,3000)||
        !Array.isArray(linkedin.hashtags)||linkedin.hashtags.length<1||
        linkedin.hashtags.some(h=>typeof h!=="string" || !h.startsWith("#")||h.length>60))bad();
    if(!exact(instagram,["caption","banner_asset_id","reel"])||
       !text(instagram.caption,2200))bad();
    if(instagram.banner_asset_id!==null)uuid(instagram.banner_asset_id);
    const reel=instagram.reel;
    if(!exact(reel,["duration_seconds","aspect_ratio","storyboard","music_asset_id","cta"]) ||
        reel.duration_seconds!==30 || reel.aspect_ratio!=="9:16" ||
        !text(reel.cta,100)||!Array.isArray(reel.storyboard)||!reel.storyboard.length)bad();
    if(reel.music_asset_id!==null)uuid(reel.music_asset_id);
    let offset=0;
    for(const shot of reel.storyboard){
      if(!exact(shot,["start_seconds","duration_seconds","asset_id","overlay_text"])||
          !Number.isInteger(shot.start_seconds)||shot.start_seconds!==offset||
          !Number.isInteger(shot.duration_seconds)||shot.duration_seconds<1||
          !text(shot.overlay_text,100))bad();
      uuid(shot.asset_id);
      offset+=shot.duration_seconds;
    }
    if(offset!==30)bad();
  }
  return c;
}
