import { useMemo, useState } from 'react'
import { filterRecommendations, safeEvidence, sourceSummary } from './trend-model.mjs'
import './TrendRecommendations.css'

// Feature-owned, additive component. Coordinator wires route/data to an
// authenticated RLS-backed API; NEVER ingest anonymous tenant profiles here.
export default function TrendRecommendations({
  recommendations = [], sources = [], onDraft = null, now = new Date(),
}) {
  const [category, setCategory] = useState('all')
  const [language, setLanguage] = useState('all')
  const [freshness, setFreshness] = useState('active')
  const [city, setCity] = useState('')
  const rows = useMemo(() => filterRecommendations(recommendations, {
    category, language, freshness, city, now,
  }), [recommendations, category, language, freshness, city, now])
  return (
    <section className="feature2-trends" aria-label="Trend intelligence recommendations">
      <header>
        <div><p className="feature2-eyebrow">RETAIL INTELLIGENCE</p>
          <h2>Recommended content opportunities</h2>
          <p>Evidence-backed ideas for retailer review. Trends do not guarantee popularity or sales.</p></div>
      </header>
      <p role="status" className="feature2-source-status">{sourceSummary(sources)}</p>
      <div className="feature2-filters" aria-label="Filter recommendations">
        <label>Category<select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="all">All categories</option><option value="clothing">Clothing</option>
          <option value="restaurant">Food</option><option value="technology">Technology</option>
          <option value="general">Other</option>
        </select></label>
        <label>Language<select value={language} onChange={(e) => setLanguage(e.target.value)}>
          <option value="all">All languages</option><option value="en-IN">English</option>
          <option value="hi-IN">Hindi</option><option value="mr-IN">Marathi</option>
        </select></label>
        <label>Freshness<select value={freshness} onChange={(e) => setFreshness(e.target.value)}>
          <option value="active">Active evidence only</option>
          <option value="all">Include expired for reference</option>
        </select></label>
        <label>City<input value={city} maxLength={80} placeholder="All cities"
          onChange={(e) => setCity(e.target.value)} /></label>
      </div>
      {!rows.length && <p role="status">No verified recommendations match these filters. Source availability may be incomplete.</p>}
      <div className="feature2-grid">
        {rows.map((item) => (
          <article className="feature2-item" key={item.trend_id}>
            <div className="feature2-item-meta"><span>{item.source === 'google_rss' ? 'Google Trends RSS' :
              item.source === 'youtube' ? 'YouTube mostPopular' : 'Seasonal calendar'}</span>
              <span>Confidence: {item.confidence === 'medium' ? 'Medium' : 'Low'}</span></div>
            <h3>{item.title}</h3>
            <p>{item.why_relevant || 'Relevance review required'}</p>
            <p className="feature2-date">Observed: {item.observed_at} · Expires: {item.expires_at}</p>
            <div className="feature2-item-actions">
              <a href={safeEvidence(item.evidence_url, item.source)} target="_blank" rel="noopener noreferrer">
                Examine source evidence
              </a>
              <button type="button" disabled={typeof onDraft !== 'function'}
                onClick={() => onDraft?.(item)} aria-label={'Draft content for ' + item.title}>
                Create draft for review
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}
