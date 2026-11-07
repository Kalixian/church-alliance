import { useEffect, useRef } from 'react'
import { Link, NavLink, useLocation } from 'react-router'
import logo from '../../assets/logo_600.jpeg'
import { useAuth } from '../../auth/authContext'
import { PUBLIC_LINKS } from './navLinks'

function AccountMenu() {
  const { userEmail, userRole, isConfirmed, isManager, logout } = useAuth()
  const menuRef = useRef(null)
  const location = useLocation()

  const close = () => {
    if (menuRef.current) {
      menuRef.current.open = false
    }
  }

  // Close on navigation and on clicks outside the menu.
  useEffect(close, [location])
  useEffect(() => {
    const onPointerDown = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        close()
      }
    }
    const onKeyDown = (event) => {
      if (event.key === 'Escape') {
        close()
      }
    }
    document.addEventListener('pointerdown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('pointerdown', onPointerDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [])

  return (
    <details className="account-menu" ref={menuRef}>
      <summary>My account</summary>
      <div className="account-menu__panel">
        <p className="account-menu__who">
          {userRole ? <small>{userRole}</small> : null}
          {userEmail}
        </p>
        <ul>
          {isConfirmed ? <li><NavLink to="/members">Members</NavLink></li> : null}
          {isManager ? <li><NavLink to="/admin">Admin</NavLink></li> : null}
          <li>
            <button
              type="button"
              onClick={() => {
                close()
                logout()
              }}
            >
              Log out
            </button>
          </li>
        </ul>
      </div>
    </details>
  )
}

function SiteHeader() {
  const { isSignedIn, openLogin } = useAuth()

  return (
    <header className="site-header">
      <div className="site-header__inner">
        <Link className="brand" to="/">
          <img src={logo} alt="" width="42" height="52" />
          <span>Church Alliance<small>Hope in Disaster</small></span>
        </Link>
        <div className="site-header__nav-group">
          <nav className="site-nav" aria-label="Main">
            <ul>
              {PUBLIC_LINKS.map((link) => (
                <li key={link.to}>
                  <NavLink to={link.to} end={link.end}>{link.label}</NavLink>
                </li>
              ))}
            </ul>
          </nav>
          {isSignedIn ? (
            <AccountMenu />
          ) : (
            <button type="button" className="button button--small button--outline" onClick={openLogin}>
              Log in
            </button>
          )}
        </div>
      </div>
    </header>
  )
}

export default SiteHeader
