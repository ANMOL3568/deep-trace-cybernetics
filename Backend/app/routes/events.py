from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import SecurityEvent, User
from ..schemas import EventCreate, EventUpdate, EventStatus, Severity
from ..security import current_user, require_roles
from ..services import audit, changes, get_resource, paginate, public, scoped

router = APIRouter(prefix='/api/security-events', tags=['Security events'])


@router.get('')
def list_events(q: str = Query('', max_length=160), severity: Severity | None = None, status: EventStatus | None = None,
                page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100), sort: str = 'created_at',
                order: Literal['asc', 'desc'] = 'desc', user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = scoped(SecurityEvent, user)
    if q:
        query = query.where(SecurityEvent.description.icontains(q, autoescape=True) | SecurityEvent.event_type.icontains(q, autoescape=True))
    if severity:
        query = query.where(SecurityEvent.severity == severity)
    if status:
        query = query.where(SecurityEvent.status == status)
    return paginate(db, query, SecurityEvent, page, page_size, sort, order)


@router.post('', status_code=201)
def create_event(body: EventCreate, user: User = Depends(require_roles('ADMIN', 'MANAGER')), db: Session = Depends(get_db)):
    row = SecurityEvent(**body.model_dump(), tenant_id=user.tenant_id)
    db.add(row)
    db.flush()
    audit(db, user, 'EVENT_CREATED', f'event:{row.id}')
    db.commit()
    return public(row)


@router.get('/{event_id}')
def detail(event_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return public(get_resource(db, SecurityEvent, event_id, user))


@router.patch('/{event_id}')
def update_event(event_id: int, body: EventUpdate, user: User = Depends(require_roles('ADMIN', 'MANAGER')), db: Session = Depends(get_db)):
    row = get_resource(db, SecurityEvent, event_id, user, lock=True)
    data = changes(body)
    transitions = {'OPEN': {'INVESTIGATING', 'RESOLVED'}, 'INVESTIGATING': {'RESOLVED'}, 'RESOLVED': set()}
    if 'status' in data and data['status'] != row.status and data['status'] not in transitions[row.status]:
        raise HTTPException(409, 'Invalid event status transition')
    for key, value in data.items():
        setattr(row, key, value)
    audit(db, user, 'EVENT_UPDATED', f'event:{row.id}; fields:{",".join(data)}')
    db.commit()
    return public(row)
