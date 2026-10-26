/** Feature #3 browser-side, fail-closed approved-input presentation filter.
 *
 * This never grants access: authenticated server-side member/campaign/asset
 * authorization and rights are required again at save/render/publish time.
 */
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

export function feature3ContextKey({ shopId, campaignId, dayId }) {
  if (![shopId, campaignId, dayId].every(x => typeof x === 'string' && UUID.test(x))) return ''
  return [shopId, campaignId, dayId].join('/')
}

export function approvedFeature3Inputs(content, context, brandKit) {
  const key = feature3ContextKey(context)
  if (!key || !brandKit || typeof brandKit !== 'object' ||
      brandKit.shopId !== context.shopId ||
      typeof brandKit.businessName !== 'string' ||
      !brandKit.businessName.trim() ||
      brandKit.businessName.length > 70) {
    return { brand: null, approved: null }
  }
  if (!content || typeof content !== 'object' ||
      content.review_state !== 'APPROVED' ||
      content.shop_id !== context.shopId ||
      content.campaign_id !== context.campaignId ||
      content.day_id !== context.dayId ||
      !Number.isInteger(content.approved_version) ||
      content.approved_version < 1 ||
      typeof content.headline !== 'string' || !content.headline.trim() ||
      content.headline.length > 100 ||
      typeof content.cta !== 'string' || !content.cta.trim() ||
      content.cta.length > 100 ||
      (content.offer_text != null &&
        (typeof content.offer_text !== 'string' ||
         !content.offer_text.trim() || content.offer_text.length > 85))) {
    return { brand: brandKit, approved: null }
  }
  return { brand: brandKit, approved: content }
}
