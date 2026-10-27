// Read-only per-shop campaign month planning. These records are not social delivery receipts.
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const MONTH = /^\d{4}-(0[1-9]|1[0-2])$/
export const MAX_MONTH_DAYS = 200

export function checkedMonth(month) {
  if (typeof month !== 'string' || !MONTH.test(month)) throw new Error('Choose a valid calendar month')
  const [year, number] = month.split('-').map(Number)
  if (year < 2000 || year > 2099) throw new Error('Calendar month is out of range')
  const next = new Date(Date.UTC(year,number,1,12)).toISOString().slice(0,10)
  return { start: month + '-01', end: next }
}

function realISODate(value) {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false
  const parsed = new Date(value + 'T12:00:00Z')
  return !Number.isNaN(parsed.getTime()) && parsed.toISOString().slice(0,10) === value
}

export function verifiedShopMonthRows(rows, shopId, month) {
  const {start,end} = checkedMonth(month)
  if (!UUID.test(shopId || '') || !Array.isArray(rows) || rows.length > MAX_MONTH_DAYS) {
    throw new Error('Business calendar data could not be verified')
  }
  const normalized = []
  for (const row of rows) {
    if (!row || row.shop_id !== shopId || !UUID.test(row.id || '') ||
      !UUID.test(row.campaign_id || '') || !realISODate(row.scheduled_date) ||
      row.scheduled_date < start || row.scheduled_date >= end ||
      typeof row.topic !== 'string' || !row.topic.trim() || row.topic.length > 300 ||
      !['DRAFT','APPROVED','REJECTED'].includes(row.review_status)) {
      throw new Error('Business calendar data could not be verified')
    }
    normalized.push({id:row.id,campaign_id:row.campaign_id,shop_id:shopId,
      scheduled_date:row.scheduled_date,topic:row.topic,
      review_status:row.review_status})
  }
  return normalized.sort((a,b)=>a.scheduled_date.localeCompare(b.scheduled_date)
    || a.campaign_id.localeCompare(b.campaign_id) || a.id.localeCompare(b.id))
}
