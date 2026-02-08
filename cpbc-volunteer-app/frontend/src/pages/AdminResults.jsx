import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { getVolunteers, exportVolunteers } from '../services/api'
import './AdminDashboard.css'

function AdminResults() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [volunteers, setVolunteers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const ministryArea = searchParams.get('ministry_area') || ''
  const sortBy = searchParams.get('sort_by') || 'date'
  const token = localStorage.getItem('adminToken')

  useEffect(() => {
    if (!token) {
      navigate('/admin')
      return
    }
    loadVolunteers()
  }, [])

  const loadVolunteers = async () => {
    setLoading(true)
    setError(null)
    try {
      const effectiveSortBy = ministryArea ? sortBy : 'name'
      const data = await getVolunteers(token, {
        ministry_area: ministryArea,
        sort_by: effectiveSortBy
      })
      setVolunteers(data.volunteers)
    } catch (err) {
      if (err.response?.status === 401) {
        localStorage.removeItem('adminToken')
        navigate('/admin')
      } else {
        setError('Failed to load volunteers.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async () => {
    try {
      const effectiveSortBy = ministryArea ? sortBy : 'name'
      await exportVolunteers(token, { ministry_area: ministryArea, sort_by: effectiveSortBy })
    } catch (err) {
      setError('Failed to export data')
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <div className="header-top">
          <div className="header-title">
            <p className="church-name">Cross Point Baptist Church</p>
            <h1 className="main-heading">Volunteer Results</h1>
          </div>
          <div className="header-actions">
            <button className="export-button" onClick={handleExport}>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10.75 2.75a.75.75 0 00-1.5 0v8.614L6.295 8.235a.75.75 0 10-1.09 1.03l4.25 4.5a.75.75 0 001.09 0l4.25-4.5a.75.75 0 00-1.09-1.03l-2.955 3.129V2.75z" />
                <path d="M3.5 12.75a.75.75 0 00-1.5 0v2.5A2.75 2.75 0 004.75 18h10.5A2.75 2.75 0 0018 15.25v-2.5a.75.75 0 00-1.5 0v2.5c0 .69-.56 1.25-1.25 1.25H4.75c-.69 0-1.25-.56-1.25-1.25v-2.5z" />
              </svg>
              Export CSV
            </button>
            <button className="logout-button" onClick={() => navigate('/admin')}>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M17 10a.75.75 0 01-.75.75H5.612l4.158 3.96a.75.75 0 11-1.04 1.08l-5.5-5.25a.75.75 0 010-1.08l5.5-5.25a.75.75 0 111.04 1.08L5.612 9.25H16.25A.75.75 0 0117 10z" clipRule="evenodd" />
              </svg>
              Back
            </button>
          </div>
        </div>
      </header>

      <div className="dashboard-content">
        {error && (
          <div className="dashboard-error">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
            </svg>
            <span>{error}</span>
            <button className="error-dismiss" onClick={() => setError(null)}>x</button>
          </div>
        )}

        {ministryArea && (
          <div className="results-filter-info">
            Filtered by: <span className="ministry-tag">{ministryArea}</span>
          </div>
        )}

        <div className="volunteers-section">
          <div className="volunteers-header">
            <h2 className="volunteers-title">Results</h2>
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
                      {ministryArea
                        ? <span className="ministry-tag">{ministryArea}</span>
                        : volunteer.ministries.map(m => (
                            <span key={m.id} className="ministry-tag">{m.ministry_area}</span>
                          ))
                      }
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
                      <td>{volunteer.email}</td>
                      <td>{volunteer.phone}</td>
                      <td>{formatDate(volunteer.signup_date)}</td>
                      <td>
                        <div className="table-ministries">
                          {ministryArea
                            ? <span className="ministry-tag">{ministryArea}</span>
                            : volunteer.ministries.map(m => (
                                <span key={m.id} className="ministry-tag">{m.ministry_area}</span>
                              ))
                          }
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

export default AdminResults
