"""Add fictional demo records to the existing TechSharthi tenant, without replacing data."""
from datetime import timedelta
from sqlalchemy import select, func
from .database import SessionLocal
from .models import Tenant, User, Campaign, CampaignMember, SecurityEvent, AuditLog, now
from .security import hash_password
from .config import settings


def seed():
    with SessionLocal() as db:
        tenant = db.scalar(select(Tenant).where(Tenant.id == 3, Tenant.slug == 'techsharthi').with_for_update())
        if not tenant:
            raise RuntimeError('Expected tenant 3 / techsharthi was not found; no changes made.')
        admin = db.scalar(select(User).where(User.tenant_id == tenant.id, User.role == 'ADMIN', User.is_active.is_(True)).order_by(User.id))
        if not admin:
            raise RuntimeError('An active TechSharthi administrator is required.')
        added = {'members': 0, 'campaigns': 0, 'events': 0, 'assignments': 0}
        people = [('Aarav Sharma', 'MANAGER'), ('Priya Verma', 'MANAGER'), ('Rohan Patel', 'USER'),
                  ('Ananya Singh', 'USER'), ('Vikram Rao', 'USER'), ('Neha Gupta', 'USER'),
                  ('Arjun Mehta', 'USER'), ('Kavya Iyer', 'USER')]
        team = []
        for name, role in people:
            email = name.lower().replace(' ', '.') + '@techsharthi.example.test'
            member = db.scalar(select(User).where(User.tenant_id == tenant.id, User.email == email))
            if not member:
                member = User(tenant_id=tenant.id, name=name, email=email, role=role,
                              password_hash=hash_password(settings.seed_password))
                db.add(member)
                db.flush()
                added['members'] += 1
            team.append(member)
        campaigns = [
            ('Mumbai Office Access Review', 'ACTIVE', 'Aarav Sharma and Rohan Patel review employee access and remove unused permissions.'),
            ('Phishing Awareness - Delhi Team', 'ACTIVE', 'Priya Verma and Ananya Singh coordinate a simulated phishing awareness workshop.'),
            ('Bengaluru Cloud Security Audit', 'ACTIVE', 'Vikram Rao and Neha Gupta review demo cloud configurations and document remediation.'),
            ('Pune Endpoint Protection Rollout', 'DRAFT', 'Arjun Mehta plans endpoint policy deployment with Kavya Iyer.'),
            ('Quarterly Password Hygiene Review', 'COMPLETED', 'Aarav Sharma completed a fictional review of password and MFA practices.'),
            ('Hyderabad Incident Response Drill', 'DRAFT', 'Priya Verma prepares a tabletop exercise with Rohan Patel.'),
            ('Chennai Vendor Access Assessment', 'ACTIVE', 'Ananya Singh and Kavya Iyer review third-party access approvals.'),
            ('Finance Team Data Protection', 'COMPLETED', 'Neha Gupta and Arjun Mehta documented data handling controls for a demo finance team.'),
            ('Legacy VPN Migration Review', 'CANCELLED', 'Vikram Rao cancelled this demo initiative after its scope was replaced.'),
            ('New Joiner Security Onboarding', 'DRAFT', 'Kavya Iyer prepares security onboarding material with Aarav Sharma.'),
            ('Backup Recovery Readiness', 'ACTIVE', 'Rohan Patel and Neha Gupta test a fictional recovery checklist.'),
            ('Privileged Account Review', 'DRAFT', 'Priya Verma reviews privileged access with Arjun Mehta.'),
        ]
        for index, (title, status, description) in enumerate(campaigns):
            campaign = db.scalar(select(Campaign).where(Campaign.tenant_id == tenant.id, Campaign.title == title))
            if not campaign:
                campaign = Campaign(tenant_id=tenant.id, created_by=admin.id, title=title, status=status,
                                    description='[Demo] ' + description, created_at=now()-timedelta(days=index+1))
                db.add(campaign)
                db.flush()
                added['campaigns'] += 1
                for person in [p for p in team if p.name in description]:
                    db.add(CampaignMember(tenant_id=tenant.id, campaign_id=campaign.id, user_id=person.id))
                    added['assignments'] += 1
        examples = [
            ('Suspicious sign-in', 'CRITICAL', 'OPEN', 'Aarav Sharma is reviewing a simulated sign-in from an unfamiliar device in Mumbai.'),
            ('Privilege escalation', 'CRITICAL', 'INVESTIGATING', 'Priya Verma is investigating a fictional service-account permission change.'),
            ('Malware detection', 'HIGH', 'INVESTIGATING', 'Rohan Patel is checking a simulated quarantine alert on a Delhi demo laptop.'),
            ('Phishing email reported', 'HIGH', 'OPEN', 'Ananya Singh reported a fictional credential-request email for awareness training.'),
            ('Unmanaged device access', 'MEDIUM', 'OPEN', 'Vikram Rao is reviewing a demo device that does not meet endpoint policy.'),
            ('Cloud configuration drift', 'MEDIUM', 'INVESTIGATING', 'Neha Gupta is comparing a demo cloud configuration with its approved baseline.'),
            ('Backup verification', 'LOW', 'RESOLVED', 'Arjun Mehta completed a simulated backup integrity check.'),
            ('Outdated endpoint agent', 'LOW', 'OPEN', 'Kavya Iyer is coordinating a demo endpoint agent update.'),
            ('Unusual outbound traffic', 'HIGH', 'RESOLVED', 'Aarav Sharma resolved a simulated traffic spike in the Bengaluru test environment.'),
            ('MFA challenge failures', 'MEDIUM', 'RESOLVED', 'Priya Verma completed a fictional review of failed MFA challenges.'),
            ('Demo data exposure alert', 'CRITICAL', 'RESOLVED', 'Rohan Patel closed a tabletop data exposure scenario; no real information was exposed.'),
            ('Dormant account detected', 'LOW', 'INVESTIGATING', 'Ananya Singh is reviewing a fictional inactive account for cleanup.'),
        ]
        for index in range(24):
            event_type, severity, status, description = examples[index % len(examples)]
            description = f'[TechSharthi demo {index+1:02d}] {description}'
            if not db.scalar(select(SecurityEvent.id).where(SecurityEvent.tenant_id == tenant.id, SecurityEvent.description == description)):
                db.add(SecurityEvent(tenant_id=tenant.id, event_type=event_type, severity=severity, status=status,
                                     description=description, created_at=now()-timedelta(days=index % 7, hours=index % 4)))
                added['events'] += 1
        if any(added.values()):
            db.add(AuditLog(tenant_id=tenant.id, actor='demo-seed', action='DEMO_DATA_ADDED',
                            resource='TechSharthi: ' + ', '.join(f'{key}={value}' for key,value in added.items())))
        db.commit()
        print('TechSharthi added:', added)
        for model in [User, Campaign, SecurityEvent, CampaignMember]:
            print(model.__tablename__, db.scalar(select(func.count()).select_from(model).where(model.tenant_id == tenant.id)))


if __name__ == '__main__':
    seed()
