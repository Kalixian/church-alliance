import { useEffect, useState } from 'react'
import ArticleEditor from './ArticleEditor'

const PAGE_SIZE = 10

const formatArticleDate = (value) => new Intl.DateTimeFormat(undefined, {
  year: 'numeric',
  month: 'short',
  day: 'numeric',
}).format(new Date(value))

const creatorName = (creator) => {
  const name = [creator?.first_name, creator?.last_name].filter(Boolean).join(' ').trim()
  return name || creator?.email || 'Unknown author'
}

function ArticleContent({ content }) {
  return (
    <div className="article-rendered-content">
      {content.map((element, index) => (
        <ArticleBlock key={`${element.type || 'paragraph'}-${index}`} element={element} />
      ))}
    </div>
  )
}

function ArticleBlock({ element }) {
  const children = element.children || []
  const renderedChildren = <ArticleChildren nodes={children} />
  if (element.type === 'heading-one') return <h2>{renderedChildren}</h2>
  if (element.type === 'heading-two') return <h3>{renderedChildren}</h3>
  if (element.type === 'blockquote') return <blockquote>{renderedChildren}</blockquote>
  if (element.type === 'bulleted-list') return <ul>{children.map((item, index) => <li key={index}><ArticleChildren nodes={item.children || []} /></li>)}</ul>
  if (element.type === 'list-item') return <li>{renderedChildren}</li>
  return <p>{renderedChildren}</p>
}

function ArticleChildren({ nodes }) {
  return nodes.map((node, index) => {
    if (typeof node.text === 'string') {
      let text = node.text
      if (node.bold) text = <strong key={index}>{text}</strong>
      if (node.italic) text = <em key={index}>{text}</em>
      if (node.underline) text = <u key={index}>{text}</u>
      return <span key={index}>{text}</span>
    }
    return <ArticleBlock key={index} element={node} />
  })
}

function ArticlesTool({ apiBaseUrl, token, userRole, backendUserId }) {
  const [articles, setArticles] = useState([])
  const [page, setPage] = useState(0)
  const [selectedArticle, setSelectedArticle] = useState(null)
  const [isEditorVisible, setIsEditorVisible] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)

  const canCreate = Boolean(token) && userRole !== 'applicant'
  const canManage = (article) => Boolean(token) && (
    userRole === 'administrator' || (userRole === 'coordinator' && article.creator_id === backendUserId)
  )

  useEffect(() => {
    const params = new URLSearchParams({ skip: String(page * PAGE_SIZE), limit: String(PAGE_SIZE) })
    fetch(`${apiBaseUrl}/api/v1/articles?${params}`)
      .then(async (response) => {
        if (!response.ok) throw new Error('Unable to load articles.')
        return response.json()
      })
      .then(setArticles)
      .catch((loadError) => {
        setArticles([])
        setError(loadError.message || 'Unable to load articles.')
      })
      .finally(() => setIsLoading(false))
  }, [apiBaseUrl, page, refreshKey])

  const openCreate = () => {
    setSelectedArticle(null)
    setIsEditorVisible(true)
  }

  const handleSaved = (article) => {
    setSelectedArticle(article)
    setIsEditorVisible(false)
    setRefreshKey((key) => key + 1)
  }

  const handleDelete = async () => {
    if (!selectedArticle || !window.confirm('Delete this article? This action cannot be undone.')) return
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/articles/${selectedArticle.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!response.ok) {
        const responseError = await response.json().catch(() => ({}))
        throw new Error(responseError.detail || 'Unable to delete article.')
      }
      setSelectedArticle(null)
      setRefreshKey((key) => key + 1)
    } catch (deleteError) {
      setError(deleteError.message || 'Unable to delete article.')
    }
  }

  if (isEditorVisible) {
    return (
      <ArticleEditor
        article={selectedArticle}
        apiBaseUrl={apiBaseUrl}
        token={token}
        onSaved={handleSaved}
        onCancel={() => setIsEditorVisible(false)}
      />
    )
  }

  if (selectedArticle) {
    return (
      <section className="article-detail" aria-labelledby="article-detail-title">
        <div className="article-detail-actions">
          <button type="button" className="secondary-button" onClick={() => setSelectedArticle(null)}>Back to News</button>
          {canManage(selectedArticle) ? (
            <div className="form-actions">
              <button type="button" onClick={() => setIsEditorVisible(true)}>Edit article</button>
              <button type="button" className="danger-button" onClick={handleDelete}>Delete article</button>
            </div>
          ) : null}
        </div>
        <p className="section-kicker">News</p>
        <h2 id="article-detail-title">{selectedArticle.title}</h2>
        <div className="article-meta">{formatArticleDate(selectedArticle.created_at)} <span aria-hidden="true">/</span> {creatorName(selectedArticle.creator)}</div>
        <ArticleContent content={selectedArticle.content} />
      </section>
    )
  }

  return (
    <section className="news-tool" aria-labelledby="news-title">
      <div className="tool-header">
        <div>
          <p className="section-kicker">Updates and stories</p>
          <h2 id="news-title">News</h2>
        </div>
        {canCreate ? <button type="button" className="new-event-button" onClick={openCreate}>+ Add article</button> : null}
      </div>
      {error ? <p className="gallery-message gallery-error">{error}</p> : null}
      {isLoading ? <p className="gallery-message">Loading articles...</p> : null}
      {!isLoading && !error && articles.length === 0 ? <p className="gallery-message">No articles have been published yet.</p> : null}
      {!isLoading && articles.length > 0 ? (
        <div className="article-list">
          {articles.map((article) => (
            <button type="button" className="article-list-item" key={article.id} onClick={() => setSelectedArticle(article)}>
              <span className="article-list-date">{formatArticleDate(article.created_at)}</span>
              <span className="article-list-title">{article.title}</span>
              <span className="article-list-summary">{article.summary}</span>
              <span className="article-list-author">By {creatorName(article.creator)}</span>
            </button>
          ))}
        </div>
      ) : null}
      <div className="pagination-controls article-pagination" aria-label="News pagination">
        <button type="button" disabled={page === 0 || isLoading} onClick={() => setPage((current) => current - 1)}>Previous</button>
        <span>Page {page + 1}</span>
        <button type="button" disabled={articles.length < PAGE_SIZE || isLoading} onClick={() => setPage((current) => current + 1)}>Next</button>
      </div>
    </section>
  )
}

export default ArticlesTool
