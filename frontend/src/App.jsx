import { useEffect, useMemo, useState } from 'react'
import { createClient } from '@supabase/supabase-js'
import './App.css'
import AuthModal from './components/AuthModal'
import MainContent from './components/MainContent'

const quickLinks = ['Volunteer', 'Events', 'Resources', 'News']
const managementRoles = new Set(['administrator', 'organizer'])

const getApiBaseUrl = () => import.meta.env.VITE_API_URL || 'http://localhost:8000'

const getSupabaseClient = () => {
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
  const supabasePublishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY

  if (!supabaseUrl || !supabasePublishableKey) {
    return null
  }

  return createClient(supabaseUrl, supabasePublishableKey)
}

function App() {
  const [supabaseClient, setSupabaseClient] = useState(null)
  const [session, setSession] = useState(null)
  const [isLoginOpen, setIsLoginOpen] = useState(false)
  const [showSignupForm, setShowSignupForm] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [apiMessage, setApiMessage] = useState('')
  const [authNotice, setAuthNotice] = useState('')
  const [userRole, setUserRole] = useState('')
  const [activeSection, setActiveSection] = useState('Volunteer')

  useEffect(() => {
    const client = getSupabaseClient()
    setSupabaseClient(client)

    if (!client) {
      return undefined
    }

    const { data: { subscription } } = client.auth.onAuthStateChange(
      async (_event, nextSession) => {
        setSession(nextSession)
        const nextToken = nextSession?.access_token
        if (nextToken) {
          const role = await fetchUserRole(nextToken)
          setUserRole(role)
        } else {
          setUserRole('')
        }
      },
    )

    client.auth.getSession().then(async ({ data: { session: currentSession } }) => {
      setSession(currentSession)
      if (currentSession?.access_token) {
        const role = await fetchUserRole(currentSession.access_token)
        setUserRole(role)
      }
    })

    return () => subscription.unsubscribe()
  }, [])

  const userEmail = useMemo(
    () => session?.user?.email || 'Signed in user',
    [session],
  )

  const visibleQuickLinks = managementRoles.has(userRole)
    ? [...quickLinks, 'Management']
    : quickLinks
  const allowedActiveSections = [
    ...visibleQuickLinks,
    'Members',
    ...(userRole === 'administrator' ? ['Site Access Applications'] : []),
  ]
  const visibleActiveSection = allowedActiveSections.includes(activeSection)
    ? activeSection
    : 'Volunteer'

  const fetchUserRole = async (token) => {
    if (!token) {
      return ''
    }

    const syncResponse = await fetch(`${getApiBaseUrl()}/api/v1/auth/sync-user`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    })

    if (!syncResponse.ok) {
      return ''
    }

    const user = await syncResponse.json().catch(() => ({}))
    return user.role || ''
  }

  const resetAuthForm = () => {
    setEmail('')
    setPassword('')
    setConfirmPassword('')
    setFirstName('')
    setLastName('')
    setError('')
    setAuthNotice('')
  }

  const handleLogin = async (event) => {
    event.preventDefault()

    if (!supabaseClient) {
      setError('Supabase environment variables are not configured.')
      return
    }

    setIsSubmitting(true)
    setError('')
    setApiMessage('')

    try {
      const { data, error: signInError } = await supabaseClient.auth.signInWithPassword({
        email,
        password,
      })

      if (signInError) {
        throw signInError
      }

      const token = data.session?.access_token
      if (!token) {
        throw new Error('No access token was returned. Please try again.')
      }

      const syncResponse = await fetch(`${getApiBaseUrl()}/api/v1/auth/sync-user`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!syncResponse.ok) {
        const syncError = await syncResponse.json().catch(() => ({ detail: 'Authentication failed.' }))
        throw new Error(syncError.detail || 'Authentication failed.')
      }

      const backendUser = await syncResponse.json().catch(() => ({}))
      setSession(data.session)
      setUserRole(backendUser.role || '')
      setIsLoginOpen(false)
      setShowSignupForm(false)
      resetAuthForm()
      setApiMessage(`Logged in as ${data.user.email}`)
    } catch (submitError) {
      setError(submitError.message || 'Login failed. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleSignup = async (event) => {
    event.preventDefault()

    if (!supabaseClient) {
      setError('Supabase environment variables are not configured.')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    const displayName = `${firstName.trim()} ${lastName.trim()}`.trim()
    if (!firstName.trim() || !lastName.trim()) {
      setError('Please enter both your first and last name.')
      return
    }

    setIsSubmitting(true)
    setError('')
    setApiMessage('')
    setAuthNotice('')

    try {
      const { data, error: signUpError } = await supabaseClient.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: displayName,
            first_name: firstName.trim(),
            last_name: lastName.trim(),
          },
        },
      })

      if (signUpError) {
        throw signUpError
      }

      if (!data.user) {
        throw new Error('Unable to create account. Please try again.')
      }

      const confirmationMessage = `A confirmation email has been sent to ${email}.`
      setShowSignupForm(false)
      setIsLoginOpen(true)
      setEmail(email)
      setPassword(password)
      setConfirmPassword('')
      setFirstName('')
      setLastName('')
      setError('')
      setAuthNotice(confirmationMessage)
    } catch (submitError) {
      setError(submitError.message || 'Account creation failed. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleLogout = async () => {
    if (!supabaseClient) {
      return
    }

    await supabaseClient.auth.signOut()
    setSession(null)
    setUserRole('')
    setApiMessage('Logged out successfully.')
  }

  return (
    <div className="page-shell">
      <header className="topbar">
        <div className="brand-block">
          <span className="eyebrow">Church alliance</span>
          <h1>Welcome</h1>
        </div>

        <div className="login-card" aria-label="Authentication panel">
          {session ? (
            <div className="login-user-row">
              <span className="user-pill">
                {userEmail}
                {userRole ? ` (${userRole})` : ''}
              </span>
              <button type="button" onClick={handleLogout}>Log out</button>
            </div>
          ) : (
            <button type="button" onClick={() => setIsLoginOpen(true)}>
              Log in
            </button>
          )}
        </div>
      </header>

      <main className="content-column">
        <section className="banner-block" aria-label="Featured banner">
          <div className="banner-overlay">
            <p className="banner-kicker">Featured update</p>
            <h2>Community rooted in faith and service</h2>
          </div>
        </section>

        <section className="info-strip" aria-label="Quick links">
          {visibleQuickLinks.map((item) => (
            <button
              key={item}
              type="button"
              className={`chip ${visibleActiveSection === item ? 'chip-active' : ''}`}
              aria-current={visibleActiveSection === item ? 'page' : undefined}
              onClick={() => setActiveSection(item)}
            >
              {item}
            </button>
          ))}
        </section>

        {apiMessage ? <p className="status-banner">{apiMessage}</p> : null}

        <MainContent
          activeSection={visibleActiveSection}
          authToken={session?.access_token}
          authUserId={session?.user?.id}
          apiBaseUrl={getApiBaseUrl()}
          userRole={userRole}
          onSelectMembers={() => setActiveSection('Members')}
          onSelectApplications={() => setActiveSection('Site Access Applications')}
          onBackToManagement={() => setActiveSection('Management')}
        />
      </main>

      <footer className="site-footer">
        <p>Copyright 2026 Church Alliance. All rights reserved.</p>
      </footer>

      {isLoginOpen ? (
        <AuthModal
          showSignupForm={showSignupForm}
          email={email}
          password={password}
          confirmPassword={confirmPassword}
          firstName={firstName}
          lastName={lastName}
          isSubmitting={isSubmitting}
          error={error}
          authNotice={authNotice}
          onClose={() => {
            setIsLoginOpen(false)
            setShowSignupForm(false)
            resetAuthForm()
          }}
          onLogin={handleLogin}
          onSignup={handleSignup}
          onFieldChange={(field, value) => {
            const setters = {
              email: setEmail,
              password: setPassword,
              confirmPassword: setConfirmPassword,
              firstName: setFirstName,
              lastName: setLastName,
            }
            setters[field](value)
          }}
          onShowSignup={() => {
            setShowSignupForm(true)
            resetAuthForm()
          }}
          onShowLogin={() => {
            setShowSignupForm(false)
            resetAuthForm()
          }}
        />
      ) : null}
    </div>
  )
}

export default App
