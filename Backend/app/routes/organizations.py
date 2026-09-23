from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Tenant, User
from ..schemas import UserCreate
from ..security import hash_password
from ..services import audit
from .auth import throttle

router = APIRouter(prefix='/api/organizations', tags=['Organization onboarding'])


class OrganizationCreate(UserCreate):
    organization_name: str = Field(min_length=2, max_length=120)
    slug: str = Field(min_length=2, max_length=80, pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$')

    @field_validator('role')
    @classmethod
    def fixed_admin_role(cls, value):
        if value != 'ADMIN':
            raise ValueError('The first organization member must be an administrator')
        return value

    role: str = 'ADMIN'


@router.post('', status_code=201)
def create_organization(body: OrganizationCreate, request: Request, db: Session = Depends(get_db)):
    # Share the authentication attempt budget to limit unauthenticated provisioning.
    throttle(request.client.host if request.client else 'unknown')
    if db.scalar(select(Tenant.id).where(Tenant.slug == body.slug)):
        raise HTTPException(409, 'This organization ID is already taken. Choose another ID.')
    try:
        tenant = Tenant(name=body.organization_name, slug=body.slug)
        db.add(tenant)
        db.flush()
        admin = User(tenant_id=tenant.id, name=body.name, email=body.email,
                     password_hash=hash_password(body.password), role='ADMIN')
        db.add(admin)
        db.flush()
        audit(db, admin, 'ORGANIZATION_CREATED', f'organization:{tenant.slug}')
        audit(db, admin, 'USER_CREATED', f'user:{admin.id}; role:ADMIN')
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'This organization ID is already taken. Choose another ID.')
    return {'message': 'Organization created. Sign in with your organization ID and administrator credentials.',
            'tenant': {'name': tenant.name, 'slug': tenant.slug}, 'email': admin.email}
