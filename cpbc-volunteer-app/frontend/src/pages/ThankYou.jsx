import { useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import './ThankYou.css'

// Category order for consistent display
const CATEGORY_ORDER = [
  "Children's Ministry",
  "Hospitality",
  "Media",
  "Missions",
  "Member Care",
  "Community Outreach",
  "Building/Grounds"
]

function ThankYou() {
  const location = useLocation()
  const navigate = useNavigate()
  const volunteer = location.state?.volunteer

  useEffect(() => {
    // Redirect to form if accessed directly without data
    if (!volunteer) {
      navigate('/', { replace: true })
    }
  }, [volunteer, navigate])

  if (!volunteer) {
    return null
  }

  // Group ministries by category
  const groupedMinistries = volunteer.ministries.reduce((acc, ministry) => {
    if (!acc[ministry.category]) {
      acc[ministry.category] = []
    }
    acc[ministry.category].push(ministry.ministry_area)
    return acc
  }, {})

  // Sort categories by the defined order
  const sortedCategories = CATEGORY_ORDER.filter(
    category => groupedMinistries[category]
  )

  const handleSignUpAnother = () => {
    navigate('/', { replace: true })
  }

  return (
    <div className="thank-you-page">
      <div className="thank-you-container">
        <header className="thank-you-header">
          <div className="success-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="thank-you-heading">Thank You!</h1>
          <p className="thank-you-message">
            Thank you for signing up to serve at Cross Point! We're so glad you want
            to be part of what God is doing here.
          </p>
        </header>

        <section className="summary-section">
          <h2 className="summary-title">Your Signup Summary</h2>

          <div className="volunteer-info">
            <div className="info-row">
              <span className="info-label">Name</span>
              <span className="info-value">{volunteer.name}</span>
            </div>
          </div>

          <div className="ministry-summary">
            <h3 className="ministry-summary-title">Ministry Areas</h3>

            {sortedCategories.map(category => (
              <div key={category} className="ministry-group">
                <h4 className="ministry-category-name">{category}</h4>
                <ul className="ministry-list">
                  {groupedMinistries[category].map(area => (
                    <li key={area} className="ministry-item">
                      <svg className="check-icon" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      {area}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>

        <div className="thank-you-actions">
          <p className="next-steps">
            A member of our team will be in touch soon about next steps for the
            ministry areas you selected.
          </p>

          <button
            className="another-signup-button"
            onClick={handleSignUpAnother}
          >
            Sign Up Another Person
          </button>
        </div>

        <footer className="thank-you-footer">
          <p className="church-name">Cross Point Baptist Church</p>
        </footer>
      </div>
    </div>
  )
}

export default ThankYou
