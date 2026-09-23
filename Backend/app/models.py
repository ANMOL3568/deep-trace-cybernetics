from datetime import datetime, timezone
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


def now():
    return datetime.now(timezone.utc)


class Tenant(Base):
    __tablename__ = 'tenants'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(80), unique=True)


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (UniqueConstraint('tenant_id', 'email'), UniqueConstraint('tenant_id', 'id'),
                     CheckConstraint("role IN ('ADMIN','MANAGER','USER')"), Index('ix_users_tenant_role', 'tenant_id', 'role'))
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey('tenants.id'))
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254))
    password_hash: Mapped[str] = mapped_column(String(300))
    role: Mapped[str] = mapped_column(String(20), default='USER')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    token_version: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Campaign(Base):
    __tablename__ = 'campaigns'
    __table_args__ = (UniqueConstraint('tenant_id', 'id'),
                     ForeignKeyConstraint(['tenant_id', 'created_by'], ['users.tenant_id', 'users.id']),
                     CheckConstraint("status IN ('DRAFT','ACTIVE','COMPLETED','CANCELLED')"),
                     Index('ix_campaigns_tenant_status', 'tenant_id', 'status', 'created_at'))
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey('tenants.id'))
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default='')
    status: Mapped[str] = mapped_column(String(20), default='DRAFT')
    created_by: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class CampaignMember(Base):
    __tablename__ = 'campaign_members'
    __table_args__ = (
        ForeignKeyConstraint(['tenant_id', 'campaign_id'], ['campaigns.tenant_id', 'campaigns.id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['tenant_id', 'user_id'], ['users.tenant_id', 'users.id'], ondelete='CASCADE'))
    tenant_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)


class SecurityEvent(Base):
    __tablename__ = 'security_events'
    __table_args__ = (
        CheckConstraint("severity IN ('LOW','MEDIUM','HIGH','CRITICAL')"),
        CheckConstraint("status IN ('OPEN','INVESTIGATING','RESOLVED')"),
        Index('ix_events_tenant_filters', 'tenant_id', 'status', 'severity', 'created_at'))
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey('tenants.id'))
    event_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default='OPEN')
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    __table_args__ = (Index('ix_audit_tenant_time', 'tenant_id', 'created_at'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey('tenants.id'))
    actor: Mapped[str] = mapped_column(String(254))
    action: Mapped[str] = mapped_column(String(80))
    resource: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
