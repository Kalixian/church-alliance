import { useEffect, useState } from 'react'
import { Link } from 'react-router'

const RECENT_COUNT = 3

const formatDate = (value) => new Intl.DateTimeFormat(undefined, {
  year: 'numeric',
  month: 'short',
  day: 'numeric',
}).format(new Date(value))

// The three newest News articles, each linking to its page in the News section.
// Renders nothing until articles load, and nothing at all if there are none or the API is unavailable.
function RecentActivity({ apiBaseUrl }) {
  const [articles, setArticles] = useState([])

  useEffect(() => {
    const params = new URLSearchParams({ skip: '0', limit: String(RECENT_COUNT) })
    fetch(`${apiBaseUrl}/api/v1/articles?${params}`)
      .then((response) => (response.ok ? response.json() : []))
      .then(setArticles)
      .catch(() => setArticles([]))
  }, [apiBaseUrl])

  if (!articles.length) return null

  return (
    <section className="band recent-activity-band" aria-labelledby="recent-activity-title">
      <div className="band__heading">
        <h2 id="recent-activity-title">Recent Activity</h2>
      </div>

      <ul className="recent-activity">
        {articles.map((article) => (
          <li key={article.id}>
            <Link className="recent-activity__item" to={`/news/${article.id}`}>
              {article.cover_url ? (
                <img className="recent-activity__photo" src={article.cover_url} alt="" loading="lazy" />
              ) : null}
              <div className="recent-activity__body">
                <span className="recent-activity__date">{formatDate(article.created_at)}</span>
                <h3>{article.title}</h3>
                <p className="recent-activity__summary">{article.summary}</p>
              </div>
            </Link>
          </li>
        ))}
      </ul>

      <Link className="button" to="/news">See all news</Link>
    </section>
  )
}

export default RecentActivity
