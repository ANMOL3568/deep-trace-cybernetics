from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Tenant, User
from ..schemas import Role, UserCreate, UserUpdate
from ..security import current_user, hash_password, require_roles
from ..services import audit, changes, get_resource, paginate, public, scoped

router = APIRouter(prefix='/api/users', tags=['Users'])


@router.get('')
def list_users(q: str = Query('', max_length=160), role: Role | None = None, active: bool | None = None,
               page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100), sort: str = 'created_at',
               order: Literal['asc', 'desc'] = 'desc', user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = scoped(User, user)
    if q:
        query = query.where(User.name.icontains(q, autoescape=True) | User.email.icontains(q, autoescape=True))
    if role:
        query = query.where(User.role == role)
    if active is not None:
        query = query.where(User.is_active == active)
    return paginate(db, query, User, page, page_size, sort, order)


@router.post('', status_code=201)
def create_user(body: UserCreate, user: User = Depends(require_roles('ADMIN')), db: Session = Depends(get_db)):
    data = body.model_dump(exclude={'password'})
    row = User(**data, tenant_id=user.tenant_id, password_hash=hash_password(body.password))
    db.add(row)
    db.flush()
    audit(db, user, 'USER_CREATED', f'user:{row.id}')
    db.commit()
    return public(row)


@router.patch('/{user_id}')
def update_user(user_id: int, body: UserUpdate, user: User = Depends(require_roles('ADMIN')), db: Session = Depends(get_db)):
    # Serialize role/active changes per tenant so concurrent requests cannot remove every admin.
    db.scalar(select(Tenant).where(Tenant.id == user.tenant_id).with_for_update())
    row = get_resource(db, User, user_id, user, lock=True)
    data = changes(body)
    if row.id == user.id and (data.get('is_active') is False or data.get('role', row.role) != 'ADMIN'):
        raise HTTPException(409, 'You cannot deactivate or demote your own account')
    if row.role == 'ADMIN' and (data.get('is_active') is False or data.get('role', row.role) != 'ADMIN'):
        others = db.scalar(select(User.id).where(User.tenant_id == user.tenant_id, User.id != row.id,
                                                User.role == 'ADMIN', User.is_active.is_(True)).limit(1))
        if not others:
            raise HTTPException(409, 'At least one active administrator is required')
    fields = list(data)
    if 'password' in data:
        row.password_hash = hash_password(data.pop('password'))
    if any(key in fields for key in ['password', 'role', 'is_active']):
        row.token_version += 1
    for key, value in data.items():
        setattr(row, key, value)
    audit(db, user, 'USER_UPDATED', f'user:{row.id}; fields:{",".join(fields)}')
    db.commit()
    return public(row)
