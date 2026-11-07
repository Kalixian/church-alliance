from pydantic import BaseModel, Field, field_validator


def single_line(value: str) -> str:
    """Collapse line breaks so a value can't inject extra email headers."""
    return " ".join(value.split())


class ContactMessage(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    subject: str = Field(default="", max_length=150)
    message: str = Field(min_length=1, max_length=5000)
    # Honeypot: hidden from people, filled in by bots.
    website: str = Field(default="", max_length=500)

    @field_validator("name", "email", "subject", mode="after")
    @classmethod
    def collapse_to_single_line(cls, value: str) -> str:
        return single_line(value)

    @field_validator("message", mode="after")
    @classmethod
    def strip_message(cls, value: str) -> str:
        return value.strip()

    @field_validator("name", "message", mode="after")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("email", mode="after")
    @classmethod
    def plausible_email(cls, value: str) -> str:
        local, _, domain = value.partition("@")
        if not local or "." not in domain or " " in value or "@" in domain:
            raise ValueError("invalid email address")
        return value
