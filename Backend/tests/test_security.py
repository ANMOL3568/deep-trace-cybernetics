import pytest
import jwt
from datetime import timedelta
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.config import settings
from app.models import AuditLog, CampaignMember, User, now
from app.security import hash_password, verify_password


def test_login_and_secret_redaction(context):
    c = context
    response = c['client'].post('/api/auth/login', json={'organization':'test-alpha', 'email':'admin@a.test', 'password':c['password']})
    assert response.status_code == 200
    body = response.json()
    assert body['tenant']['slug'] == 'test-alpha'
    assert 'password_hash' not in body['user'] and 'token_version' not in body['user']
    assert c['client'].get('/api/auth/me', headers={'Authorization': f"Bearer {body['access_token']}"}).status_code == 200
    assert c['client'].post('/api/auth/login', json={'organization':'test-beta', 'email':'admin@a.test', 'password':c['password']}).status_code == 401


@pytest.mark.parametrize('method', ['get', 'patch', 'delete'])
def test_campaign_cross_tenant_idor(context, method):
    c = context
    kwargs = {'headers': c['tokens']['a_admin']}
    if method == 'patch': kwargs['json'] = {'title': 'Hacked title'}
    response = getattr(c['client'], method)(f"/api/campaigns/{c['campaigns']['b']}", **kwargs)
    assert response.status_code == 404


def test_isolation_all_lists_and_dashboard(context):
    c = context; auth = c['tokens']['a_admin']
    campaigns = c['client'].get('/api/campaigns', headers=auth).json()
    assert [row['id'] for row in campaigns['items']] == [c['campaigns']['a']]
    assert c['client'].get('/api/security-events', headers=auth).json()['total'] == 1
    assert c['client'].get('/api/users', headers=auth).json()['total'] == 3
    dashboard = c['client'].get('/api/dashboard', headers=auth).json()
    assert dashboard['users'] == 3 and dashboard['critical_events'] == 1 and dashboard['campaigns'] == 1
    assert c['client'].get(f"/api/security-events/{c['events']['b']}", headers=auth).status_code == 404
    assert c['client'].patch(f"/api/security-events/{c['events']['b']}", headers=auth, json={'status':'RESOLVED'}).status_code == 404
    assert c['client'].patch(f"/api/users/{c['ids']['b_user']}", headers=auth, json={'role':'ADMIN'}).status_code == 404


def test_cross_tenant_assignments_rejected(context):
    c = context; path = f"/api/campaigns/{c['campaigns']['a']}/members"
    assert c['client'].post(path, headers=c['tokens']['a_admin'], json={'user_id':c['ids']['b_user']}).status_code == 404
    assert c['client'].post(f"/api/campaigns/{c['campaigns']['b']}/members", headers=c['tokens']['a_admin'], json={'user_id':c['ids']['a_user']}).status_code == 404
    with c['factory']() as db:
        tenant_id = db.get(User, c['ids']['a_user']).tenant_id
        db.add(CampaignMember(tenant_id=tenant_id, campaign_id=c['campaigns']['a'], user_id=c['ids']['b_user']))
        with pytest.raises(IntegrityError): db.commit()


def test_role_permissions_and_assignments(context):
    c = context; member = c['tokens']['a_user']; manager = c['tokens']['a_manager']; path = f"/api/campaigns/{c['campaigns']['a']}"
    assert c['client'].post('/api/campaigns', headers=member, json={'title':'Forbidden campaign'}).status_code == 403
    assert c['client'].get('/api/audit-logs', headers=manager).status_code == 403
    assert c['client'].delete(path, headers=manager).status_code == 403
    assert c['client'].post('/api/users', headers=manager, json={'name':'Someone', 'email':'someone@a.test','password':'LongPassword123!'}).status_code == 403
    assert c['client'].post('/api/security-events', headers=member, json={'event_type':'Test', 'severity':'HIGH','description':'Test description'}).status_code == 403
    assert c['client'].get(path, headers=member).status_code == 404
    assert c['client'].get('/api/campaigns', headers=member).json()['total'] == 0
    assert c['client'].post(path+'/members', headers=manager, json={'user_id':c['ids']['a_user']}).status_code == 201
    assert c['client'].post(path+'/members', headers=manager, json={'user_id':c['ids']['a_user']}).status_code == 409
    assert c['client'].get(path, headers=member).status_code == 200
    assert c['client'].get('/api/dashboard', headers=member).json()['campaigns'] == 1
    assert c['client'].delete(path+f"/members/{c['ids']['a_user']}", headers=manager).status_code == 204
    assert c['client'].get(path, headers=member).status_code == 404


