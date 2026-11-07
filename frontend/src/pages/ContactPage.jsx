import { useState } from 'react'
import { Link } from 'react-router'
import { useAuth } from '../auth/authContext'
import PageBanner from '../components/layout/PageBanner'

const emptyForm = { name: '', email: '', subject: '', message: '', website: '' }

const statusMessages = {
  sent: 'Thank you. Your message has been sent, and we will reply to the email address you gave us.',
  error: 'Sorry, your message could not be sent. Please check each field and try again.',
  busy: 'We have received several messages from your connection recently. Please try again in an hour.',
}

function ContactPage() {
  const { apiBaseUrl } = useAuth()
  const [form, setForm] = useState(emptyForm)
  const [status, setStatus] = useState('')
  const [isSending, setIsSending] = useState(false)

  const update = (field) => (event) => setForm((current) => ({ ...current, [field]: event.target.value }))

  const submit = async (event) => {
    event.preventDefault()
    setIsSending(true)
    setStatus('')

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      if (response.ok) {
        setForm(emptyForm)
        setStatus('sent')
      } else {
        setStatus(response.status === 429 ? 'busy' : 'error')
      }
    } catch {
      setStatus('error')
    } finally {
      setIsSending(false)
    }
  }

  return (
    <>
      <PageBanner eyebrow="Get in touch" title="Contact Us">
        Questions about the Alliance, training, or deployments? Send us a message and we will get back to you.
      </PageBanner>

      <div className="band">
        <div className="contact-layout">
          <form className="contact-form" onSubmit={submit}>
            {status === 'sent' ? (
              <p className="form-status form-status--ok form-status--shown" role="status">{statusMessages.sent}</p>
            ) : null}
            {status === 'error' || status === 'busy' ? (
              <p className="form-status form-status--error form-status--shown" role="alert">{statusMessages[status]}</p>
            ) : null}

            <div className="field-row">
              <label className="field">
                <span>Name <abbr title="required">*</abbr></span>
                <input type="text" name="name" autoComplete="name" maxLength={100} required value={form.name} onChange={update('name')} />
              </label>
              <label className="field">
                <span>Email <abbr title="required">*</abbr></span>
                <input type="email" name="email" autoComplete="email" maxLength={254} required value={form.email} onChange={update('email')} />
              </label>
            </div>

            <label className="field">
              <span>Subject</span>
              <input type="text" name="subject" maxLength={150} value={form.subject} onChange={update('subject')} />
            </label>

            <label className="field">
              <span>Message <abbr title="required">*</abbr></span>
              <textarea name="message" rows={8} maxLength={5000} required value={form.message} onChange={update('message')} />
            </label>

            {/* Honeypot: hidden from people, filled in by bots. */}
            <div className="field-trap" aria-hidden="true">
              <label>
                Leave this empty
                <input type="text" name="website" tabIndex={-1} autoComplete="off" value={form.website} onChange={update('website')} />
              </label>
            </div>

            <button className="button" type="submit" disabled={isSending}>
              {isSending ? 'Sending…' : 'Send message'}
            </button>
          </form>

          <aside className="contact-aside">
            <h2>Before you write</h2>
            <p>
              ERT members should contact their local church ERT Coordinator first.
              The Alliance communicates with each church through its Coordinator.
            </p>
            <p>
              We are always glad to hear about deployments, training classes,
              special training opportunities, and special events.
            </p>
            <p><Link to="/about#communication">How the Alliance communicates &rarr;</Link></p>
          </aside>
        </div>
      </div>
    </>
  )
}

export default ContactPage
