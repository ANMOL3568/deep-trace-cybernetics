from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

Role = Literal['ADMIN', 'MANAGER', 'USER']
CampaignStatus = Literal['DRAFT', 'ACTIVE', 'COMPLETED', 'CANCELLED']
Severity = Literal['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
EventStatus = Literal['OPEN', 'INVESTIGATING', 'RESOLVED']


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Login(Input):
    organization: str = Field(min_length=1, max_length=80)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class CampaignCreate(Input):
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(default='', max_length=5000)


class CampaignUpdate(Input):
    title: str | None = Field(default=None, min_length=3, max_length=160)
    description: str | None = Field(default=None, max_length=5000)
    status: CampaignStatus | None = None


class MemberCreate(Input):
    user_id: int = Field(gt=0)


class EventCreate(Input):
    event_type: str = Field(min_length=3, max_length=100)
    severity: Severity
    description: str = Field(min_length=5, max_length=5000)


class EventUpdate(Input):
    severity: Severity | None = None
    status: EventStatus | None = None
    description: str | None = Field(default=None, min_length=5, max_length=5000)


class UserCreate(Input):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=128)
    role: Role = 'USER'

    @field_validator('email')
    @classmethod
    def valid_email(cls, value):
        import re
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
            raise ValueError('Enter a valid email address')
        return value.lower()


class UserUpdate(Input):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    role: Role | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=12, max_length=128)
