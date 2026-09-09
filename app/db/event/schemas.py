"""Pydantic schemas for Event model"""

from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional
from datetime import date, datetime, time
from uuid import UUID

from app.db.user.schemas import UserResponse
from app.db.certification.schemas import CertificationResponse


def _parse_date_only_values(values):
    if not isinstance(values, dict):
        return values
    parsed_values = dict(values)
    for field_name in ("start_datetime", "end_datetime"):
        value = parsed_values.get(field_name)
        if isinstance(value, str) and len(value) == 10:
            try:
                parsed_values[field_name] = date.fromisoformat(value)
            except ValueError:
                pass
    return parsed_values


class EventBase(BaseModel):
    """Base event schema with common fields"""
    name: str
    description: Optional[str] = None
    start_datetime: datetime | date
    end_datetime: datetime | date
    all_day: bool = False
    certification_id: Optional[UUID] = None
    certification: Optional[CertificationResponse] = None
    certification_name: Optional[str] = None
    coordinator_id: Optional[UUID] = None

    @model_validator(mode="before")
    @classmethod
    def parse_date_only_values(cls, values):
        return _parse_date_only_values(values)

    @model_validator(mode="after")
    def validate_schedule(self):
        start_is_date_only = isinstance(self.start_datetime, date) and not isinstance(self.start_datetime, datetime)
        end_is_date_only = isinstance(self.end_datetime, date) and not isinstance(self.end_datetime, datetime)

        if self.all_day:
            if start_is_date_only:
                self.start_datetime = datetime.combine(self.start_datetime, time.min)
            elif self.start_datetime.time() != time.min:
                raise ValueError("All-day events must use dates without times")
            if end_is_date_only:
                self.end_datetime = datetime.combine(self.end_datetime, time.min)
            elif self.end_datetime.time() != time.min:
                raise ValueError("All-day events must use dates without times")
        elif start_is_date_only or end_is_date_only:
            raise ValueError("Timed events require exact start and end times")

        if (self.end_datetime < self.start_datetime) if self.all_day else (self.end_datetime <= self.start_datetime):
            raise ValueError("Event end must be after event start")
        return self


class EventCreate(EventBase):
    """Schema for creating an event"""
    pass


class EventUpdate(BaseModel):
    """Schema for updating an event"""
    name: Optional[str] = None
    description: Optional[str] = None
    start_datetime: Optional[datetime | date] = None
    end_datetime: Optional[datetime | date] = None
    all_day: Optional[bool] = None
    certification_id: Optional[UUID] = None
    coordinator_id: Optional[UUID] = None

    @model_validator(mode="before")
    @classmethod
    def parse_date_only_values(cls, values):
        return _parse_date_only_values(values)

    @model_validator(mode="after")
    def validate_schedule(self):
        supplied_dates = [value for value in (self.start_datetime, self.end_datetime) if value is not None]
        has_date_only_value = any(isinstance(value, date) and not isinstance(value, datetime) for value in supplied_dates)

        if self.all_day is True:
            if len(supplied_dates) != 2 or not all(isinstance(value, date) and not isinstance(value, datetime) for value in supplied_dates):
                raise ValueError("All-day updates must include both dates without times")
            self.start_datetime = datetime.combine(self.start_datetime, time.min)
            self.end_datetime = datetime.combine(self.end_datetime, time.min)
        elif has_date_only_value:
            raise ValueError("Timed event updates require exact start and end times")

        if self.start_datetime is not None and self.end_datetime is not None and (
            (self.end_datetime < self.start_datetime)
            if self.all_day
            else (self.end_datetime <= self.start_datetime)
        ):
            raise ValueError("Event end must be after event start")
        return self


class EventResponse(EventBase):
    """Schema for event response"""
    id: UUID
    coordinator_id: UUID
    coordinator: Optional["UserResponse"] = None
    members: list["UserResponse"] = []
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Update forward references after both schemas are defined
EventResponse.model_rebuild()
