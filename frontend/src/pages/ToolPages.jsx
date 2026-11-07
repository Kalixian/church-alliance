// Route wrappers for the app tools: each puts the static site's page banner
// above an existing tool and supplies its props from the auth context.
import { useLocation, useNavigate, useParams } from 'react-router'
import { useAuth } from '../auth/authContext'
import ApplicationsTool from '../components/ApplicationsTool'
import ArticlesTool from '../components/ArticlesTool'
import CalendarTool from '../components/CalendarTool'
import EventDetails from '../components/EventDetails'
import EventsTool from '../components/EventsTool'
import GalleryTool from '../components/GalleryTool'
import MembersTool from '../components/MembersTool'
import PageBanner from '../components/layout/PageBanner'

export function ToolPage({ eyebrow, title, intro, children }) {
  return (
    <>
      <PageBanner eyebrow={eyebrow} title={title}>{intro}</PageBanner>
      <div className="band">
        <div className="tool-page">{children}</div>
      </div>
    </>
  )
}

export function EventsPage() {
  const { apiBaseUrl, token, userRole, authUserId } = useAuth()
  const navigate = useNavigate()

  return (
    <ToolPage eyebrow="Get involved" title="Events" intro="Deployments, training classes, and special events across the Alliance.">
      <EventsTool
        apiBaseUrl={apiBaseUrl}
        token={token}
        userRole={userRole}
        authUserId={authUserId}
        onSelectEvent={(eventId) => navigate(`/events/${eventId}`)}
      />
    </ToolPage>
  )
}

export function EventDetailPage() {
  const { apiBaseUrl, token, userRole, authUserId } = useAuth()
  const { eventId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  // The calendar links here too; go back to wherever the visitor came from.
  const backTo = location.state?.from || '/events'

  return (
    <ToolPage eyebrow="Get involved" title="Events">
      <EventDetails
        key={eventId}
        eventId={eventId}
        apiBaseUrl={apiBaseUrl}
        token={token}
        userRole={userRole}
        authUserId={authUserId}
        onBack={() => navigate(backTo)}
        onChanged={() => navigate(backTo)}
      />
    </ToolPage>
  )
}

export function CalendarPage() {
  const { apiBaseUrl, token } = useAuth()
  const navigate = useNavigate()

  return (
    <ToolPage eyebrow="Get involved" title="Calendar">
      <CalendarTool
        apiBaseUrl={apiBaseUrl}
        token={token}
        onSelectEvent={(eventId) => navigate(`/events/${eventId}`, { state: { from: '/calendar' } })}
      />
    </ToolPage>
  )
}

export function NewsPage() {
  const { apiBaseUrl, token, userRole, backendUserId } = useAuth()

  return (
    <ToolPage eyebrow="Updates and stories" title="News">
      <ArticlesTool apiBaseUrl={apiBaseUrl} token={token} userRole={userRole} backendUserId={backendUserId} />
    </ToolPage>
  )
}

export function GalleryPage() {
  const { apiBaseUrl, token, userRole, backendUserId } = useAuth()

  return (
    <ToolPage eyebrow="Photo archive" title="Gallery">
      <GalleryTool apiBaseUrl={apiBaseUrl} token={token} userRole={userRole} backendUserId={backendUserId} />
    </ToolPage>
  )
}

export function MembersPage() {
  const { apiBaseUrl, token, authUserId, isAdmin } = useAuth()

  return (
    <ToolPage eyebrow="Members area" title="Members">
      <MembersTool token={token} authUserId={authUserId} apiBaseUrl={apiBaseUrl} canEditRoles={isAdmin} />
    </ToolPage>
  )
}

export function ApplicationsPage() {
  const { apiBaseUrl, token, authUserId } = useAuth()
  const navigate = useNavigate()

  return (
    <ToolPage eyebrow="Admin" title="Site Access Applications">
      <ApplicationsTool token={token} authUserId={authUserId} apiBaseUrl={apiBaseUrl} onBack={() => navigate('/admin')} />
    </ToolPage>
  )
}
