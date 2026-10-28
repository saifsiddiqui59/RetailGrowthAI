/**
 * SOURCE ONLY. Campaign creation via existing user-RLS campaigns INSERT +
 * existing DB trigger's transactional planning outbox; saved-day PATCH via
 * user-JWT optimistic compare-and-swap SQL RPC. NO direct Azure Queue writes.
 * No automatic retries on uncertain POST/PATCH.
 */
import { randomUUID } from "node:crypto";
import { AuthDenied, UpstreamUnavailable, canonicalUuid } from "./security.mjs";
import { ContractDenied, validateCampaignBrief, validateCampaign } from "./v1-contract.mjs";
import { PosterRpcWriter, RpcSubscriptionError } from "./poster-writes.mjs";

const deny=(status,error)=>({status,jsonBody:{error},headers:{"Cache-Control":"no-store"}});
const response=(status,jsonBody)=>({status,jsonBody,headers:{"Cache-Control":"no-store"}});
const plain=x=>x!==null && typeof x==="object" && !Array.isArray(x) &&
  Object.getPrototypeOf(x)===Object.prototype;
const ONLY_FIELDS=["topic","linkedin","instagram"];

export class CampaignDayWriter extends PosterRpcWriter {
  async createCampaign(token,userId,body) {
    const brief=validateCampaignBrief(body);
    const shop=brief.shop_id;
    if(!await this.memberWrite(token,userId,shop))return deny(403,"FORBIDDEN");
    for(const aid of brief.media_asset_ids){
      if(!await this._asset(token,shop,aid))return deny(403,"FORBIDDEN");
    }
    const campaignId=randomUUID();
    const row={
      id:campaignId,shop_id:shop,created_by:canonicalUuid(userId),
      brief:brief.brief,duration_days:brief.duration_days,
      start_date:brief.start_date,timezone:brief.timezone,
      language:brief.language,platforms:brief.platforms,
      media_asset_ids:brief.media_asset_ids,offer:brief.offer,status:"PLANNING",
    };
    let res;
    try {
      res=await this.fetchImpl(this.origin+"/rest/v1/campaigns",{
        method:"POST",redirect:"error",cache:"no-store",
        headers:{apikey:this.key,Authorization:"Bearer "+token,
          "Content-Type":"application/json",Accept:"application/json",
          Prefer:"return=representation"},
        body:JSON.stringify(row),signal:AbortSignal.timeout(8000),
      });
    } catch {throw new UpstreamUnavailable();}
    if(res.status===401||res.status===403)throw new AuthDenied();
    if(!res.ok){
      if([400,402,409,429,500].includes(res.status)){
        try{
          const code=(await res.json())?.code;
          if(code==="RG001"||code==="RG002")throw new RpcSubscriptionError(code);
        }catch(error){if(error instanceof RpcSubscriptionError)throw error;}
      }
      throw new UpstreamUnavailable();
    }
    let inserted;
    try { inserted=await res.json(); } catch {throw new UpstreamUnavailable();}
    if(!Array.isArray(inserted)||inserted.length!==1 ||
        inserted[0]?.id!==campaignId||inserted[0]?.shop_id!==shop){
      throw new UpstreamUnavailable();
    }
    // Original DB INSERT trigger atomically persists the private planning outbox.
    return response(202,{campaign_id:campaignId,status:"PLANNING"});
  }

  async saveDay(token,userId,campaignId,dayId,body) {
    const cid=canonicalUuid(campaignId),did=canonicalUuid(dayId);
    if(!plain(body) || Object.keys(body).length!==3 ||
        !ONLY_FIELDS.every(key=>Object.prototype.hasOwnProperty.call(body,key))){
      return deny(400,"INVALID_REQUEST");
    }
    const campaign=await this.campaign(token,userId,cid);
    if(!campaign)return deny(404,"NOT_FOUND");
    if(campaign.status!=="DRAFT")return deny(409,"CAMPAIGN_NOT_DRAFT");
    const matching=campaign.days.filter(d=>d.id===did);
    if(matching.length!==1)return deny(404,"NOT_FOUND");
    const old=matching[0],shop=canonicalUuid(campaign.shop_id);
    if(!await this.memberWrite(token,userId,shop))return deny(403,"FORBIDDEN");
    const candidate={...campaign,days:campaign.days.map(day=>
      day.id===did?{...day,...body}:day)};
    validateCampaign(candidate);
    const replacement=candidate.days.find(day=>day.id===did);
    const reel=replacement.instagram.reel;
    const ids=[...reel.storyboard.map(x=>canonicalUuid(x.asset_id)),
      ...(reel.music_asset_id===null?[]:[canonicalUuid(reel.music_asset_id)]),
      ...(replacement.instagram.banner_asset_id===null?[]:
        [canonicalUuid(replacement.instagram.banner_asset_id)])];
    for(const aid of new Set(ids)){
      if(!await this._asset(token,shop,aid))return deny(403,"ASSET_ACCESS_DENIED");
    }
    const expected={topic:old.topic,linkedin:old.linkedin,instagram:old.instagram};
    let res;
    try {
      res=await this.fetchImpl(this.origin+"/rest/v1/rpc/save_campaign_day",{
        method:"POST",redirect:"error",cache:"no-store",
        headers:{apikey:this.key,Authorization:"Bearer "+token,
          "Content-Type":"application/json",Accept:"application/json"},
        body:JSON.stringify({
          p_shop_id:shop,p_campaign_id:cid,p_day_id:did,
          p_expected:expected,p_changes:body,
        }),signal:AbortSignal.timeout(8000),
      });
    } catch {throw new UpstreamUnavailable();}
    if(res.status===401||res.status===403)throw new AuthDenied();
    if(!res.ok)throw new UpstreamUnavailable();
    let accepted;
    try {accepted=await res.json();} catch {throw new UpstreamUnavailable();}
    if(typeof accepted!=="boolean")throw new UpstreamUnavailable();
    if(!accepted)return deny(409,"EDIT_CONFLICT");
    const refreshed=await this.campaign(token,userId,cid);
    const saved=refreshed?.days?.filter(d=>d.id===did)??[];
    if(saved.length!==1)throw new UpstreamUnavailable();
    // Never auto-reissue the CAS operation on an ambiguous network failure.
    return response(200,{day:saved[0]});
  }
}

export function createCampaignDayGateway({verifyJwt,writer}) {
  if(typeof verifyJwt!=="function" || !writer)throw new TypeError("MISSING_DEPENDENCIES");
  return async function handle(method,path,authorization,body) {
    const create=method==="POST" && path==="/api/campaigns";
    const save=method==="PATCH" &&
      /^\/api\/campaigns\/([^/]+)\/days\/([^/]+)$/.exec(path);
    if(!create && !save)return deny(404,"NOT_FOUND");
    try{
      if(typeof authorization!=="string" || !authorization.startsWith("Bearer "))throw new AuthDenied();
      const token=authorization.slice(7);
      const user=await verifyJwt(token);
      return create
        ? await writer.createCampaign(token,user,body)
        : await writer.saveDay(token,user,save[1],save[2],body);
    } catch(error){
      if(error instanceof AuthDenied)return deny(401,"UNAUTHORIZED");
      if(error instanceof RpcSubscriptionError)return deny(error.code==="RG002"?429:402,
        error.code==="RG002"?"QUOTA_EXCEEDED":"SUBSCRIPTION_REQUIRED");
      if(error instanceof TypeError || error instanceof ContractDenied)return deny(400,"INVALID_REQUEST");
      return deny(503,"SERVICE_UNAVAILABLE");
    }
  };
}
