import PageBanner from '../components/layout/PageBanner'

const courses = [
  ['clean-out', 'ER 200 Clean Out'],
  ['site-assessment', 'ER 200 Site Assessment'],
  ['team-leader', 'ER 200 Team Leader'],
  ['on-site-manager', 'On-Site Manager'],
  ['long-term-recovery', 'Long-Term Recovery'],
  ['cpr', 'CPR'],
]

function CoursesPage() {
  return (
    <>
      <PageBanner eyebrow="Training" title="Courses">
        Equipping Early Response Teams to serve safely, effectively, and as a caring Christian presence.
      </PageBanner>

      <div className="band">
        <div className="layout">
          <nav className="toc" aria-label="Courses on this page">
            <h2>Courses</h2>
            <ol>
              {courses.map(([id, label]) => (
                <li key={id}><a href={`#${id}`}>{label}</a></li>
              ))}
            </ol>
          </nav>

          <div>
            <section className="article-section" id="er-200-series" aria-label="About the ER 200 series">
              <div className="callout">
                <p>
                  The ERT 200 Series of classes was created to provide trained
                  ERTs with supplementary tools and technical information to
                  strengthen their capacity for safe and effective disaster
                  response while being the caring Christian presence to a
                  community.
                </p>
              </div>
            </section>

            <section className="article-section" id="clean-out">
              <h2><span className="tag">ER 200</span>Clean Out (Muck-Out)</h2>
              <p>
                Participants in this class, Cleaning Out Flooded Homes, more
                commonly referred to as “mucking out,” will learn about current
                best practices and safety procedures for cleaning out,
                stabilizing, and sanitizing water-damaged homes.
              </p>
            </section>

            <section className="article-section" id="site-assessment">
              <h2><span className="tag">ER 200</span>Site Assessment</h2>
              <p>
                Participants in this class, Site Assessment (ERT200SA), will
                learn how to assess the physical damage to a disaster-affected
                residence in order to plan and prepare for the Early Response
                Team to safely access and secure the property from further
                damage.
              </p>
              <p>
                Participants will learn how to look for structural problems that
                impact ER safety and effectiveness. The class will help identify
                tools useful for damage assessment and, as always, how to
                sensitively and respectfully discuss the needs with the
                homeowners.
              </p>
            </section>

            <section className="article-section" id="team-leader">
              <h2><span className="tag">ER 200</span>Team Leader</h2>
              <p>
                Servant leadership is a philosophy and set of practices that
                enrich the lives of individuals, build better organizations, and
                ultimately create a more just and caring world. A servant leader
                focuses primarily on the growth and well-being of people and the
                communities to which they belong. Traditional leadership
                generally involves the accumulation and exercise of power by one
                at the “top of the pyramid.” By comparison, the servant leader
                shares power, puts the needs of others first, and helps people
                develop and perform as well as possible.
              </p>
              <p>
                In this class, we will discuss the job functions of all ERT
                members, as well as give some helpful hints and checklists for
                planning the trip.
              </p>
            </section>

            <section className="article-section" id="on-site-manager">
              <h2><span className="tag">OSM</span>On-Site Manager</h2>
              <p>
                This class will give a volunteer the tools to help establish a
                temporary response center at a local church (or other facility
                as designated by the community) for the purpose of coordinating
                the work of the ERTs and thus bringing the response quickly to a
                community.
              </p>
            </section>

            <section className="article-section" id="long-term-recovery">
              <h2><span className="tag">LTR</span>Long-Term Recovery</h2>
              <p>
                The storms have come and gone, but the evidence of their impact
                will be with us for years to come. As these words are being
                written, we are in the midst of hurricane season once again.
                There have been storms, and more storms will come. But we also
                know that with God’s help and with one another, there will also
                be hope, healing, and recovery.
              </p>
              <p>
                We work to restore hope to families who thought they were
                forgotten. Our hope is to continue rebuilding the homes and lives
                of disaster survivors, which would not be possible without your
                gift of service.
              </p>
              <p>
                The goal of recovery is to bring a community back to a new normal
                after it has been devastated by a disaster.
              </p>
              <p>
                No matter how a group is structured or what it calls
                itself (unmet needs committee, interfaith organization,
                coalition, roundtable, partnership, coordinating council, etc.),
                the goal is the same: to unite recovery resources with community
                needs in order to ensure that even the most vulnerable in the
                community recover from disaster.
              </p>
            </section>

            <section className="article-section" id="cpr">
              <h2>CPR</h2>
              <p>
                Cardiopulmonary resuscitation (CPR) is an emergency procedure
                used during cardiac or respiratory arrest that involves chest
                compressions. You can save someone’s life, no matter who you are.
                Lay rescuers include people with CPR certification (you take
                classes and get an official certificate). The course will include
                AED training.
              </p>
              <ul className="facts">
                <li>About 2 hours</li>
                <li>$55 per person</li>
                <li>Includes AED training</li>
              </ul>
            </section>
          </div>
        </div>
      </div>
    </>
  )
}

export default CoursesPage
