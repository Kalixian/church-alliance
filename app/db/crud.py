"""CRUD operations - re-exports from domain modules for backwards compatibility"""

from app.db.user import (
    create_user,
    get_user_by_id,
    get_user_by_auth_id,
    get_user_by_email,
    get_all_users,
    get_users_by_role,
    update_user,
    delete_user,
)
from app.db.event import (
    create_event,
    get_event_by_id,
    get_all_events,
    get_events_by_organizer,
    update_event,
    delete_event,
    add_member_to_event,
    remove_member_from_event,
    get_event_members,
)
from app.db.certification import (
    create_certification,
    get_certification_by_id,
    get_certification_by_name,
    get_all_certifications,
    get_users_by_certification,
)
from app.db.asset import (
    create_asset,
    get_asset_by_id,
    get_asset_by_name,
    get_all_assets,
    get_users_by_asset,
)

__all__ = [
    # User CRUD
    "create_user",
    "get_user_by_id",
    "get_user_by_auth_id",
    "get_user_by_email",
    "get_all_users",
    "get_users_by_role",
    "update_user",
    "delete_user",
    # Event CRUD
    "create_event",
    "get_event_by_id",
    "get_all_events",
    "get_events_by_organizer",
    "update_event",
    "delete_event",
    "add_member_to_event",
    "remove_member_from_event",
    "get_event_members",
    # Certification CRUD
    "create_certification",
    "get_certification_by_id",
    "get_certification_by_name",
    "get_all_certifications",
    "get_users_by_certification",
    # Asset CRUD
    "create_asset",
    "get_asset_by_id",
    "get_asset_by_name",
    "get_all_assets",
    "get_users_by_asset",
]


