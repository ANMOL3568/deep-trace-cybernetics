import { useState, type FormEvent } from 'react';
import { ArrowRight, Building2, CheckCircle2, Eye, EyeOff } from 'lucide-react';
import { write } from './api';
import { ErrorBox } from './components';

export type CreatedOrganization = { tenant: {name:string;slug:string}; email:string };
export default function OrganizationForm({onCreated}: {onCreated:(result:CreatedOrganization)=>void}) {
  const [slug,setSlug]=useState('');const [editedSlug,setEditedSlug]=useState(false);
  const [error,setError]=useState('');const [busy,setBusy]=useState(false);const [visible,setVisible]=useState(false);
  async function submit(e:FormEvent<HTMLFormElement>) {
    e.preventDefault();setError('');const values=Object.fromEntries(new FormData(e.currentTarget));
    if(values.password!==values.confirm_password){setError('Passwords do not match. Please try again.');return;}
    delete values.confirm_password;setBusy(true);
    try {onCreated(await write<CreatedOrganization>('/organizations','POST',values));}
    catch(e){setError((e as Error).message);}finally{setBusy(false);}
  }
  return <form className="onboarding-form" onSubmit={submit}><div className="form-section-title"><Building2 size={16}/>Your organization</div><label>Organization name<input name="organization_name" autoComplete="organization" placeholder="Apex Cybersecurity" minLength={2} maxLength={120} required onChange={e=>{if(!editedSlug)setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,80));}}/></label><label>Organization ID<input name="slug" value={slug} onChange={e=>{setEditedSlug(true);setSlug(e.target.value.toLowerCase());}} placeholder="apex-cybersecurity" minLength={2} maxLength={80} pattern="[a-z0-9]+(-[a-z0-9]+)*" required autoCapitalize="none" spellCheck={false}/><small>Use this unique ID when signing in. Lowercase letters, numbers and hyphens.</small></label><div className="form-section-title"><CheckCircle2 size={16}/>First administrator</div><div className="form-columns"><label>Full name<input name="name" placeholder="Your full name" autoComplete="name" required minLength={2} maxLength={120}/></label><label>Email address<input name="email" type="email" placeholder="you@company.com" autoComplete="email" required maxLength={254}/></label></div><label>Password<div className="password-input"><input name="password" type={visible?'text':'password'} placeholder="At least 12 characters" autoComplete="new-password" required minLength={12} maxLength={128}/><button type="button" aria-label={visible?'Hide password':'Show password'} onClick={()=>setVisible(v=>!v)}>{visible?<EyeOff size={17}/>:<Eye size={17}/>}</button></div></label><label>Confirm password<input name="confirm_password" type="password" placeholder="Re-enter your password" autoComplete="new-password" required minLength={12} maxLength={128}/></label><ErrorBox message={error}/><p className="signup-note">You'll be the administrator of this new workspace. Invite your team after signing in.</p><button className="cyber-button full" disabled={busy}>{busy?'Creating workspace…':'Create organization'}<ArrowRight size={17}/></button></form>;
}
