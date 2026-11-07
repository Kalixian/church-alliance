import { Link } from 'react-router'
import PageBanner from '../components/layout/PageBanner'

const sections = [
  ['who-we-are', 'Who We Are'],
  ['purpose', 'Purpose'],
  ['history', 'History'],
  ['training', 'Training'],
  ['deployment', 'Deployment'],
  ['communication', 'Communication'],
]

function AboutPage() {
  return (
    <>
      <PageBanner eyebrow="Church Alliance" title="About Us">
        A caring Christian presence in the aftermath of disaster.
      </PageBanner>

      <div className="band">
        <div className="layout">
          <nav className="toc" aria-label="On this page">
            <h2>On this page</h2>
            <ol>
              {sections.map(([id, label]) => (
                <li key={id}><a href={`#${id}`}>{label}</a></li>
              ))}
            </ol>
          </nav>

          <div>
            <section className="article-section" id="who-we-are">
              <h2>Who We Are</h2>
              <p>
                Our organization is an alliance of affiliated and disaffiliated
                UM churches as well as independent churches whose mission is to
                provide a caring Christian presence in the aftermath of disaster.
                We serve the call of the survivor regardless of the originating
                agency.
              </p>
              <p>
                An Alliance is a relationship among groups of states that come
                together for mutual benefit of a common purpose, often without a
                formal agreement. Our alliance came together to enhance our
                ability to accomplish our mission. Each of our member churches’
                Early Response Teams is an autonomous unit choosing to work as a
                team with other Alliance members. Each team is responsible for
                certifying their members as capable and ready to serve.
              </p>
              <p>
                Before we begin the work of restoring hope to the survivor, we
                must prepare. We prepare by being trained, being available when
                the call is issued, being flexible when we deploy, and by
                following the Holy Spirit as He guides us to care for the
                survivor. We live to Romans 15:2:
              </p>
              <blockquote className="callout">
                <p>
                  Each one of us needs to look after the good of the people
                  around us, asking ourselves, “How can I help?”
                </p>
                <cite>Romans 15:2 (The Message)</cite>
              </blockquote>
            </section>

            <section className="article-section" id="purpose">
              <h2>Purpose</h2>
              <p>
                Several churches decided to form an alliance of churches to
                respond in the aftermath of disaster. The purpose of the alliance
                is to enhance our ability to source manpower for multiple teams
                to serve on a sustained basis. All member churches have manpower
                willing and able to serve. Some member churches have equipment
                needed for deployment. Serving together, utilizing the resources
                of all teams, the Alliance can better sustain serving as the
                hands and feet of Christ after a disaster.
              </p>
              <p>
                The Alliance facilitates communication between members. A
                pyramid structure helps us visualize how we interact. The base of
                the pyramid is the largest and strongest part: the Local Church.
                Deployments are planned and sponsored by the local church. This
                includes housing, food, logistics, transportation, and work
                assignments. This information is transmitted to the Church
                Alliance for publication to members. During deployment, teams are
                asked to provide brief updates to the Alliance regarding
                conditions, type of work needed, and what you are seeing. Updates
                will then be provided to Alliance members to enhance their
                capacity to serve.
              </p>
              <p>
                The Alliance will create a database of member ERT leaders, number
                of members, capabilities, and equipment.
              </p>
            </section>

            <section className="article-section" id="history">
              <h2>History</h2>
              <p>
                The Church Alliance for Disaster Response began in October 2023.
                Original membership totaled 17 churches. Membership included
                affiliated and disaffiliated UMC churches as well as independent
                churches. As of September 2025 the Alliance now has 27 member
                churches.
              </p>
              <ul className="facts">
                <li>Founded October 2023</li>
                <li>17 founding churches</li>
                <li>27 churches as of September 2025</li>
              </ul>
            </section>

            <section className="article-section" id="training">
              <h2>Training</h2>
              <p>
                The alliance operates under a hybrid model. Some members continue
                to use UMCOR trainers and training materials. Some members have
                created their own training materials and certified their own
                trainers. The Global Methodist Church is creating their own
                training for GMC churches. Regardless of the methodology used,
                all issue badges to trainees upon completion. Badges certify
                background checks have been done and a responsible, known
                organization stands behind the certification.
              </p>
              <p><Link to="/courses">See the courses our teams offer &rarr;</Link></p>
            </section>

            <section className="article-section" id="deployment">
              <h2>Deployment</h2>
              <p>
                Disaster response ultimately belongs to the disaster’s local
                community. Our members have deployed in a variety of ways. We
                always use established protocols and never self-deploy. These
                protocols include invitation from affected Conference(s), or
                invitation from local churches. By adhering to these protocols,
                we ensure there is work, housing is available, and that we are
                advised of materials teams need to provide.
              </p>
            </section>

            <section className="article-section" id="communication">
              <h2>Communication</h2>
              <p>
                The Alliance will communicate with the local church ERT
                Coordinator. It is the responsibility of the Coordinator to
                communicate with members of their ERT. We look forward to
                receiving information about your events: deployments, training
                classes, special training opportunities, and special events.
              </p>
            </section>
          </div>
        </div>
      </div>
    </>
  )
}

export default AboutPage
