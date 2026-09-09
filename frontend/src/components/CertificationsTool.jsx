import { useEffect, useState } from 'react'

const pageSize = 8

function CertificationsTool({ token, apiBaseUrl, onBack }) {
  const [certifications, setCertifications] = useState([])
  const [totalCertifications, setTotalCertifications] = useState(0)
  const [page, setPage] = useState(0)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [savingId, setSavingId] = useState(null)
  const [error, setError] = useState('')

  const fetchCertifications = async () => {
    setIsLoading(true)
    setError('')

    try {
      const query = new URLSearchParams({
        skip: String(page * pageSize),
        limit: String(pageSize),
      })
      const headers = { Authorization: `Bearer ${token}` }
      const [listResponse, countResponse] = await Promise.all([
        fetch(`${apiBaseUrl}/api/v1/certifications?${query}`, { headers }),
        fetch(`${apiBaseUrl}/api/v1/certifications/count`, { headers }),
      ])

      if (!listResponse.ok || !countResponse.ok) {
        throw new Error('Unable to load certifications.')
      }

      setCertifications(await listResponse.json())
      setTotalCertifications(await countResponse.json())
    } catch (loadError) {
      setError(loadError.message || 'Unable to load certifications.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchCertifications()
  }, [apiBaseUrl, page, token])

  const resetForm = () => {
    setName('')
    setDescription('')
    setEditingId(null)
  }

  const saveCertification = async (event) => {
    event.preventDefault()
    if (!name.trim()) {
      setError('Certification name is required.')
      return
    }

    setSavingId(editingId || 'new')
    setError('')
    try {
      const isEditing = Boolean(editingId)
      const response = await fetch(
        isEditing
          ? `${apiBaseUrl}/api/v1/certifications/${editingId}`
          : `${apiBaseUrl}/api/v1/certifications`,
        {
          method: isEditing ? 'PATCH' : 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ name: name.trim(), description: description.trim() || null }),
        },
      )
      if (!response.ok) {
        const responseError = await response.json().catch(() => ({}))
        throw new Error(responseError.detail || 'Unable to save certification.')
      }

      resetForm()
      await fetchCertifications()
    } catch (saveError) {
      setError(saveError.message || 'Unable to save certification.')
    } finally {
      setSavingId(null)
    }
  }

  const editCertification = (certification) => {
    setEditingId(certification.id)
    setName(certification.name)
    setDescription(certification.description || '')
    setError('')
  }

  const removeCertification = async (certification) => {
    if (!window.confirm(`Remove ${certification.name}? This action cannot be undone.`)) {
      return
    }

    setSavingId(certification.id)
    setError('')
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/certifications/${certification.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!response.ok) {
        const responseError = await response.json().catch(() => ({}))
        throw new Error(responseError.detail || 'Unable to remove certification.')
      }

      if (editingId === certification.id) {
        resetForm()
      }
      if (certifications.length === 1 && page > 0) {
        setPage((currentPage) => currentPage - 1)
      } else {
        await fetchCertifications()
      }
    } catch (deleteError) {
      setError(deleteError.message || 'Unable to remove certification.')
    } finally {
      setSavingId(null)
    }
  }

  const pageCount = Math.max(1, Math.ceil(totalCertifications / pageSize))

  return (
    <section className="main-content certifications-tool" aria-live="polite" aria-labelledby="certifications-title">
      <div className="tool-header">
        <div>
          <button type="button" className="text-button" onClick={onBack}>Back to Admin</button>
          <h2 id="certifications-title">Certifications</h2>
        </div>
        <span className="tool-count">{totalCertifications} certifications</span>
      </div>

      <form className="certification-form content-block" onSubmit={saveCertification}>
        <h3>{editingId ? 'Edit certification' : 'Add certification'}</h3>
        <label>
          <span>Name</span>
          <input value={name} onChange={(event) => setName(event.target.value)} maxLength={255} required />
        </label>
        <label>
          <span>Description</span>
          <textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={4} />
        </label>
        <div className="form-actions">
          <button type="submit" disabled={savingId !== null}>{editingId ? 'Save changes' : 'Add certification'}</button>
          {editingId ? <button type="button" className="secondary-button" onClick={resetForm}>Cancel</button> : null}
        </div>
      </form>

      {error ? <p className="error-message">{error}</p> : null}
      <div className="certification-list">
        {isLoading ? <p className="content-block">Loading certifications...</p> : null}
        {!isLoading && certifications.length === 0 ? <p className="content-block">No certifications found.</p> : null}
        {certifications.map((certification) => (
          <article key={certification.id} className="certification-row content-block">
            <div>
              <h3>{certification.name}</h3>
              <p>{certification.description || 'No description provided.'}</p>
            </div>
            <div className="form-actions">
              <button type="button" onClick={() => editCertification(certification)} disabled={savingId !== null}>Edit</button>
              <button type="button" className="danger-button" onClick={() => removeCertification(certification)} disabled={savingId !== null}>Delete</button>
            </div>
          </article>
        ))}
      </div>

      {totalCertifications > 0 ? (
        <div className="pagination-controls">
          <button type="button" onClick={() => setPage((currentPage) => currentPage - 1)} disabled={page === 0 || isLoading}>Previous</button>
          <span>Page {page + 1} of {pageCount}</span>
          <button type="button" onClick={() => setPage((currentPage) => currentPage + 1)} disabled={page + 1 >= pageCount || isLoading}>Next</button>
        </div>
      ) : null}
    </section>
  )
}

export default CertificationsTool