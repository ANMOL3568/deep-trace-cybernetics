from datetime import timedelta
from typing import Literal
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import AuditLog, Campaign, SecurityEvent, User, now
from ..security import current_user, require_roles
from ..services import paginate, public, scoped

router = APIRouter(prefix='/api', tags=['Dashboard and audit'])


@router.get('/dashboard')
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    def count(query):
        return db.scalar(select(func.count()).select_from(query.subquery()))
    events = scoped(SecurityEvent, user)
    campaigns = scoped(Campaign, user)
    trend = []
    today = now().replace(hour=0, minute=0, second=0, microsecond=0)
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        trend.append({'day': day.strftime('%a'), 'count': count(events.where(SecurityEvent.created_at >= day, SecurityEvent.created_at < day + timedelta(days=1)))})
    return {
        'users': count(scoped(User, user).where(User.is_active.is_(True))),
        'campaigns': count(campaigns),
        'active_campaigns': count(campaigns.where(Campaign.status == 'ACTIVE')),
        'open_events': count(events.where(SecurityEvent.status != 'RESOLVED')),
        'critical_events': count(events.where(SecurityEvent.severity == 'CRITICAL', SecurityEvent.status != 'RESOLVED')),
        'severity_counts': {severity: count(events.where(SecurityEvent.severity == severity, SecurityEvent.status != 'RESOLVED')) for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']},
        'trend': trend,
        'recent_events': [public(row) for row in db.scalars(events.order_by(SecurityEvent.created_at.desc()).limit(5))],
        'recent_campaigns': [public(row) for row in db.scalars(campaigns.order_by(Campaign.updated_at.desc()).limit(4))],
    }


@router.get('/audit-logs')
def audit_logs(q: str = Query('', max_length=160), page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
               sort: str = 'created_at', order: Literal['asc', 'desc'] = 'desc',
               user: User = Depends(require_roles('ADMIN')), db: Session = Depends(get_db)):
    query = scoped(AuditLog, user)
    if q:
        query = query.where(AuditLog.action.icontains(q, autoescape=True) | AuditLog.actor.icontains(q, autoescape=True))
    return paginate(db, query, AuditLog, page, page_size, sort, order)
