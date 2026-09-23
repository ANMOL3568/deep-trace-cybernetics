import os
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.engine import make_url

os.environ['DATABASE_URL'] = os.environ.get('TEST_DATABASE_URL', 'sqlite://')
if not os.environ['DATABASE_URL'].startswith('sqlite') and not (make_url(os.environ['DATABASE_URL']).database or '').endswith('_test'):
    raise RuntimeError('TEST_DATABASE_URL must use a dedicated database ending in _test; tests drop application tables')
os.environ['JWT_SECRET'] = 'test-only-secret-with-at-least-32-characters'

from fastapi.testclient import TestClient
from app.database import Base, get_db
from app.main import app
from app.models import Campaign, CampaignMember, SecurityEvent, Tenant, User
from app.routes.auth import attempts
from app.security import hash_password, issue_token


@pytest.fixture()
def context():
    url = os.environ['DATABASE_URL']
    engine = create_engine(url, **({'connect_args': {'check_same_thread': False}, 'poolclass': StaticPool} if url.startswith('sqlite') else {}))
    if url.startswith('sqlite'):
        @event.listens_for(engine, 'connect')
        def foreign_keys(conn, _):
            conn.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    def override_db():
        with factory() as db:
            yield db
    app.dependency_overrides[get_db] = override_db
    attempts.clear()
    password = 'TestPassword123!'
    with factory() as db:
        first = Tenant(slug='test-alpha', name='Alpha')
        second = Tenant(slug='test-beta', name='Beta')
        db.add_all([first, second]); db.flush()
        users = {}
        for tenant, prefix in [(first, 'a'), (second, 'b')]:
            for role in ['ADMIN', 'MANAGER', 'USER']:
                account = User(tenant_id=tenant.id, name=f'{prefix} {role}', email=f'{role.lower()}@{prefix}.test', role=role, password_hash=hash_password(password))
                db.add(account); db.flush(); users[f'{prefix}_{role.lower()}'] = account
        campaigns = {}
        events = {}
        for tenant, prefix in [(first, 'a'), (second, 'b')]:
            campaign = Campaign(tenant_id=tenant.id, title=f'{prefix} confidential campaign', description='Test campaign', created_by=users[f'{prefix}_admin'].id)
            security_event = SecurityEvent(tenant_id=tenant.id, event_type='Suspicious login', description='Test event description', severity='CRITICAL')
            db.add_all([campaign, security_event]); db.flush()
            campaigns[prefix] = campaign.id; events[prefix] = security_event.id
        db.commit()
        tokens = {name: {'Authorization': f'Bearer {issue_token(account)}'} for name, account in users.items()}
        ids = {name: account.id for name, account in users.items()}
    with TestClient(app) as client:
        yield {'client': client, 'tokens': tokens, 'ids': ids, 'campaigns': campaigns, 'events': events, 'factory': factory, 'password': password}
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()
