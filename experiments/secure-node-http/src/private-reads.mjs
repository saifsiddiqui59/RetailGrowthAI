/**
 * Node source-only user-RLS private poster/Reel read parity.
 * No service-role secrets, queue enqueue, billing or job-state writes.
 * A storage sign request is a bounded ephemeral RLS-scoped POST, not a
 * mutation to a business-owned job or media asset.
 */
import { AuthDenied, UpstreamUnavailable, canonicalUuid } from "./security.mjs";
import { TenantReader } from "./tenant-read.mjs";

const BUCKET = "retailgrowth-media";
const MIME_VIDEO = "video/mp4";
const MIME_POSTER = "image/png";
const draftFields = "id,shop_id,campaign_id,day_id,status,template,format,business_name,accent_color,background_color,offer_text,source_asset_id,output_asset_id";
const jobFields = "id,shop_id,poster_id,status,output_asset_id,error_code";

function one(rows, id) {
  if (rows.length === 0) return null;
  if (rows.length !== 1 || rows[0]?.id !== id) throw new UpstreamUnavailable();
  return rows[0];
}
function validPath(shopId, path) {
  if (typeof path !== "string" || !path.startsWith(shopId + "/") ||
      path.length > 1024 || path.includes("\\") || path.includes("?") ||
      path.includes("#") || path.includes("%") || path.includes("//") ||
      path.split("/").some(segment => segment === "." || segment === ".." || segment === "")) {
    return false;
  }
  return true;
}

export class PrivateReader extends TenantReader {
  async posterDraft(token, userId, posterId) {
    const pid = canonicalUuid(posterId);
    const draft = one(await this.read("poster_drafts", token, {
      select: draftFields, id: "eq." + pid, limit: "1",
    }), pid);
    if (!draft) return null;
    const shop = canonicalUuid(draft.shop_id);
    if (!await this.member(token, userId, shop)) return null;
    return draft;
  }

  async postersForDay(token, userId, campaignId, dayId) {
    const cid = canonicalUuid(campaignId);
    const did = canonicalUuid(dayId);
    const campaign = await this.campaign(token, userId, cid);
    if (!campaign || !campaign.days.some(d => d.id === did && d.shop_id === campaign.shop_id)) {
      return null;
    }
    const shop = canonicalUuid(campaign.shop_id);
    const drafts = await this.read("poster_drafts", token, {
      select: draftFields + ",revision",
      shop_id: "eq." + shop, campaign_id: "eq." + cid, day_id: "eq." + did,
      order: "created_at.desc", limit: "21",
    });
    if (drafts.length > 21 || drafts.some(d =>
      d.shop_id !== shop || d.campaign_id !== cid || d.day_id !== did)) {
      throw new UpstreamUnavailable();
    }
    if (!drafts.length) return [];
    const ids = drafts.map(d => canonicalUuid(d.id));
    if (new Set(ids).size !== ids.length) throw new UpstreamUnavailable();
    const jobs = await this.read("poster_jobs", token, {
      select: "id,shop_id,poster_id,status,output_asset_id",
      shop_id: "eq." + shop, poster_id: "in.(" + ids.join(",") + ")", limit: "21",
    });
    if (jobs.length > 21 || jobs.some(j => j.shop_id !== shop || !ids.includes(j.poster_id))) {
      throw new UpstreamUnavailable();
    }
    const byPoster = new Map();
    for (const job of jobs) {
      if (byPoster.has(job.poster_id)) throw new UpstreamUnavailable();
      byPoster.set(job.poster_id, job);
    }
    return drafts.map(d => ({
      ...d, job_id: byPoster.get(d.id)?.id ?? null,
      job_status: byPoster.get(d.id)?.status ?? null,
    }));
  }

  async posterJob(token, userId, jobId) {
    const jid = canonicalUuid(jobId);
    const job = one(await this.read("poster_jobs", token, {
      select: jobFields, id: "eq." + jid, limit: "1",
    }), jid);
    if (!job) return null;
    const shop = canonicalUuid(job.shop_id);
    if (!await this.member(token, userId, shop)) return null;
    return job;
  }

