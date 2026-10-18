import {validate} from './schema.mjs';
import {readRepository} from './repository.mjs';
export const KEY='nextnudge.workbench.v2';
export const PRIVATE_KEY='nextnudge.device-chats.v1';
export function cache(state) {
  localStorage.setItem(KEY,JSON.stringify({db:state.db,baseSha:state.baseSha,
    dirty:state.dirty,prepared:state.prepared||null}));
}
export async function bootstrap() {
  let local=null,error='';
  try {
    const value=localStorage.getItem(KEY);
    if(value){local=JSON.parse(value);validate(local.db);}
  } catch {error='Local draft could not be read; it has not been overwritten.';}
  try {
    const remote=await readRepository();
    if(local?.dirty) return {...local,warning:remote.sha!==local.baseSha?
      'GitHub changed while this draft was open. Export and reconcile before saving.':error};
    return {...remote,baseSha:remote.sha,dirty:false,warning:error};
  } catch(e) {
    if(local)return {...local,warning:e.message};
    const response=await fetch('../nextnudge-data/workbench.json',{cache:'no-store'});
    if(!response.ok)throw Error('Neither GitHub nor the deployed snapshot is available. Restore an export to continue.');
    return {db:validate(await response.json()),baseSha:null,dirty:false,
      warning:e.message+' Showing the deployed snapshot; GitHub save needs a fresh base.'};
  }
}
export function getPrivateChat(runId) {
  try{return JSON.parse(localStorage.getItem(PRIVATE_KEY)||'{}')[runId]||'';}catch{return '';}
}
export function setPrivateChat(runId,url) {
  if(url&&!/^https:\/\//i.test(url))throw Error('Chat URL must use https.');
  const chats=JSON.parse(localStorage.getItem(PRIVATE_KEY)||'{}');chats[runId]=url;
  localStorage.setItem(PRIVATE_KEY,JSON.stringify(chats));
}
