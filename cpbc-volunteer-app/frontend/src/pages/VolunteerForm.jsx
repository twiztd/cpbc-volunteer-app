import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getMinistryAreas, submitVolunteer } from '../services/api'
import './VolunteerForm.css'

// Fallback ministry categories for when backend is unavailable
const FALLBACK_CATEGORIES = {
  "Children's Ministry": [
    "Childcare and/or Teaching",
    "VBS"
  ],
  "Hospitality": [
    "Greeters",
    "Make Contact with Visitors",
    "Kitchen Cleanup"
  ],
  "Media": [
    "Sound, etc.",
    "Social Media"
  ],
  "Missions": [
    "Guatemala Mission Trip",
    "El Salvador Mission Trip",
    "3:18 Church (Third Saturday)",
    "5 Loaves 2 Fish (Thursday before 1st Saturday)"
  ],
  "Member Care": [
    "Meal Trains for members in need",
    "Help for Elderly/Widows"
  ],
  "Community Outreach": [
    "Trunk or Treat",
    "Easter Event",
    "New Outreach Programs"
  ],
  "Building/Grounds": [
    "Maintenance",
    "Security"
  ]
}

// Preserve category order
const CATEGORY_ORDER = [
  "Children's Ministry",
  "Hospitality",
  "Media",
  "Missions",
  "Member Care",
  "Community Outreach",
  "Building/Grounds"
]

