import { useId, useState } from 'react'

// Add/edit form for a course (a certification in the API). The parent does the request.
function CourseForm({ course, isSaving, onSave, onDelete, onCancel }) {
  const [name, setName] = useState(course?.name || '')
  const [description, setDescription] = useState(course?.description || '')
  const [error, setError] = useState('')
  const id = useId()

  const submit = async (event) => {
    event.preventDefault()
    if (!name.trim()) {
      setError('Course name is required.')
      return
    }
    setError('')
    try {
      await onSave({ name: name.trim(), description: description.trim() || null })
    } catch (saveError) {
      setError(saveError.message || 'Unable to save course.')
    }
  }

  const remove = async () => {
    setError('')
    try {
      await onDelete()
    } catch (deleteError) {
      setError(deleteError.message || 'Unable to delete course.')
    }
  }

  return (
    <form className="contact-form course-form" onSubmit={submit} aria-label={course ? `Edit ${course.name}` : 'Add a course'}>
      <h3>{course ? 'Edit course' : 'Add a course'}</h3>
      <div className="field">
        <label htmlFor={`${id}-name`}>Name <abbr title="required">*</abbr></label>
        <input id={`${id}-name`} value={name} onChange={(event) => setName(event.target.value)} maxLength={255} required />
      </div>
      <div className="field">
        <label htmlFor={`${id}-description`}>Description</label>
        <textarea
          id={`${id}-description`}
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          rows={8}
          aria-describedby={`${id}-hint`}
        />
        <small id={`${id}-hint`} className="field-hint">
          Leave a blank line between paragraphs. Lines starting with &quot;- &quot; become a short list of facts.
        </small>
      </div>
      {error ? <p className="error-message" role="alert">{error}</p> : null}
      <div className="form-actions">
        <button type="submit" disabled={isSaving}>{isSaving ? 'Saving…' : course ? 'Save changes' : 'Add course'}</button>
        <button type="button" className="secondary-button" onClick={onCancel} disabled={isSaving}>Cancel</button>
        {course && onDelete ? (
          <button type="button" className="danger-button course-form__delete" onClick={remove} disabled={isSaving}>
            Delete course
          </button>
        ) : null}
      </div>
    </form>
  )
}

export default CourseForm
