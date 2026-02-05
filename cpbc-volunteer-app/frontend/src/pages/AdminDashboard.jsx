import { useState, useEffect, useMemo } from 'react'
import { adminLogin, getVolunteers, exportVolunteers, getMinistryAreas } from '../services/api'
import './AdminDashboard.css'

function AdminDashboard() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [token, setToken] = useState(localStorage.getItem('adminToken'))
  const [loginData, setLoginData] = useState({ email: '', password: '' })
  const [volunteers, setVolunteers] = useState([])
  const [ministryAreas, setMinistryAreas] = useState({})
  const [loading, setLoading] = useState(false)
  const [loginLoading, setLoginLoading] = useState(false)
  const [error, setError] = useState(null)
  const [loginError, setLoginError] = useState(null)
  const [filters, setFilters] = useState({ ministry_area: '', sort_by: 'date' })

  useEffect(() => {
    if (token) {
      setIsAuthenticated(true)
      loadVolunteers()
      loadMinistryAreas()
    }
  }, [token])

  const loadMinistryAreas = async () => {
    try {
      const data = await getMinistryAreas()
      setMinistryAreas(data.categories)
    } catch (err) {
      console.error('Failed to load ministry areas:', err)
    }
  }

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoginLoading(true)
    setLoginError(null)

    try {
      const data = await adminLogin(loginData.email, loginData.password)
      localStorage.setItem('adminToken', data.access_token)
      setToken(data.access_token)
      setIsAuthenticated(true)
    } catch (err) {
      setLoginError(err.response?.data?.detail || 'Invalid email or password')
    } finally {
      setLoginLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('adminToken')
    setToken(null)
    setIsAuthenticated(false)
    setVolunteers([])
    setLoginData({ email: '', password: '' })
  }

  const loadVolunteers = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getVolunteers(token, filters)
      setVolunteers(data.volunteers)
    } catch (err) {
      if (err.response?.status === 401) {
        handleLogout()
      } else {
        setError('Failed to load volunteers. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async () => {
    try {
      await exportVolunteers(token)
    } catch (err) {
      setError('Failed to export data')
    }
  }

  const handleFilterChange = (e) => {
    const { name, value } = e.target
    setFilters(prev => ({ ...prev, [name]: value }))
  }

  useEffect(() => {
    if (isAuthenticated && token) {
      loadVolunteers()
    }
  }, [filters])

  // Calculate stats
  const stats = useMemo(() => {
    const now = new Date()
    const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)

    const thisWeek = volunteers.filter(v =>
      new Date(v.signup_date) >= oneWeekAgo
    ).length

    const totalMinistries = volunteers.reduce((sum, v) =>
      sum + v.ministries.length, 0
    )

    const uniqueMinistries = new Set(
      volunteers.flatMap(v => v.ministries.map(m => m.ministry_area))
    ).size

    return {
      total: volunteers.length,
      thisWeek,
      totalMinistries,
      uniqueMinistries
    }
  }, [volunteers])

  // Get all ministry areas for filter dropdown
  const allMinistryAreas = useMemo(() => {
    const areas = []
    Object.entries(ministryAreas).forEach(([category, ministries]) => {
      ministries.forEach(ministry => {
        areas.push({ category, ministry })
      })
    })
    return areas
  }, [ministryAreas])

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  // Login Page
  if (!isAuthenticated) {
    return (
      <div className="login-page">
        <div className="login-container">
          <div className="login-header">
            <p className="church-name">Cross Point Baptist Church</p>
            <h1 className="main-heading">Admin Login</h1>
          </div>

          <form className="login-form" onSubmit={handleLogin}>
            {loginError && (
              <div className="login-error">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
                </svg>
                <span>{loginError}</span>
              </div>
            )}

            <div className="form-group">
              <label className="form-label" htmlFor="email">
                Email <span className="required">*</span>
              </label>
              <input
                type="email"
                id="email"
                className="form-input"
                placeholder="admin@crosspoint.org"
                value={loginData.email}
                onChange={(e) => setLoginData(prev => ({ ...prev, email: e.target.value }))}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="password">
                Password <span className="required">*</span>
              </label>
              <input
                type="password"
                id="password"
                className="form-input"
                placeholder="Enter your password"
                value={loginData.password}
                onChange={(e) => setLoginData(prev => ({ ...prev, password: e.target.value }))}
                required
              />
            </div>
          </form>

          <div className="login-actions">
            <button
              type="submit"
              className="submit-button"
              disabled={loginLoading}
              onClick={handleLogin}
            >
              {loginLoading ? (
                <>
                  <span className="button-spinner"></span>
                  Logging in...
                </>
              ) : (
                'Login'
              )}
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Dashboard Page
  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <div className="header-top">
          <div className="header-title">
            <p className="church-name">Cross Point Baptist Church</p>
            <h1 className="main-heading">Admin Dashboard</h1>
          </div>
          <button className="logout-button" onClick={handleLogout}>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M3 4.25A2.25 2.25 0 015.25 2h5.5A2.25 2.25 0 0113 4.25v2a.75.75 0 01-1.5 0v-2a.75.75 0 00-.75-.75h-5.5a.75.75 0 00-.75.75v11.5c0 .414.336.75.75.75h5.5a.75.75 0 00.75-.75v-2a.75.75 0 011.5 0v2A2.25 2.25 0 0110.75 18h-5.5A2.25 2.25 0 013 15.75V4.25z" clipRule="evenodd" />
              <path fillRule="evenodd" d="M19 10a.75.75 0 00-.75-.75H8.704l1.048-.943a.75.75 0 10-1.004-1.114l-2.5 2.25a.75.75 0 000 1.114l2.5 2.25a.75.75 0 101.004-1.114l-1.048-.943h9.546A.75.75 0 0019 10z" clipRule="evenodd" />
            </svg>
            Logout
          </button>
        </div>
      </header>

      <div className="dashboard-content">
        {error && (
          <div className="dashboard-error">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        {/* Stats Cards */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{stats.total}</div>
            <div className="stat-label">Total Volunteers</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.thisWeek}</div>
            <div className="stat-label">This Week</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.totalMinistries}</div>
            <div className="stat-label">Ministry Signups</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.uniqueMinistries}</div>
            <div className="stat-label">Active Ministries</div>
          </div>
        </div>

        {/* Filters */}
        <div className="filters-section">
          <div className="filters-row">
            <div className="filter-group">
              <label className="filter-label">Sort By</label>
              <select
                name="sort_by"
                className="filter-select"
                value={filters.sort_by}
                onChange={handleFilterChange}
              >
                <option value="date">Signup Date (Newest)</option>
                <option value="name">Name (A-Z)</option>
                <option value="ministry">Ministry Count</option>
              </select>
            </div>

            <div className="filter-group">
              <label className="filter-label">Filter by Ministry</label>
              <select
                name="ministry_area"
                className="filter-select"
                value={filters.ministry_area}
                onChange={handleFilterChange}
              >
                <option value="">All Ministries</option>
                {allMinistryAreas.map(({ category, ministry }) => (
                  <option key={ministry} value={ministry}>
                    {ministry}
                  </option>
                ))}
              </select>
            </div>

            <div className="filter-actions">
              <button className="export-button" onClick={handleExport}>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M10.75 2.75a.75.75 0 00-1.5 0v8.614L6.295 8.235a.75.75 0 10-1.09 1.03l4.25 4.5a.75.75 0 001.09 0l4.25-4.5a.75.75 0 00-1.09-1.03l-2.955 3.129V2.75z" />
                  <path d="M3.5 12.75a.75.75 0 00-1.5 0v2.5A2.75 2.75 0 004.75 18h10.5A2.75 2.75 0 0018 15.25v-2.5a.75.75 0 00-1.5 0v2.5c0 .69-.56 1.25-1.25 1.25H4.75c-.69 0-1.25-.56-1.25-1.25v-2.5z" />
                </svg>
                Export CSV
              </button>
            </div>
          </div>
        </div>

        {/* Volunteers List */}
        <div className="volunteers-section">
          <div className="volunteers-header">
            <h2 className="volunteers-title">Volunteer Signups</h2>
            <span className="volunteers-count">{volunteers.length} total</span>
          </div>

          {loading ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <span>Loading volunteers...</span>
            </div>
          ) : volunteers.length === 0 ? (
            <div className="empty-state">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
              </svg>
              <p>No volunteers found</p>
            </div>
          ) : (
            <>
              {/* Mobile Cards */}
              <div className="volunteer-cards">
                {volunteers.map(volunteer => (
                  <div key={volunteer.id} className="volunteer-card">
                    <div className="volunteer-card-header">
                      <h3 className="volunteer-name">{volunteer.name}</h3>
                      <span className="volunteer-date">{formatDate(volunteer.signup_date)}</span>
                    </div>
                    <div className="volunteer-contact">
                      <div className="volunteer-contact-item">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                          <path d="M3 4a2 2 0 00-2 2v1.161l8.441 4.221a1.25 1.25 0 001.118 0L19 7.162V6a2 2 0 00-2-2H3z" />
                          <path d="M19 8.839l-7.77 3.885a2.75 2.75 0 01-2.46 0L1 8.839V14a2 2 0 002 2h14a2 2 0 002-2V8.839z" />
                        </svg>
                        <a href={`mailto:${volunteer.email}`}>{volunteer.email}</a>
                      </div>
                      <div className="volunteer-contact-item">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M2 3.5A1.5 1.5 0 013.5 2h1.148a1.5 1.5 0 011.465 1.175l.716 3.223a1.5 1.5 0 01-1.052 1.767l-.933.267c-.41.117-.643.555-.48.95a11.542 11.542 0 006.254 6.254c.395.163.833-.07.95-.48l.267-.933a1.5 1.5 0 011.767-1.052l3.223.716A1.5 1.5 0 0118 15.352V16.5a1.5 1.5 0 01-1.5 1.5H15c-1.149 0-2.263-.15-3.326-.43A13.022 13.022 0 012.43 8.326 13.019 13.019 0 012 5V3.5z" clipRule="evenodd" />
                        </svg>
                        <a href={`tel:${volunteer.phone}`}>{volunteer.phone}</a>
                      </div>
                    </div>
                    <div className="volunteer-ministries">
                      {volunteer.ministries.map(m => (
                        <span key={m.id} className="ministry-tag">
                          {m.ministry_area}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {/* Desktop Table */}
              <table className="volunteers-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Signup Date</th>
                    <th>Ministry Areas</th>
                  </tr>
                </thead>
                <tbody>
                  {volunteers.map(volunteer => (
                    <tr key={volunteer.id}>
                      <td><strong>{volunteer.name}</strong></td>
                      <td>
                        <a href={`mailto:${volunteer.email}`} style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>
                          {volunteer.email}
                        </a>
                      </td>
                      <td>{volunteer.phone}</td>
                      <td>{formatDate(volunteer.signup_date)}</td>
                      <td>
                        <div className="table-ministries">
                          {volunteer.ministries.map(m => (
                            <span key={m.id} className="ministry-tag">
                              {m.ministry_area}
                            </span>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default AdminDashboard
