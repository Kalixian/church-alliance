import { useEffect, useState } from 'react'

const roles = ['member', 'coordinator', 'administrator']
const pageSize = 10

function MembersTool({ token, authUserId, apiBaseUrl, canEditRoles }) {
  const columnCount = canEditRoles ? 5 : 4
  const [users, setUsers] = useState([])
  const [totalUsers, setTotalUsers] = useState(0)
  const [page, setPage] = useState(0)
  const [sortBy, setSortBy] = useState('last_name')
  const [descending, setDescending] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [savingUserId, setSavingUserId] = useState(null)
  const [error, setError] = useState('')

  const fetchMembers = async () => {
    setIsLoading(true)
    setError('')

    try {
      const query = new URLSearchParams({
        skip: String(page * pageSize),
        limit: String(pageSize),
        sort_by: sortBy,
        descending: String(descending),
        exclude_role: 'applicant',
      })
      const response = await fetch(`${apiBaseUrl}/api/v1/users?${query}`, {
        headers: { Authorization: `Bearer ${token}` },
      })

      if (!response.ok) {
        const responseError = await response.json().catch(() => ({}))
        throw new Error(responseError.detail || 'Unable to load members.')
      }

      setUsers(await response.json())

      const countResponse = await fetch(`${apiBaseUrl}/api/v1/users/count?exclude_role=applicant`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!countResponse.ok) {
        throw new Error('Unable to load the member count.')
      }
      setTotalUsers(await countResponse.json())
    } catch (loadError) {
      setError(loadError.message || 'Unable to load members.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchMembers()
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

  const updateRole = async (userId, role) => {
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
        throw new Error(responseError.detail || 'Unable to update role.')
      }

      const updatedUser = await response.json()
      setUsers((currentUsers) => currentUsers.map((user) => (
        user.id === updatedUser.id ? updatedUser : user
      )))
    } catch (updateError) {
      setError(updateError.message || 'Unable to update role.')
    } finally {
      setSavingUserId(null)
    }
  }

  const deleteMember = async (userId) => {
    if (!window.confirm('Delete this user? This action cannot be undone.')) {
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
        throw new Error(responseError.detail || 'Unable to delete user.')
      }

      setUsers((currentUsers) => currentUsers.filter((user) => user.id !== userId))
      setTotalUsers((currentTotal) => currentTotal - 1)
    } catch (deleteError) {
      setError(deleteError.message || 'Unable to delete user.')
    } finally {
      setSavingUserId(null)
    }
  }

  const pageCount = Math.max(1, Math.ceil(totalUsers / pageSize))

  return (
    <article className="members-tool content-block">
      <div className="tool-header">
        <div>
          <h3>Members</h3>
          <p>Additional control for church membership, certifications, experience, assets, and notes will be added. Users wil be able to update their own info but not others, unless admin.</p>
        </div>
        <span className="tool-count">{totalUsers} members</span>
      </div>

      {error ? <p className="error-message">{error}</p> : null}

      <div className="members-table-wrap">
        <table className="members-table">
          <thead>
            <tr>
              {[
                ['first_name', 'First name'],
                ['last_name', 'Last name'],
                ['email', 'Email'],
                ['role', 'Role'],
                ...(canEditRoles ? [['actions', 'Actions']] : []),
              ].map(([column, label]) => (
                <th key={column} scope="col">
                  <button type="button" className="sort-button" onClick={() => updateSort(column)}>
                    {label}
                    {sortBy === column ? (descending ? ' ↓' : ' ↑') : ''}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={columnCount}>Loading members...</td></tr>
            ) : users.length === 0 ? (
              <tr><td colSpan={columnCount}>No members found.</td></tr>
            ) : users.map((user) => (
              <tr key={user.id}>
                <td>{user.first_name || '—'}</td>
                <td>{user.last_name || '—'}</td>
                <td>{user.email}</td>
                <td>
                  <select
                    value={user.role}
                    disabled={!canEditRoles || user.auth_id === authUserId || savingUserId === user.id}
                    onChange={(event) => updateRole(user.id, event.target.value)}
                    aria-label={`Role for ${user.email}`}
                  >
                    {roles.map((role) => <option key={role} value={role}>{role}</option>)}
                  </select>
                </td>
                {canEditRoles ? (
                  <td>
                    {user.auth_id === authUserId ? (
                      <span className="self-action-note">Current user</span>
                    ) : (
                      <button
                        type="button"
                        className="danger-button"
                        disabled={savingUserId === user.id}
                        onClick={() => deleteMember(user.id)}
                      >
                        Delete
                      </button>
                    )}
                  </td>
                ) : null}
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

export default MembersTool
