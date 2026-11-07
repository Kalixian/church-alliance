import { useEffect, useState } from 'react'
import { useLocation } from 'react-router'
import PageBanner from '../components/layout/PageBanner'
import CourseForm from '../components/CourseForm'
import { useAuth } from '../auth/authContext'
import PencilIcon from '../components/icons/PencilIcon'

// Courses are the certifications stored by the API ("courses" to visitors).
const COURSE_LIMIT = 100

function slugify(text) {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'course'
}

// Paragraphs are separated by a blank line; a paragraph whose lines all
// start with "- " is a list of short facts (see app/db/certification/seed.py).
function CourseDescription({ text }) {
  if (!text?.trim()) {
    return <p>Details coming soon.</p>
  }

  return text.trim().split(/\n\s*\n/).map((block, index) => {
    const lines = block.split('\n').map((line) => line.trim()).filter(Boolean)
    if (lines.every((line) => line.startsWith('- '))) {
      return (
        <ul key={index} className="facts">
          {lines.map((line) => <li key={line}>{line.slice(2)}</li>)}
        </ul>
      )
    }
    return <p key={index}>{lines.join(' ')}</p>
  })
}

async function errorDetail(response, fallback) {
  const body = await response.json().catch(() => ({}))
  return typeof body.detail === 'string' ? body.detail : fallback
}

function CoursesPage() {
  const { apiBaseUrl, token, isManager } = useAuth()
  const { hash } = useLocation()
  const [courses, setCourses] = useState([])
  const [status, setStatus] = useState('loading')
  const [reloadKey, setReloadKey] = useState(0)
  // null, 'new', or the id of the course being edited.
  const [editing, setEditing] = useState(null)
  const [busyId, setBusyId] = useState(null)
  const canManage = isManager && Boolean(token)

  // Bring the form that just opened into view and put the cursor in it.
  useEffect(() => {
    if (!editing) return
    const form = document.querySelector('.course-form')
    form?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    form?.querySelector('input')?.focus({ preventScroll: true })
  }, [editing])

  useEffect(() => {
    let cancelled = false
    fetch(`${apiBaseUrl}/api/v1/certifications?limit=${COURSE_LIMIT}`)
      .then((response) => {
        if (!response.ok) throw new Error('Unable to load courses.')
        return response.json()
      })
      .then((data) => {
        if (cancelled) return
        setCourses(data)
        setStatus('ready')
      })
      .catch(() => {
        if (!cancelled) setStatus('error')
      })
    return () => {
      cancelled = true
    }
  }, [apiBaseUrl, reloadKey])

  // Give each course a unique anchor for the table of contents.
  const seen = new Map()
  const anchored = courses.map((course) => {
    const base = slugify(course.name)
    const count = seen.get(base) || 0
    seen.set(base, count + 1)
    return { ...course, anchor: count ? `${base}-${count + 1}` : base }
  })

  // The layout's scroll-to-hash runs before the courses arrive; retry once they render.
  useEffect(() => {
    if (status !== 'ready' || !hash) return
    document.getElementById(decodeURIComponent(hash.slice(1)))?.scrollIntoView()
  }, [status, hash])

  const saveCourse = async (course, values) => {
    setBusyId(course?.id || 'new')
    try {
      const response = await fetch(
        course ? `${apiBaseUrl}/api/v1/certifications/${course.id}` : `${apiBaseUrl}/api/v1/certifications`,
        {
          method: course ? 'PATCH' : 'POST',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify(values),
        },
      )
      if (!response.ok) {
        throw new Error(await errorDetail(response, 'Unable to save course.'))
      }
      setEditing(null)
      setReloadKey((key) => key + 1)
    } finally {
      setBusyId(null)
    }
  }

  // Called from the edit form; errors propagate so the form can show them.
  const deleteCourse = async (course) => {
    if (!window.confirm(`Delete the course "${course.name}"? This cannot be undone.`)) {
      return
    }
    setBusyId(course.id)
    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/certifications/${course.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!response.ok) {
        throw new Error(await errorDetail(response, 'Unable to delete course.'))
      }
      setEditing(null)
      setReloadKey((key) => key + 1)
    } finally {
      setBusyId(null)
    }
  }

  return (
    <>
      <PageBanner eyebrow="Training" title="Courses">
        Equipping Early Response Teams to serve safely, effectively, and as a caring Christian presence.
      </PageBanner>

      <div className="band">
        <div className="layout">
          <nav className="toc" aria-label="Courses on this page">
            <h2>Courses</h2>
            {anchored.length ? (
              <ol>
                {anchored.map((course) => (
                  <li key={course.id}><a href={`#${course.anchor}`}>{course.name}</a></li>
                ))}
              </ol>
            ) : null}
          </nav>

          <div className="courses-content" aria-live="polite">
            <section className="article-section" id="er-200-series" aria-label="About the ER 200 series">
              <div className="callout">
                <p>
                  The ERT 200 Series of classes was created to provide trained
                  ERTs with supplementary tools and technical information to
                  strengthen their capacity for safe and effective disaster
                  response while being the caring Christian presence to a
                  community.
                </p>
              </div>

              {canManage ? (
                <div className="course-manage">
                  {editing === 'new' ? (
                    <CourseForm
                      isSaving={busyId === 'new'}
                      onSave={(values) => saveCourse(null, values)}
                      onCancel={() => setEditing(null)}
                    />
                  ) : (
                    <button type="button" className="button button--small button--outline" onClick={() => setEditing('new')}>
                      <span aria-hidden="true">+</span> Add Course
                    </button>
                  )}
                </div>
              ) : null}
            </section>

            {status === 'loading' ? <p>Loading courses…</p> : null}
            {status === 'error' ? (
              <p>Sorry, the course list could not be loaded. Please try again later.</p>
            ) : null}
            {status === 'ready' && anchored.length === 0 ? (
              <p>No courses are listed right now. Please check back soon.</p>
            ) : null}

            {anchored.map((course) => (
              <section key={course.id} className="article-section course-section" id={course.anchor}>
                {canManage && editing === course.id ? (
                  <CourseForm
                    course={course}
                    isSaving={busyId === course.id}
                    onSave={(values) => saveCourse(course, values)}
                    onDelete={() => deleteCourse(course)}
                    onCancel={() => setEditing(null)}
                  />
                ) : (
                  <>
                    {canManage ? (
                      <button
                        type="button"
                        className="course-edit-button"
                        onClick={() => setEditing(course.id)}
                        disabled={busyId !== null}
                        aria-label={`Edit ${course.name}`}
                        title="Edit course"
                      >
                        <PencilIcon />
                      </button>
                    ) : null}
                    <h2>{course.name}</h2>
                    <CourseDescription text={course.description} />
                  </>
                )}
              </section>
            ))}
          </div>
        </div>
      </div>
    </>
  )
}

export default CoursesPage
