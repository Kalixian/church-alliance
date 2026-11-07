import { useEffect, useMemo, useRef, useState } from 'react'
import { createEditor, Editor, Element as SlateElement, Range, Transforms } from 'slate'
import { Editable, Slate, withReact } from 'slate-react'
import { withHistory } from 'slate-history'
import { ArticlePhotosEditor } from './ArticlePhotos'
import { fetchGalleryPictures, uploadPictures } from '../utils/uploads'

const EMPTY_CONTENT = [{ type: 'paragraph', children: [{ text: '' }] }]

const serializeValue = (value) => value?.length ? value : EMPTY_CONTENT

function renderElement({ attributes, children, element }) {
  switch (element.type) {
    case 'heading-one':
      return <h2 {...attributes}>{children}</h2>
    case 'heading-two':
      return <h3 {...attributes}>{children}</h3>
    case 'blockquote':
      return <blockquote {...attributes}>{children}</blockquote>
    case 'bulleted-list':
      return <ul {...attributes}>{children}</ul>
    case 'list-item':
      return <li {...attributes}>{children}</li>
    default:
      return <p {...attributes}>{children}</p>
  }
}

function renderLeaf({ attributes, children, leaf }) {
  if (leaf.bold) children = <strong>{children}</strong>
  if (leaf.italic) children = <em>{children}</em>
  if (leaf.underline) children = <u>{children}</u>
  return <span {...attributes}>{children}</span>
}

function toggleMark(editor, format) {
  const marks = Editor.marks(editor)
  if (marks?.[format]) {
    Editor.removeMark(editor, format)
  } else {
    Editor.addMark(editor, format, true)
  }
}

const isList = (node) => SlateElement.isElement(node) && node.type === 'bulleted-list'
const isListItem = (node) => SlateElement.isElement(node) && node.type === 'list-item'

// Moves the selected list items out of their list as blocks of `type`. `split` keeps the items before
// and after the selection in their own lists instead of breaking the whole list apart.
function liftOutOfList(editor, type) {
  Transforms.setNodes(editor, { type }, { match: isListItem })
  Transforms.unwrapNodes(editor, { match: isList, split: true })
}

function setBlockType(editor, type) {
  if (Editor.above(editor, { match: isList })) {
    liftOutOfList(editor, type)
    return
  }
  Transforms.setNodes(editor, { type }, { match: (node) => SlateElement.isElement(node) && Editor.isBlock(editor, node) })
}

function toggleBulletedList(editor) {
  if (Editor.nodes(editor, { match: isList }).next().value) {
    liftOutOfList(editor, 'paragraph')
    return
  }

  Transforms.setNodes(editor, { type: 'list-item' }, {
    match: (node) => SlateElement.isElement(node) && Editor.isBlock(editor, node),
  })
  Transforms.wrapNodes(editor, { type: 'bulleted-list', children: [] }, { match: isListItem })
}

// Enter on an empty bullet, or Backspace at the start of a bullet, ends the list there,
// as in most word processors.
function handleListKeys(editor, event) {
  if (event.key !== 'Enter' && event.key !== 'Backspace') return
  if (event.key === 'Enter' && event.shiftKey) return
  const { selection } = editor
  if (!selection || !Range.isCollapsed(selection)) return
  const item = Editor.above(editor, { match: isListItem })
  if (!item) return
  const [, itemPath] = item

  const isEmpty = Editor.string(editor, itemPath) === ''
  const isAtStart = Editor.isStart(editor, selection.anchor, itemPath)
  if ((event.key === 'Enter' && isEmpty) || (event.key === 'Backspace' && isAtStart)) {
    event.preventDefault()
    liftOutOfList(editor, 'paragraph')
  }
}

const responseError = async (response, fallback) => {
  const body = await response.json().catch(() => ({}))
  return new Error(body.detail || fallback)
}

