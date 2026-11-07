// Pages that are built but not public yet: left out of the nav and their
// routes redirect home. Remove a path from this set to bring the page back.
export const HIDDEN_PAGES = new Set(['/events', '/calendar', '/gallery'])

export const isPageVisible = (path) => !HIDDEN_PAGES.has(path)

const ALL_LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/about', label: 'About Us' },
  { to: '/courses', label: 'Courses' },
  { to: '/events', label: 'Events' },
  { to: '/calendar', label: 'Calendar' },
  { to: '/news', label: 'News' },
  { to: '/gallery', label: 'Gallery' },
  { to: '/contact', label: 'Contact Us' },
]

export const PUBLIC_LINKS = ALL_LINKS.filter((link) => isPageVisible(link.to))