def test_crud_status_transitions_and_audit(context):
    c = context; auth=c['tokens']['a_admin']
    created=c['client'].post('/api/campaigns',headers=auth,json={'title':'New security campaign','description':'Review controls'})
    assert created.status_code == 201
    path=f"/api/campaigns/{created.json()['id']}"
    assert c['client'].patch(path,headers=auth,json={'status':'COMPLETED'}).status_code == 409
    assert c['client'].patch(path,headers=auth,json={'status':'ACTIVE'}).status_code == 200
    assert c['client'].patch(path,headers=auth,json={'status':'COMPLETED'}).status_code == 200
    assert c['client'].patch(path,headers=auth,json={'status':'ACTIVE'}).status_code == 409
    assert c['client'].delete(path,headers=auth).status_code == 204
    assert c['client'].get(path,headers=auth).status_code == 404
    actions=[row['action'] for row in c['client'].get('/api/audit-logs',headers=auth).json()['items']]
    assert {'CAMPAIGN_CREATED','CAMPAIGN_UPDATED','CAMPAIGN_DELETED'} <= set(actions)
    assert c['client'].get('/api/audit-logs',headers=c['tokens']['b_admin']).json()['total'] == 0


def test_validation_and_injection(context):
    c=context; auth=c['tokens']['a_admin']
    assert c['client'].post('/api/campaigns',headers=auth,json={'title':'Valid title','tenant_id':999}).status_code == 422
    assert c['client'].post('/api/campaigns',headers=auth,json={'title':'  '}).status_code == 422
    for body in [{}, {'title':None}, {'status':'INVALID'}]:
        assert c['client'].patch(f"/api/campaigns/{c['campaigns']['a']}",headers=auth,json=body).status_code == 422
    for query in ['page=0','page_size=101','sort=password_hash','order=sideways']:
        assert c['client'].get('/api/campaigns?'+query,headers=auth).status_code == 422
    assert c['client'].get('/api/campaigns',params={'q':"' OR 1=1 --"},headers=auth).json()['total'] == 0
    assert c['client'].get('/api/campaigns',params={'q':'%'},headers=auth).json()['total'] == 0


def test_logout_revokes_token_and_expired_tokens_fail(context):
    c=context; auth=c['tokens']['a_admin']
    assert c['client'].post('/api/auth/logout',headers=auth).status_code == 204
    assert c['client'].get('/api/auth/me',headers=auth).status_code == 401
    expired=jwt.encode({'sub':str(c['ids']['a_user']),'ver':0,'iat':now()-timedelta(hours=2),'exp':now()-timedelta(hours=1),'iss':'deeptrace','aud':'deeptrace-app'},settings.jwt_secret,algorithm='HS256')
    assert c['client'].get('/api/auth/me',headers={'Authorization':f'Bearer {expired}'}).status_code == 401
    assert c['client'].get('/api/auth/me',headers={'Authorization':'Bearer invalid'}).status_code == 401
    assert c['client'].get('/api/campaigns').status_code == 401


def test_user_lifecycle(context):
    c=context; auth=c['tokens']['a_admin']
    values={'name':'New User','email':'new@a.test','password':'BrandNewPassword123!','role':'USER'}
    response=c['client'].post('/api/users',headers=auth,json=values)
    assert response.status_code == 201 and 'password_hash' not in response.json()
    assert c['client'].post('/api/users',headers=auth,json=values).status_code == 409
    user_id=c['ids']['a_user']
    assert c['client'].patch(f'/api/users/{user_id}',headers=auth,json={'is_active':False}).status_code == 200
    assert c['client'].get('/api/auth/me',headers=c['tokens']['a_user']).status_code == 401
    assert c['client'].patch(f"/api/users/{c['ids']['a_admin']}",headers=auth,json={'role':'USER'}).status_code == 409
    assert c['client'].patch(f"/api/users/{c['ids']['a_admin']}",headers=auth,json={'is_active':False}).status_code == 409


def test_events_filters_pagination_and_transitions(context):
    c=context; auth=c['tokens']['a_manager']
    response=c['client'].post('/api/security-events',headers=auth,json={'event_type':'Network anomaly','severity':'LOW','description':'Unusual traffic in network'})
    assert response.status_code == 201
    path=f"/api/security-events/{response.json()['id']}"
    assert c['client'].get('/api/security-events?severity=LOW',headers=auth).json()['total'] == 1
    page=c['client'].get('/api/security-events?page_size=1&page=2',headers=auth).json()
    assert page['total']==2 and len(page['items'])==1
    assert c['client'].patch(path,headers=auth,json={'status':'RESOLVED'}).status_code == 200
    assert c['client'].patch(path,headers=auth,json={'status':'OPEN'}).status_code == 409


def test_password_hashes_are_salted():
    password='LongPassword123!'
    first=hash_password(password);second=hash_password(password)
    assert first!=second and password not in first
    assert verify_password(password,first)
    assert not verify_password('wrong',first)


def test_login_rate_limit(context):
    c=context
    payload={'organization':'test-alpha','email':'admin@a.test','password':'wrong'}
    for _ in range(10): assert c['client'].post('/api/auth/login',json=payload).status_code == 401
    assert c['client'].post('/api/auth/login',json=payload).status_code == 429
