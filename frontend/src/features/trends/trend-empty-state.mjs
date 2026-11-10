/** Feature2 explicitly offers the EXISTING campaign editor, never forges trend evidence. */
export function offerStandardCampaignFallback({ loading, error, results }) {
  if (loading) return false
  if (typeof error === 'string' && error.length > 0) return true
  if (!results || results.profile_required) return false
  return Array.isArray(results.recommendations) && results.recommendations.length === 0
}
