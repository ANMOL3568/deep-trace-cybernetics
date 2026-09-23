from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .models import AuditLog, Campaign, CampaignMember, User


def public(row):
    return {c.name: getattr(row, c.name) for c in row.__table__.columns
            if c.name not in {'password_hash', 'token_version'}}


def audit(db: Session, user: User, action: str, resource: str):
    db.add(AuditLog(tenant_id=user.tenant_id, actor=user.email, action=action, resource=resource))


def scoped(model, user):
    query = select(model).where(model.tenant_id == user.tenant_id)
    if model is Campaign and user.role == 'USER':
        query = query.where(Campaign.id.in_(select(CampaignMember.campaign_id).where(
            CampaignMember.tenant_id == user.tenant_id, CampaignMember.user_id == user.id)))
    return query


def get_resource(db, model, resource_id, user, lock=False):
    query = scoped(model, user).where(model.id == resource_id)
    if lock:
        query = query.with_for_update()
    row = db.scalar(query)
    if row is None:
        raise HTTPException(404, 'Resource not found')
    return row


def paginate(db, query, model, page, page_size, sort, order):
    allowed = {'created_at', 'id'}
    allowed.update({'title', 'status'} if model is Campaign else set())
    allowed.update({'name', 'email', 'role'} if model is User else set())
    allowed.update({'severity', 'status', 'event_type'} if model.__tablename__ == 'security_events' else set())
    if sort not in allowed:
        raise HTTPException(422, 'Unsupported sort field')
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    column = getattr(model, sort)
    rows = db.scalars(query.order_by(column.asc() if order == 'asc' else column.desc(), model.id.desc())
                      .offset((page - 1) * page_size).limit(page_size)).all()
    return {'items': [public(row) for row in rows], 'total': total, 'page': page, 'page_size': page_size}


def changes(body):
    data = body.model_dump(exclude_unset=True)
    if not data or any(value is None for value in data.values()):
        raise HTTPException(422, 'Provide at least one non-null field; null updates are not supported')
    return data
