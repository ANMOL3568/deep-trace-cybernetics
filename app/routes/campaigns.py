from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Campaign, CampaignMember, User
from ..schemas import CampaignCreate, CampaignUpdate, CampaignStatus, MemberCreate
from ..security import current_user, require_roles
from ..services import audit, changes, get_resource, paginate, public, scoped

router = APIRouter(prefix='/api/campaigns', tags=['Campaigns'])
writers = require_roles('ADMIN', 'MANAGER')
TRANSITIONS = {'DRAFT': {'ACTIVE', 'CANCELLED'}, 'ACTIVE': {'COMPLETED', 'CANCELLED'}, 'COMPLETED': set(), 'CANCELLED': set()}


@router.get('')
def list_campaigns(q: str = Query('', max_length=160), status: CampaignStatus | None = None,
                   page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
                   sort: str = 'created_at', order: Literal['asc', 'desc'] = 'desc',
                   user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = scoped(Campaign, user)
    if q:
        query = query.where(Campaign.title.icontains(q, autoescape=True))
    if status:
        query = query.where(Campaign.status == status)
    return paginate(db, query, Campaign, page, page_size, sort, order)


@router.post('', status_code=201)
def create_campaign(body: CampaignCreate, user: User = Depends(writers), db: Session = Depends(get_db)):
    row = Campaign(**body.model_dump(), tenant_id=user.tenant_id, created_by=user.id)
    db.add(row)
    db.flush()
    audit(db, user, 'CAMPAIGN_CREATED', f'campaign:{row.id}')
    db.commit()
    return public(row)


@router.get('/{campaign_id}')
def detail(campaign_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = get_resource(db, Campaign, campaign_id, user)
    members = db.scalars(select(User).join(CampaignMember, (User.id == CampaignMember.user_id) & (User.tenant_id == CampaignMember.tenant_id))
                         .where(CampaignMember.campaign_id == row.id, CampaignMember.tenant_id == user.tenant_id)).all()
    return {**public(row), 'members': [public(member) for member in members]}


@router.patch('/{campaign_id}')
def update_campaign(campaign_id: int, body: CampaignUpdate, user: User = Depends(writers), db: Session = Depends(get_db)):
    row = get_resource(db, Campaign, campaign_id, user, lock=True)
    data = changes(body)
    if 'status' in data and data['status'] != row.status and data['status'] not in TRANSITIONS[row.status]:
        raise HTTPException(409, f'Cannot transition from {row.status} to {data["status"]}')
    for key, value in data.items():
        setattr(row, key, value)
    audit(db, user, 'CAMPAIGN_UPDATED', f'campaign:{row.id}; fields:{",".join(data)}')
    db.commit()
    return public(row)


@router.delete('/{campaign_id}', status_code=204)
def delete_campaign(campaign_id: int, user: User = Depends(require_roles('ADMIN')), db: Session = Depends(get_db)):
    row = get_resource(db, Campaign, campaign_id, user, lock=True)
    audit(db, user, 'CAMPAIGN_DELETED', f'campaign:{row.id}')
    db.delete(row)
    db.commit()


@router.post('/{campaign_id}/members', status_code=201)
def add_member(campaign_id: int, body: MemberCreate, user: User = Depends(writers), db: Session = Depends(get_db)):
    row = get_resource(db, Campaign, campaign_id, user, lock=True)
    member = get_resource(db, User, body.user_id, user)
    if not member.is_active:
        raise HTTPException(409, 'Cannot assign an inactive user')
    if db.get(CampaignMember, (user.tenant_id, row.id, member.id)):
        raise HTTPException(409, 'User is already assigned')
    db.add(CampaignMember(tenant_id=user.tenant_id, campaign_id=row.id, user_id=member.id))
    audit(db, user, 'CAMPAIGN_MEMBER_ADDED', f'campaign:{row.id}; user:{member.id}')
    db.commit()
    return {'message': 'User assigned'}


@router.delete('/{campaign_id}/members/{user_id}', status_code=204)
def remove_member(campaign_id: int, user_id: int, user: User = Depends(writers), db: Session = Depends(get_db)):
    row = get_resource(db, Campaign, campaign_id, user, lock=True)
    member = db.get(CampaignMember, (user.tenant_id, row.id, user_id))
    if not member:
        raise HTTPException(404, 'Assignment not found')
    db.delete(member)
    audit(db, user, 'CAMPAIGN_MEMBER_REMOVED', f'campaign:{row.id}; user:{user_id}')
    db.commit()