  async _asset(token, shopId, assetId) {
    const sid = canonicalUuid(shopId), aid = canonicalUuid(assetId);
    const asset = one(await this.read("media_assets", token, {
      select: "id,shop_id,storage_bucket,object_path,mime_type",
      id: "eq." + aid, shop_id: "eq." + sid, limit: "1",
    }), aid);
    if (!asset || asset.shop_id !== sid || asset.storage_bucket !== BUCKET ||
        !validPath(sid, asset.object_path)) return null;
    return asset;
  }

  async _signedUrl(token, shopId, objectPath) {
    const sid = canonicalUuid(shopId);
    if (!validPath(sid, objectPath)) throw new UpstreamUnavailable();
    const encoded = objectPath.split("/").map(encodeURIComponent).join("/");
    const relative = "/object/sign/" + BUCKET + "/" + encoded;
    const url = this.origin + "/storage/v1" + relative;
    let response;
    try {
      response = await this.fetchImpl(url, {
        method: "POST", redirect: "error", cache: "no-store",
        headers: {
          apikey: this.key, Authorization: "Bearer " + token,
          Accept: "application/json", "Content-Type": "application/json",
        },
        body: JSON.stringify({ expiresIn: 60 }),
        signal: AbortSignal.timeout(8000),
      });
      if (!response.ok) throw new UpstreamUnavailable();
      const answer = await response.json();
      const signed = answer?.signedURL;
      if (typeof signed !== "string" || signed.length > 4096 ||
          !signed.startsWith(relative + "?token=")) throw new UpstreamUnavailable();
      const parsed = new URL(signed, this.origin);
      if (parsed.origin !== this.origin || parsed.pathname !== relative ||
          !parsed.searchParams.get("token") || parsed.username || parsed.password ||
          parsed.hash) throw new UpstreamUnavailable();
      return this.origin + "/storage/v1" + signed;
    } catch {
      // Do not expose provider error payloads or any signed object tokens.
      throw new UpstreamUnavailable();
    }
  }

  async videoDownload(token, userId, jobId) {
    const jid = canonicalUuid(jobId);
    const row = one(await this.read("render_jobs", token, {
      select: "id,shop_id,status,output_asset_id,error_code",
      id: "eq." + jid, limit: "1",
    }), jid);
    if (!row) return {status: 404, body: {error: "NOT_FOUND"}};
    const shop = canonicalUuid(row.shop_id);
    if (!await this.member(token, userId, shop)) return {status: 404, body: {error: "NOT_FOUND"}};
    if (row.status !== "SUCCEEDED" || !row.output_asset_id) {
      return {status: 409, body: {error: "OUTPUT_NOT_READY"}};
    }
    const asset = await this._asset(token, shop, row.output_asset_id);
    if (!asset || asset.mime_type !== MIME_VIDEO) {
      return {status: 404, body: {error: "OUTPUT_NOT_FOUND"}};
    }
    return {status: 200, body: {url: await this._signedUrl(token, shop, asset.object_path)}};
  }

  async posterDownload(token, userId, jobId) {
    const job = await this.posterJob(token, userId, jobId);
    if (!job) return {status: 404, body: {error: "NOT_FOUND"}};
    if (job.status !== "SUCCEEDED" || !job.output_asset_id) {
      return {status: 409, body: {error: "OUTPUT_NOT_READY"}};
    }
    const shop = canonicalUuid(job.shop_id);
    const asset = await this._asset(token, shop, job.output_asset_id);
    const expectedPrefix = shop + "/posters/" + canonicalUuid(job.poster_id) + "/";
    if (!asset || asset.mime_type !== MIME_POSTER ||
        !asset.object_path.startsWith(expectedPrefix)) {
      return {status: 404, body: {error: "OUTPUT_NOT_FOUND"}};
    }
    return {status: 200, body: {url: await this._signedUrl(token, shop, asset.object_path)}};
  }
}
