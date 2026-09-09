import { useMemo, useRef, useState } from 'react'
import { createEditor, Editor, Element as SlateElement, Transforms } from 'slate'
import { Editable, Slate, withReact } from 'slate-react'
import { withHistory } from 'slate-history'

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

function setBlockType(editor, type) {
  Transforms.unwrapNodes(editor, {
    match: (node) => SlateElement.isElement(node) && node.type === 'bulleted-list',
  })
  Transforms.setNodes(editor, { type }, { match: (node) => SlateElement.isElement(node) && Editor.isBlock(editor, node) })
}

function toggleBulletedList(editor) {
  const isInList = Editor.nodes(editor, {
    match: (node) => SlateElement.isElement(node) && node.type === 'bulleted-list',
  }).next().value

  if (isInList) {
    Transforms.unwrapNodes(editor, {
      match: (node) => SlateElement.isElement(node) && node.type === 'bulleted-list',
    })
    Transforms.setNodes(editor, { type: 'paragraph' }, {
      match: (node) => SlateElement.isElement(node) && node.type === 'list-item',
    })
    return
  }

  Transforms.setNodes(editor, { type: 'list-item' }, {
    match: (node) => SlateElement.isElement(node) && Editor.isBlock(editor, node),
  })
  Transforms.wrapNodes(editor, { type: 'bulleted-list', children: [] }, {
    match: (node) => SlateElement.isElement(node) && node.type === 'list-item',
  })
}

function ArticleEditor({ article, apiBaseUrl, token, onSaved, onCancel }) {
  const editor = useMemo(() => withHistory(withReact(createEditor())), [])
  const initialContent = useMemo(() => serializeValue(article?.content), [article])
  const contentRef = useRef(initialContent)
  const [title, setTitle] = useState(article?.title || '')
  const [summary, setSummary] = useState(article?.summary || '')
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')

  const submit = async (event) => {
    event.preventDefault()
    setIsSaving(true)
    setError('')
    try {
      const response = await fetch(
        article ? `${apiBaseUrl}/api/v1/articles/${article.id}` : `${apiBaseUrl}/api/v1/articles`,
        {
          method: article ? 'PATCH' : 'POST',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: title.trim(),
            content: contentRef.current,
            summary: summary.trim() || null,
          }),
        },
      )
      if (!response.ok) {
        const responseError = await response.json().catch(() => ({}))
        throw new Error(responseError.detail || 'Unable to save article.')
      }
      onSaved(await response.json())
    } catch (saveError) {
      setError(saveError.message || 'Unable to save article.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <form className="article-editor content-block" onSubmit={submit}>
      <div className="article-editor-heading">
        <div>
          <p className="section-kicker">Newsroom</p>
          <h2>{article ? 'Edit article' : 'New article'}</h2>
        </div>
        <button type="button" className="secondary-button" onClick={onCancel}>Cancel</button>
      </div>
      {error ? <p className="gallery-message gallery-error">{error}</p> : null}
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
              placeholder="Write the article..."
              spellCheck
            />
          </Slate>
        </div>
      </div>
      <div className="form-actions">
        <button type="submit" disabled={isSaving}>{isSaving ? 'Saving...' : article ? 'Save article' : 'Publish article'}</button>
        <button type="button" className="secondary-button" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  )
}

export default ArticleEditor
