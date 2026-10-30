const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/
const ISO_MONTH = /^\d{4}-(0[1-9]|1[0-2])$/

function realDate(value) {
  if (!ISO_DATE.test(value || '')) return false
  const parsed = new Date(value + 'T12:00:00Z')
  return !Number.isNaN(parsed.getTime()) && parsed.toISOString().slice(0,10) === value
}

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
    realDate(day.scheduled_date) &&
    ['DRAFT', 'APPROVED', 'NEEDS_REVIEW'].includes(day.review_status))
    .sort((a,b) => a.scheduled_date.localeCompare(b.scheduled_date) || a.day_index - b.day_index)
}

/** Month choices are derived exclusively from signed-in, shop-verified DRAFTs.
 * No dates outside this one campaign are implied to be scheduled. */
export function verifiedDraftMonths(days) {
  if (!Array.isArray(days)) return []
  return [...new Set(days.filter(day => day && realDate(day.scheduled_date))
    .map(day => day.scheduled_date.slice(0,7)))].sort()
}

/** Fixed Monday-first seven-column calendar with UTC arithmetic to prevent
 * browser locale/DST from moving a shop's scheduled date to another day. */
export function draftMonthCells(days, month) {
  if (!ISO_MONTH.test(month || '')) return []
  const [year, number] = month.split('-').map(Number)
  const first = new Date(Date.UTC(year, number-1, 1, 12))
  if (first.toISOString().slice(0,7) !== month) return []
  const offset = (first.getUTCDay()+6)%7
  const count = new Date(Date.UTC(year,number,0,12)).getUTCDate()
  const gridSize = Math.ceil((offset+count)/7)*7
  const eventCounts = new Map()
  for (const day of Array.isArray(days) ? days : []) {
    if (day && realDate(day.scheduled_date) && day.scheduled_date.startsWith(month)) {
      eventCounts.set(day.scheduled_date,(eventCounts.get(day.scheduled_date)||0)+1)
    }
  }
  return Array.from({length:gridSize},(_,i)=>{
    const dayDate = new Date(Date.UTC(year,number-1,i-offset+1,12))
    const date = dayDate.toISOString().slice(0,10)
    const inMonth = date.startsWith(month)
    return {date,day:dayDate.getUTCDate(),inMonth,drafts:inMonth?(eventCounts.get(date)||0):0}
  })
}
