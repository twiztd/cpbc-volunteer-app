import { useState, useEffect, useMemo } from 'react'
import { adminLogin, getVolunteers, exportVolunteers, getMinistryAreas, getAdminUsers, createAdminUser, updateAdminUser, getVolunteer, updateVolunteer, deleteVolunteer, addVolunteerNote } from '../services/api'
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

  // Admin management state
  const [activeTab, setActiveTab] = useState('volunteers')
  const [adminUsers, setAdminUsers] = useState([])
  const [adminLoading, setAdminLoading] = useState(false)
  const [showAddAdminModal, setShowAddAdminModal] = useState(false)
  const [newAdminData, setNewAdminData] = useState({ email: '', password: '', confirmPassword: '', name: '' })
  const [newAdminError, setNewAdminError] = useState(null)
  const [newAdminLoading, setNewAdminLoading] = useState(false)

  // Volunteer edit modal state
  const [showEditVolunteerModal, setShowEditVolunteerModal] = useState(false)
  const [selectedVolunteer, setSelectedVolunteer] = useState(null)
  const [editVolunteerData, setEditVolunteerData] = useState({ name: '', email: '', phone: '', ministries: [] })
  const [editVolunteerNotes, setEditVolunteerNotes] = useState([])
  const [newNoteText, setNewNoteText] = useState('')
  const [editVolunteerLoading, setEditVolunteerLoading] = useState(false)
  const [editVolunteerError, setEditVolunteerError] = useState(null)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)

  useEffect(() => {
    if (token) {
      setIsAuthenticated(true)
      loadVolunteers()
      loadMinistryAreas()
    }
  }, [token])

  useEffect(() => {
    if (isAuthenticated && activeTab === 'admins') {
      loadAdminUsers()
    }
  }, [activeTab, isAuthenticated])

  const loadMinistryAreas = async () => {
    try {
      const data = await getMinistryAreas()
      setMinistryAreas(data.categories)
    } catch (err) {
      console.error('Failed to load ministry areas:', err)
    }
  }

  const loadAdminUsers = async () => {
    setAdminLoading(true)
    try {
      const data = await getAdminUsers(token)
      setAdminUsers(data.admins)
    } catch (err) {
      if (err.response?.status === 401) {
        handleLogout()
      } else {
        setError('Failed to load admin users')
      }
    } finally {
      setAdminLoading(false)
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
    setAdminUsers([])
    setLoginData({ email: '', password: '' })
    setActiveTab('volunteers')
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

  // Admin management handlers
  const handleAddAdmin = async (e) => {
    e.preventDefault()
    setNewAdminError(null)

    // Validate passwords match
    if (newAdminData.password !== newAdminData.confirmPassword) {
      setNewAdminError('Passwords do not match')
      return
    }

    if (newAdminData.password.length < 6) {
      setNewAdminError('Password must be at least 6 characters')
      return
    }

    setNewAdminLoading(true)

    try {
      await createAdminUser(token, {
        email: newAdminData.email,
        password: newAdminData.password,
        name: newAdminData.name || null
      })
      setShowAddAdminModal(false)
      setNewAdminData({ email: '', password: '', confirmPassword: '', name: '' })
      loadAdminUsers()
    } catch (err) {
      setNewAdminError(err.response?.data?.detail || 'Failed to create admin')
    } finally {
      setNewAdminLoading(false)
    }
  }

  const handleToggleAdminStatus = async (admin) => {
    try {
      await updateAdminUser(token, admin.id, { is_active: !admin.is_active })
      loadAdminUsers()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update admin status')
    }
  }

  // Volunteer edit handlers
  const handleOpenEditVolunteer = async (volunteer) => {
    setEditVolunteerLoading(true)
    setEditVolunteerError(null)
    setShowEditVolunteerModal(true)
    setShowDeleteConfirm(false)
    setNewNoteText('')

    try {
      const data = await getVolunteer(token, volunteer.id)
      setSelectedVolunteer(data)
      setEditVolunteerData({
        name: data.name,
        email: data.email,
        phone: data.phone,
        ministries: data.ministries.map(m => ({ ministry_area: m.ministry_area, category: m.category }))
      })
      setEditVolunteerNotes(data.notes || [])
    } catch (err) {
      if (err.response?.status === 401) {
        handleLogout()
      } else {
        setEditVolunteerError('Failed to load volunteer details')
      }
    } finally {
      setEditVolunteerLoading(false)
    }
  }

  const handleCloseEditVolunteer = () => {
    setShowEditVolunteerModal(false)
    setSelectedVolunteer(null)
    setEditVolunteerData({ name: '', email: '', phone: '', ministries: [] })
    setEditVolunteerNotes([])
    setEditVolunteerError(null)
    setShowDeleteConfirm(false)
    setNewNoteText('')
  }

  const handleMinistryToggle = (ministryArea, category) => {
    setEditVolunteerData(prev => {
      const exists = prev.ministries.some(m => m.ministry_area === ministryArea)
      if (exists) {
        return {
          ...prev,
          ministries: prev.ministries.filter(m => m.ministry_area !== ministryArea)
        }
      } else {
        return {
          ...prev,
          ministries: [...prev.ministries, { ministry_area: ministryArea, category }]
        }
      }
    })
  }

  const handleSaveVolunteer = async (e) => {
    e.preventDefault()
    setEditVolunteerError(null)
    setEditVolunteerLoading(true)

    try {
      await updateVolunteer(token, selectedVolunteer.id, {
        name: editVolunteerData.name,
        email: editVolunteerData.email,
        phone: editVolunteerData.phone,
        ministries: editVolunteerData.ministries
      })
      handleCloseEditVolunteer()
      loadVolunteers()
    } catch (err) {
      setEditVolunteerError(err.response?.data?.detail || 'Failed to update volunteer')
    } finally {
      setEditVolunteerLoading(false)
    }
  }

  const handleDeleteVolunteer = async () => {
    setEditVolunteerLoading(true)
    try {
      await deleteVolunteer(token, selectedVolunteer.id)
      handleCloseEditVolunteer()
      loadVolunteers()
    } catch (err) {
      setEditVolunteerError(err.response?.data?.detail || 'Failed to delete volunteer')
    } finally {
      setEditVolunteerLoading(false)
    }
  }

  const handleAddNote = async () => {
    if (!newNoteText.trim()) return

    setEditVolunteerLoading(true)
    try {
      const newNote = await addVolunteerNote(token, selectedVolunteer.id, newNoteText.trim())
      setEditVolunteerNotes(prev => [newNote, ...prev])
      setNewNoteText('')
    } catch (err) {
      setEditVolunteerError(err.response?.data?.detail || 'Failed to add note')
    } finally {
      setEditVolunteerLoading(false)
    }
  }

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
            <button className="error-dismiss" onClick={() => setError(null)}>×</button>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="tab-navigation">
          <button
            className={`tab-button ${activeTab === 'volunteers' ? 'active' : ''}`}
            onClick={() => setActiveTab('volunteers')}
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10 9a3 3 0 100-6 3 3 0 000 6zM6 8a2 2 0 11-4 0 2 2 0 014 0zM1.49 15.326a.78.78 0 01-.358-.442 3 3 0 014.308-3.516 6.484 6.484 0 00-1.905 3.959c-.023.222-.014.442.025.654a4.97 4.97 0 01-2.07-.655zM16.44 15.98a4.97 4.97 0 002.07-.654.78.78 0 00.357-.442 3 3 0 00-4.308-3.517 6.484 6.484 0 011.907 3.96 2.32 2.32 0 01-.026.654zM18 8a2 2 0 11-4 0 2 2 0 014 0zM5.304 16.19a.844.844 0 01-.277-.71 5 5 0 019.947 0 .843.843 0 01-.277.71A6.975 6.975 0 0110 18a6.974 6.974 0 01-4.696-1.81z" />
            </svg>
            Volunteers
          </button>
          <button
            className={`tab-button ${activeTab === 'admins' ? 'active' : ''}`}
            onClick={() => setActiveTab('admins')}
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-5.5-2.5a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0zM10 12a5.99 5.99 0 00-4.793 2.39A6.483 6.483 0 0010 16.5a6.483 6.483 0 004.793-2.11A5.99 5.99 0 0010 12z" clipRule="evenodd" />
            </svg>
            Manage Admins
          </button>
        </div>

        {activeTab === 'volunteers' ? (
          <>
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
                      <div key={volunteer.id} className="volunteer-card clickable" onClick={() => handleOpenEditVolunteer(volunteer)}>
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
                            <span>{volunteer.email}</span>
                          </div>
                          <div className="volunteer-contact-item">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M2 3.5A1.5 1.5 0 013.5 2h1.148a1.5 1.5 0 011.465 1.175l.716 3.223a1.5 1.5 0 01-1.052 1.767l-.933.267c-.41.117-.643.555-.48.95a11.542 11.542 0 006.254 6.254c.395.163.833-.07.95-.48l.267-.933a1.5 1.5 0 011.767-1.052l3.223.716A1.5 1.5 0 0118 15.352V16.5a1.5 1.5 0 01-1.5 1.5H15c-1.149 0-2.263-.15-3.326-.43A13.022 13.022 0 012.43 8.326 13.019 13.019 0 012 5V3.5z" clipRule="evenodd" />
                            </svg>
                            <span>{volunteer.phone}</span>
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
                        <tr key={volunteer.id} className="clickable" onClick={() => handleOpenEditVolunteer(volunteer)}>
                          <td><strong>{volunteer.name}</strong></td>
                          <td>{volunteer.email}</td>
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
          </>
        ) : (
          /* Admin Management Tab */
          <div className="admin-management">
            <div className="admin-section-header">
              <h2 className="section-title">Admin Users</h2>
              <button className="add-admin-button" onClick={() => setShowAddAdminModal(true)}>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
                </svg>
                Add New Admin
              </button>
            </div>

            <div className="admin-list-section">
              {adminLoading ? (
                <div className="loading-state">
                  <div className="loading-spinner"></div>
                  <span>Loading admins...</span>
                </div>
              ) : adminUsers.length === 0 ? (
                <div className="empty-state">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
                  </svg>
                  <p>No admin users found</p>
                </div>
              ) : (
                <>
                  {/* Mobile Admin Cards */}
                  <div className="admin-cards">
                    {adminUsers.map(admin => (
                      <div key={admin.id} className={`admin-card ${!admin.is_active ? 'inactive' : ''}`}>
                        <div className="admin-card-header">
                          <div className="admin-info">
                            <h3 className="admin-name">{admin.name || admin.email}</h3>
                            {admin.name && <p className="admin-email">{admin.email}</p>}
                          </div>
                          <span className={`status-badge ${admin.is_active ? 'active' : 'inactive'}`}>
                            {admin.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                        <div className="admin-card-footer">
                          <span className="admin-created">Added {formatDate(admin.created_at)}</span>
                          <button
                            className={`toggle-status-button ${admin.is_active ? 'deactivate' : 'activate'}`}
                            onClick={() => handleToggleAdminStatus(admin)}
                          >
                            {admin.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Desktop Admin Table */}
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>Email</th>
                        <th>Name</th>
                        <th>Created</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {adminUsers.map(admin => (
                        <tr key={admin.id} className={!admin.is_active ? 'inactive-row' : ''}>
                          <td><strong>{admin.email}</strong></td>
                          <td>{admin.name || '—'}</td>
                          <td>{formatDate(admin.created_at)}</td>
                          <td>
                            <span className={`status-badge ${admin.is_active ? 'active' : 'inactive'}`}>
                              {admin.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td>
                            <button
                              className={`toggle-status-button ${admin.is_active ? 'deactivate' : 'activate'}`}
                              onClick={() => handleToggleAdminStatus(admin)}
                            >
                              {admin.is_active ? 'Deactivate' : 'Activate'}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Add Admin Modal */}
      {showAddAdminModal && (
        <div className="modal-overlay" onClick={() => setShowAddAdminModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Add New Admin</h2>
              <button className="modal-close" onClick={() => setShowAddAdminModal(false)}>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                </svg>
              </button>
            </div>

            <form className="modal-form" onSubmit={handleAddAdmin}>
              {newAdminError && (
                <div className="login-error">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
                  </svg>
                  <span>{newAdminError}</span>
                </div>
              )}

              <div className="form-group">
                <label className="form-label" htmlFor="new-admin-email">
                  Email <span className="required">*</span>
                </label>
                <input
                  type="email"
                  id="new-admin-email"
                  className="form-input"
                  placeholder="newadam@crosspoint.org"
                  value={newAdminData.email}
                  onChange={(e) => setNewAdminData(prev => ({ ...prev, email: e.target.value }))}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="new-admin-name">
                  Name (Optional)
                </label>
                <input
                  type="text"
                  id="new-admin-name"
                  className="form-input"
                  placeholder="John Smith"
                  value={newAdminData.name}
                  onChange={(e) => setNewAdminData(prev => ({ ...prev, name: e.target.value }))}
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="new-admin-password">
                  Password <span className="required">*</span>
                </label>
                <input
                  type="password"
                  id="new-admin-password"
                  className="form-input"
                  placeholder="Min 6 characters"
                  value={newAdminData.password}
                  onChange={(e) => setNewAdminData(prev => ({ ...prev, password: e.target.value }))}
                  required
                  minLength={6}
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="new-admin-confirm">
                  Confirm Password <span className="required">*</span>
                </label>
                <input
                  type="password"
                  id="new-admin-confirm"
                  className="form-input"
                  placeholder="Re-enter password"
                  value={newAdminData.confirmPassword}
                  onChange={(e) => setNewAdminData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                  required
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="cancel-button"
                  onClick={() => setShowAddAdminModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="submit-button"
                  disabled={newAdminLoading}
                >
                  {newAdminLoading ? (
                    <>
                      <span className="button-spinner"></span>
                      Creating...
                    </>
                  ) : (
                    'Create Admin'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Volunteer Modal */}
      {showEditVolunteerModal && (
        <div className="modal-overlay" onClick={handleCloseEditVolunteer}>
          <div className="modal-content edit-volunteer-modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Edit Volunteer</h2>
              <button className="modal-close" onClick={handleCloseEditVolunteer}>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                </svg>
              </button>
            </div>

            {editVolunteerLoading && !selectedVolunteer ? (
              <div className="modal-loading">
                <div className="loading-spinner"></div>
                <span>Loading volunteer details...</span>
              </div>
            ) : (
              <>
                <form className="modal-form" onSubmit={handleSaveVolunteer}>
                  {editVolunteerError && (
                    <div className="login-error">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
                      </svg>
                      <span>{editVolunteerError}</span>
                    </div>
                  )}

                  <div className="form-group">
                    <label className="form-label" htmlFor="edit-volunteer-name">
                      Name <span className="required">*</span>
                    </label>
                    <input
                      type="text"
                      id="edit-volunteer-name"
                      className="form-input"
                      value={editVolunteerData.name}
                      onChange={(e) => setEditVolunteerData(prev => ({ ...prev, name: e.target.value }))}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label" htmlFor="edit-volunteer-email">
                      Email <span className="required">*</span>
                    </label>
                    <input
                      type="email"
                      id="edit-volunteer-email"
                      className="form-input"
                      value={editVolunteerData.email}
                      onChange={(e) => setEditVolunteerData(prev => ({ ...prev, email: e.target.value }))}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label" htmlFor="edit-volunteer-phone">
                      Phone <span className="required">*</span>
                    </label>
                    <input
                      type="tel"
                      id="edit-volunteer-phone"
                      className="form-input"
                      value={editVolunteerData.phone}
                      onChange={(e) => setEditVolunteerData(prev => ({ ...prev, phone: e.target.value }))}
                      required
                    />
                  </div>

                  {/* Ministry Areas Selection */}
                  <div className="form-group">
                    <label className="form-label">Ministry Areas</label>
                    <div className="ministry-checkboxes">
                      {Object.entries(ministryAreas).map(([category, ministries]) => (
                        <div key={category} className="ministry-category">
                          <h4 className="category-title">{category}</h4>
                          <div className="ministry-options">
                            {ministries.map(ministry => (
                              <label key={ministry} className="ministry-checkbox">
                                <input
                                  type="checkbox"
                                  checked={editVolunteerData.ministries.some(m => m.ministry_area === ministry)}
                                  onChange={() => handleMinistryToggle(ministry, category)}
                                />
                                <span className="checkbox-label">{ministry}</span>
                              </label>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </form>

                {/* Notes Section */}
                <div className="notes-section">
                  <h3 className="notes-title">Notes</h3>
                  <div className="add-note">
                    <textarea
                      className="note-input"
                      placeholder="Add a note about this volunteer..."
                      value={newNoteText}
                      onChange={(e) => setNewNoteText(e.target.value)}
                      rows={3}
                    />
                    <button
                      type="button"
                      className="add-note-button"
                      onClick={handleAddNote}
                      disabled={!newNoteText.trim() || editVolunteerLoading}
                    >
                      Add Note
                    </button>
                  </div>
                  <div className="notes-list">
                    {editVolunteerNotes.length === 0 ? (
                      <p className="no-notes">No notes yet</p>
                    ) : (
                      editVolunteerNotes.map(note => (
                        <div key={note.id} className="note-item">
                          <div className="note-header">
                            <span className="note-author">{note.admin_name || note.admin_email || 'Admin'}</span>
                            <span className="note-date">{formatDate(note.created_at)}</span>
                          </div>
                          <p className="note-text">{note.note_text}</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                <div className="modal-actions edit-volunteer-actions">
                  {!showDeleteConfirm ? (
                    <>
                      <button
                        type="button"
                        className="delete-button"
                        onClick={() => setShowDeleteConfirm(true)}
                      >
                        Delete
                      </button>
                      <div className="action-spacer"></div>
                      <button
                        type="button"
                        className="cancel-button"
                        onClick={handleCloseEditVolunteer}
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="submit-button"
                        disabled={editVolunteerLoading}
                        onClick={handleSaveVolunteer}
                      >
                        {editVolunteerLoading ? 'Saving...' : 'Save Changes'}
                      </button>
                    </>
                  ) : (
                    <>
                      <span className="delete-confirm-text">Delete this volunteer?</span>
                      <button
                        type="button"
                        className="cancel-button"
                        onClick={() => setShowDeleteConfirm(false)}
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        className="confirm-delete-button"
                        onClick={handleDeleteVolunteer}
                        disabled={editVolunteerLoading}
                      >
                        {editVolunteerLoading ? 'Deleting...' : 'Yes, Delete'}
                      </button>
                    </>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default AdminDashboard
