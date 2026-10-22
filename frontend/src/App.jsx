import { NavLink, Navigate, Route, Routes } from 'react-router-dom'
import sampleCampaign from './features/campaigns/fixtures/sample-campaign.json'
import CampaignDashboard from './features/campaigns/CampaignDashboard.jsx'

const links = [
  { to: '/', label: 'Overview', end: true },
  { to: '/campaigns', label: 'Campaigns' },
  { to: '/account', label: 'Account' },
]

function Overview() {
  return (
    <>
      <div className="eyebrow">PART 1 · FOUNDATION</div>
      <h1>Campaign workspace</h1>
      <p className="lead">A starting point for creating multi-day social campaigns. The live services are not connected yet.</p>
      <div className="metrics">
        <div className="metric"><strong>{sampleCampaign.days.length}</strong><span>Mock campaign days</span></div>
        <div className="metric"><strong>2</strong><span>Planned channels</span></div>
        <div className="metric"><strong>30s</strong><span>Reel storyboard target</span></div>
      </div>
      <section className="panel">
        <div className="panel-heading">
          <div><div className="eyebrow">DEVELOPER PREVIEW</div><h2>Shared campaign contract</h2></div>
          <span className="tag">Fixture only</span>
        </div>
        <p>The seven-day example follows <code>docs/INTERFACES_V1.md</code>. AI generation, rendering, authentication and publishing are not available in this bootstrap.</p>
        <NavLink className="text-link" to="/campaigns">Inspect sample days →</NavLink>
      </section>
    </>
  )
}

function Account() {
  return (
    <>
      <div className="eyebrow">FOUNDATION WORKSTREAM</div>
      <h1>Account</h1>
      <section className="panel">
        <h2>Authentication is not configured</h2>
        <p>This placeholder is reserved for the tenant-safe Supabase authentication workstream. No credentials or live shop data are used.</p>
      </section>
    </>
  )
}

export default function App() {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark">R</div><div><strong>RetailGrowthAI</strong><small>Marketing studio</small></div></div>
        <div className="nav-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.end} className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>{link.label}</NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">Developer bootstrap <span>v0.1</span></div>
      </aside>
      <div className="page">
        <header className="topbar"><span>RetailGrowthAI / Part 1</span><span className="environment">LOCAL MOCK MODE</span></header>
        <main className="content">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/campaigns" element={<CampaignDashboard />} />
            <Route path="/account" element={<Account />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