function ArticleEditor({ article, apiBaseUrl, token, onSaved, onDelete, onCancel }) {
  const editor = useMemo(() => withHistory(withReact(createEditor())), [])
  const initialContent = useMemo(() => serializeValue(article?.content), [article])
  const contentRef = useRef(initialContent)
  const [title, setTitle] = useState(article?.title || '')
  const [summary, setSummary] = useState(article?.summary || '')
  // The latest saved version; a new article gets one on its first save, so retries PATCH it.
  const [savedArticle, setSavedArticle] = useState(article)
  const [photos, setPhotos] = useState([])
  const [queued, setQueued] = useState([])
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')
  const hasFailedUploads = queued.some((item) => item.status === 'error')
  const queuedRef = useRef(queued)

  useEffect(() => {
    queuedRef.current = queued
  }, [queued])

  useEffect(() => {
    if (!article?.gallery_id) return
    fetchGalleryPictures(apiBaseUrl, article.gallery_id)
      .then(setPhotos)
      .catch((loadError) => setError(loadError.message))
  }, [apiBaseUrl, article?.gallery_id])

  // Release the preview images when the editor closes.
  useEffect(() => () => queuedRef.current.forEach((item) => URL.revokeObjectURL(item.previewUrl)), [])

  const saveArticle = async () => {
    const response = await fetch(
      savedArticle ? `${apiBaseUrl}/api/v1/articles/${savedArticle.id}` : `${apiBaseUrl}/api/v1/articles`,
      {
        method: savedArticle ? 'PATCH' : 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title.trim(),
          content: contentRef.current,
          summary: summary.trim() || null,
        }),
      },
    )
    if (!response.ok) throw await responseError(response, 'Unable to save article.')
    return response.json()
  }

  const ensureGallery = async (articleId) => {
    const response = await fetch(`${apiBaseUrl}/api/v1/articles/${articleId}/gallery`, {
      method: 'PUT',
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!response.ok) throw await responseError(response, 'Unable to prepare the photo gallery.')
    return response.json()
  }

  // Uploads queued files; finished ones move into the saved photos. Returns how many failed.
  const uploadQueued = async (galleryId, items) => {
    let failed = 0
    await uploadPictures({
      apiBaseUrl,
      token,
      galleryId,
      items,
      onItemChange: (key, changes) => {
        if (changes.status === 'done') {
          setQueued((current) => current.filter((item) => {
            if (item.key === key) URL.revokeObjectURL(item.previewUrl)
            return item.key !== key
          }))
          setPhotos((current) => [...current, changes.picture])
          return
        }
        if (changes.status === 'error') failed += 1
        setQueued((current) => current.map((item) => item.key === key ? { ...item, ...changes } : item))
      },
    })
    return failed
  }

  const submit = async (event) => {
    event.preventDefault()
    setIsSaving(true)
    setError('')
    try {
      let saved = await saveArticle()
      setSavedArticle(saved)
      if (queued.length) {
        const gallery = await ensureGallery(saved.id)
        saved = { ...saved, gallery_id: gallery.id }
        setSavedArticle(saved)
        const failed = await uploadQueued(gallery.id, queued)
        if (failed) {
          setError(`The article was saved, but ${failed} of ${queued.length} photos did not upload. Save again to retry them, or remove them.`)
          return
        }
      }
      onSaved(saved)
    } catch (saveError) {
      setError(saveError.message || 'Unable to save article.')
    } finally {
      setIsSaving(false)
    }
  }

  const remove = async () => {
    if (!window.confirm('Delete this article and its photos? This cannot be undone.')) return
    setIsSaving(true)
    setError('')
    try {
      await onDelete(savedArticle.id)
    } catch (deleteError) {
      setError(deleteError.message || 'Unable to delete article.')
      setIsSaving(false)
    }
  }

  // If the article was saved while photos were failing, leaving should still show the saved version.
  const leave = () => (savedArticle && savedArticle !== article ? onSaved(savedArticle) : onCancel())

  const submitLabel = () => {
    if (isSaving) return queued.length ? 'Saving and uploading...' : 'Saving...'
    if (hasFailedUploads) return 'Retry failed photos'
    return savedArticle ? 'Save article' : 'Publish article'
  }

  return (
    <form className="article-editor content-block" onSubmit={submit}>
      <div className="article-editor-heading">
        <div>
          <p className="section-kicker">Newsroom</p>
          <h2>{article ? 'Edit article' : 'New article'}</h2>
        </div>
        <button type="button" className="secondary-button" onClick={leave} disabled={isSaving}>
          {hasFailedUploads ? 'Continue without them' : 'Cancel'}
        </button>
      </div>
      {error ? <p className="gallery-message gallery-error" role="alert">{error}</p> : null}
      <div className="article-editor-field">
        <span>Title</span>
        <input value={title} onChange={(event) => setTitle(event.target.value)} maxLength={255} required />
      </div>
      <div className="article-editor-field">
        <span>Summary <small>(optional)</small></span>
        <textarea value={summary} onChange={(event) => setSummary(event.target.value)} maxLength={2000} rows={3} placeholder="Leave blank to use the opening lines." />
      </div>
      <div className="article-editor-field">
        <span>Article</span>
        <div className="article-rich-text-editor">
          <Slate editor={editor} initialValue={initialContent} onChange={(value) => { contentRef.current = value }}>
            <div className="article-editor-toolbar" role="toolbar" aria-label="Article formatting">
              <button type="button" onMouseDown={(event) => { event.preventDefault(); toggleMark(editor, 'bold') }}><strong>B</strong></button>
              <button type="button" onMouseDown={(event) => { event.preventDefault(); toggleMark(editor, 'italic') }}><em>I</em></button>
              <button type="button" onMouseDown={(event) => { event.preventDefault(); toggleMark(editor, 'underline') }}><u>U</u></button>
              <button type="button" onMouseDown={(event) => { event.preventDefault(); setBlockType(editor, 'heading-one') }}>Heading</button>
              <button type="button" onMouseDown={(event) => { event.preventDefault(); setBlockType(editor, 'blockquote') }}>Quote</button>
              <button type="button" onMouseDown={(event) => { event.preventDefault(); toggleBulletedList(editor) }}>List</button>
              <button type="button" onMouseDown={(event) => { event.preventDefault(); setBlockType(editor, 'paragraph') }}>Text</button>
            </div>
            <Editable
              className="article-editor-input"
              renderElement={renderElement}
              renderLeaf={renderLeaf}
              onKeyDown={(event) => handleListKeys(editor, event)}
              placeholder="Write the article..."
              spellCheck
            />
          </Slate>
        </div>
      </div>
      <ArticlePhotosEditor
        apiBaseUrl={apiBaseUrl}
        token={token}
        photos={photos}
        setPhotos={setPhotos}
        queued={queued}
        setQueued={setQueued}
        disabled={isSaving}
      />
      <div className="form-actions">
        <button type="submit" disabled={isSaving}>{submitLabel()}</button>
        <button type="button" className="secondary-button" onClick={leave} disabled={isSaving}>
          {hasFailedUploads ? 'Continue without them' : 'Cancel'}
        </button>
        {savedArticle && onDelete ? (
          <button type="button" className="danger-button article-editor-delete" onClick={remove} disabled={isSaving}>
            Delete article
          </button>
        ) : null}
      </div>
    </form>
  )
}

export default ArticleEditor
