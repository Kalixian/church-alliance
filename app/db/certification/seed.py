"""Starter courses (certifications), taken from the static site's Courses page.

Run `uv run python -m app.db.certification.seed` to add any that are missing.
Existing rows (matched by name) are left alone, so edits made in the Admin
tool survive re-running it.

Description format, as rendered by the React Courses page: paragraphs are
separated by a blank line, and a paragraph whose lines all start with "- "
becomes a list of short facts.
"""

from sqlalchemy.orm import Session

from app.db.certification.crud import create_certification, get_certification_by_name

COURSES = [
    (
        "ER 200 Clean Out (Muck-Out)",
        "Participants in this class, Cleaning Out Flooded Homes, more commonly "
        "referred to as “mucking out,” will learn about current best practices "
        "and safety procedures for cleaning out, stabilizing, and sanitizing "
        "water-damaged homes.",
    ),
    (
        "ER 200 Site Assessment",
        "Participants in this class, Site Assessment (ERT200SA), will learn how "
        "to assess the physical damage to a disaster-affected residence in order "
        "to plan and prepare for the Early Response Team to safely access and "
        "secure the property from further damage.\n\n"
        "Participants will learn how to look for structural problems that impact "
        "ER safety and effectiveness. The class will help identify tools useful "
        "for damage assessment and, as always, how to sensitively and "
        "respectfully discuss the needs with the homeowners.",
    ),
    (
        "ER 200 Team Leader",
        "Servant leadership is a philosophy and set of practices that enrich the "
        "lives of individuals, build better organizations, and ultimately create "
        "a more just and caring world. A servant leader focuses primarily on the "
        "growth and well-being of people and the communities to which they "
        "belong. Traditional leadership generally involves the accumulation and "
        "exercise of power by one at the “top of the pyramid.” By comparison, the "
        "servant leader shares power, puts the needs of others first, and helps "
        "people develop and perform as well as possible.\n\n"
        "In this class, we will discuss the job functions of all ERT members, as "
        "well as give some helpful hints and checklists for planning the trip.",
    ),
    (
        "On-Site Manager",
        "This class will give a volunteer the tools to help establish a temporary "
        "response center at a local church (or other facility as designated by "
        "the community) for the purpose of coordinating the work of the ERTs and "
        "thus bringing the response quickly to a community.",
    ),
    (
        "Long-Term Recovery",
        "The storms have come and gone, but the evidence of their impact will be "
        "with us for years to come. As these words are being written, we are in "
        "the midst of hurricane season once again. There have been storms, and "
        "more storms will come. But we also know that with God’s help and with "
        "one another, there will also be hope, healing, and recovery.\n\n"
        "We work to restore hope to families who thought they were forgotten. Our "
        "hope is to continue rebuilding the homes and lives of disaster "
        "survivors, which would not be possible without your gift of service.\n\n"
        "The goal of recovery is to bring a community back to a new normal after "
        "it has been devastated by a disaster.\n\n"
        "No matter how a group is structured or what it calls itself (unmet needs "
        "committee, interfaith organization, coalition, roundtable, partnership, "
        "coordinating council, etc.), the goal is the same: to unite recovery "
        "resources with community needs in order to ensure that even the most "
        "vulnerable in the community recover from disaster.",
    ),
    (
        "CPR",
        "Cardiopulmonary resuscitation (CPR) is an emergency procedure used "
        "during cardiac or respiratory arrest that involves chest compressions. "
        "You can save someone’s life, no matter who you are. Lay rescuers include "
        "people with CPR certification (you take classes and get an official "
        "certificate). The course will include AED training.\n\n"
        "- About 2 hours\n"
        "- $55 per person\n"
        "- Includes AED training",
    ),
]


def seed_courses(db: Session) -> list[str]:
    """Create each starter course that doesn't exist yet; return the names added."""
    added = []
    for name, description in COURSES:
        if get_certification_by_name(db, name) is None:
            create_certification(db, name, description)
            added.append(name)
    return added


if __name__ == "__main__":
    import app.db.event  # noqa: F401  # User's relationships need Event registered
    from app.db import SessionLocal, create_tables

    create_tables()
    session = SessionLocal()
    try:
        names = seed_courses(session)
    finally:
        session.close()
    print(f"Added {len(names)} course(s)" + (": " + ", ".join(names) if names else "; all already present."))
