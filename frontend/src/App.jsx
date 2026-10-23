import { NavLink, Navigate, Route, Routes } from 'react-router-dom'
import sampleCampaign from './features/campaigns/fixtures/sample-campaign.json'
import CampaignDashboard from './features/campaigns/CampaignDashboard.jsx'
import { AuthProvider } from './auth/AuthProvider.jsx'
import { AccountWorkspace } from './auth/AccountWorkspace.jsx'
import { useRetailAuth } from './auth/AuthProvider.jsx'

const links = [
  { to: '/', label: 'Overview', end: true },
  { to: '/campaigns', label: 'Campaigns' },
  { to: '/account', label: 'Account' },
]

function Overview() {
  const { client, user } = useRetailAuth()
  const connected = client.configured && Boolean(import.meta.env?.VITE_CAMPAIGN_API_BASE_URL)
  return (
    <>
      <div className="eyebrow">PART 1 · FOUNDATION</div>
      <h1>Campaign workspace</h1>
      <p className="lead">{connected
        ? (user ? 'Connected DEV workspace. Create drafts with your authorized business images; review before downloading.' : 'DEV services configured. Sign in under Account to use real private campaign data.')
        : 'A starting point for creating multi-day social campaigns. Demo-only until live services are configured.'}</p>
      <div className="metrics">
        <div className="metric"><strong>{sampleCampaign.days.length}</strong><span>Mock campaign days</span></div>
        <div className="metric"><strong>2</strong><span>Planned channels</span></div>
        <div className="metric"><strong>30s</strong><span>Reel storyboard target</span></div>
      </div>
      <section className="panel">
        <div className="panel-heading">
          <div><div className="eyebrow">DEVELOPER PREVIEW</div><h2>Shared campaign contract</h2></div>
          <span className="tag">{connected ? 'DEV connected · Fixture illustration' : 'Fixture only'}</span>
        </div>
        <p>The seven-day example follows <code>docs/INTERFACES_V1.md</code>. {connected
          ? 'The sample is illustrative; live drafts, private media, status and signed downloads require sign-in, a valid shop, backend workers and provider configuration. Publishing is not implemented.'
          : 'This overview is a fixture. No remote AI generation, rendering or publishing is connected.'}</p>
        <NavLink className="text-link" to="/campaigns">Inspect sample days →</NavLink>
      </section>
    </>
  )
}

function AppShell() {
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
        <header className="topbar"><span>RetailGrowthAI / Part 1</span><span className="environment">{import.meta.env?.VITE_CAMPAIGN_API_BASE_URL && import.meta.env?.VITE_SUPABASE_PUBLISHABLE_KEY
          ? 'DEV CONNECTED · SIGN IN FOR LIVE DATA' : 'CAMPAIGNS: MOCK · ACCOUNT: CONFIGURABLE'}</span></header>
        <main className="content">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/campaigns" element={<CampaignDashboard />} />
            <Route path="/account" element={<AccountWorkspace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return <AuthProvider><AppShell /></AuthProvider>
}
