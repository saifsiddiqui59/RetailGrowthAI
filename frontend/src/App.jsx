import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { Link, NavLink, Navigate, Route, Routes, useLocation } from 'react-router-dom'

import { AuthProvider, useRetailAuth } from './auth/AuthProvider.jsx'





import LoginPage from './auth/LoginPage.jsx'



import './features/dashboard/dashboard-v2.css'

// Download only the authenticated workspace the user opens. This keeps the
// public login small and avoids loading video editor and Chart.js on entry.
const CampaignDashboard = lazy(() => import('./features/campaigns/CampaignDashboard.jsx'))
const TrendWorkspace = lazy(() => import('./features/trends/TrendWorkspace.jsx'))
const TestingConsole = lazy(() => import('./features/testing/TestingConsole.jsx'))
const AccountWorkspace = lazy(() => import('./auth/AccountWorkspace.jsx').then(m => ({ default: m.AccountWorkspace })))
const DashboardOverview = lazy(() => import('./features/dashboard/DashboardOverview.jsx'))
const SubscriptionPage = lazy(() => import('./features/subscription/SubscriptionPage.jsx'))
const PlatformAdmin = lazy(() => import('./features/platform/PlatformAdmin.jsx'))
const PlatformAlerts = lazy(() => import('./features/platform/PlatformAlerts.jsx'))
const WorkspacePage = lazy(() => import('./features/dashboard/WorkspacePages.jsx'))
const MediaLibrary = lazy(() => import('./features/dashboard/MediaLibrary.jsx'))
const RetailerInbox = lazy(() => import('./features/dashboard/RetailerInbox.jsx'))
const RecentCampaignCalendar = lazy(() => import('./features/dashboard/RecentCampaignCalendar.jsx'))
const BusinessSettings = lazy(() => import('./features/dashboard/BusinessSettings.jsx'))

const links = [
  { to: '/', label: 'Overview', icon: '▦', end: true, group: 'WORKSPACE' },
  { to: '/campaigns', label: 'Campaigns', icon: '▤' },
  { to: '/trends', label: 'Trend Intelligence', icon: '◉', group: 'CREATE & MANAGE' },
  { to: '/testing-chat', label: 'Testing Chat', icon: '⌘', group: 'QUALITY LAB' },
  { to: '/calendar', label: 'Campaign calendar', icon: '▦' },
  { to: '/creative-studio', label: 'Creative Studio', icon: '✧', group: 'CREATE & MANAGE' },
  { to: '/media-library', label: 'Media library', icon: '▧' },
  { to: '/connections', label: 'Social accounts', icon: '◎', group: 'PUBLISH' },
  { to: '/publishing', label: 'Publishing history', icon: '◷' },
  { to: '/subscription', label: 'Subscription', icon: '◈', group: 'ACCOUNT' },
  { to: '/notifications', label: 'My inbox', icon: '◇' },
  { to: '/settings', label: 'Settings', icon: '⚙' },
]

function PlatformBoundary({ children }) {
  const { user, loading, platformLoading, platformAdmin } = useRetailAuth()
  if (loading || platformLoading) return <p role="status">Checking platform authorization…</p>
  if (!user) return <Navigate to="/account" replace />
  if (!platformAdmin) return <section className="panel" aria-label="Platform access denied"><h1>Platform access denied</h1><p>This account does not have a verified Platform Super Admin grant.</p><Link to="/">Return to workspace</Link></section>
  return children || <PlatformAdmin />
}

