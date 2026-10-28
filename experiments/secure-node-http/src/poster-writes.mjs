/**
 * Source-only, *unregistered* Node poster mutation adapter.
 * Business writes use ONLY existing user-JWT Supabase SQL RPCs:
 * create_poster_draft (rights + quota), request_poster_job (atomic outbox),
 * select_poster_banner (optimistic-CAS).
 *
 * NEVER directly enqueue an Azure job or use a service-role token. An
 * uncertain POST acknowledgement must NOT cause an automatic retry.
 */
import { AuthDenied, UpstreamUnavailable, canonicalUuid } from "./security.mjs";
import { PrivateReader } from "./private-reads.mjs";

const RPCS = new Set(["create_poster_draft", "request_poster_job", "select_poster_banner"]);
const WRITE_ROLES = new Set(["OWNER", "EDITOR"]);
const HEX = /^#[a-fA-F0-9]{6}$/;
const TEMPLATES = new Set(["editorial", "bold", "minimal"]);
const FORMATS = new Set(["square", "portrait"]);
const REQUIRED = ["day_id", "source_asset_id", "template", "format", "business_name",
  "accent_color", "background_color"];
const OPTIONAL = ["logo_asset_id", "offer_text"];

const own = (value, key) => Object.prototype.hasOwnProperty.call(value, key);
const object = value => value !== null && typeof value === "object" &&
  !Array.isArray(value) && Object.getPrototypeOf(value) === Object.prototype;
const publicResponse = (status, jsonBody) => ({
  status, jsonBody, headers: { "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff", "X-RGAI-Secure-Adapter": "poster-rpc-source-v1" },
});
const denied = (status, code) => publicResponse(status, { error: code });

export class RpcSubscriptionError extends Error {
  constructor(code) { super("SUBSCRIPTION_DENIED"); this.code = code; }
}

export class PosterRpcWriter extends PrivateReader {
  async memberWrite(token, userId, shopId) {
    const uid = canonicalUuid(userId), sid = canonicalUuid(shopId);
    const rows = await this.read("shop_memberships", token, {
      select: "user_id,shop_id,role,active",
      user_id: "eq." + uid, shop_id: "eq." + sid, active: "eq.true", limit: "1",
    });
    return rows.length === 1 && rows[0].user_id === uid &&
      rows[0].shop_id === sid && rows[0].active === true &&
      WRITE_ROLES.has(rows[0].role);
  }

