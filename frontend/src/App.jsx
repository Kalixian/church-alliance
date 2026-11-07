import { Navigate, Route, Routes } from 'react-router'
import './styles/site.css'
import './App.css'
import AuthProvider from './auth/AuthProvider'
import Layout from './components/layout/Layout'
import RequireRole from './components/layout/RequireRole'
import AboutPage from './pages/AboutPage'
import AdminPage from './pages/AdminPage'
import ContactPage from './pages/ContactPage'
import CoursesPage from './pages/CoursesPage'
import HomePage from './pages/HomePage'
import {
  ApplicationsPage,
  CalendarPage,
  CertificationsPage,
  EventDetailPage,
  EventsPage,
  GalleryPage,
  MembersPage,
  NewsPage,
} from './pages/ToolPages'

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="about" element={<AboutPage />} />
          <Route path="courses" element={<CoursesPage />} />
          <Route path="contact" element={<ContactPage />} />
          <Route path="events" element={<EventsPage />} />
          <Route path="events/:eventId" element={<EventDetailPage />} />
          <Route path="calendar" element={<CalendarPage />} />
          <Route path="news" element={<NewsPage />} />
          <Route path="gallery" element={<GalleryPage />} />

          <Route element={<RequireRole level="confirmed" />}>
            <Route path="members" element={<MembersPage />} />
          </Route>
          <Route element={<RequireRole level="manager" />}>
            <Route path="admin" element={<AdminPage />} />
            <Route path="admin/certifications" element={<CertificationsPage />} />
          </Route>
          <Route element={<RequireRole level="admin" />}>
            <Route path="admin/applications" element={<ApplicationsPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}

export default App
