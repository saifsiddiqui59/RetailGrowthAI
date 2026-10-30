/** Feature #3 browser-side, fail-closed approved-input presentation filter.
 *
 * This never grants access: authenticated server-side member/campaign/asset
 * authorization and rights are required again at save/render/publish time.
 */
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
// Presentation-only guard: never display unreviewed control or bidi-override
// characters as approved retail offers. Backend rights remain authoritative.
const UNSAFE_COPY = /[\u0000-\u001f\u007f-\u009f\u202a-\u202e\u2066-\u2069]/
function approvedCopy(value, max) {
  return typeof value === 'string' && value.trim().length > 0 &&
    value.length <= max && !UNSAFE_COPY.test(value)
}

export function feature3ContextKey(context) {
  if (!context || typeof context !== 'object' || Array.isArray(context)) return ''
  const { shopId, campaignId, dayId } = context
  if (![shopId, campaignId, dayId].every(x => typeof x === 'string' && UUID.test(x))) return ''
  return [shopId, campaignId, dayId].join('/')
}

export function approvedFeature3Inputs(content, context, brandKit) {
  const key = feature3ContextKey(context)
  if (!key || !brandKit || typeof brandKit !== 'object' ||
      brandKit.shopId !== context.shopId ||
      !approvedCopy(brandKit.businessName, 70)) {
    return { brand: null, approved: null }
  }
  if (!content || typeof content !== 'object' ||
      content.review_state !== 'APPROVED' ||
      content.shop_id !== context.shopId ||
      content.campaign_id !== context.campaignId ||
      content.day_id !== context.dayId ||
      !Number.isSafeInteger(content.approved_version) ||
      content.approved_version < 1 || content.approved_version > 2147483646 ||
      !approvedCopy(content.headline, 100) ||
      !approvedCopy(content.cta, 100) ||
      (content.offer_text != null && !approvedCopy(content.offer_text, 85))) {
    return { brand: brandKit, approved: null }
  }
  return { brand: brandKit, approved: content }
}
