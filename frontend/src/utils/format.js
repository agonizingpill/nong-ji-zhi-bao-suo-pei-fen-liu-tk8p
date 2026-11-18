export const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const pct=x=>x==null?'待评估':(x*100).toFixed(1)+'%';
export const num=x=>Number(x).toLocaleString('zh-CN');
export function formData(form){return Object.fromEntries(new FormData(form))}
export const localTime=x=>new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(x));
