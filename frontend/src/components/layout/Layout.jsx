import { useEffect } from 'react'
import { Outlet, useLocation } from 'react-router'
import { useAuth } from '../../auth/authContext'
import SiteFooter from './SiteFooter'
import SiteHeader from './SiteHeader'

// Scroll to the #fragment after navigation (e.g. /about#communication),
// otherwise to the top of the new page.
function useScrollOnNavigate() {
  const { pathname, hash } = useLocation()

  useEffect(() => {
    if (hash) {
      const target = document.getElementById(decodeURIComponent(hash.slice(1)))
      if (target) {
        target.scrollIntoView()
        return
      }
    }
    window.scrollTo(0, 0)
  }, [pathname, hash])
}

function Layout() {
  const { statusMessage } = useAuth()
  useScrollOnNavigate()

  return (
    <>
      <a className="skip-link" href="#main">Skip to content</a>
      <SiteHeader />
      <main id="main">
        {statusMessage ? (
          <div className="status-strip">
            <p className="status-banner" role="status">{statusMessage}</p>
          </div>
        ) : null}
        <Outlet />
      </main>
      <SiteFooter />
    </>
  )
}

export default Layout
