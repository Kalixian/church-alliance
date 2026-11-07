import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { useAuth } from '../auth/authContext'
import { ToolPage } from './ToolPages'

function AdminPage() {
  const { apiBaseUrl, token, isAdmin } = useAuth()
  const [applicantCount, setApplicantCount] = useState(0)

  useEffect(() => {
    if (!isAdmin || !token) {
      return
    }

    fetch(`${apiBaseUrl}/api/v1/users/count?role=applicant`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((response) => (response.ok ? response.json() : 0))
      .then((count) => setApplicantCount(count))
      .catch(() => setApplicantCount(0))
  }, [apiBaseUrl, token, isAdmin])

  return (
    <ToolPage eyebrow="Members area" title="Admin" intro="Tools for coordinators and administrators.">
      <div className="management-tools">
        <p>Asset, Experience management incomplete. Maybe Participating Church information management as well?</p>
        <Link className="management-tool-link" to="/admin/certifications">
          Certifications
        </Link>
        {isAdmin ? (
          <Link className="management-tool-link" to="/admin/applications">
            Site Access Applications ({applicantCount})
          </Link>
        ) : null}
      </div>
    </ToolPage>
  )
}

export default AdminPage
