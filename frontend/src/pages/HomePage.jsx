import { Link } from 'react-router'
import logo from '../assets/logo_600.jpeg'
import { useAuth } from '../auth/authContext'
import RecentActivity from '../components/RecentActivity'

function HomePage() {
  const { apiBaseUrl } = useAuth()

  return (
    <>
      <section className="hero" aria-labelledby="hero-title">
        <img
          className="hero__logo"
          src={logo}
          alt="Church Alliance ERT logo: Hope in Disaster"
          width="479"
          height="600"
        />
        <div>
          <p className="hero__eyebrow">Early Response Teams</p>
          <h1 id="hero-title">Church Alliance for Disaster Response</h1>
          <p className="hero__lead">
            An alliance of churches providing a caring Christian presence in the
            aftermath of disaster, serving the survivor regardless of the
            originating agency.
          </p>
          <blockquote className="hero__verse">
            Each one of us needs to look after the good of the people around us,
            asking ourselves, “How can I help?”
            <cite>Romans 15:2 (The Message)</cite>
          </blockquote>
        </div>
      </section>

      <RecentActivity apiBaseUrl={apiBaseUrl} />

      <section className="band band--alt stats-band" aria-label="At a glance">
        <ul className="stats">
          <li><strong>2023</strong> Alliance founded in October</li>
          <li><strong>27</strong> Member churches as of September 2025</li>
          <li><strong>6</strong> Training courses offered</li>
        </ul>
      </section>

      <section className="band" aria-labelledby="explore-title">
        <div className="band__heading">
          <h2 id="explore-title">Learn more</h2>
          <p>Find out who we are and how we serve, then see the training that prepares our teams to respond.</p>
        </div>

        <div className="summary-grid">
          <article className="summary-card">
            <h2>About Us</h2>
            <p>
              We are an alliance of affiliated and disaffiliated UM churches and
              independent churches. Each member church’s Early Response Team is
              an autonomous unit that chooses to work alongside other Alliance
              members, so that together we can source manpower for multiple teams
              and serve on a sustained basis as the hands and feet of Christ.
            </p>
            <ul>
              <li>Who we are and our purpose</li>
              <li>Our history, from 17 to 27 member churches</li>
              <li>How we train, deploy and communicate</li>
            </ul>
            <Link className="button" to="/about">Read About Us</Link>
          </article>

          <article className="summary-card">
            <h2>Courses</h2>
            <p>
              Our training equips Early Response Team members to serve safely and
              effectively, from cleaning out flood-damaged homes and assessing
              damage to leading teams, coordinating response centers, supporting
              long-term recovery, and providing life-saving CPR.
            </p>
            <ul>
              <li>ER 200 series: Clean Out, Site Assessment, Team Leader</li>
              <li>On-Site Manager and Long-Term Recovery</li>
              <li>CPR with AED training</li>
            </ul>
            <Link className="button" to="/courses">View all courses</Link>
          </article>
        </div>
      </section>
    </>
  )
}

export default HomePage
