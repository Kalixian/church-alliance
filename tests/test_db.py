"""Database tests"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.user import User, UserRole, UserCreate
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


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    yield db
    
    db.close()


class TestUserCRUD:
    """Test CRUD operations for User model"""
    
    def test_create_user(self, test_db):
        """Test creating a user"""
        user_data = UserCreate(
            auth_id="supabase-123",
            email="john@example.com",
            role=UserRole.ADMINISTRATOR,
        )
        user = create_user(test_db, user_data)
        
        assert user.id is not None
        assert user.auth_id == "supabase-123"
        assert user.email == "john@example.com"
        assert user.role == UserRole.ADMINISTRATOR
    
    def test_first_user_becomes_administrator(self, test_db):
        """Test the first user is promoted to administrator"""
        user_data = UserCreate(
            auth_id="supabase-123b",
            email="default@example.com",
        )
        user = create_user(test_db, user_data)
        
        assert user.role == UserRole.ADMINISTRATOR

    def test_only_first_user_is_promoted(self, test_db):
        """Test subsequent users retain their requested roles"""
        first_user = UserCreate(
            auth_id="supabase-first",
            email="first@example.com",
        )
        second_user = UserCreate(
            auth_id="supabase-second",
            email="second@example.com",
        )

        create_user(test_db, first_user)
        created_second_user = create_user(test_db, second_user)

        assert created_second_user.role == UserRole.APPLICANT
    
    def test_get_user_by_id(self, test_db):
        """Test getting user by ID"""
        user_data = UserCreate(
            auth_id="supabase-124",
            email="jane@example.com",
            role=UserRole.MEMBER,
        )
        created_user = create_user(test_db, user_data)
        
        retrieved_user = get_user_by_id(test_db, created_user.id)
        assert retrieved_user is not None
        assert retrieved_user.email == "jane@example.com"
    
    def test_get_user_by_auth_id(self, test_db):
        """Test getting user by auth ID"""
        user_data = UserCreate(
            auth_id="supabase-125",
            email="bob@example.com",
            role=UserRole.MEMBER,
        )
        create_user(test_db, user_data)
        
        retrieved_user = get_user_by_auth_id(test_db, "supabase-125")
        assert retrieved_user is not None
        assert retrieved_user.email == "bob@example.com"
    
    def test_get_user_by_email(self, test_db):
        """Test getting user by email"""
        user_data = UserCreate(
            auth_id="supabase-126",
            email="alice@example.com",
            role=UserRole.APPLICANT,
        )
        create_user(test_db, user_data)
        
        retrieved_user = get_user_by_email(test_db, "alice@example.com")
        assert retrieved_user is not None
        assert retrieved_user.auth_id == "supabase-126"
    
    def test_get_all_users(self, test_db):
        """Test getting all users"""
        for i in range(3):
            user_data = UserCreate(
                auth_id=f"supabase-{200+i}",
                email=f"user{i}@example.com",
                role=UserRole.MEMBER,
            )
            create_user(test_db, user_data)
        
        users = get_all_users(test_db)
        assert len(users) == 3
    
    def test_get_users_by_role(self, test_db):
        """Test getting users by role"""
        admin_user = UserCreate(
            auth_id="supabase-admin",
            email="admin@example.com",
            role=UserRole.ADMINISTRATOR,
        )
        member_user = UserCreate(
            auth_id="supabase-member",
            email="member@example.com",
            role=UserRole.MEMBER,
        )
        create_user(test_db, admin_user)
        create_user(test_db, member_user)
        
        admins = get_users_by_role(test_db, UserRole.ADMINISTRATOR)
        assert len(admins) == 1
        assert admins[0].email == "admin@example.com"
    
    def test_update_user(self, test_db):
        """Test updating a user"""
        user_data = UserCreate(
            auth_id="supabase-127",
            email="before@example.com",
            role=UserRole.APPLICANT,
        )
        user = create_user(test_db, user_data)
        
        from app.db.user import UserUpdate
        update_data = UserUpdate(email="after@example.com", role=UserRole.ADMINISTRATOR)
        updated_user = update_user(test_db, user.id, update_data)
        
        assert updated_user is not None
        assert updated_user.email == "after@example.com"
        assert updated_user.role == UserRole.ADMINISTRATOR
    
    def test_delete_user(self, test_db):
        """Test deleting a user"""
        user_data = UserCreate(
            auth_id="supabase-128",
            email="delete@example.com",
            role=UserRole.MEMBER,
        )
        user = create_user(test_db, user_data)
        
        success = delete_user(test_db, user.id)
        assert success is True
        
        retrieved_user = get_user_by_id(test_db, user.id)
        assert retrieved_user is None