function AccountMenu() {
  const { user, loading, signOut, platformAdmin } = useRetailAuth()
  const [open, setOpen] = useState(false)
  const [error, setError] = useState('')
  const ref = useRef(null)
  const location = useLocation()

  useEffect(() => { setOpen(false) }, [location.pathname])
  useEffect(() => {
    const dismiss = (event) => { if (!ref.current?.contains(event.target)) setOpen(false) }
    const escape = (event) => { if (event.key === 'Escape') setOpen(false) }
    document.addEventListener('pointerdown', dismiss)
    document.addEventListener('keydown', escape)
    return () => {
      document.removeEventListener('pointerdown', dismiss)
      document.removeEventListener('keydown', escape)
    }
  }, [])

  if (loading) return <span className="topbar-session" role="status">Checking session…</span>
  if (!user) return <Link className="topbar-signin" to="/account">Sign in / Create account</Link>

  const initials = (user.email || 'U').slice(0, 1).toUpperCase()
  return (
    <div className="account-menu" ref={ref}>
      <button type="button" className="account-trigger" onClick={() => setOpen(!open)}
        aria-label="Open account menu" aria-haspopup="menu" aria-expanded={open}>
        <span className="avatar" aria-hidden="true">{initials}</span>
        <span className="account-trigger-copy"><strong>My account</strong><small>{user.email}</small></span>
        <span aria-hidden="true">⌄</span>
      </button>
      {open && <div className="account-popover" role="menu" aria-label="Account options">
        <div className="account-popover-heading"><strong>Signed in</strong><span>{user.email}</span></div>
        <Link role="menuitem" to="/account" onClick={() => setOpen(false)}>Business account &amp; profile</Link>
        <Link role="menuitem" to="/subscription" onClick={() => setOpen(false)}>Plan &amp; usage</Link>
        {platformAdmin && <Link role="menuitem" to="/platform-admin" onClick={() => setOpen(false)}>Platform Control</Link>}
        {platformAdmin && <Link role="menuitem" to="/platform-alerts" onClick={() => setOpen(false)}>Notifications &amp; alerts</Link>}
        <button type="button" role="menuitem" onClick={async () => {
          try {
            setError('')
            await signOut()
            setOpen(false)
          } catch {
            setError('Unable to sign out. Please try again.')
          }
        }}>Sign out</button>
        {error && <p role="alert">{error}</p>}
      </div>}
    </div>
  )
}

