const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/

export function recentCampaignHint(storage, userId, shopId) {
  if (!UUID.test(userId || '') || !UUID.test(shopId || '')) return ''
  try {
    const value = storage?.getItem('retailgrowthai-last-campaign:' + userId + ':' + shopId)
    return UUID.test(value || '') ? value : ''
  } catch { return '' }
}

export function verifiedCampaignDays(campaign, shopId) {
  if (!campaign || !UUID.test(shopId || '') || campaign.shop_id !== shopId ||
      !UUID.test(campaign.id || '') || campaign.status !== 'DRAFT' ||
      !Array.isArray(campaign.days)) return []
  return campaign.days.filter(day => day && day.shop_id === shopId &&
    day.campaign_id === campaign.id && UUID.test(day.id || '') &&
    Number.isSafeInteger(day.day_index) && day.day_index > 0 &&
    typeof day.topic === 'string' && day.topic.trim() && day.topic.length <= 300 &&
    ISO_DATE.test(day.scheduled_date || '') &&
    !Number.isNaN(Date.parse(day.scheduled_date + 'T12:00:00Z')) &&
    ['DRAFT', 'APPROVED', 'NEEDS_REVIEW'].includes(day.review_status))
    .sort((a,b) => a.scheduled_date.localeCompare(b.scheduled_date) || a.day_index - b.day_index)
}
