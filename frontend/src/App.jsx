import { Navigate, Route, Routes } from 'react-router'
import './styles/site.css'
import './App.css'
import AuthProvider from './auth/AuthProvider'
import Layout from './components/layout/Layout'
import RequireRole from './components/layout/RequireRole'
import { isPageVisible } from './components/layout/navLinks'
import AboutPage from './pages/AboutPage'
import AdminPage from './pages/AdminPage'
import ContactPage from './pages/ContactPage'
import CoursesPage from './pages/CoursesPage'
import HomePage from './pages/HomePage'
import {
  ApplicationsPage,
  CalendarPage,
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
          <Route path="news" element={<NewsPage />} />
          <Route path="news/:articleId" element={<NewsPage />} />
          {/* Hidden pages fall through to the catch-all redirect below. */}
          {isPageVisible('/events') ? (
            <>
              <Route path="events" element={<EventsPage />} />
              <Route path="events/:eventId" element={<EventDetailPage />} />
            </>
          ) : null}
          {isPageVisible('/calendar') ? <Route path="calendar" element={<CalendarPage />} /> : null}
          {isPageVisible('/gallery') ? <Route path="gallery" element={<GalleryPage />} /> : null}

          <Route element={<RequireRole level="confirmed" />}>
            <Route path="members" element={<MembersPage />} />
          </Route>
          <Route element={<RequireRole level="manager" />}>
            <Route path="admin" element={<AdminPage />} />
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