function AppShell() {
  const location = useLocation()
  const { platformAdmin, platformLoading, user, loading, configured, recoveryMode } = useRetailAuth()
  const [collapsed, setCollapsed] = useState(() => {
    try { return window.localStorage.getItem('rgai-sidebar-collapsed') === '1' } catch { return false }
  })
  const [mobileOpen, setMobileOpen] = useState(false)
  const [theme, setTheme] = useState(() => {
    try { return window.localStorage.getItem('rgai-theme') === 'dark' ? 'dark' : 'light' }
    catch { return 'light' }
  })
  useEffect(() => {
    document.documentElement.dataset.rgTheme = theme
    try { window.localStorage.setItem('rgai-theme', theme) } catch { /* storage unavailable */ }
    return () => { delete document.documentElement.dataset.rgTheme }
  }, [theme])

  useEffect(() => {
    try { window.localStorage.setItem('rgai-sidebar-collapsed', collapsed ? '1' : '0') } catch { /* storage unavailable */ }
  }, [collapsed])
  useEffect(() => { setMobileOpen(false) }, [location.pathname])
  useEffect(() => {
    const escape = (event) => { if (event.key === 'Escape') setMobileOpen(false) }
    window.addEventListener('keydown', escape)
    return () => window.removeEventListener('keydown', escape)
  }, [])

  if (configured && loading) return <div className="login-loading" role="status">Checking your session…</div>
  if (configured && !user) {
    if (location.pathname !== '/' && location.pathname !== '/account') return <Navigate to="/account" replace />
    return <LoginPage />
  }
  // A verified recovery token must only render password reset, not business/root UI.
  if (configured && recoveryMode) return <LoginPage />
  if (configured && platformLoading) return <div className="login-loading" role="status">Verifying dashboard access…</div>
  const availableLinks = platformAdmin
    ? [{ to: '/platform-admin', label: 'Platform Control', icon: '⚙', group: 'PLATFORM' },
        { to: '/platform-alerts', label: 'Notifications', icon: '◇' },
        { to: '/business', label: 'My business', icon: '▦', group: 'WORKSPACE' },
        ...links.filter(item => item.to !== '/' && item.to !== '/notifications')]
    : links
  const title = availableLinks.find((item) => item.to === location.pathname)?.label ||
    (location.pathname === '/account' ? 'Account' : 'Workspace')
  return (
    <div className={'shell retail-shell' + (collapsed ? ' sidebar-collapsed' : '') + (mobileOpen ? ' mobile-open' : '')}>
      <aside className="sidebar" aria-label="Workspace sidebar">
        <Link to="/" className="brand brand-link">
          <span className="brand-mark" aria-hidden="true">R</span>
          <span className="brand-copy"><strong>RetailGrowthAI</strong><small>Marketing studio</small></span>
        </Link>
        <nav aria-label="Main navigation">
          {availableLinks.map((link) => (
            <div className="rg-nav-group" key={link.to}>
              {link.group && <span className="rg-nav-section">{link.group}</span>}
              <NavLink to={link.to} end={link.end}
                aria-label={link.label}
                title={collapsed ? link.label : undefined}
                className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
                <span className="nav-glyph" aria-hidden="true">{link.icon}</span><span className="nav-text">{link.label}</span>
              </NavLink>
            </div>
          ))}
        </nav>
        <div className="sidebar-bottom"><span className="sidebar-caption">RetailGrowthAI DEV</span>
          <button type="button" className="collapse-toggle"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-expanded={!collapsed}
            onClick={() => setCollapsed(!collapsed)}>
            <span aria-hidden="true">{collapsed ? '»' : '«'}</span><span className="collapse-text">{collapsed ? '' : 'Collapse'}</span>
          </button>
        </div>
      </aside>
      {mobileOpen && <button type="button" className="sidebar-backdrop"
        aria-label="Close navigation" onClick={() => setMobileOpen(false)} />}
      <div className="page">
        <header className="topbar">
          <div className="topbar-context">
            <button type="button" className="mobile-nav-toggle" aria-label="Toggle navigation"
              aria-expanded={mobileOpen} onClick={() => setMobileOpen(!mobileOpen)}>☰</button>
            <div><span className="topbar-kicker">RETAILGROWTHAI / DEV</span><strong>{title}</strong></div>
          </div>
          <div className="topbar-right">
            <button className="rg-theme-button" type="button" onClick={() => setTheme(value => value === 'dark' ? 'light' : 'dark')}
              aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              aria-pressed={theme === 'dark'}><span aria-hidden="true">{theme === 'dark' ? '☀' : '☾'}</span><span className="rg-theme-copy">{theme === 'dark' ? 'Light' : 'Dark'}</span></button>
            <span className="environment">{import.meta.env?.VITE_CAMPAIGN_API_BASE_URL && import.meta.env?.VITE_SUPABASE_PUBLISHABLE_KEY
              ? 'API configured' : configured && user ? 'Supabase only' : 'Demo / setup'}</span>
            <AccountMenu />
          </div>
        </header>
        <main className="content">
          <Suspense fallback={<div className="rg-route-loading" role="status">Loading workspace…</div>}>
          <Routes>
            <Route path="/" element={platformAdmin ? <Navigate to="/platform-admin" replace /> : <DashboardOverview />} />
            <Route path="/business" element={<DashboardOverview />} />
            <Route path="/campaigns" element={<CampaignDashboard />} />
            <Route path="/trends" element={<TrendWorkspace />} />
            <Route path="/testing-chat" element={<TestingConsole />} />
            <Route path="/subscription" element={<SubscriptionPage />} />
            <Route path="/calendar" element={<RecentCampaignCalendar />} />
            <Route path="/creative-studio" element={<WorkspacePage section="creative" />} />
            <Route path="/media-library" element={<MediaLibrary />} />
            <Route path="/connections" element={<WorkspacePage section="connections" />} />
            <Route path="/publishing" element={<WorkspacePage section="publishing" />} />
            <Route path="/notifications" element={<RetailerInbox />} />
            <Route path="/settings" element={<BusinessSettings />} />
            <Route path="/platform-admin" element={<PlatformBoundary />} />
            <Route path="/platform-alerts" element={<PlatformBoundary><PlatformAlerts /></PlatformBoundary>} />
            <Route path="/account" element={<AccountWorkspace />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          </Suspense>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return <AuthProvider><AppShell /></AuthProvider>
}
