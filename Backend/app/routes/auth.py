import time
from collections import defaultdict, deque
from threading import Lock
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Tenant, User, AuditLog
from ..schemas import Login
from ..security import current_user, issue_token, verify_password, DUMMY_HASH
from ..services import audit, public

router = APIRouter(prefix='/api/auth', tags=['Authentication'])
attempts = defaultdict(deque)
attempt_lock = Lock()


def throttle(key):
    timestamp = time.monotonic()
    with attempt_lock:
        for stale in [k for k, entries in attempts.items() if not entries or entries[-1] < timestamp - 60]:
            del attempts[stale]
        bucket = attempts[key]
        while bucket and bucket[0] < timestamp - 60:
            bucket.popleft()
        if len(bucket) >= 10:
            raise HTTPException(429, 'Too many login attempts. Retry after one minute.', headers={'Retry-After': '60'})
        bucket.append(timestamp)


@router.post('/login')
def login(body: Login, request: Request, response: Response, db: Session = Depends(get_db)):
    throttle(request.client.host if request.client else 'unknown')
    tenant = db.scalar(select(Tenant).where(Tenant.slug == body.organization.lower()))
    user = db.scalar(select(User).where(User.tenant_id == tenant.id, User.email == body.email.lower())) if tenant else None
    valid = verify_password(body.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid or not user.is_active:
        if tenant:
            db.add(AuditLog(tenant_id=tenant.id, actor='anonymous', action='LOGIN_FAILED', resource='authentication'))
            db.commit()
        raise HTTPException(401, 'Invalid organization, email or password')
    audit(db, user, 'LOGIN', 'authentication')
    db.commit()
    response.headers['Cache-Control'] = 'no-store'
    return {'access_token': issue_token(user), 'token_type': 'bearer', 'user': public(user), 'tenant': {'name': tenant.name, 'slug': tenant.slug}}


@router.get('/me')
def me(user: User = Depends(current_user), db: Session = Depends(get_db)):
    tenant = db.get(Tenant, user.tenant_id)
    return {'user': public(user), 'tenant': {'name': tenant.name, 'slug': tenant.slug}}


@router.post('/logout', status_code=204)
def logout(user: User = Depends(current_user), db: Session = Depends(get_db)):
    user.token_version += 1
    audit(db, user, 'LOGOUT', 'all sessions revoked')
    db.commit()
