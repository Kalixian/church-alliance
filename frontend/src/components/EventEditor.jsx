import { useEffect, useRef, useState } from 'react'

function EventEditor({ event, apiBaseUrl, token, certifications, coordinators, onSaved, onCancel }) {
  const [name, setName] = useState(event?.name || '')
  const [description, setDescription] = useState(event?.description || '')
  const [allDay, setAllDay] = useState(event?.all_day ?? true)
  const [start, setStart] = useState(event ? (event.all_day ? event.start_datetime.slice(0, 10) : event.start_datetime.slice(0, 16)) : '')
  const [end, setEnd] = useState(event ? (event.all_day ? event.end_datetime.slice(0, 10) : event.end_datetime.slice(0, 16)) : '')
  const [coordinatorId, setCoordinatorId] = useState(event?.coordinator_id || '')
  const [certificationId, setCertificationId] = useState(event?.certification_id || '')
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')
  const editorRef = useRef(null)

  useEffect(() => {
    if (editorRef.current) editorRef.current.innerHTML = description
  }, [event, description])

  const formatDescription = (command) => {
    editorRef.current?.focus()
    document.execCommand(command)
    setDescription(editorRef.current?.innerHTML || '')
  }

  const submit = async (submitEvent) => {
    submitEvent.preventDefault()
    setIsSaving(true)
    setError('')
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/events/${event.id}`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name.trim(),
          description: description.trim() || null,
          start_datetime: start,
          end_datetime: end,
          all_day: allDay,
          coordinator_id: coordinatorId,
          certification_id: certificationId || null,
        }),
      })
      if (!response.ok) {
        const responseError = await response.json().catch(() => ({}))
        throw new Error(responseError.detail || 'Unable to save event.')
      }
      onSaved(await response.json())
    } catch (saveError) {
      setError(saveError.message || 'Unable to save event.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <form className="new-event-form content-block" onSubmit={submit}>
      <h3>Edit Event</h3>
      {error ? <p className="error-message">{error}</p> : null}
      <label><span>Title</span><input value={name} onChange={(e) => setName(e.target.value)} maxLength={255} required /></label>
      <label>
        <span>Rich text description</span>
        <div className="rich-text-editor">
          <div className="rich-text-toolbar" role="toolbar" aria-label="Description formatting">
            <button type="button" onClick={() => formatDescription('bold')}>B</button>
            <button type="button" onClick={() => formatDescription('italic')}><em>I</em></button>
            <button type="button" onClick={() => formatDescription('insertUnorderedList')}>List</button>
          </div>
          <div ref={editorRef} className="rich-text-input" contentEditable role="textbox" aria-multiline="true" onInput={(e) => setDescription(e.currentTarget.innerHTML)} data-placeholder="Describe the event..." />
        </div>
      </label>
      <label className="event-form-checkbox"><input type="checkbox" checked={allDay} onChange={(e) => setAllDay(e.target.checked)} /><span>All-day event</span></label>
      <div className="event-date-fields">
        <label><span>{allDay ? 'Start date' : 'Starts'}</span><input type={allDay ? 'date' : 'datetime-local'} value={start} onChange={(e) => setStart(e.target.value)} required /></label>
        <label><span>{allDay ? 'End date' : 'Ends'}</span><input type={allDay ? 'date' : 'datetime-local'} value={end} onChange={(e) => setEnd(e.target.value)} required /></label>
      </div>
      <label><span>Coordinator</span><select value={coordinatorId} onChange={(e) => setCoordinatorId(e.target.value)} required>{coordinators.map((coordinator) => <option key={coordinator.id} value={coordinator.id}>{coordinator.first_name || coordinator.last_name ? `${coordinator.first_name || ''} ${coordinator.last_name || ''}`.trim() : coordinator.email} ({coordinator.role})</option>)}</select></label>
      <label><span>Certification (optional)</span><select value={certificationId} onChange={(e) => setCertificationId(e.target.value)}><option value="">No certification</option>{certifications.map((certification) => <option key={certification.id} value={certification.id}>{certification.name}</option>)}</select></label>
      <div className="form-actions"><button type="submit" disabled={isSaving}>{isSaving ? 'Saving...' : 'Save Event'}</button><button type="button" className="secondary-button" onClick={onCancel}>Cancel</button></div>
    </form>
  )
}

export default EventEditor