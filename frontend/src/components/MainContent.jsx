import { useEffect, useState } from 'react'
import ApplicationsTool from './ApplicationsTool'
import ArticlesTool from './ArticlesTool'
import CalendarTool from './CalendarTool'
import CertificationsTool from './CertificationsTool'
import EventDetails from './EventDetails'
import EventsTool from './EventsTool'
import GalleryTool from './GalleryTool'
import MembersTool from './MembersTool'

const sectionContent = {
  Home: {
    title: 'Home',
    blocks: [
      {
        title: 'Landing Page',
        text:
          'Landing page contains featured news and photos, upcoming events, and some basic info',
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
  'About Us': {
    title: 'About Us',
    blocks: [
      {
        title: 'Who We Are',
        text: `
            Our organization is an alliance of affiliated and disaffiliated UM churces as well as independent churches whose mission is to provide a caring Christian presence in the aftermath of disaster. We serve the call of the survivor regardless of the originating agency.
            
            An Alliance is a relationship among groups of states that come together for mutual benefit of a common purpose, often without a formal agreement. Our alliance came together to enhance our ability to accomplish our mission. Each of our member churches' Early Response Teams is an autonomous unit choosing to work as a team with other Alliance members. Each team is responsible for certifying their members as capable and ready to serve.
            
            Before we beign the work of restoring hope to the survivor, we must prepare. We prepare by being trained, being available when the call is issued, being flexible when we deploy, and by folling the Holy Spirit as He guides us to care for the survivor. We live to Romans 15:2 (The Message): Each one of us needs to look after the good of the people around us, asking ourselves, "How can I help?"
            `,
      },{
        title: 'Purpose',
        text: `
          Several churches decided to form an alliance of churches to respond in the aftermath of disaster. The purpose of the alliance is to enhance our ability to source manpower for multiple teams to serve on a sustained basis. All member churches have manpower willing and able to serve. Some member churches have equipment needed for deployment. Serving together, utilizing the resources of all teams, the Alliance can better sustain serving as the hands and feet of Christ after a disaster.

          The Alliance faciliates communication between members. A pyramid structure helps us visualize how we interact. The base of the pyramid is the largest and strongest part - the Local Church. Deployments are planned and sponsored by the local church. This includes housing, food, logistics, transportation, and work assignments. This information is transmitted to the Church Alliance for publication to members. During deployment, teams are asked to provide brief updates to the Alliance regarding conditions, type of work needed, and what you are seeing. Updates will then be provided to Alliance members to enhance their capacity to serve.

          The Alliance wil create a database of member ERT leaders, number of members, capabilities, and equipment.
        `,
      },{
        title: 'History',
        text: `
          The Church Alliance for Disaster Response began in October 2023. Original Membership totaled 17 churches. Membership included affiliated and disaffiliated UMC churches as well as independent churches. As of September 2025 the Alliance now has 27 member churches.
        `
      },{
        title: 'Training',
        text: `
          The alliance operates under a hybrid model. Some members continue to use UMCOR trainers and training materials. Some members have created their own training materials and certified their own  trainers. The Global Methodist Church is creating their own training for GMC churches. Regardless of the methodology used, all issue badges to trainees upon completion. Badges certify background checks have been done and a responsible, known organization stands behind the certification.
        `
      },{
        title: 'Deployment',
        text: `
          Disaster Response ultimately belongs to the disaster's local community. Our members have deployed in a variety of ways. We always use established protocols and never self-deploy. These protocols include by invitation from affected Conference(s), or by invitation from local churches. By adhering to these protocols, we ensure there is work, housing is available, and we that we are advised of materials teams need to provide.
        `
      },{
        title: 'Communication',
        text: `
          Protocol - The Allliance will communicate with hte local church ERT Coordinator. It is the responsibility of the Coordinator to communicate with members of their ERT. We look forward to receiving information about your events (deployments, training classes, special training opportunities, and special events).
        `
      }
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
  Admin: {
    title: 'Admin',
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

function MainContent({ activeSection, authToken, authUserId, backendUserId, apiBaseUrl, userRole, onSelectApplications, onSelectCertifications, onBackToManagement }) {
  const [applicantCount, setApplicantCount] = useState(0)
  const [selectedEventId, setSelectedEventId] = useState(null)

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
      />
    )
  }

  if (activeSection === 'Events') {
    if (selectedEventId) {
      return (
        <EventDetails
          eventId={selectedEventId}
          apiBaseUrl={apiBaseUrl}
          token={authToken}
          userRole={userRole}
          authUserId={authUserId}
          onBack={() => setSelectedEventId(null)}
          onChanged={() => setSelectedEventId(null)}
        />
      )
    }
    return (
      <EventsTool
        apiBaseUrl={apiBaseUrl}
        token={authToken}
        userRole={userRole}
        authUserId={authUserId}
        onSelectEvent={setSelectedEventId}
      />
    )
  }

  if (activeSection === 'Calendar') {
    if (selectedEventId) {
      return (
        <EventDetails
          eventId={selectedEventId}
          apiBaseUrl={apiBaseUrl}
          token={authToken}
          userRole={userRole}
          authUserId={authUserId}
          onBack={() => setSelectedEventId(null)}
          onChanged={() => setSelectedEventId(null)}
        />
      )
    }
    return <CalendarTool apiBaseUrl={apiBaseUrl} token={authToken} onSelectEvent={setSelectedEventId} />
  }

  if (activeSection === 'Gallery') {
    return <GalleryTool apiBaseUrl={apiBaseUrl} token={authToken} userRole={userRole} backendUserId={backendUserId} />
  }

  if (activeSection === 'News') {
    return <ArticlesTool apiBaseUrl={apiBaseUrl} token={authToken} userRole={userRole} backendUserId={backendUserId} />
  }

  if (activeSection === 'Certifications') {
    return (
      <CertificationsTool
        token={authToken}
        apiBaseUrl={apiBaseUrl}
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

  const content = sectionContent[activeSection] || sectionContent.Home

  return (
    <section className="main-content" aria-live="polite" aria-labelledby="main-content-title">
      <h2 id="main-content-title" className="sr-only">{content.title}</h2>
      {activeSection === 'Admin' ? (
        <div className="management-tools">
          <h3>Admin Tools</h3>
          <p>Asset, Experience management incomplete. Maybe Participating Church information management as well?</p>
          {['administrator', 'coordinator'].includes(userRole) ? (
            <button type="button" className="management-tool-link" onClick={onSelectCertifications}>
              Certifications
            </button>
          ) : null}
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
