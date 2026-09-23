import base64
import hashlib
import hmac
import secrets
from datetime import timedelta
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import User, now

bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=32768, r=8, p=1, maxmem=67108864)
    return 'scrypt$' + base64.b64encode(salt).decode() + '$' + base64.b64encode(digest).decode()


def verify_password(password: str, encoded: str) -> bool:
    try:
        _, salt, expected = encoded.split('$')
        digest = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt), n=32768, r=8, p=1, maxmem=67108864)
        return hmac.compare_digest(digest, base64.b64decode(expected))
    except (ValueError, TypeError):
        return False


DUMMY_HASH = hash_password(secrets.token_urlsafe(24))


def issue_token(user: User):
    return jwt.encode({'sub': str(user.id), 'ver': user.token_version, 'iat': now(),
                       'exp': now() + timedelta(minutes=settings.access_token_minutes),
                       'iss': 'deeptrace', 'aud': 'deeptrace-app'}, settings.jwt_secret, algorithm='HS256')


def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
    error = HTTPException(401, 'Session expired or invalid. Please sign in.', headers={'WWW-Authenticate': 'Bearer'})
    if not credentials:
        raise error
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=['HS256'],
                             issuer='deeptrace', audience='deeptrace-app', options={'require': ['sub', 'exp', 'iat', 'ver']})
        user = db.get(User, int(payload['sub']))
        if not user or not user.is_active or user.token_version != payload['ver']:
            raise error
        return user
    except (jwt.PyJWTError, ValueError, TypeError):
        raise error


def require_roles(*roles):
    def dependency(user: User = Depends(current_user)):
        if user.role not in roles:
            raise HTTPException(403, 'Your role does not permit this action')
        return user
    return dependency
