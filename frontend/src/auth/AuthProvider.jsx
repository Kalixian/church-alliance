import { useEffect, useState } from 'react'
import { createClient } from '@supabase/supabase-js'
import AuthModal from '../components/AuthModal'
import { AuthContext, MANAGER_ROLES } from './authContext'

const apiBaseUrl = import.meta.env.VITE_API_URL

const getSupabaseClient = () => {
  const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
  const supabasePublishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY

  if (!supabaseUrl || !supabasePublishableKey) {
    return null
  }

  return createClient(supabaseUrl, supabasePublishableKey)
}

async function syncUser(token) {
  return fetch(`${apiBaseUrl}/api/v1/auth/sync-user`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })
}

function AuthProvider({ children }) {
  const [supabaseClient, setSupabaseClient] = useState(null)
  const [session, setSession] = useState(null)
  const [isAuthReady, setIsAuthReady] = useState(false)
  const [isLoginOpen, setIsLoginOpen] = useState(false)
  const [showSignupForm, setShowSignupForm] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [statusMessage, setStatusMessage] = useState('')
  const [authNotice, setAuthNotice] = useState('')
  const [userRole, setUserRole] = useState('')
  const [backendUserId, setBackendUserId] = useState('')

  const fetchUserRole = async (token) => {
    if (!token) {
      return ''
    }

    const syncResponse = await syncUser(token)
    if (!syncResponse.ok) {
      return ''
    }

    const user = await syncResponse.json().catch(() => ({}))
    setUserRole(user.role || '')
    setBackendUserId(user.id || '')
    return user
  }

  useEffect(() => {
    const client = getSupabaseClient()
    setSupabaseClient(client)

    if (!client) {
      setIsAuthReady(true)
      return undefined
    }

    const { data: { subscription } } = client.auth.onAuthStateChange(
      async (_event, nextSession) => {
        setSession(nextSession)
        const nextToken = nextSession?.access_token
        if (nextToken) {
          await fetchUserRole(nextToken)
        } else {
          setUserRole('')
          setBackendUserId('')
        }
      },
    )

    client.auth.getSession()
      .then(async ({ data: { session: currentSession } }) => {
        setSession(currentSession)
        if (currentSession?.access_token) {
          await fetchUserRole(currentSession.access_token)
        }
      })
      .catch(() => {})
      .finally(() => setIsAuthReady(true))

    return () => subscription.unsubscribe()
  }, [])

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
    setStatusMessage('')

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

      const syncResponse = await syncUser(token)
      if (!syncResponse.ok) {
        const syncError = await syncResponse.json().catch(() => ({ detail: 'Authentication failed.' }))
        throw new Error(syncError.detail || 'Authentication failed.')
      }

      const backendUser = await syncResponse.json().catch(() => ({}))
      setSession(data.session)
      setUserRole(backendUser.role || '')
      setBackendUserId(backendUser.id || '')
      setIsLoginOpen(false)
      setShowSignupForm(false)
      resetAuthForm()
      setStatusMessage(`Logged in as ${data.user.email}`)
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
    setStatusMessage('')
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

      setShowSignupForm(false)
      setIsLoginOpen(true)
      setConfirmPassword('')
      setFirstName('')
      setLastName('')
      setError('')
      setAuthNotice(`A confirmation email has been sent to ${email}.`)
    } catch (submitError) {
      setError(submitError.message || 'Account creation failed. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const logout = async () => {
    if (!supabaseClient) {
      return
    }

    await supabaseClient.auth.signOut()
    setSession(null)
    setUserRole('')
    setBackendUserId('')
    setStatusMessage('Logged out successfully.')
  }

  const isSignedIn = Boolean(session)
  const isConfirmed = isSignedIn && Boolean(userRole) && userRole !== 'applicant'
  const isManager = isSignedIn && MANAGER_ROLES.includes(userRole)

  const value = {
    apiBaseUrl,
    session,
    token: session?.access_token,
    authUserId: session?.user?.id,
    userEmail: session?.user?.email || 'Signed in user',
    userRole,
    backendUserId,
    isAuthReady,
    isSignedIn,
    isConfirmed,
    isManager,
    isAdmin: isSignedIn && userRole === 'administrator',
    statusMessage,
    setStatusMessage,
    openLogin: () => setIsLoginOpen(true),
    logout,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
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
          onFieldChange={(field, nextValue) => {
            const setters = {
              email: setEmail,
              password: setPassword,
              confirmPassword: setConfirmPassword,
              firstName: setFirstName,
              lastName: setLastName,
            }
            setters[field](nextValue)
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
    </AuthContext.Provider>
  )
}

export default AuthProvider
