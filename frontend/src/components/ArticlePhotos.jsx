import { useEffect, useRef, useState } from 'react'
import { fetchGalleryPictures, queueFiles } from '../utils/uploads'

function SavedPhoto({ apiBaseUrl, token, photo, disabled, onChanged, onDeleted }) {
  const [caption, setCaption] = useState(photo.caption || '')
  const [status, setStatus] = useState('')

  const saveCaption = async () => {
    if (caption.trim() === (photo.caption || '')) return
    setStatus('Saving...')
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/pictures/${photo.id}`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ caption: caption.trim() }),
      })
      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        throw new Error(body.detail || 'Unable to save caption.')
      }
      onChanged(await response.json())
      setStatus('Saved')
    } catch (error) {
      setStatus(error.message || 'Unable to save caption.')
    }
  }

  const deletePhoto = async () => {
    if (!window.confirm('Delete this photo? This cannot be undone.')) return
    setStatus('Deleting...')
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/pictures/${photo.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        throw new Error(body.detail || 'Unable to delete photo.')
      }
      onDeleted(photo.id)
    } catch (error) {
      setStatus(error.message || 'Unable to delete photo.')
    }
  }

  return (
    <li className="article-photo-card">
      {photo.url ? <img src={photo.url} alt={photo.caption || ''} loading="lazy" /> : <span className="missing-image">No image</span>}
      <input
        value={caption}
        onChange={(event) => { setCaption(event.target.value); setStatus('') }}
        onBlur={saveCaption}
        maxLength={2000}
        placeholder="Caption (optional)"
        aria-label="Photo caption"
        disabled={disabled}
      />
      <div className="article-photo-card-footer">
        <span className="article-photo-status">{status}</span>
        <button type="button" className="danger-link" onClick={deletePhoto} disabled={disabled}>Delete</button>
      </div>
    </li>
  )
}

function QueuedPhoto({ item, disabled, onCaptionChange, onRemove }) {
  const isUploading = item.status === 'uploading'
  return (
    <li className={`article-photo-card article-photo-${item.status}`}>
      <img src={item.previewUrl} alt="" />
      <input
        value={item.caption}
        onChange={(event) => onCaptionChange(item.key, event.target.value)}
        maxLength={2000}
        placeholder="Caption (optional)"
        aria-label={`Caption for ${item.file.name}`}
        disabled={disabled}
      />
      {isUploading ? (
        <progress className="article-photo-progress" value={item.progress} max={100} aria-label={`Uploading ${item.file.name}`} />
      ) : null}
      <div className="article-photo-card-footer">
        <span className="article-photo-status" role={item.status === 'error' ? 'alert' : undefined}>
          {item.status === 'error' ? item.error : isUploading ? `Uploading ${item.progress}%` : 'Uploads when saved'}
        </span>
        <button type="button" className="danger-link" onClick={() => onRemove(item.key)} disabled={disabled}>Remove</button>
      </div>
    </li>
  )
}

// The photo section of the article editor: saved photos (edited and deleted immediately) and newly
// picked files, which the editor uploads when the article is saved.
export function ArticlePhotosEditor({ apiBaseUrl, token, photos, setPhotos, queued, setQueued, disabled }) {
  const inputRef = useRef(null)
  const [rejected, setRejected] = useState([])
  const [isDragging, setIsDragging] = useState(false)

  const addFiles = (fileList) => {
    const result = queueFiles(Array.from(fileList || []))
    setRejected(result.rejected)
    if (result.queued.length) setQueued((items) => [...items, ...result.queued])
  }

  const removeQueued = (key) => {
    setQueued((items) => items.filter((item) => {
      if (item.key === key) URL.revokeObjectURL(item.previewUrl)
      return item.key !== key
    }))
  }

  const setQueuedCaption = (key, caption) => {
    setQueued((items) => items.map((item) => item.key === key ? { ...item, caption } : item))
  }

  return (
    <div className="article-editor-field">
      <span>Photos <small>(optional)</small></span>
      <div
        className={`article-photo-dropzone${isDragging ? ' is-dragging' : ''}`}
        onDragOver={(event) => { event.preventDefault(); if (!disabled) setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(event) => {
          event.preventDefault()
          setIsDragging(false)
          if (!disabled) addFiles(event.dataTransfer.files)
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          multiple
          hidden
          onChange={(event) => {
            addFiles(event.target.files)
            event.target.value = ''
          }}
        />
        <button type="button" className="secondary-button" onClick={() => inputRef.current?.click()} disabled={disabled}>
          Choose photos
        </button>
        <span>or drag them here. You can select several at once.</span>
      </div>
      {rejected.length ? (
        <ul className="gallery-message gallery-error article-photo-rejected">
          {rejected.map((message) => <li key={message}>{message}</li>)}
        </ul>
      ) : null}
      {photos.length || queued.length ? (
        <ul className="article-photo-grid" aria-label="Article photos">
          {photos.map((photo) => (
            <SavedPhoto
              key={photo.id}
              apiBaseUrl={apiBaseUrl}
              token={token}
              photo={photo}
              disabled={disabled}
              onChanged={(updated) => setPhotos((items) => items.map((item) => item.id === updated.id ? updated : item))}
              onDeleted={(id) => setPhotos((items) => items.filter((item) => item.id !== id))}
            />
          ))}
          {queued.map((item) => (
            <QueuedPhoto
              key={item.key}
              item={item}
              disabled={disabled}
              onCaptionChange={setQueuedCaption}
              onRemove={removeQueued}
            />
          ))}
        </ul>
      ) : null}
    </div>
  )
}

// Read-only photo grid with a lightbox, shown under a published article.
export function ArticlePhotoGallery({ apiBaseUrl, galleryId }) {
  const [photos, setPhotos] = useState([])
  const [openIndex, setOpenIndex] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchGalleryPictures(apiBaseUrl, galleryId)
      .then(setPhotos)
      .catch((loadError) => setError(loadError.message))
  }, [apiBaseUrl, galleryId])

  useEffect(() => {
    if (openIndex === null) return undefined
    const onKey = (event) => {
      if (event.key === 'Escape') setOpenIndex(null)
      if (event.key === 'ArrowRight') setOpenIndex((index) => (index + 1) % photos.length)
      if (event.key === 'ArrowLeft') setOpenIndex((index) => (index - 1 + photos.length) % photos.length)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [openIndex, photos.length])

  if (error) return <p className="gallery-message gallery-error">{error}</p>
  if (!photos.length) return null

  const openPhoto = openIndex === null ? null : photos[openIndex]
  return (
    <section className="article-photos" aria-labelledby="article-photos-title">
      <h3 id="article-photos-title">Photos</h3>
      <div className="thumbnail-table">
        {photos.map((photo, index) => (
          <button
            type="button"
            className="thumbnail-tile"
            key={photo.id}
            onClick={() => setOpenIndex(index)}
            aria-label={`View ${photo.caption || 'untitled photo'}`}
          >
            {photo.url ? <img src={photo.url} alt={photo.caption || ''} loading="lazy" /> : <span className="missing-image">No image</span>}
          </button>
        ))}
      </div>
      {openPhoto ? (
        <div className="gallery-lightbox" role="presentation" onClick={() => setOpenIndex(null)}>
          <div className="gallery-lightbox-content" role="dialog" aria-modal="true" aria-label="Article photo" onClick={(event) => event.stopPropagation()}>
            <button type="button" className="gallery-lightbox-close" onClick={() => setOpenIndex(null)} aria-label="Close photo">Close</button>
            {openPhoto.url ? <img src={openPhoto.url} alt={openPhoto.caption || 'Untitled photo'} /> : null}
            {openPhoto.caption ? <p className="article-lightbox-caption">{openPhoto.caption}</p> : null}
            {photos.length > 1 ? (
              <div className="article-lightbox-nav">
                <button type="button" onClick={() => setOpenIndex((openIndex - 1 + photos.length) % photos.length)}>Previous</button>
                <span>{openIndex + 1} of {photos.length}</span>
                <button type="button" onClick={() => setOpenIndex((openIndex + 1) % photos.length)}>Next</button>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}
    </section>
  )
}
