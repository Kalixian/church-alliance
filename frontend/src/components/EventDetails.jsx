import { useEffect, useState } from 'react'
import DOMPurify from 'dompurify'
import EventEditor from './EventEditor'

const formatDates = (event) => event.all_day
  ? `${new Date(event.start_datetime).toLocaleDateString()}${event.start_datetime.slice(0, 10) === event.end_datetime.slice(0, 10) ? '' : ` - ${new Date(event.end_datetime).toLocaleDateString()}`}`
  : `${new Date(event.start_datetime).toLocaleString()} - ${new Date(event.end_datetime).toLocaleString()}`

function EventDetails({ eventId, apiBaseUrl, token, userRole, authUserId, onBack, onChanged }) {
  const [event, setEvent] = useState(null)
  const [members, setMembers] = useState([])
  const [certifications, setCertifications] = useState([])
  const [coordinators, setCoordinators] = useState([])
  const [isEditing, setIsEditing] = useState(false)
  const [error, setError] = useState('')
  const canManage = userRole === 'administrator' || event?.coordinator?.auth_id === authUserId
  const canRegister = Boolean(token) && userRole !== 'applicant'
  const registered = event?.members?.some((member) => member.auth_id === authUserId)

  const load = async () => {
    const headers = token ? { Authorization: `Bearer ${token}` } : {}
    const response = await fetch(`${apiBaseUrl}/api/v1/events/${eventId}`, { headers })
    if (!response.ok) throw new Error('Unable to load event details.')
    const data = await response.json()
    setEvent(data)
    if (token && userRole !== 'applicant') {
      const membersResponse = await fetch(`${apiBaseUrl}/api/v1/events/${eventId}/members`, { headers })
      if (membersResponse.ok) setMembers(await membersResponse.json())
    }
  }

  useEffect(() => { load().catch((loadError) => setError(loadError.message)) }, [eventId, token, userRole])

  useEffect(() => {
    fetch(`${apiBaseUrl}/api/v1/certifications?skip=0&limit=100`).then((response) => response.ok ? response.json() : []).then(setCertifications)
    if (token && userRole !== 'applicant') {
      const headers = { Authorization: `Bearer ${token}` }
      Promise.all([
        fetch(`${apiBaseUrl}/api/v1/users?role=coordinator&limit=100`, { headers }),
        fetch(`${apiBaseUrl}/api/v1/users?role=administrator&limit=100`, { headers }),
      ]).then(async ([coordinatorResponse, administratorResponse]) => {
        const users = await Promise.all([coordinatorResponse.json(), administratorResponse.json()])
        setCoordinators([...users[0], ...users[1]])
      }).catch(() => setCoordinators([]))
    }
  }, [apiBaseUrl, token, userRole])

  const toggleRegistration = async () => {
    const response = await fetch(`${apiBaseUrl}/api/v1/events/${eventId}/register`, { method: registered ? 'DELETE' : 'POST', headers: { Authorization: `Bearer ${token}` } })
    if (!response.ok) { setError('Unable to update registration.'); return }
    await load()
  }

  const deleteEvent = async () => {
    if (!window.confirm('Delete this event? This action cannot be undone.')) return
    const response = await fetch(`${apiBaseUrl}/api/v1/events/${eventId}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } })
    if (!response.ok) { setError('Unable to delete event.'); return }
    onChanged()
  }

  if (error) return <section className="content-block"><p className="error-message">{error}</p><button type="button" onClick={onBack}>Back to Events</button></section>
  if (!event) return <section className="content-block">Loading event...</section>
  if (isEditing) return <EventEditor event={event} apiBaseUrl={apiBaseUrl} token={token} certifications={certifications} coordinators={coordinators} onSaved={(updated) => { setEvent(updated); setIsEditing(false) }} onCancel={() => setIsEditing(false)} />

  return (
    <section className="event-details main-content">
      <button type="button" className="text-button" onClick={onBack}>Back to Events</button>
      <article className="content-block">
        <h2>{event.name}</h2>
        <p className="event-coordinator">Organized by {[event.coordinator?.first_name, event.coordinator?.last_name].filter(Boolean).join(' ') || 'Unknown coordinator'}{token && userRole !== 'applicant' ? ` (${event.coordinator?.email})` : ''}</p>
        <p className="event-date-detail">{formatDates(event)}</p>
        {event.certification_name ? <p className="event-certification">{event.certification_name}</p> : null}
        <div className="event-description" dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(event.description || '<p>No description provided.</p>') }} />
        {canRegister || canManage ? (
          <div className="event-actions">
            {canRegister ? <button type="button" onClick={toggleRegistration}>{registered ? 'Deregister' : 'Register'}</button> : null}
            {canManage ? <button type="button" onClick={() => setIsEditing(true)}>Edit</button> : null}
            {canManage ? <button type="button" className="danger-button" onClick={deleteEvent}>Delete</button> : null}
          </div>
        ) : null}
      </article>
      {token && userRole !== 'applicant' ? <section className="content-block registered-members"><h3>Registered members</h3>{members.length ? <ul>{members.map((member) => <li key={member.id}>{[member.first_name, member.last_name].filter(Boolean).join(' ') || member.email}</li>)}</ul> : <p>No members have registered yet.</p>}</section> : null}
    </section>
  )
}

export default EventDetails