import { Link } from 'react-router'
import { PUBLIC_LINKS } from './navLinks'

function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer__inner">
        <div>
          <strong>Church Alliance for Disaster Response</strong>
          <p>Hope in Disaster</p>
        </div>
        <nav aria-label="Footer">
          <ul>
            {PUBLIC_LINKS.map((link) => (
              <li key={link.to}><Link to={link.to}>{link.label}</Link></li>
            ))}
          </ul>
        </nav>
      </div>
    </footer>
  )
}

export default SiteFooter
