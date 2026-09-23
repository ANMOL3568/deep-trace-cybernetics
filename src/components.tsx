import { useEffect, useRef, type ReactNode } from 'react';
import { X, ChevronLeft, ChevronRight, Search, Loader2 } from 'lucide-react';

export function Brand() { return <div className="brand dt-brand"><img src="/deeptrace-mark.svg" alt=""/><span><span className="brand-deep">DEEP</span> TRACE<small>CYBERNETICS</small></span></div>; }
export function Badge({value}: {value: string}) { return <span className={`badge ${value.toLowerCase()}`}><i/>{value.replaceAll('_', ' ')}</span>; }
export function Loading() { return <div className="empty"><Loader2 className="spin" size={25}/><span>Loading workspace…</span></div>; }
export function Empty({text = 'No records found. Try adjusting your filters.'}: {text?: string}) { return <div className="empty"><Search size={26}/><span>{text}</span></div>; }
export function ErrorBox({message}: {message: string}) { return message ? <div className="error" role="alert">{message}</div> : null; }
export function date(value: string) { return new Date(value).toLocaleDateString('en-GB', {day:'2-digit', month:'short', year:'numeric'}); }
export function time(value: string) { return new Date(value).toLocaleString('en-GB', {day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit'}); }
export function Pagination({page, total, size=10, onChange}: {page: number; total: number; size?: number; onChange: (page: number)=>void}) {
  return <div className="pagination"><span>{total ? (page-1)*size+1 : 0}–{Math.min(page*size,total)} of {total} records</span><div><button className="icon-button" aria-label="Previous page" disabled={page<=1} onClick={()=>onChange(page-1)}><ChevronLeft size={17}/></button><span>Page {page} of {Math.max(1,Math.ceil(total/size))}</span><button className="icon-button" aria-label="Next page" disabled={page*size>=total} onClick={()=>onChange(page+1)}><ChevronRight size={17}/></button></div></div>;
}
export function Modal({title, onClose, children}: {title: string; onClose: ()=>void; children: ReactNode}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(()=>{ref.current?.showModal();}, []);
  return <dialog ref={ref} className="modal" onCancel={e=>{e.preventDefault();onClose();}} onClick={e=>{if(e.target===ref.current) onClose();}}><div className="modal-head"><h2>{title}</h2><button type="button" className="icon-button" aria-label="Close dialog" onClick={onClose}><X size={20}/></button></div>{children}</dialog>;
}
export function SearchBox({value,onChange,placeholder='Search records…'}: {value:string;onChange:(v:string)=>void;placeholder?:string}) { return <div className="search-box"><Search size={17}/><input aria-label={placeholder} placeholder={placeholder} value={value} onChange={e=>onChange(e.target.value)}/></div>; }