function VolunteerForm() {
  const navigate = useNavigate()

  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    email: '',
    ministries: []
  })

  const [ministryCategories, setMinistryCategories] = useState(FALLBACK_CATEGORIES)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [fieldErrors, setFieldErrors] = useState({})
  const [touched, setTouched] = useState({})

  useEffect(() => {
    loadMinistryAreas()
  }, [])

  const loadMinistryAreas = async () => {
    try {
      const data = await getMinistryAreas()
      setMinistryCategories(data.categories)
    } catch (err) {
      // Use fallback categories if API fails
      console.warn('Using fallback ministry categories')
      setMinistryCategories(FALLBACK_CATEGORIES)
    } finally {
      setLoading(false)
    }
  }

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  const validateField = (name, value) => {
    switch (name) {
      case 'name':
        return value.trim() ? '' : 'Name is required'
      case 'phone':
        return value.trim() ? '' : 'Phone number is required'
      case 'email':
        if (!value.trim()) return 'Email is required'
        if (!validateEmail(value)) return 'Please enter a valid email address'
        return ''
      default:
        return ''
    }
  }

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))

    // Clear error when user starts typing
    if (touched[name]) {
      const error = validateField(name, value)
      setFieldErrors(prev => ({ ...prev, [name]: error }))
    }
  }

  const handleBlur = (e) => {
    const { name, value } = e.target
    setTouched(prev => ({ ...prev, [name]: true }))
    const error = validateField(name, value)
    setFieldErrors(prev => ({ ...prev, [name]: error }))
  }

  const handleMinistryToggle = (category, ministryArea) => {
    setFormData(prev => {
      const existing = prev.ministries.find(
        m => m.category === category && m.ministry_area === ministryArea
      )

      if (existing) {
        return {
          ...prev,
          ministries: prev.ministries.filter(
            m => !(m.category === category && m.ministry_area === ministryArea)
          )
        }
      } else {
        return {
          ...prev,
          ministries: [...prev.ministries, { category, ministry_area: ministryArea }]
        }
      }
    })

    // Clear ministry error when user selects something
    if (fieldErrors.ministries) {
      setFieldErrors(prev => ({ ...prev, ministries: '' }))
    }
  }

  const isMinistrySelected = (category, ministryArea) => {
    return formData.ministries.some(
      m => m.category === category && m.ministry_area === ministryArea
    )
  }

  const validateForm = () => {
    const errors = {
      name: validateField('name', formData.name),
      phone: validateField('phone', formData.phone),
      email: validateField('email', formData.email),
      ministries: formData.ministries.length === 0 ? 'Please select at least one ministry area' : ''
    }

    setFieldErrors(errors)
    setTouched({ name: true, phone: true, email: true })

    return !errors.name && !errors.phone && !errors.email && !errors.ministries
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    if (!validateForm()) {
      return
    }

    setSubmitting(true)

    try {
      const response = await submitVolunteer(formData)
      // Navigate to thank you page with the submitted data
      navigate('/thank-you', {
        state: {
          volunteer: {
            name: formData.name,
            email: formData.email,
            phone: formData.phone,
            ministries: formData.ministries
          }
        }
      })
    } catch (err) {
      setError('Something went wrong. Please try again, or see a staff member for help.')
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="volunteer-form-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="volunteer-form-page">
      <div className="form-container">
        <header className="form-header">
          <p className="church-name">Cross Point Baptist Church</p>
          <h1 className="main-heading">CROSS POINT NEEDS YOU!</h1>
          <p className="welcome-message">
            Get plugged in to serving with your church family! Complete your contact
            information and check the areas you're interested in serving in.
          </p>
        </header>

        {error && (
          <div className="error-banner" role="alert">
            <svg className="error-icon" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <section className="form-section contact-section">
            <h2 className="section-title">Your Information</h2>

            <div className="form-group">
              <label htmlFor="name" className="form-label">
                Name <span className="required">*</span>
              </label>
              <input
                type="text"
                id="name"
                name="name"
                className={`form-input ${fieldErrors.name && touched.name ? 'input-error' : ''}`}
                value={formData.name}
                onChange={handleInputChange}
                onBlur={handleBlur}
                placeholder="Enter your full name"
                autoComplete="name"
              />
              {fieldErrors.name && touched.name && (
                <span className="field-error">{fieldErrors.name}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="phone" className="form-label">
                Phone Number <span className="required">*</span>
              </label>
              <input
                type="tel"
                id="phone"
                name="phone"
                className={`form-input ${fieldErrors.phone && touched.phone ? 'input-error' : ''}`}
                value={formData.phone}
                onChange={handleInputChange}
                onBlur={handleBlur}
                placeholder="(555) 555-5555"
                autoComplete="tel"
              />
              {fieldErrors.phone && touched.phone && (
                <span className="field-error">{fieldErrors.phone}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="email" className="form-label">
                Email <span className="required">*</span>
              </label>
              <input
                type="email"
                id="email"
                name="email"
                className={`form-input ${fieldErrors.email && touched.email ? 'input-error' : ''}`}
                value={formData.email}
                onChange={handleInputChange}
                onBlur={handleBlur}
                placeholder="you@example.com"
                autoComplete="email"
              />
              {fieldErrors.email && touched.email && (
                <span className="field-error">{fieldErrors.email}</span>
              )}
            </div>
          </section>

          <section className="form-section ministry-section">
            <h2 className="section-title">Ministry Areas</h2>
            <p className="section-description">
              Select all areas where you would like to serve:
            </p>

            {fieldErrors.ministries && (
              <div className="ministry-error">{fieldErrors.ministries}</div>
            )}

            <div className="ministry-categories">
              {CATEGORY_ORDER.map((category, index) => (
                <div
                  key={category}
                  className={`ministry-category ${index % 2 === 1 ? 'category-alt' : ''}`}
                >
                  <h3 className="category-title">{category}</h3>
                  <div className="ministry-options">
                    {ministryCategories[category]?.map(area => (
                      <label key={area} className="checkbox-label">
                        <input
                          type="checkbox"
                          className="checkbox-input"
                          checked={isMinistrySelected(category, area)}
                          onChange={() => handleMinistryToggle(category, area)}
                        />
                        <span className="checkbox-custom"></span>
                        <span className="checkbox-text">{area}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>

          <div className="form-actions">
            <button
              type="submit"
              className="submit-button"
              disabled={submitting}
            >
              {submitting ? (
                <>
                  <span className="button-spinner"></span>
                  Submitting...
                </>
              ) : (
                'Sign Up to Serve'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default VolunteerForm
