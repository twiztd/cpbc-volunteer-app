import { useState, useEffect } from 'react'
import { adminLogin, getVolunteers, exportVolunteers } from '../services/api'

function AdminDashboard() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [token, setToken] = useState(localStorage.getItem('adminToken'))
  const [loginData, setLoginData] = useState({ email: '', password: '' })
  const [volunteers, setVolunteers] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [filters, setFilters] = useState({ ministry_area: '', sort_by: 'date' })

  useEffect(() => {
    if (token) {
      setIsAuthenticated(true)
      loadVolunteers()
    }
  }, [token])

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const data = await adminLogin(loginData.email, loginData.password)
      localStorage.setItem('adminToken', data.access_token)
      setToken(data.access_token)
      setIsAuthenticated(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('adminToken')
    setToken(null)
    setIsAuthenticated(false)
    setVolunteers([])
  }

  const loadVolunteers = async () => {
    setLoading(true)
    try {
      const data = await getVolunteers(token, filters)
      setVolunteers(data.volunteers)
    } catch (err) {
      if (err.response?.status === 401) {
        handleLogout()
      }
      setError('Failed to load volunteers')
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
    if (isAuthenticated) {
      loadVolunteers()
    }
  }, [filters])

  if (!isAuthenticated) {
    return (
      <div className="login-container">
        <h1>Admin Login</h1>
        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={loginData.email}
              onChange={(e) => setLoginData(prev => ({ ...prev, email: e.target.value }))}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={loginData.password}
              onChange={(e) => setLoginData(prev => ({ ...prev, password: e.target.value }))}
              required
            />
          </div>

          <button type="submit" disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      </div>
    )
  }

  return (
    <div className="dashboard-container">
      <header>
        <h1>Volunteer Dashboard</h1>
        <button onClick={handleLogout}>Logout</button>
      </header>

      {error && <div className="error-message">{error}</div>}

      <div className="filters">
        <select name="sort_by" value={filters.sort_by} onChange={handleFilterChange}>
          <option value="date">Sort by Date</option>
          <option value="name">Sort by Name</option>
          <option value="ministry">Sort by Ministry Count</option>
        </select>

        <input
          type="text"
          name="ministry_area"
          placeholder="Filter by ministry area..."
          value={filters.ministry_area}
          onChange={handleFilterChange}
        />

        <button onClick={handleExport}>Export CSV</button>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : (
        <div className="volunteer-list">
          <p>Total volunteers: {volunteers.length}</p>

          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Phone</th>
                <th>Email</th>
                <th>Signup Date</th>
                <th>Ministry Areas</th>
              </tr>
            </thead>
            <tbody>
              {volunteers.map(volunteer => (
                <tr key={volunteer.id}>
                  <td>{volunteer.name}</td>
                  <td>{volunteer.phone}</td>
                  <td>{volunteer.email}</td>
                  <td>{new Date(volunteer.signup_date).toLocaleDateString()}</td>
                  <td>
                    {volunteer.ministries.map(m => m.ministry_area).join(', ')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default AdminDashboard
