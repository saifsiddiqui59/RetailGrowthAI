// Read-only UI guidance derived from a single RLS-protected business profile.
// This is NOT a hosted generation, publishing, or onboarding approval status.
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const value = input => typeof input === 'string' ? input.trim() : ''

export function validatedCreativeProfile(profile, shopId) {
  if (!UUID.test(shopId || '') || !profile ||
      typeof profile !== 'object' || Array.isArray(profile) ||
      profile.shop_id !== shopId) return null
  return profile
}

export function creativeReadiness(profile, shopId) {
  const scoped = validatedCreativeProfile(profile, shopId)
  if (!scoped) return null
  const checks = [
    { key: 'name', label: 'Business name', satisfied: value(scoped.business_name).length > 0,
      guidance: 'Add your storefront name to identify who the content represents.' },
    { key: 'category', label: 'Retail category', satisfied: value(scoped.category).length > 0 &&
      !['other', 'unknown', 'uncategorized'].includes(value(scoped.category).toLowerCase()),
      guidance: 'Set a specific retail category so trend ideas fit the business.' },
    { key: 'city', label: 'Business city', satisfied: value(scoped.city).length > 0,
      guidance: 'Provide your city for local festival and regional marketing context.' },
    { key: 'description', label: 'Business description', satisfied: value(scoped.description).length >= 20,
      guidance: 'Describe your actual products and intended customers (at least 20 characters).' },
    { key: 'voice', label: 'Brand voice', satisfied: value(scoped.brand_voice).length >= 3,
      guidance: 'Set the tone to keep suggested captions consistent with your brand.' },
  ]
  return { checks, completed: checks.filter(item => item.satisfied).length, total: checks.length }
}
