import { useEffect, useState } from 'react'

const roles = ['member', 'coordinator', 'administrator']
const pageSize = 10

function ApplicationsTool({ token, authUserId, apiBaseUrl, onBack }) {
  const columnCount = 5
  const [applicants, setApplicants] = useState([])
  const [totalApplicants, setTotalApplicants] = useState(0)
  const [page, setPage] = useState(0)
  const [sortBy, setSortBy] = useState('last_name')
  const [descending, setDescending] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [savingUserId, setSavingUserId] = useState(null)
  const [error, setError] = useState('')

  const fetchApplications = async () => {
    setIsLoading(true)
    setError('')

    try {
      const query = new URLSearchParams({
        skip: String(page * pageSize),
        limit: String(pageSize),
        sort_by: sortBy,
        descending: String(descending),
        role: 'applicant',
      })
      const response = await fetch(`${apiBaseUrl}/api/v1/users?${query}`, {
        headers: { Authorization: `Bearer ${token}` },
      })

      if (!response.ok) {
        const responseError = await response.json().catch(() => ({}))
        throw new Error(responseError.detail || 'Unable to load applications.')
      }

      setApplicants(await response.json())

      const countResponse = await fetch(`${apiBaseUrl}/api/v1/users/count?role=applicant`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!countResponse.ok) {
        throw new Error('Unable to load the application count.')
      }
      setTotalApplicants(await countResponse.json())
    } catch (loadError) {
      setError(loadError.message || 'Unable to load applications.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchApplications()
  }, [page, sortBy, descending, token])

  const updateSort = (nextSortBy) => {
    if (sortBy === nextSortBy) {
      setDescending((currentDescending) => !currentDescending)
    } else {
      setSortBy(nextSortBy)
      setDescending(false)
    }
    setPage(0)
  }

  const updateApplicationRole = async (userId, role) => {
    setSavingUserId(userId)
    setError('')

    try {
      const query = new URLSearchParams({ new_role: role })
      const response = await fetch(`${apiBaseUrl}/api/v1/users/${userId}/role?${query}`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}` },
      })

      if (!response.ok) {
        const responseError = await response.json().catch(() => ({}))
        throw new Error(responseError.detail || 'Unable to approve application.')
      }

      setApplicants((currentApplicants) => currentApplicants.filter((user) => user.id !== userId))
      setTotalApplicants((currentTotal) => currentTotal - 1)
    } catch (updateError) {
      setError(updateError.message || 'Unable to approve application.')
    } finally {
      setSavingUserId(null)
    }
  }

  const rejectApplication = async (userId) => {
    if (!window.confirm('Reject and delete this access application? This action cannot be undone.')) {
      return
    }

    setSavingUserId(userId)
    setError('')

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/users/${userId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })

      if (!response.ok) {
        const responseError = await response.json().catch(() => ({}))
        throw new Error(responseError.detail || 'Unable to reject application.')
      }

      setApplicants((currentApplicants) => currentApplicants.filter((user) => user.id !== userId))
      setTotalApplicants((currentTotal) => currentTotal - 1)
    } catch (deleteError) {
      setError(deleteError.message || 'Unable to reject application.')
    } finally {
      setSavingUserId(null)
    }
  }

  const pageCount = Math.max(1, Math.ceil(totalApplicants / pageSize))

  return (
    <article className="members-tool content-block">
      <div className="tool-header">
        <div>
          <button type="button" className="text-button" onClick={onBack}>
            Back to Admin
          </button>
          <h3>Site Access Applications</h3>
        </div>
        <span className="tool-count">{totalApplicants} applications</span>
      </div>

      {error ? <p className="error-message">{error}</p> : null}

      <p className="tool-description">Review and manage requests</p>

      <div className="members-table-wrap">
        <table className="members-table">
          <thead>
            <tr>
              {[
                ['first_name', 'First name'],
                ['last_name', 'Last name'],
                ['email', 'Email'],
                ['role', 'Role'],
              ].map(([column, label]) => (
                <th key={column} scope="col">
                  <button type="button" className="sort-button" onClick={() => updateSort(column)}>
                    {label}
                    {sortBy === column ? (descending ? ' ↓' : ' ↑') : ''}
                  </button>
                </th>
              ))}
              <th scope="col">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={columnCount}>Loading applications...</td></tr>
            ) : applicants.length === 0 ? (
              <tr><td colSpan={columnCount}>No applications found.</td></tr>
            ) : applicants.map((user) => (
              <tr key={user.id}>
                <td>{user.first_name || '—'}</td>
                <td>{user.last_name || '—'}</td>
                <td>{user.email}</td>
                <td>
                  <select
                    value={user.role}
                    disabled={savingUserId === user.id || user.auth_id === authUserId}
                    onChange={(event) => updateApplicationRole(user.id, event.target.value)}
                    aria-label={`Role for ${user.email}`}
                  >
                    {roles.map((role) => <option key={role} value={role}>{role}</option>)}
                  </select>
                </td>
                <td>
                  <button
                    type="button"
                    className="danger-button"
                    disabled={savingUserId === user.id || user.auth_id === authUserId}
                    onClick={() => rejectApplication(user.id)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="pagination-controls">
        <button type="button" onClick={() => setPage((currentPage) => currentPage - 1)} disabled={page === 0 || isLoading}>
          Previous
        </button>
        <span>Page {page + 1} of {pageCount}</span>
        <button type="button" onClick={() => setPage((currentPage) => currentPage + 1)} disabled={page + 1 >= pageCount || isLoading}>
          Next
        </button>
      </div>
    </article>
  )
}

export default ApplicationsTool
