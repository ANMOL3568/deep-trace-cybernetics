from datetime import timedelta
from sqlalchemy import select
from .config import settings
from .database import SessionLocal
from .models import AuditLog, Campaign, CampaignMember, SecurityEvent, Tenant, User, now
from .security import hash_password


def seed():
    with SessionLocal() as db:
        for slug, name in [('acme', 'Acme Corporation'), ('nexus', 'Nexus Labs')]:
            if db.scalar(select(Tenant).where(Tenant.slug == slug)):
                continue
            tenant = Tenant(name=name, slug=slug)
            db.add(tenant)
            db.flush()
            people = []
            for role, person in [('ADMIN', 'Alex Morgan'), ('MANAGER', 'Jordan Lee'), ('USER', 'Sam Taylor')]:
                person_row = User(tenant_id=tenant.id, name=person, email=f'{role.lower()}@{slug}.test',
                                  role=role, password_hash=hash_password(settings.seed_password))
                db.add(person_row)
                people.append(person_row)
            db.flush()
            for index, (title, status) in enumerate([
                ('Quarterly access review', 'ACTIVE'), ('Phishing awareness program', 'ACTIVE'),
                ('Cloud infrastructure audit', 'DRAFT'), ('Endpoint hardening', 'COMPLETED'),
                ('Incident response readiness', 'DRAFT'), ('Legacy network assessment', 'CANCELLED')]):
                campaign = Campaign(tenant_id=tenant.id, created_by=people[0].id, title=title, status=status,
                                    description='Review controls, coordinate the security team, and document findings and remediation.',
                                    created_at=now() - timedelta(days=index + 1))
                db.add(campaign)
                db.flush()
                db.add(CampaignMember(tenant_id=tenant.id, campaign_id=campaign.id, user_id=people[1].id))
                if index % 2 == 0:
                    db.add(CampaignMember(tenant_id=tenant.id, campaign_id=campaign.id, user_id=people[2].id))
            examples = [
                ('Suspicious sign-in', 'CRITICAL', 'Unusual login activity detected from an unrecognized location.'),
                ('Privilege escalation', 'HIGH', 'Unexpected permission change detected on a service account.'),
                ('Malware detection', 'HIGH', 'Endpoint protection quarantined a suspicious executable.'),
                ('Policy violation', 'MEDIUM', 'An unmanaged device attempted to access a protected resource.'),
                ('Network anomaly', 'MEDIUM', 'Unusual outbound traffic volume detected on the gateway.'),
                ('Configuration drift', 'LOW', 'A security configuration differs from the approved baseline.'),
            ]
            for index in range(18):
                event_type, severity, description = examples[index % len(examples)]
                db.add(SecurityEvent(tenant_id=tenant.id, event_type=event_type, severity=severity, description=description,
                                     status=['OPEN', 'INVESTIGATING', 'RESOLVED'][index % 3],
                                     created_at=now() - timedelta(days=index % 7, hours=index % 4)))
            db.add(AuditLog(tenant_id=tenant.id, actor=people[0].email, action='TENANT_INITIALIZED', resource=slug))
        db.commit()
    print('Demo tenants ready: acme and nexus. See README for credentials.')


if __name__ == '__main__':
    seed()