  async rpc(token, procedure, args) {
    if (!RPCS.has(procedure) || !object(args) ||
        typeof token !== "string" || !token) throw new TypeError("INVALID_RPC");
    let response;
    try {
      response = await this.fetchImpl(this.origin + "/rest/v1/rpc/" + procedure, {
        method: "POST", redirect: "error", cache: "no-store",
        headers: { apikey: this.key, Authorization: "Bearer " + token,
          "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(args),
        signal: AbortSignal.timeout(8000),
      });
    } catch {
      throw new UpstreamUnavailable();
    }
    if (response.status === 401 || response.status === 403) throw new AuthDenied();
    if (!response.ok) {
      // Only these existing server-authored SQLSTATEs get billing statuses.
      if ([400,402,409,429,500].includes(response.status)) {
        try {
          const code = (await response.json())?.code;
          if (code === "RG001" || code === "RG002") throw new RpcSubscriptionError(code);
        } catch (error) {
          if (error instanceof RpcSubscriptionError) throw error;
        }
      }
      throw new UpstreamUnavailable();
    }
    try { return await response.json(); }
    catch { throw new UpstreamUnavailable(); }
  }

  async createDraft(token, userId, campaignId, body) {
    const cid = canonicalUuid(campaignId);
    if (!object(body) || REQUIRED.some(k => !own(body,k)) ||
        Object.keys(body).some(k => !REQUIRED.includes(k) && !OPTIONAL.includes(k))) {
      return denied(400,"INVALID_REQUEST");
    }
    const did = canonicalUuid(body.day_id), source = canonicalUuid(body.source_asset_id);
    const logo = body.logo_asset_id == null ? null : canonicalUuid(body.logo_asset_id);
    const name = body.business_name;
    const offer = body.offer_text ?? null;
    if (!TEMPLATES.has(body.template) || !FORMATS.has(body.format) ||
        typeof name !== "string" || name.trim().length < 1 || name.trim().length > 70 ||
        /[\x00-\x1f]/.test(name) ||
        typeof body.accent_color !== "string" || !HEX.test(body.accent_color) ||
        typeof body.background_color !== "string" || !HEX.test(body.background_color) ||
        (offer !== null && (typeof offer !== "string" || offer.trim().length < 1 ||
          offer.trim().length > 110 || /[\x00-\x1f]/.test(offer)))) {
      return denied(400,"INVALID_REQUEST");
    }
    const campaign = await this.campaign(token,userId,cid);
    if (!campaign) return denied(404,"NOT_FOUND");
    if (campaign.status !== "DRAFT") return denied(409,"CAMPAIGN_NOT_DRAFT");
    const shop = canonicalUuid(campaign.shop_id);
    if (!await this.memberWrite(token,userId,shop)) return denied(403,"FORBIDDEN");
    const days = campaign.days.filter(d=> d.id === did && d.shop_id === shop &&
      d.campaign_id === cid);
    if (days.length !== 1) return denied(404,"NOT_FOUND");
    if (days[0].review_status !== "DRAFT") return denied(409,"DAY_NOT_DRAFT");
    const shots = days[0]?.instagram?.reel?.storyboard;
    if (!Array.isArray(shots) || !shots.some(s=>object(s) && s.asset_id === source)) {
      return denied(403,"ASSET_ACCESS_DENIED");
    }
    for (const id of [source,...(logo ? [logo] : [])]) {
      if (!await this._asset(token,shop,id)) return denied(403,"ASSET_ACCESS_DENIED");
    }
    // DB RLS RPC *rechecks* shop/day, licensed rights, quota and revision constraints.
    const draftId = await this.rpc(token,"create_poster_draft",{
      p_shop_id:shop,p_campaign_id:cid,p_day_id:did,
      p_source_asset_id:source,p_logo_asset_id:logo,
      p_template:body.template,p_format:body.format,
      p_business_name:name.trim(),p_accent_color:body.accent_color,
      p_background_color:body.background_color,
      p_offer_text:offer?.trim() ?? null,
    });
    return draftId === null ? denied(403,"POSTER_DRAFT_DENIED") :
      publicResponse(201,{poster_id:canonicalUuid(draftId),status:"DRAFT"});
  }

  // Dedicated poster entrypoint: ReelIntentWriter derives from this class and
  // uses requestRender() for campaign videos. Never dispatch poster jobs via
  // that overridden Reel method (its {day_id,preset} body is incompatible).
  async requestPosterRender(token,userId,posterId,body) {
    const pid = canonicalUuid(posterId);
    if (body !== undefined && body !== null && !(object(body) && Object.keys(body).length===0)) {
      return denied(400,"INVALID_REQUEST");
    }
    const draft = await this.posterDraft(token,userId,pid);
    if (!draft) return denied(404,"NOT_FOUND");
    if (!await this.memberWrite(token,userId,draft.shop_id)) return denied(403,"FORBIDDEN");
    // Existing SQL RPC reserves quota and persists job+outbox atomically.
    const jobId = await this.rpc(token,"request_poster_job",{p_poster_id:pid});
    return jobId === null ? denied(409,"POSTER_NOT_RENDERABLE") :
      publicResponse(202,{job_id:canonicalUuid(jobId),status:"QUEUED"});
  }

  async selectBanner(token,userId,posterId,body) {
    const pid = canonicalUuid(posterId);
    if (!object(body) || Object.keys(body).length!==1 ||
        !own(body,"expected_instagram") || !object(body.expected_instagram) ||
        Object.keys(body.expected_instagram).length!==3 ||
        !["caption","banner_asset_id","reel"].every(k=>own(body.expected_instagram,k))) {
      return denied(400,"INVALID_REQUEST");
    }
    const draft = await this.posterDraft(token,userId,pid);
    if (!draft) return denied(404,"NOT_FOUND");
    if (!await this.memberWrite(token,userId,draft.shop_id)) return denied(403,"FORBIDDEN");
    if (draft.status!=="READY" || !draft.output_asset_id) {
      return denied(409,"OUTPUT_NOT_READY");
    }
    // SQL compares expected Instagram draft and current revision atomically.
    const saved = await this.rpc(token,"select_poster_banner",{
      p_poster_id:pid,p_expected_instagram:body.expected_instagram,
    });
    if (typeof saved !== "boolean") throw new UpstreamUnavailable();
    return saved ? publicResponse(200,{poster_id:pid,banner_asset_id:draft.output_asset_id}) :
      denied(409,"POSTER_SELECTION_STALE_OR_DENIED");
  }
}

export function createPosterWriteGateway({verifyJwt, writer}) {
  if(typeof verifyJwt!=="function" || !writer)throw new TypeError("MISSING_WRITER");
  return async function handle(method,path,authorization,body) {
    if(method!=="POST") return denied(405,"METHOD_NOT_ALLOWED");
    const match = /^\/api\/campaigns\/([^/]+)\/posters$/.exec(path);
    const render = /^\/api\/poster-drafts\/([^/]+)\/renders$/.exec(path);
    const select = /^\/api\/poster-drafts\/([^/]+)\/select$/.exec(path);
    if (!match && !render && !select) return denied(404,"NOT_FOUND");
    try {
      if(typeof authorization!=="string" || !authorization.startsWith("Bearer "))throw new AuthDenied();
      const token=authorization.slice(7);
      const user=await verifyJwt(token);
      if(match) return await writer.createDraft(token,user,match[1],body);
      if(render) return await writer.requestPosterRender(token,user,render[1],body);
      return await writer.selectBanner(token,user,select[1],body);
    } catch(error) {
      if(error instanceof AuthDenied)return denied(401,"UNAUTHORIZED");
      if(error instanceof RpcSubscriptionError)return denied(error.code==="RG002"?429:402,
        error.code==="RG002"?"QUOTA_EXCEEDED":"SUBSCRIPTION_REQUIRED");
      if(error instanceof TypeError)return denied(400,"INVALID_REQUEST");
      return denied(503,"SERVICE_UNAVAILABLE");
    }
  };
}
