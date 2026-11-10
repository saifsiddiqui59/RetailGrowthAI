/**
 * SOURCE ONLY: unregistered, un-deployed Part 1 Reel render-intent adapter.
 *
 * A new caller-authorized Postgres RPC must be created/reviewed before this can
 * work. Existing RetailGrowthAI DEV render_jobs rejects authenticated INSERT,
 * and the Python AdminStore's service key MUST NOT move into Free SWA.
 *
 * The future RPC is the sole authority for complete media licensing, billing,
 * Python-hash-compatible idempotency, concurrency and atomic job/outbox writes.
 * No HTTP action can call worker endpoints or perform a direct render_jobs INSERT.
 */
import { AuthDenied, UpstreamUnavailable, canonicalUuid } from "./security.mjs";
import { CampaignDayWriter } from "./campaign-day-writes.mjs";
import { validateCampaign } from "./v1-contract.mjs";
import { RpcSubscriptionError } from "./poster-writes.mjs";

const PRESET = "instagram_reel_30s";
const LICENSES = new Set(["owned","cc0","royalty_free","commercial"]);
const IMAGE_MIME = new Set(["image/png","image/jpeg","image/webp"]);
const AUDIO_MIME = new Set(["audio/mpeg","audio/mp3","audio/wav","audio/x-wav","audio/aac","audio/mp4"]);
const isPlain = value => value !== null && typeof value === "object" &&
  !Array.isArray(value) && Object.getPrototypeOf(value) === Object.prototype;
const out = (status,error) => ({
  status,jsonBody:{error},
  headers:{"Cache-Control":"no-store","X-Content-Type-Options":"nosniff"},
});
const ok = (status,jsonBody) => ({
  status,jsonBody,
  headers:{"Cache-Control":"no-store","X-Content-Type-Options":"nosniff"},
});

export class ReelIntentWriter extends CampaignDayWriter {
  async licensedMedia(token, shopId, ids, musicId) {
    const sid=canonicalUuid(shopId);
    if (!Array.isArray(ids) || ids.length < 1 || ids.length > 21) return false;
    const unique=[...new Set(ids.map(canonicalUuid))];
    if (unique.length > 21) return false;
    const rows=await this.read("media_assets", token, {
      select:"id,shop_id,storage_bucket,object_path,mime_type,license_name,license_url,attribution",
      shop_id:"eq."+sid, id:"in.("+unique.join(",")+")", limit:"21",
    });
    if(rows.length!==unique.length || new Set(rows.map(row=>row.id)).size!==unique.length) return false;
    return rows.every(a =>
      unique.includes(a.id) && a.shop_id===sid &&
      a.storage_bucket==="retailgrowth-media" &&
      typeof a.object_path==="string" && a.object_path.startsWith(sid+"/") &&
      !a.object_path.includes("..") && !a.object_path.includes("\\") &&
      LICENSES.has(a.license_name) &&
      typeof a.attribution==="string" && a.attribution.trim().length>=10 &&
      (a.license_name==="owned" ||
        (typeof a.license_url==="string" && /^https:\/\/[^\s]{4,}$/.test(a.license_url))) &&
      (a.id===musicId ? AUDIO_MIME.has(a.mime_type) : IMAGE_MIME.has(a.mime_type))
    );
  }

