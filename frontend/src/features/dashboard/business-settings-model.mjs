export const PROFILE_FIELDS = Object.freeze([
  { key: 'business_name', label: 'Business name', limit: 140, required: true },
  { key: 'category', label: 'Business category', limit: 100 },
  { key: 'description', label: 'Description', limit: 1500, multiline: true },
  { key: 'brand_voice', label: 'Brand voice', limit: 500, multiline: true },
  { key: 'city', label: 'City', limit: 120 },
  { key: 'website_url', label: 'Website (HTTPS)', limit: 500, kind: 'url' },
  { key: 'contact_email', label: 'Business contact email', limit: 254, kind: 'email' },
])
export function profileDraft(profile) {
  return Object.fromEntries(PROFILE_FIELDS.map(({key})=>[key,
    typeof profile?.[key] === 'string' ? profile[key] : '']))
}
export function profilePatch(original, draft) {
  if (!original || !draft || typeof original !== 'object' || typeof draft !== 'object') {
    throw new Error('A verified business profile is required.')
  }
  const result = {}
  for (const {key, label, limit, required, kind} of PROFILE_FIELDS) {
    const entered = draft[key]
    if (typeof entered !== 'string' || entered.length > limit) {
      throw new Error(label + ' exceeds the allowed length.')
    }
    const value = entered.trim()
    if (required && !value) throw new Error(label + ' is required.')
    if (kind === 'email' && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
      throw new Error('Enter a valid business contact email.')
    }
    if (kind === 'url' && value) {
      let address
      try { address = new URL(value) } catch { throw new Error('Website must be an HTTPS URL.') }
      if (address.protocol !== 'https:' || !address.hostname || address.username || address.password) {
        throw new Error('Website must be an HTTPS URL without embedded credentials.')
      }
    }
    const before = typeof original[key] === 'string' ? original[key].trim() : ''
    // Four text columns are NOT NULL in foundation migration. Only nullable
    // contact_email and website_url may be cleared as SQL NULL.
    if (value !== before) result[key] = value || ((kind === 'email' || kind === 'url') ? null : '')
  }
  return result
}
