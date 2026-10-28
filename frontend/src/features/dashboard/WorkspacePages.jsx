import { Link } from 'react-router-dom'
import { useRetailAuth } from '../../auth/AuthProvider.jsx'
import { Button } from '../../components/ui/button.jsx'
import { Card } from '../../components/ui/card.jsx'
import { Badge } from '../../components/ui/badge.jsx'
import CreativeLaunchpad from './CreativeLaunchpad.jsx'
import {OfflineIntegrationPreview} from './Feature1ReadViews.jsx'

const pages = {
  calendar: {
    eyebrow: 'CAMPAIGN PLANNING', title: 'Campaign calendar',
    summary: 'Plan and review your campaigns in the existing campaign studio.',
    note: 'A cross-campaign calendar API has not been contracted. We do not invent scheduled dates or pretend unqueued drafts are published.',
    actions: [['Open campaign studio', '/campaigns']],
  },
  creative: {
    eyebrow: 'CREATIVE WORKSPACE', title: 'Creative Studio',
    summary: 'Create promotional posters with the existing in-browser poster designer and edit Reel storyboards.',
    note: 'Cloud poster generation status is shown only when the existing campaign studio receives an authorized job response.',
    actions: [['Open poster & video studio', '/campaigns']],
  },
  media: {
    eyebrow: 'PRIVATE ASSETS', title: 'Media library',
    summary: 'Your business images can be uploaded and managed from the existing campaign workflow.',
    note: 'A dedicated tenant-scoped asset-list contract has not been approved. Other businesses’ uploads are never enumerated.',
    actions: [['Open image uploader', '/campaigns'], ['Business profile', '/account']],
  },
  connections: {
    eyebrow: 'SOCIAL CHANNELS', title: 'Connected accounts',
    summary: 'Social authentication and permissions are managed by the separate publishing integration workstream.',
    note: 'Connection status is unavailable in Feature #1 until an authorized per-business read contract is merged. No account is shown as connected by default.',
    actions: [['Review business account', '/account']],
    guide: [
      ['Business authorization', 'A signed-in retailer must select an authorized business. A shop name alone never grants another account access.'],
      ['Official platform consent', 'Instagram, Facebook, LinkedIn and YouTube require their own approved OAuth connection process. No password or access token belongs in this page.'],
      ['Permissions review', 'Connection identity, page/channel scope and revocation must be confirmed by the publishing service before any campaign can be sent.'],
    ],
  },
  publishing: {
    eyebrow: 'DELIVERY WORKFLOW', title: 'Publishing calendar & history',
    summary: 'This workspace will display approved scheduled posts and delivery receipts once a tenant-scoped publishing read contract is integrated.',
    note: 'No posts, followers, reach, or delivery success are assumed. Publishing controls are not enabled from a frontend-only route.',
    actions: [['Review campaign drafts', '/campaigns']],
    guide: [
      ['Approved content', 'Campaign drafts require the retailer to review product claims and authorize the content version before scheduling.'],
      ['Verified scheduled delivery', 'Timezone, business, channel and delivery status must come from authenticated publishing records, not browser-generated dates.'],
      ['Audited results', 'Delivery receipts, failed retries and revocation must be read from the authorized publisher; reach and engagement figures are never estimated.'],
    ],
  },
  notifications: {
    eyebrow: 'RETAILER INBOX', title: 'Notifications',
    summary: 'Workspace notifications will show business-specific job updates when an authorized persistent retailer inbox is available.',
    note: 'The existing persisted notifications RPC is reserved for verified Platform Super Admins, not retailer sessions. Unread counts are unavailable, not zero.',
    actions: [['Check rendering status', '/campaigns']],
    guide: [
      ['Tenant-scoped events', 'Only messages for the authenticated retailer and selected business may appear here. Platform administrator events are separate.'],
      ['Verified delivery status', 'Job failures, completed renders and follow-up actions need persisted, server-authorized records before display.'],
      ['Read state', 'Unread counts and mark-read actions require audited, per-user backend state. No browser-only read status or notification total is claimed.'],
    ],
  },

}

export const WORKSPACE_PAGES = Object.freeze(pages)

export default function WorkspacePage({ section }) {
  const page = pages[section]
  const { user, configured } = useRetailAuth()
  if (section === 'creative') return <CreativeLaunchpad />
  if (!page) return null
  return <div className="rg-workspace-page">
    <div className="page-heading">
      <div><div className="eyebrow">{page.eyebrow}</div><h1>{page.title}</h1>
        <p className="lead">{page.summary}</p></div>
      <Badge className="rg-state-label">{configured && user ? 'Authorized workspace' : 'Demo / setup'}</Badge>
    </div>
    <Card className="panel rg-availability-panel" aria-label={page.title + ' availability'}>
      <span className="rg-availability-mark" aria-hidden="true">◇</span>
      <div><h2>Integration status</h2><p>{page.note}</p>
        <Badge className="rg-state-label">No fabricated live data</Badge>
      </div>
    </Card>
    {page.guide && <Card className="panel rg-integration-guide" aria-label={page.title + ' integration requirements'}>
      <div className="eyebrow">WHAT MUST BE VERIFIED</div>
      <h2>Required before live use</h2>
      <ol className="rg-integration-steps">
        {page.guide.map(([title, description], index) => <li key={title}>
          <span className="rg-integration-number" aria-hidden="true">{index + 1}</span>
          <div><strong>{title}</strong><p>{description}</p></div>
        </li>)}
      </ol>
      <p className="rg-integration-safety" role="status">No connection, message, post, payment or scheduled delivery is created by viewing this guide.</p>
    </Card>}
    {['connections','publishing'].includes(section) && <OfflineIntegrationPreview key={section} section={section} />}
    <Card className="panel rg-next-actions" aria-label="Available actions">
      <h2>Continue working</h2><div className="rg-action-list">
        {page.actions.map(([label, to]) =>
          <Button asChild variant="outline" className="rg-action-tile" key={to}>
            <Link to={to}><span>{label}</span><span aria-hidden="true">→</span></Link>
          </Button>)}
      </div>
    </Card>
  </div>
}
