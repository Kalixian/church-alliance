import { useEffect, useState } from 'react'
import ApplicationsTool from './ApplicationsTool'
import MembersTool from './MembersTool'

const sectionContent = {
  Volunteer: {
    title: 'Volunteer',
    blocks: [
      {
        title: 'Mission and vision',
        text:
          'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec odio. Praesent libero. Sed cursus ante dapibus diam. Sed nisi. Nulla quis sem at nibh elementum imperdiet. Duis sagittis ipsum. Praesent mauris. Fusce nec tellus sed augue semper porta.',
      },
      {
        title: 'Upcoming gatherings',
        text:
          'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec odio. Praesent libero. Sed cursus ante dapibus diam. Sed nisi. Nulla quis sem at nibh elementum imperdiet. Duis sagittis ipsum. Praesent mauris. Fusce nec tellus sed augue semper porta.',
      },
      {
        title: 'Community support',
        text:
          'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec odio. Praesent libero. Sed cursus ante dapibus diam. Sed nisi. Nulla quis sem at nibh elementum imperdiet. Duis sagittis ipsum. Praesent mauris. Fusce nec tellus sed augue semper porta.',
      },
    ],
  },
  Events: {
    title: 'Events',
    blocks: [
      {
        title: 'Upcoming events',
        text: 'Event information will appear here soon.',
      },
    ],
  },
  Resources: {
    title: 'Resources',
    blocks: [
      {
        title: 'Community resources',
        text: 'Helpful resources for the church alliance will appear here soon.',
      },
    ],
  },
  News: {
    title: 'News',
    blocks: [
      {
        title: 'Latest news',
        text: 'The latest church alliance news will appear here soon.',
      },
    ],
  },
  Management: {
    title: 'Management',
    blocks: [],
  },
  'Site Access Applications': {
    title: 'Site Access Applications',
    blocks: [
      {
        title: 'Site access applications',
        text: 'Review and manage requests for site access here.',
      },
    ],
  },
}

function MainContent({ activeSection, authToken, authUserId, apiBaseUrl, userRole, onSelectMembers, onSelectApplications, onBackToManagement }) {
  const [applicantCount, setApplicantCount] = useState(0)

  useEffect(() => {
    if (userRole !== 'administrator' || !authToken) {
      setApplicantCount(0)
      return
    }

    fetch(`${apiBaseUrl}/api/v1/users/count?role=applicant`, {
      headers: { Authorization: `Bearer ${authToken}` },
    })
      .then((response) => response.ok ? response.json() : 0)
      .then((count) => setApplicantCount(count))
      .catch(() => setApplicantCount(0))
  }, [apiBaseUrl, authToken, userRole])

  if (activeSection === 'Members') {
    return (
      <MembersTool
        token={authToken}
        authUserId={authUserId}
        apiBaseUrl={apiBaseUrl}
        canEditRoles={userRole === 'administrator'}
        onBack={onBackToManagement}
      />
    )
  }

  if (activeSection === 'Site Access Applications') {
    return (
      <ApplicationsTool
        token={authToken}
        authUserId={authUserId}
        apiBaseUrl={apiBaseUrl}
        onBack={onBackToManagement}
      />
    )
  }

  const content = sectionContent[activeSection] || sectionContent.Volunteer

  return (
    <section className="main-content" aria-live="polite" aria-labelledby="main-content-title">
      <h2 id="main-content-title" className="sr-only">{content.title}</h2>
      {activeSection === 'Management' ? (
        <div className="management-tools">
          <h3>Site Management Tools</h3>
          <button type="button" className="management-tool-link" onClick={onSelectMembers}>
            Members
          </button>
          {userRole === 'administrator' ? (
            <button type="button" className="management-tool-link" onClick={onSelectApplications}>
              Site Access Applications ({applicantCount})
            </button>
          ) : null}
        </div>
      ) : null}
      {content.blocks.map((block) => (
        <article key={block.title} className="content-block">
          <h3>{block.title}</h3>
          <p>{block.text}</p>
        </article>
      ))}
    </section>
  )
}

export default MainContent
