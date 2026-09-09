import { useEffect, useRef, useState } from 'react'
import DOMPurify from 'dompurify'

const pageSize = 5

const parseCalendarDate = (value) => {
  const [year, month, day] = value.slice(0, 10).split('-').map(Number)
  return new Date(year, month - 1, day)
}

const formatEventDates = (event) => {
  const start = event.all_day ? parseCalendarDate(event.start_datetime) : new Date(event.start_datetime)
  const end = event.all_day ? parseCalendarDate(event.end_datetime) : new Date(event.end_datetime)
  const dateOptions = { dateStyle: 'medium' }

  if (event.all_day) {
    if (start.toDateString() === end.toDateString()) {
      return start.toLocaleDateString(undefined, dateOptions)
    }
    return `${start.toLocaleDateString(undefined, dateOptions)} - ${end.toLocaleDateString(undefined, dateOptions)}`
  }

  const dateTimeOptions = { dateStyle: 'medium', timeStyle: 'short' }
  return `${start.toLocaleString(undefined, dateTimeOptions)} - ${end.toLocaleString(undefined, dateTimeOptions)}`
}

function EventsTool({ apiBaseUrl, token, userRole, authUserId, onSelectEvent }) {
  const [events, setEvents] = useState([])
  const [totalEvents, setTotalEvents] = useState(0)
  const [page, setPage] = useState(0)
  const [search, setSearch] = useState('')
  const [showAllEvents, setShowAllEvents] = useState(false)
  const [certifications, setCertifications] = useState([])
  const [certificationId, setCertificationId] = useState('')
  const [isSearchOptionsVisible, setIsSearchOptionsVisible] = useState(false)
  const [isCreateFormVisible, setIsCreateFormVisible] = useState(false)
  const [editingEventId, setEditingEventId] = useState(null)
  const [newEventName, setNewEventName] = useState('')
  const [newEventDescription, setNewEventDescription] = useState('')
  const [newEventAllDay, setNewEventAllDay] = useState(true)
  const [newEventStart, setNewEventStart] = useState('')
  const [newEventEnd, setNewEventEnd] = useState('')
  const [coordinators, setCoordinators] = useState([])
  const [newEventCoordinatorId, setNewEventCoordinatorId] = useState('')
  const [newEventCertificationId, setNewEventCertificationId] = useState('')
  const [isSavingEvent, setIsSavingEvent] = useState(false)
  const [eventsRefreshKey, setEventsRefreshKey] = useState(0)
  const descriptionEditorRef = useRef(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const canCreateEvents = userRole === 'administrator' || userRole === 'coordinator'
  const canRegister = Boolean(token) && userRole !== 'applicant'

  useEffect(() => {
    const fetchEvents = async () => {
      setIsLoading(true)
      setError('')

      try {
        const query = new URLSearchParams({
          skip: String(page * pageSize),
          limit: String(pageSize),
          search,
          include_all: String(showAllEvents),
        })
        if (certificationId) query.set('certification_id', certificationId)
        const countQuery = new URLSearchParams({
          search,
          include_all: String(showAllEvents),
        })
        if (certificationId) countQuery.set('certification_id', certificationId)
        const [eventsResponse, countResponse] = await Promise.all([
          fetch(`${apiBaseUrl}/api/v1/events/upcoming?${query}`, {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
          }),
          fetch(`${apiBaseUrl}/api/v1/events/upcoming/count?${countQuery}`),
        ])

        if (!eventsResponse.ok) {
          throw new Error('Unable to load upcoming events.')
        }
        if (!countResponse.ok) {
          throw new Error('Unable to load the event count.')
        }

        setEvents(await eventsResponse.json())
        setTotalEvents(await countResponse.json())
      } catch (loadError) {
        setError(loadError.message || 'Unable to load upcoming events.')
      } finally {
        setIsLoading(false)
      }
    }

    fetchEvents()
  }, [apiBaseUrl, page, search, showAllEvents, certificationId, eventsRefreshKey, token, userRole])

  useEffect(() => {
    fetch(`${apiBaseUrl}/api/v1/certifications?skip=0&limit=100`)
      .then((response) => response.ok ? response.json() : [])
      .then((data) => setCertifications(data))
      .catch(() => setCertifications([]))
  }, [apiBaseUrl])

  useEffect(() => {
    if (!token || !canCreateEvents) {
      setCoordinators([])
      setNewEventCoordinatorId('')
      return
    }

    const headers = { Authorization: `Bearer ${token}` }
    Promise.all([
      fetch(`${apiBaseUrl}/api/v1/users?role=coordinator&limit=100`, { headers }),
      fetch(`${apiBaseUrl}/api/v1/users?role=administrator&limit=100`, { headers }),
    ])
      .then(async ([coordinatorResponse, administratorResponse]) => {
        if (!coordinatorResponse.ok || !administratorResponse.ok) {
          throw new Error('Unable to load event coordinators.')
        }
        const users = await Promise.all([
          coordinatorResponse.json(),
          administratorResponse.json(),
        ])
        const availableCoordinators = [...users[0], ...users[1]]
          .sort((first, second) => (first.last_name || first.email).localeCompare(second.last_name || second.email))
        setCoordinators(availableCoordinators)
        const currentUser = availableCoordinators.find((user) => user.auth_id === authUserId)
        setNewEventCoordinatorId(currentUser?.id || availableCoordinators[0]?.id || '')
      })
      .catch(() => {
        setCoordinators([])
        setNewEventCoordinatorId('')
      })
  }, [apiBaseUrl, authUserId, token, userRole])

  const pageCount = Math.max(1, Math.ceil(totalEvents / pageSize))

  const resetEventForm = () => {
    setEditingEventId(null)
    setNewEventName('')
    setNewEventDescription('')
    setNewEventAllDay(true)
    setNewEventStart('')
    setNewEventEnd('')
    const currentCoordinator = coordinators.find((user) => user.auth_id === authUserId)
    setNewEventCoordinatorId(currentCoordinator?.id || coordinators[0]?.id || '')
    setNewEventCertificationId('')
    if (descriptionEditorRef.current) {
      descriptionEditorRef.current.innerHTML = ''
    }
  }

  const beginEditEvent = (event) => {
    setEditingEventId(event.id)
    setIsCreateFormVisible(true)
    setNewEventName(event.name)
    setNewEventDescription(event.description || '')
    setNewEventAllDay(event.all_day)
    setNewEventStart(event.all_day ? event.start_datetime.slice(0, 10) : event.start_datetime.slice(0, 16))
    setNewEventEnd(event.all_day ? event.end_datetime.slice(0, 10) : event.end_datetime.slice(0, 16))
    setNewEventCoordinatorId(event.coordinator_id)
    setNewEventCertificationId(event.certification_id || '')
    setTimeout(() => {
      if (descriptionEditorRef.current) descriptionEditorRef.current.innerHTML = event.description || ''
    }, 0)
  }

  const formatDescription = (command) => {
    descriptionEditorRef.current?.focus()
    document.execCommand(command)
    setNewEventDescription(descriptionEditorRef.current?.innerHTML || '')
  }

  const createNewEvent = async (event) => {
    event.preventDefault()
    setIsSavingEvent(true)
    setError('')

    try {
      const payload = {
        name: newEventName.trim(),
        description: newEventDescription.trim() || null,
        start_datetime: newEventStart,
        end_datetime: newEventEnd,
        all_day: newEventAllDay,
        certification_id: newEventCertificationId || null,
        coordinator_id: newEventCoordinatorId,
      }
      const response = await fetch(
        editingEventId ? `${apiBaseUrl}/api/v1/events/${editingEventId}` : `${apiBaseUrl}/api/v1/events`,
        {
        method: editingEventId ? 'PATCH' : 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })
      if (!response.ok) {
        const responseError = await response.json().catch(() => ({}))
        throw new Error(responseError.detail || 'Unable to create event.')
      }

      resetEventForm()
      setIsCreateFormVisible(false)
      setPage(0)
      setShowAllEvents(false)
      setSearch('')
      setCertificationId('')
      setEventsRefreshKey((key) => key + 1)
    } catch (createError) {
      setError(createError.message || 'Unable to create event.')
    } finally {
      setIsSavingEvent(false)
    }
  }

  const deleteEvent = async (eventId) => {
    if (!window.confirm('Delete this event? This action cannot be undone.')) return
    setError('')
    const response = await fetch(`${apiBaseUrl}/api/v1/events/${eventId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!response.ok) {
      const responseError = await response.json().catch(() => ({}))
      setError(responseError.detail || 'Unable to delete event.')
      return
    }
    setEvents((currentEvents) => currentEvents.filter((event) => event.id !== eventId))
    setTotalEvents((count) => Math.max(0, count - 1))
  }

  const toggleRegistration = async (event) => {
    const registered = event.members?.some((member) => member.auth_id === authUserId)
    const response = await fetch(`${apiBaseUrl}/api/v1/events/${event.id}/register`, {
      method: registered ? 'DELETE' : 'POST',
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!response.ok) {
      const responseError = await response.json().catch(() => ({}))
      setError(responseError.detail || 'Unable to update event registration.')
      return
    }
    setEvents((currentEvents) => currentEvents.map((currentEvent) => {
      if (currentEvent.id !== event.id) return currentEvent
      const members = currentEvent.members || []
      return {
        ...currentEvent,
        members: registered
          ? members.filter((member) => member.auth_id !== authUserId)
          : [...members, { id: authUserId, auth_id: authUserId }],
      }
    }))
  }

  return (
    <section className="main-content events-tool" aria-live="polite" aria-labelledby="events-title">
      <div className="tool-header">
        <div>
          <h2 id="events-title">Events</h2>
        </div>
        <div className="events-header-actions">
          <span className="tool-count">{totalEvents} events</span>
          {canCreateEvents ? (
            <button
              type="button"
              className="new-event-button"
              aria-expanded={isCreateFormVisible}
              onClick={() => setIsCreateFormVisible((visible) => !visible)}
            >
              {isCreateFormVisible ? 'Cancel' : '+ New Event'}
            </button>
          ) : null}
        </div>
      </div>

      {isCreateFormVisible ? (
        <form className="new-event-form content-block" onSubmit={createNewEvent}>
          <h3>{editingEventId ? 'Edit Event' : 'New Event'}</h3>
          <label>
            <span>Title</span>
            <input value={newEventName} onChange={(event) => setNewEventName(event.target.value)} maxLength={255} required />
          </label>
          <label>
            <span>Rich text description</span>
            <div className="rich-text-editor">
              <div className="rich-text-toolbar" role="toolbar" aria-label="Description formatting">
                <button type="button" onClick={() => formatDescription('bold')} aria-label="Bold">B</button>
                <button type="button" onClick={() => formatDescription('italic')} aria-label="Italic"><em>I</em></button>
                <button type="button" onClick={() => formatDescription('insertUnorderedList')} aria-label="Bullet list">List</button>
              </div>
              <div
                ref={descriptionEditorRef}
                className="rich-text-input"
                contentEditable
                role="textbox"
                aria-multiline="true"
                onInput={(event) => setNewEventDescription(event.currentTarget.innerHTML)}
                data-placeholder="Describe the event..."
              />
            </div>
          </label>
          <label className="event-form-checkbox">
            <input type="checkbox" checked={newEventAllDay} onChange={(event) => setNewEventAllDay(event.target.checked)} />
            <span>All-day event</span>
          </label>
          <div className="event-date-fields">
            <label>
              <span>{newEventAllDay ? 'Start date' : 'Starts'}</span>
              <input type={newEventAllDay ? 'date' : 'datetime-local'} value={newEventStart} onChange={(event) => setNewEventStart(event.target.value)} required />
            </label>
            <label>
              <span>{newEventAllDay ? 'End date' : 'Ends'}</span>
              <input type={newEventAllDay ? 'date' : 'datetime-local'} value={newEventEnd} onChange={(event) => setNewEventEnd(event.target.value)} required />
            </label>
          </div>
          <label>
            <span>Coordinator</span>
            <select
              value={newEventCoordinatorId}
              onChange={(event) => setNewEventCoordinatorId(event.target.value)}
              required
            >
              {coordinators.map((coordinator) => (
                <option key={coordinator.id} value={coordinator.id}>
                  {coordinator.first_name || coordinator.last_name
                    ? `${coordinator.first_name || ''} ${coordinator.last_name || ''}`.trim()
                    : coordinator.email}
                  {' '}({coordinator.role})
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Certification (optional)</span>
            <select value={newEventCertificationId} onChange={(event) => setNewEventCertificationId(event.target.value)}>
              <option value="">No certification</option>
              {certifications.map((certification) => (
                <option key={certification.id} value={certification.id}>{certification.name}</option>
              ))}
            </select>
          </label>
          <button type="submit" disabled={isSavingEvent}>{isSavingEvent ? 'Saving...' : editingEventId ? 'Save Event' : 'Create Event'}</button>
        </form>
      ) : null}

      <button
        type="button"
        className="search-options-toggle"
        aria-expanded={isSearchOptionsVisible}
        onClick={() => setIsSearchOptionsVisible((visible) => !visible)}
      >
        {isSearchOptionsVisible ? 'Hide Search Options' : 'Show Search Options'}
      </button>

      {isSearchOptionsVisible ? (
        <div className="events-controls content-block">
          <div className="events-controls-top-row">
            <label className="event-search-field">
              <span>Search events</span>
              <input
                type="search"
                value={search}
                placeholder="Search by title"
                onChange={(event) => {
                  setSearch(event.target.value)
                  setPage(0)
                }}
              />
            </label>
          </div>
          <div className="events-controls-second-row">
            <label className="event-certification-field">
              <span>Search by certification</span>
              <select
                value={certificationId}
                onChange={(event) => {
                  setCertificationId(event.target.value)
                  setPage(0)
                }}
              >
                <option value="">All certifications</option>
                {certifications.map((certification) => (
                  <option key={certification.id} value={certification.id}>{certification.name}</option>
                ))}
              </select>
            </label>
            <label className="event-checkbox-field">
              <input
                type="checkbox"
                checked={showAllEvents}
                onChange={(event) => {
                  setShowAllEvents(event.target.checked)
                  setPage(0)
                }}
              />
              <span>Show past events</span>
            </label>
          </div>
        </div>
      ) : null}

      {error ? <p className="error-message">{error}</p> : null}

      {isLoading ? <p className="content-block">Loading events...</p> : null}
      {!isLoading && events.length === 0 ? <p className="content-block">No upcoming events.</p> : null}
      <div className="events-list">
        {events.map((event) => (
          <article
            key={event.id}
            className="event-card content-block"
            role="button"
            tabIndex="0"
            onClick={() => onSelectEvent(event.id)}
            onKeyDown={(keyboardEvent) => {
              if (keyboardEvent.key === 'Enter' || keyboardEvent.key === ' ') {
                keyboardEvent.preventDefault()
                onSelectEvent(event.id)
              }
            }}
          >
            <div className="event-card-header">
              <div>
                <h3>{event.name}</h3>
                {event.coordinator ? (
                  <p className="event-coordinator">
                    Organized by {[event.coordinator.first_name, event.coordinator.last_name].filter(Boolean).join(' ') || 'Unknown coordinator'}
                    {token && userRole !== 'applicant' ? ` (${event.coordinator.email})` : ''}
                  </p>
                ) : null}
                {event.certification_name ? (
                  <p className="event-certification">{event.certification_name}</p>
                ) : null}
              </div>
              <time dateTime={event.start_datetime}>{formatEventDates(event)}</time>
            </div>
            <div
              className="event-description event-description-preview"
              dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(event.description || '<p>No description provided.</p>') }}
            />
          </article>
        ))}
      </div>

      {totalEvents > 0 ? (
        <div className="pagination-controls">
          <button type="button" onClick={() => setPage((currentPage) => currentPage - 1)} disabled={page === 0 || isLoading}>
            Previous
          </button>
          <span>Page {page + 1} of {pageCount}</span>
          <button type="button" onClick={() => setPage((currentPage) => currentPage + 1)} disabled={page + 1 >= pageCount || isLoading}>
            Next
          </button>
        </div>
      ) : null}
    </section>
  )
}

export default EventsTool