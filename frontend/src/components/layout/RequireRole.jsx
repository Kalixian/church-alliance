import { Navigate, Outlet } from 'react-router'
import { useAuth } from '../../auth/authContext'

// Hides member/admin routes from users without the role. The backend still
// enforces every permission; this only keeps the UI consistent.
function RequireRole({ level }) {
  const { isAuthReady, isConfirmed, isManager, isAdmin } = useAuth()

  if (!isAuthReady) {
    return null
  }

  const allowed = {
    confirmed: isConfirmed,
    manager: isManager,
    admin: isAdmin,
  }[level]

  return allowed ? <Outlet /> : <Navigate to="/" replace />
}

export default RequireRole
