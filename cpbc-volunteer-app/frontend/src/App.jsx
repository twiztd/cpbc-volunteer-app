import { Routes, Route } from 'react-router-dom'
import VolunteerForm from './pages/VolunteerForm'
import ThankYou from './pages/ThankYou'
import AdminDashboard from './pages/AdminDashboard'

function App() {
  return (
    <Routes>
      <Route path="/" element={<VolunteerForm />} />
      <Route path="/thank-you" element={<ThankYou />} />
      <Route path="/admin" element={<AdminDashboard />} />
    </Routes>
  )
}

export default App
