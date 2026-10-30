/**
 * Read-only Supabase PostgREST access with caller's JWT and publishable key.
 * Every read is RLS-bound and independently verifies active shop membership.
 */
import { AuthDenied, UpstreamUnavailable, canonicalUuid, supabaseOrigin } from "./security.mjs";

const TABLES = new Set(["campaigns", "campaign_days", "render_jobs", "poster_drafts", "poster_jobs", "media_assets"]);
const MEMBERSHIP_ROLES = new Set(["OWNER", "EDITOR", "VIEWER"]);

export class TenantReader {
  constructor({ origin, publishableKey, fetchImpl = fetch }) {
    this.origin = supabaseOrigin(origin);
    if (typeof publishableKey !== "string" || !publishableKey ||
        publishableKey.startsWith("sb_secret_")) throw new TypeError("PUBLIC_KEY_REQUIRED");
    this.key = publishableKey;
    this.fetchImpl = fetchImpl;
  }
  async read(table, token, filters) {
    if (!(TABLES.has(table) || table === "shop_memberships") ||
        typeof token !== "string" || !token) throw new TypeError("INVALID_READ");
    const url = new URL(this.origin + "/rest/v1/" + table);
    for (const [k, v] of Object.entries(filters)) url.searchParams.set(k, v);
    let response;
    try {
      response = await this.fetchImpl(url.toString(), {
        method: "GET", redirect: "error", cache: "no-store",
        headers: {
          apikey: this.key, Authorization: "Bearer " + token,
          Accept: "application/json",
        },
        signal: AbortSignal.timeout(8000),
      });
      if (response.status === 401 || response.status === 403) throw new AuthDenied();
      if (!response.ok) throw new UpstreamUnavailable();
      const rows = await response.json();
      if (!Array.isArray(rows) || rows.length > 32) throw new UpstreamUnavailable();
      return rows;
    } catch (error) {
      if (error instanceof AuthDenied || error instanceof UpstreamUnavailable) throw error;
      throw new UpstreamUnavailable();
    }
  }
  async member(token, userId, shopId) {
    const uid = canonicalUuid(userId);
    const sid = canonicalUuid(shopId);
    const rows = await this.read("shop_memberships", token, {
      select: "shop_id,user_id,role,active",
      shop_id: "eq." + sid, user_id: "eq." + uid, active: "eq.true", limit: "1",
    });
    return rows.length === 1 && rows[0].shop_id === sid && rows[0].user_id === uid &&
      rows[0].active === true && MEMBERSHIP_ROLES.has(rows[0].role);
  }
  async campaign(token, userId, campaignId) {
    const cid = canonicalUuid(campaignId);
    const rows = await this.read("campaigns", token, {
      select: "id,shop_id,status", id: "eq." + cid, limit: "1",
    });
    if (rows.length !== 1 || rows[0].id !== cid) return null;
    const shop = canonicalUuid(rows[0].shop_id);
    if (!await this.member(token, userId, shop)) return null;
    const days = await this.read("campaign_days", token, {
      select: "id,campaign_id,shop_id,day_index,scheduled_date,topic,linkedin,instagram,review_status",
      campaign_id: "eq." + cid, shop_id: "eq." + shop, order: "day_index.asc", limit: "32",
    });
    if (days.some(d => d.shop_id !== shop || d.campaign_id !== cid)) throw new UpstreamUnavailable();
    return { id: cid, shop_id: shop, status: rows[0].status, days };
  }
  async renderJob(token, userId, jobId) {
    const jid = canonicalUuid(jobId);
    const rows = await this.read("render_jobs", token, {
      select: "id,shop_id,status,output_asset_id,error_code", id: "eq." + jid, limit: "1",
    });
    if (rows.length !== 1 || rows[0].id !== jid) return null;
    const shop = canonicalUuid(rows[0].shop_id);
    if (!await this.member(token, userId, shop)) return null;
    const r = rows[0];
    return { job_id: jid, status: r.status, output_asset_id: r.output_asset_id,
             error_code: r.error_code };
  }
}
