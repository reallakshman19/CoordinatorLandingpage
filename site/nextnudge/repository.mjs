import {validate} from './schema.mjs';
export const REPO='reallakshman19/CoordinatorLandingpage';
export const PATH='site/nextnudge-data/workbench.json';
export const EDIT=`https://github.com/${REPO}/edit/main/${PATH}`;
const API=`https://api.github.com/repos/${REPO}/contents/${PATH}?ref=main`;
export async function readRepository() {
  const response=await fetch(API,{cache:'no-store',headers:{Accept:'application/vnd.github+json'}});
  if(!response.ok) throw Error(`GitHub read failed (${response.status}). Drafts remain local.`);
  const entry=await response.json();
  if(!/^[a-f0-9]{40}$/.test(entry.sha)||entry.encoding!=='base64'||!entry.content) throw Error('GitHub snapshot is unavailable or too large.');
  const bytes=Uint8Array.from(atob(entry.content.replace(/\s/g,'')),c=>c.charCodeAt(0));
  return {db:validate(JSON.parse(new TextDecoder().decode(bytes))),sha:entry.sha};
}
export async function fingerprint(db) {
  function sorted(v) {
    if(Array.isArray(v))return v.map(sorted);
    if(v&&typeof v==='object')return Object.fromEntries(Object.keys(v).sort().map(k=>[k,sorted(v[k])]));
    return v;
  }
  const hash=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(sorted(db))));
  return [...new Uint8Array(hash)].map(b=>b.toString(16).padStart(2,'0')).join('');
}
export async function prepareSave(db,baseSha) {
  const remote=await readRepository();
  if(!baseSha||remote.sha!==baseSha) throw Error('GitHub changed or the base is unknown. Export your draft and reload GitHub before preparing an update.');
  validate(db);
  return {text:JSON.stringify(db,null,2)+'\n',digest:await fingerprint(db)};
}
export function download(db) {
  const url=URL.createObjectURL(new Blob([JSON.stringify(db,null,2)],{type:'application/json'}));
  const a=document.createElement('a');a.href=url;a.download='nextnudge-workbench-v2.json';a.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
