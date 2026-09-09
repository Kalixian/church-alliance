import { useEffect, useMemo, useState } from 'react'

const pad = (value) => String(value).padStart(2, '0')
const dayKey = (date) => `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
const startOfDay = (date) => new Date(date.getFullYear(), date.getMonth(), date.getDate())

const parseEventDate = (value, allDay) => {
  if (allDay) {
    const [year, month, day] = value.slice(0, 10).split('-').map(Number)
    return new Date(year, month - 1, day)
  }
  return new Date(value)
}

const formatTime = (event) => {
  if (event.all_day) return 'All day'
  return parseEventDate(event.start_datetime, false).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}

const eventCoversDay = (event, date) => {
  const eventStart = startOfDay(parseEventDate(event.start_datetime, event.all_day))
  const eventEnd = startOfDay(parseEventDate(event.end_datetime, event.all_day))
  const currentDay = startOfDay(date)
  return currentDay >= eventStart && currentDay <= eventEnd
}

const eventSortValue = (event) => parseEventDate(event.start_datetime, event.all_day).getTime()

function CalendarTool({ apiBaseUrl, token, onSelectEvent }) {
  const [displayMonth, setDisplayMonth] = useState(() => new Date(new Date().getFullYear(), new Date().getMonth(), 1))
  const [events, setEvents] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const headers = token ? { Authorization: `Bearer ${token}` } : {}
    setIsLoading(true)
    fetch(`${apiBaseUrl}/api/v1/events/upcoming?include_all=true&skip=0&limit=100`, { headers })
      .then(async (response) => {
        if (!response.ok) throw new Error('Unable to load calendar events.')
        return response.json()
      })
      .then(setEvents)
      .catch((loadError) => {
        setEvents([])
        setError(loadError.message || 'Unable to load calendar events.')
      })
      .finally(() => setIsLoading(false))
  }, [apiBaseUrl, token])

  const calendarDays = useMemo(() => {
    const firstDay = new Date(displayMonth.getFullYear(), displayMonth.getMonth(), 1)
    const gridStart = new Date(displayMonth.getFullYear(), displayMonth.getMonth(), 1 - firstDay.getDay())
    return Array.from({ length: 42 }, (_, index) => new Date(gridStart.getFullYear(), gridStart.getMonth(), gridStart.getDate() + index))
  }, [displayMonth])

  const eventsByDay = useMemo(() => {
    const grouped = new Map()
    for (const date of calendarDays) {
      const dayEvents = events
        .filter((event) => eventCoversDay(event, date))
        .sort((first, second) => eventSortValue(first) - eventSortValue(second))
      grouped.set(dayKey(date), dayEvents)
    }
    return grouped
  }, [calendarDays, events])

  const monthLabel = displayMonth.toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
  const todayKey = dayKey(new Date())

  return (
    <section className="calendar-tool" aria-labelledby="calendar-title">
      <div className="tool-header calendar-header">
        <h3>I just started working on the calendar, please ignore this</h3>
        <div>
          <p className="section-kicker">Schedule</p>
          <h2 id="calendar-title">Calendar</h2>
        </div>
        <div className="calendar-navigation" aria-label="Calendar month navigation">
          <button type="button" aria-label="Previous month" onClick={() => setDisplayMonth((month) => new Date(month.getFullYear(), month.getMonth() - 1, 1))}>Previous</button>
          <strong aria-live="polite">{monthLabel}</strong>
          <button type="button" aria-label="Next month" onClick={() => setDisplayMonth((month) => new Date(month.getFullYear(), month.getMonth() + 1, 1))}>Next</button>
        </div>
      </div>
      {error ? <p className="calendar-message calendar-error">{error}</p> : null}
      {isLoading ? <p className="calendar-message">Loading calendar...</p> : null}
      {!isLoading ? (
        <div className="calendar-grid" role="grid" aria-label={monthLabel}>
          {['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].map((day) => <div className="calendar-weekday" role="columnheader" key={day}>{day.slice(0, 3)}</div>)}
          {calendarDays.map((date) => {
            const dateKey = dayKey(date)
            const isCurrentMonth = date.getMonth() === displayMonth.getMonth()
            const dayEvents = eventsByDay.get(dateKey) || []
            return (
              <div className={`calendar-day ${isCurrentMonth ? '' : 'calendar-day-muted'} ${dateKey === todayKey ? 'calendar-day-today' : ''}`} role="gridcell" key={dateKey}>
                <time dateTime={dateKey} className="calendar-day-number">{date.getDate()}</time>
                <div className="calendar-day-events">
                  {dayEvents.map((event) => (
                    <button type="button" className={`calendar-event ${event.all_day ? 'calendar-event-all-day' : ''}`} key={event.id} onClick={() => onSelectEvent(event.id)} title={`${event.name} - ${formatTime(event)}`}>
                      <span className="calendar-event-time">{formatTime(event)}</span>
                      <span className="calendar-event-name">{event.name}</span>
                    </button>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      ) : null}
    </section>
  )
}

export default CalendarTool