  async requestRender(token, userId, campaignId, body) {
    const cid=canonicalUuid(campaignId);
    if(!isPlain(body)||Object.keys(body).length!==2 ||
       !Object.prototype.hasOwnProperty.call(body,"day_id") ||
       !Object.prototype.hasOwnProperty.call(body,"preset") ||
       body.preset!==PRESET){
      return out(400,"INVALID_REQUEST");
    }
    const did=canonicalUuid(body.day_id);
    const campaign=await this.campaign(token,userId,cid);
    if(!campaign)return out(404,"NOT_FOUND");
    if(campaign.status!=="DRAFT")return out(409,"CAMPAIGN_NOT_DRAFT");
    validateCampaign(campaign);
    const sid=canonicalUuid(campaign.shop_id);
    if(!await this.memberWrite(token,userId,sid))return out(403,"FORBIDDEN");
    const matching=campaign.days.filter(d=>d.id===did && d.shop_id===sid && d.campaign_id===cid);
    if(matching.length!==1)return out(404,"NOT_FOUND");
    if(matching[0].review_status==="REJECTED")return out(409,"DAY_REJECTED");
    const reel=matching[0].instagram.reel;
    const ids=reel.storyboard.map(s=>canonicalUuid(s.asset_id));
    const music=reel.music_asset_id===null?null:canonicalUuid(reel.music_asset_id);
    // Distinct licensed MIME roles are authoritative in SQL as well. Deny
    // an audio track reused in a storyboard image slot before a quota RPC.
    if(music && ids.includes(music))return out(403,"ASSET_RIGHTS_UNVERIFIED");
    if(music)ids.push(music);
    if(!await this.licensedMedia(token,sid,ids,music))return out(403,"ASSET_RIGHTS_UNVERIFIED");

    // The RPC is NOT installed yet; until reviewed migration exists, missing RPC
    // returns SERVICE_UNAVAILABLE and no jobs are accepted or replayed.
    // No shop/user/asset paths, license assertions or client idempotency hash are
    // accepted by the SQL function: it rereads signed-in actor and saved Reel.
    let response;
    try{
      response=await this.fetchImpl(this.origin+"/rest/v1/rpc/request_reel_render_job",{
        method:"POST",redirect:"error",cache:"no-store",
        headers:{
          apikey:this.key,Authorization:"Bearer "+token,
          Accept:"application/json","Content-Type":"application/json",
        },
        body:JSON.stringify({p_campaign_id:cid,p_day_id:did}),
        signal:AbortSignal.timeout(8000),
      });
    }catch{throw new UpstreamUnavailable();}
    if(response.status===401||response.status===403)throw new AuthDenied();
    if(!response.ok){
      if([400,402,409,429,500].includes(response.status)){
        let code;
        try{code=(await response.json())?.code;}catch{ /* fail closed */ }
        if(code==="RG001"||code==="RG002")throw new RpcSubscriptionError(code);
      }
      throw new UpstreamUnavailable();
    }
    let result;
    try{result=await response.json();}catch{throw new UpstreamUnavailable();}
    if(!isPlain(result) ||
       Object.keys(result).sort().join(",")!=="job_id,status" ||
       typeof result.job_id!=="string" ||
       !["QUEUED","RUNNING","SUCCEEDED","FAILED"].includes(result.status)){
      throw new UpstreamUnavailable();
    }
    let jid;
    try{jid=canonicalUuid(result.job_id);}catch{throw new UpstreamUnavailable();}
    return ok(["QUEUED","RUNNING"].includes(result.status)?202:200,
      {job_id:jid,status:result.status});
  }
}
export function createReelIntentGateway({verifyJwt,writer}){
  if(typeof verifyJwt!=="function" || !writer)throw new TypeError("MISSING_DEPENDENCIES");
  return async function handle(method,path,authorization,body){
    if(method!=="POST")return out(405,"METHOD_NOT_ALLOWED");
    const target=typeof path==="string"
      ? /^\/api\/campaigns\/([^/]+)\/renders$/.exec(path) : null;
    if(!target)return out(404,"NOT_FOUND");
    try{
      if(typeof authorization!=="string" || !authorization.startsWith("Bearer "))throw new AuthDenied();
      const token=authorization.slice(7);
      const actor=await verifyJwt(token);
      return await writer.requestRender(token,actor,target[1],body);
    }catch(error){
      if(error instanceof AuthDenied)return out(401,"UNAUTHORIZED");
      if(error instanceof RpcSubscriptionError)return out(error.code==="RG002"?429:402,
        error.code==="RG002"?"QUOTA_EXCEEDED":"SUBSCRIPTION_REQUIRED");
      if(error instanceof TypeError)return out(400,"INVALID_REQUEST");
      return out(503,"SERVICE_UNAVAILABLE");
    }
  };
}
