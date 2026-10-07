import { useEffect, useState } from 'react'

const PAGE_SIZE = 24
const LAST_GALLERY_STORAGE_KEY = 'church-alliance:last-gallery-id'

// Uploads straight to Cloudinary using fields signed by our API; resolves with Cloudinary's signed response.
const uploadToCloudinary = (uploadUrl, fields, file, onProgress) => new Promise((resolve, reject) => {
  const formData = new FormData()
  Object.entries(fields).forEach(([key, value]) => formData.append(key, value))
  formData.append('file', file)

  const request = new XMLHttpRequest()
  request.open('POST', uploadUrl)
  request.upload.onprogress = (event) => {
    if (event.lengthComputable) onProgress(Math.round((event.loaded / event.total) * 100))
  }
  request.onload = () => {
    let body = {}
    try {
      body = JSON.parse(request.responseText)
    } catch {
      // Fall through to the generic error below.
    }
    if (request.status >= 200 && request.status < 300) {
      resolve(body)
    } else {
      reject(new Error(body.error?.message || 'Unable to upload photo.'))
    }
  }
  request.onerror = () => reject(new Error('Unable to reach the photo service. Please try again.'))
  request.send(formData)
})

function GalleryTool({ apiBaseUrl, token, userRole, backendUserId }) {
  const [galleries, setGalleries] = useState([])
  const [pictures, setPictures] = useState([])
  const [selectedGallery, setSelectedGallery] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)
  const [total, setTotal] = useState(0)
  const [selectedPicture, setSelectedPicture] = useState(null)
  const [isPictureControlsVisible, setIsPictureControlsVisible] = useState(false)
  const [pictureCaption, setPictureCaption] = useState('')
  const [pictureGalleryId, setPictureGalleryId] = useState('')
  const [isSavingPicture, setIsSavingPicture] = useState(false)
  const [pictureMessage, setPictureMessage] = useState('')
  const [isUploadFormVisible, setIsUploadFormVisible] = useState(false)
  const [isManageVisible, setIsManageVisible] = useState(false)
  const [newGalleryName, setNewGalleryName] = useState('')
  const [isSavingGallery, setIsSavingGallery] = useState(false)
  const [galleryMessage, setGalleryMessage] = useState('')
  const [uploadFile, setUploadFile] = useState(null)
  const [uploadCaption, setUploadCaption] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadMessage, setUploadMessage] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const canUpload = Boolean(token) && userRole !== 'applicant'
  const canManage = Boolean(token) && userRole === 'administrator'
  const canManageSelectedPicture = Boolean(token) && selectedPicture && (
    userRole === 'administrator' || selectedPicture.uploaded_by_id === backendUserId
  )

  const openPicture = (picture) => {
    setSelectedPicture(picture)
    setIsPictureControlsVisible(false)
    setPictureCaption(picture.caption || '')
    setPictureGalleryId(picture.gallery_id || '')
    setPictureMessage('')
  }

  useEffect(() => {
    fetch(`${apiBaseUrl}/api/v1/galleries?limit=100`)
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('Unable to load galleries.')))
      .then(setGalleries)
      .catch(() => setGalleries([]))
  }, [apiBaseUrl, refreshKey])

  useEffect(() => {
    const savedGalleryId = window.localStorage.getItem(LAST_GALLERY_STORAGE_KEY)
    if (savedGalleryId) setSelectedGallery(savedGalleryId)
  }, [])

  useEffect(() => {
    if (selectedGallery && galleries.length > 0 && !galleries.some((gallery) => gallery.id === selectedGallery)) {
      setSelectedGallery('')
    }
  }, [galleries, selectedGallery])

  useEffect(() => {
    const params = new URLSearchParams({ skip: String(page * PAGE_SIZE), limit: String(PAGE_SIZE) })
    if (search) params.set('q', search)
    if (selectedGallery) params.set('gallery_id', selectedGallery)

    setIsLoading(true)
    setError('')
    fetch(`${apiBaseUrl}/api/v1/pictures?${params}`)
      .then(async (response) => {
        if (!response.ok) throw new Error('Unable to load photos.')
        return { pictures: await response.json(), total: response.headers.get('X-Total-Count') }
      })
      .then(({ pictures: nextPictures, total: nextTotal }) => {
        setPictures(nextPictures)
        setTotal(Number(nextTotal) || 0)
      })
      .catch((loadError) => {
        setPictures([])
        setTotal(0)
        setError(loadError.message)
      })
      .finally(() => setIsLoading(false))
  }, [apiBaseUrl, page, search, selectedGallery, refreshKey])

  const galleryNames = new Map(galleries.map((gallery) => [gallery.id, gallery.name]))
  const pageCount = Math.ceil(total / PAGE_SIZE)

  const handleSearch = (event) => {
    event.preventDefault()
    setPage(0)
    setSearch(searchInput.trim())
  }

  const handleGalleryChange = (event) => {
    setPage(0)
    setSelectedGallery(event.target.value)
    if (event.target.value) {
      window.localStorage.setItem(LAST_GALLERY_STORAGE_KEY, event.target.value)
    } else {
      window.localStorage.removeItem(LAST_GALLERY_STORAGE_KEY)
    }
  }

  const handleUpload = async (event) => {
    event.preventDefault()
    if (!uploadFile || !selectedGallery) {
      setUploadMessage('Choose an image and gallery before uploading.')
      return
    }

    setIsUploading(true)
    setUploadMessage('')
    setUploadProgress(0)
    try {
      const signatureResponse = await fetch(`${apiBaseUrl}/api/v1/pictures/upload-signature`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!signatureResponse.ok) {
        const responseError = await signatureResponse.json().catch(() => ({}))
        throw new Error(responseError.detail || 'Unable to upload photo.')
      }
      const { upload_url: uploadUrl, fields } = await signatureResponse.json()
      const uploaded = await uploadToCloudinary(uploadUrl, fields, uploadFile, setUploadProgress)

      const response = await fetch(`${apiBaseUrl}/api/v1/pictures`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          public_id: uploaded.public_id,
          version: uploaded.version,
          signature: uploaded.signature,
          caption: uploadCaption.trim(),
          gallery_id: selectedGallery,
        }),
      })
      if (!response.ok) {
        const responseError = await response.json().catch(() => ({}))
        throw new Error(responseError.detail || 'Unable to upload photo.')
      }
      setUploadFile(null)
      setUploadCaption('')
      setUploadMessage('Photo uploaded successfully.')
      setIsUploadFormVisible(false)
      setPage(0)
      setRefreshKey((key) => key + 1)
    } catch (uploadError) {
      setUploadMessage(uploadError.message || 'Unable to upload photo.')
    } finally {
      setIsUploading(false)
    }
  }

  const handleCreateGallery = async (event) => {
    event.preventDefault()
    const name = newGalleryName.trim()
    if (!name) return

    setIsSavingGallery(true)
    setGalleryMessage('')
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/galleries`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name }),
      })
      if (!response.ok) {
        const responseError = await response.json().catch(() => ({}))
        throw new Error(responseError.detail || 'Unable to add gallery.')
      }
      const gallery = await response.json()
      setGalleries((currentGalleries) => [...currentGalleries, gallery].sort((first, second) => first.name.localeCompare(second.name)))
      setNewGalleryName('')
      setGalleryMessage('Gallery added successfully.')
    } catch (createError) {
      setGalleryMessage(createError.message || 'Unable to add gallery.')
    } finally {
      setIsSavingGallery(false)
    }
  }

  const handleDeleteGallery = async (gallery) => {
    if (!window.confirm(`Remove "${gallery.name}" and its photos? This action cannot be undone.`)) return

    setGalleryMessage('')
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/galleries/${gallery.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!response.ok) {
        const responseError = await response.json().catch(() => ({}))
        throw new Error(responseError.detail || 'Unable to remove gallery.')
      }
      setGalleries((currentGalleries) => currentGalleries.filter((currentGallery) => currentGallery.id !== gallery.id))
      if (selectedGallery === gallery.id) {
        setSelectedGallery('')
        window.localStorage.removeItem(LAST_GALLERY_STORAGE_KEY)
        setPage(0)
      }
      setGalleryMessage('Gallery removed successfully.')
      setRefreshKey((key) => key + 1)
    } catch (deleteError) {
      setGalleryMessage(deleteError.message || 'Unable to remove gallery.')
    }
  }

  const handleUpdatePicture = async (event) => {
    event.preventDefault()
    if (!selectedPicture) return

    setIsSavingPicture(true)
    setPictureMessage('')
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/pictures/${selectedPicture.id}`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          caption: pictureCaption.trim(),
          ...(userRole === 'administrator' ? { gallery_id: pictureGalleryId } : {}),
        }),
      })
      if (!response.ok) {
        const responseError = await response.json().catch(() => ({}))
        throw new Error(responseError.detail || 'Unable to update photo.')
      }
      const updatedPicture = await response.json()
      setSelectedPicture(null)
      setRefreshKey((key) => key + 1)
    } catch (updateError) {
      setPictureMessage(updateError.message || 'Unable to update photo.')
    } finally {
      setIsSavingPicture(false)
    }
  }

  const handleDeletePicture = async () => {
    if (!selectedPicture || !window.confirm('Delete this photo? This action cannot be undone.')) return

    setIsSavingPicture(true)
    setPictureMessage('')
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/pictures/${selectedPicture.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!response.ok) {
        const responseError = await response.json().catch(() => ({}))
        throw new Error(responseError.detail || 'Unable to delete photo.')
      }
      setSelectedPicture(null)
      setRefreshKey((key) => key + 1)
    } catch (deleteError) {
      setPictureMessage(deleteError.message || 'Unable to delete photo.')
    } finally {
      setIsSavingPicture(false)
    }
  }

  return (
    <section className="gallery-tool" aria-labelledby="gallery-title">
      <div className="tool-header">
        <div>
          <p className="section-kicker">Photo archive</p>
          <h2 id="gallery-title">Photo Gallery</h2>
        </div>
        <div className="events-header-actions">
          <span className="gallery-count">{total} {total === 1 ? 'photo' : 'photos'}</span>
          {canUpload ? (
            <button
              type="button"
              className="new-event-button"
              aria-expanded={isUploadFormVisible}
              onClick={() => setIsUploadFormVisible((visible) => !visible)}
            >
              {isUploadFormVisible ? 'Cancel Upload' : '+ Upload'}
            </button>
          ) : null}
          {canManage ? (
            <button
              type="button"
              className="new-event-button"
              aria-expanded={isManageVisible}
              onClick={() => setIsManageVisible((visible) => !visible)}
            >
              {isManageVisible ? 'Close Album Manager' : 'Manage Albums'}
            </button>
          ) : null}
        </div>
      </div>

      {isManageVisible ? (
        <section className="gallery-management" aria-labelledby="gallery-management-title">
          <h3 id="gallery-management-title">Manage albums</h3>
          <form className="gallery-create-form" onSubmit={handleCreateGallery}>
            <label htmlFor="new-gallery-name">Album name</label>
            <div className="gallery-search-row">
              <input
                id="new-gallery-name"
                value={newGalleryName}
                onChange={(event) => setNewGalleryName(event.target.value)}
                maxLength={255}
                placeholder="e.g. 2026 response trip"
                required
              />
              <button type="submit" disabled={isSavingGallery}>{isSavingGallery ? 'Adding...' : 'Add album'}</button>
            </div>
          </form>
          <div className="gallery-management-table-wrap">
            <table className="gallery-management-table">
              <caption className="sr-only">Album list and picture counts</caption>
              <thead>
                <tr><th scope="col">Photo Albums</th><th scope="col">Pictures</th><th scope="col"><span className="sr-only">Actions</span></th></tr>
              </thead>
              <tbody>
                {galleries.map((gallery) => (
                  <tr key={gallery.id}>
                    <th scope="row">{gallery.name}</th>
                    <td>{gallery.picture_count}</td>
                    <td><button type="button" className="danger-button" onClick={() => handleDeleteGallery(gallery)}>Remove</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
      {galleryMessage ? <p className="gallery-message">{galleryMessage}</p> : null}

      {isUploadFormVisible ? (
        <form className="new-event-form content-block" onSubmit={handleUpload}>
          <h3>Upload photo</h3>
          <label>
            <span>Choose a photo from your device</span>
            <input type="file" accept="image/*" onChange={(event) => setUploadFile(event.target.files?.[0] || null)} required />
          </label>
          <label>
            <span>Add a caption (optional)</span>
            <input value={uploadCaption} onChange={(event) => setUploadCaption(event.target.value)} maxLength={2000} />
          </label>
          <label>
            <span>Select which album the photo will appear in</span>
            <select value={selectedGallery} onChange={handleGalleryChange} required>
              <option value="">Choose an album...</option>
              {galleries.map((gallery) => <option key={gallery.id} value={gallery.id}>{gallery.name}</option>)}
            </select>
          </label>
          <button type="submit" disabled={isUploading}>{isUploading ? `Uploading... ${uploadProgress}%` : 'Upload photo'}</button>
        </form>
      ) : null}
      {uploadMessage ? <p className="gallery-message">{uploadMessage}</p> : null}

      <div className="gallery-filters">
        <label className="gallery-select" htmlFor="gallery-filter">
          Show a specific album
          <select id="gallery-filter" value={selectedGallery} onChange={handleGalleryChange}>
            <option value="">Show all albums</option>
            {galleries.map((gallery) => <option key={gallery.id} value={gallery.id}>{gallery.name}</option>)}
          </select>
        </label>
        <form className="gallery-search" onSubmit={handleSearch}>
          <label htmlFor="gallery-search-input">Find a picture by its caption</label>
          <div className="gallery-search-row">
            <input
              id="gallery-search-input"
              type="search"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Find a photo by caption"
            />
            <button type="submit">Search</button>
          </div>
        </form>
      </div>

      {error ? <p className="gallery-message gallery-error">{error}</p> : null}
      {isLoading ? <p className="gallery-message">Loading photos...</p> : null}
      {!isLoading && !error && pictures.length === 0 ? <p className="gallery-message">No photos match these filters.</p> : null}

      {!isLoading && pictures.length > 0 ? (
        <div className="thumbnail-table" aria-label="Photo thumbnails">
          {pictures.map((picture) => (
            <button
              type="button"
              className="thumbnail-tile"
              key={picture.id}
              onClick={() => openPicture(picture)}
              aria-label={`View ${picture.caption || 'untitled photo'}`}
            >
              {picture.url ? <img src={picture.url} alt={picture.caption || ''} loading="lazy" /> : <span className="missing-image">No image</span>}
              <span className="thumbnail-caption">{picture.caption || ''}</span>
              <span className="thumbnail-gallery">{galleryNames.get(picture.gallery_id) || 'Unassigned'}</span>
            </button>
          ))}
        </div>
      ) : null}

      {pageCount > 1 ? (
        <div className="pagination-controls" aria-label="Gallery pagination">
          <button type="button" disabled={page === 0} onClick={() => setPage((current) => current - 1)}>Previous</button>
          <span>Page {page + 1} of {pageCount}</span>
          <button type="button" disabled={page + 1 >= pageCount} onClick={() => setPage((current) => current + 1)}>Next</button>
        </div>
      ) : null}

      {selectedPicture ? (
        <div className="gallery-lightbox" role="presentation" onClick={() => setSelectedPicture(null)}>
          <div className="gallery-lightbox-content" role="dialog" aria-modal="true" aria-labelledby="selected-photo-caption" onClick={(event) => event.stopPropagation()}>
            <button type="button" className="gallery-lightbox-close" onClick={() => setSelectedPicture(null)} aria-label="Close photo">Close</button>
            {selectedPicture.url ? <img src={selectedPicture.url} alt={selectedPicture.caption || 'Untitled photo'} /> : null}
            <p id="selected-photo-caption">{selectedPicture.caption || ''}</p>
            {canManageSelectedPicture ? (
              <>
                <button
                  type="button"
                  className="picture-controls-toggle"
                  aria-expanded={isPictureControlsVisible}
                  onClick={() => setIsPictureControlsVisible((visible) => !visible)}
                >
                  {isPictureControlsVisible ? 'Hide Controls' : 'See Controls'}
                </button>
                {isPictureControlsVisible ? (
                  <form className="picture-controls" onSubmit={handleUpdatePicture}>
                    <label>
                      <span>Edit optional caption</span>
                      <input value={pictureCaption} onChange={(event) => setPictureCaption(event.target.value)} maxLength={2000} />
                    </label>
                    <label>
                      <span>Change this photo's album</span>
                      <select value={pictureGalleryId} onChange={(event) => setPictureGalleryId(event.target.value)} disabled={userRole !== 'administrator'}>
                        {galleries.map((gallery) => <option key={gallery.id} value={gallery.id}>{gallery.name}</option>)}
                      </select>
                    </label>
                    <div className="picture-controls-actions">
                      <button type="submit" disabled={isSavingPicture}>{isSavingPicture ? 'Saving...' : 'Save changes'}</button>
                      <button type="button" className="danger-button" onClick={handleDeletePicture} disabled={isSavingPicture}>Delete photo</button>
                    </div>
                    {pictureMessage ? <p className="gallery-message">{pictureMessage}</p> : null}
                  </form>
                ) : null}
              </>
            ) : null}
          </div>
        </div>
      ) : null}
    </section>
  )
}

export default GalleryTool
