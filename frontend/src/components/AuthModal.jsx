function AuthModal({
  showSignupForm,
  email,
  password,
  confirmPassword,
  firstName,
  lastName,
  isSubmitting,
  error,
  authNotice,
  onClose,
  onLogin,
  onSignup,
  onFieldChange,
  onShowSignup,
  onShowLogin,
}) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="login-modal" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <h3>{showSignupForm ? 'Member Access Setup' : 'Church Alliance Login'}</h3>
          <button type="button" className="close-button" onClick={onClose}>
            ×
          </button>
        </div>

        {showSignupForm ? (
          <form className="login-form" onSubmit={onSignup}>
            <p className="signup-note">
              If you are involved with the organization and would like access to the site, tell us who you are below.
            </p>

            <label>
              <span>Email</span>
              <input
                type="email"
                value={email}
                onChange={(event) => onFieldChange('email', event.target.value)}
                placeholder="you@example.com"
                required
              />
            </label>

            <label>
              <span>Password</span>
              <input
                type="password"
                value={password}
                onChange={(event) => onFieldChange('password', event.target.value)}
                placeholder="Create a password"
                required
              />
            </label>

            <label>
              <span>Confirm password</span>
              <input
                type="password"
                value={confirmPassword}
                onChange={(event) => onFieldChange('confirmPassword', event.target.value)}
                placeholder="Re-type your password"
                required
              />
            </label>

            <div className="name-row">
              <label>
                <span>First Name</span>
                <input
                  type="text"
                  value={firstName}
                  onChange={(event) => onFieldChange('firstName', event.target.value)}
                  placeholder="First name"
                  required
                />
              </label>

              <label>
                <span>Last Name</span>
                <input
                  type="text"
                  value={lastName}
                  onChange={(event) => onFieldChange('lastName', event.target.value)}
                  placeholder="Last name"
                  required
                />
              </label>
            </div>

            {error ? <p className="error-message">{error}</p> : null}

            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Submitting...' : 'Request Access'}
            </button>

            <button type="button" className="secondary-button" onClick={onShowLogin}>
              Back to login
            </button>
          </form>
        ) : (
          <form className="login-form" onSubmit={onLogin}>
            <label>
              <span>Email</span>
              <input
                type="email"
                value={email}
                onChange={(event) => onFieldChange('email', event.target.value)}
                placeholder="you@example.com"
                required
              />
            </label>

            <label>
              <span>Password</span>
              <input
                type="password"
                value={password}
                onChange={(event) => onFieldChange('password', event.target.value)}
                placeholder="••••••••"
                required
              />
            </label>

            {authNotice ? <p className="status-banner">{authNotice}</p> : null}
            {error ? <p className="error-message">{error}</p> : null}

            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Signing in...' : 'Log in'}
            </button>

            <button type="button" className="secondary-button" onClick={onShowSignup}>
              Create Site Account
            </button>
          </form>
        )}
      </div>
    </div>
  )
}

export default AuthModal
