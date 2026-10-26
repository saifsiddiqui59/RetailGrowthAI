// Read-after-uncertain-POST reconciliation. No POST retries or client-side guesses.
// This is NOT server-side idempotency; a late commit can remain unconfirmed.
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

export function reconcileSubmittedDraft(rows, { shopId, trendId, submissionId }) {
  if (!Array.isArray(rows) || !UUID.test(shopId || '') ||
      !UUID.test(submissionId || '') || !/^[a-f0-9]{32}$/.test(trendId || '')) {
    throw new Error('Invalid authoritative draft reconciliation input')
  }
  const marked = rows.filter(row => row?.content?.submission_id === submissionId)
  if (marked.length === 0) return null
  if (marked.length !== 1) throw new Error('Ambiguous submission persisted')
  const row = marked[0]
  if (row.shop_id !== shopId || row.content?.campaign?.shop_id !== shopId ||
      row.trend_id !== trendId || row.review_state !== 'DRAFT' ||
      row.content?.review?.status !== 'DRAFT' ||
      row.content?.review?.can_publish !== false || !UUID.test(row.id || '')) {
    throw new Error('Untrusted or cross-tenant submission')
  }
  return row.id
}
