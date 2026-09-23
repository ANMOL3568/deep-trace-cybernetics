from sqlalchemy import func, select
from app.models import Tenant, User, AuditLog


def payload(**updates):
    return {'organization_name':'Apex Cybersecurity', 'slug':'apex-cybersecurity',
            'name':'Anmol', 'email':'admin@apex.test', 'password':'SecurePassword123!', **updates}


def test_signup_login_and_empty_tenant_isolation(context):
    client=context['client']
    response=client.post('/api/organizations',json=payload())
    assert response.status_code==201, response.text
    assert response.json()['tenant']['slug']=='apex-cybersecurity'
    assert 'password' not in response.text
    login=client.post('/api/auth/login',json={'organization':'apex-cybersecurity','email':'admin@apex.test','password':'SecurePassword123!'})
    assert login.status_code==200
    assert login.json()['user']['role']=='ADMIN'
    auth={'Authorization':'Bearer '+login.json()['access_token']}
    dashboard=client.get('/api/dashboard',headers=auth).json()
    assert dashboard['users']==1 and dashboard['campaigns']==0 and dashboard['open_events']==0
    assert client.get(f"/api/campaigns/{context['campaigns']['a']}",headers=auth).status_code==404
    assert client.get('/api/audit-logs',headers=auth).json()['total']==3


def test_duplicate_organization_does_not_create_orphan_user(context):
    client=context['client']
    assert client.post('/api/organizations',json=payload()).status_code==201
    assert client.post('/api/organizations',json=payload(email='other@apex.test')).status_code==409
    with context['factory']() as db:
        tenant=db.scalar(select(Tenant).where(Tenant.slug=='apex-cybersecurity'))
        assert db.scalar(select(func.count()).select_from(User).where(User.tenant_id==tenant.id))==1
        assert db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.tenant_id==tenant.id))==2


def test_signup_validation_and_tenant_injection(context):
    client=context['client']
    for updates in [{'slug':'Apex Company'},{'slug':'-apex'},{'password':'short'},{'email':'invalid'}, {'tenant_id':1}, {'role':'USER'}]:
        assert client.post('/api/organizations',json=payload(**updates)).status_code==422
    with context['factory']() as db:
        assert db.scalar(select(Tenant).where(Tenant.slug=='apex-cybersecurity')) is None


def test_signup_keeps_authenticated_workspace_separate(context):
    client=context['client'];auth=context['tokens']['a_admin']
    assert client.post('/api/organizations',headers=auth,json=payload()).status_code==201
    assert client.get('/api/auth/me',headers=auth).json()['tenant']['slug']=='test-alpha'
