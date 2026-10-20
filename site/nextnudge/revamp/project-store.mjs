import {validateProject,PROJECT_ID,assertAppendOnly} from './project-model.mjs';
import {REPO,issueUrl,issueBody} from './save.mjs';
const ROOT='site/nextnudge-data/projects/';
const LOCAL='nextnudge.projects.v1',SHAS='nextnudge.projects.sha.v1';
const readKey=key=>{try{return JSON.parse(localStorage.getItem(key)||'{}');}catch{return {};}};
export function localProjects(){const rows=readKey(LOCAL);for(const p of Object.values(rows))validateProject(p);return rows;}
export function persistProject(p){
  validateProject(p);
  const rows=localProjects();rows[p.id]=p;
  localStorage.setItem(LOCAL,JSON.stringify(rows));return p;
}
export function projectForThread(threadId,projects=localProjects()){
  const matches=Object.values(projects).filter(p=>p.threads.some(t=>t.id===threadId));
  if(matches.length>1)throw Error('Ambiguous project association; resolve explicitly');
  return matches[0]||null;
}
export function projectSha(id){return readKey(SHAS)[id]||null;}
export function recordProjectSha(id,sha){
  if(sha!==null&&!/^[a-f0-9]{40}$/.test(sha))throw Error('Invalid project SHA');
  const rows=readKey(SHAS);rows[id]=sha;localStorage.setItem(SHAS,JSON.stringify(rows));
}
const path=id=>ROOT+id+'.json';
async function readFile(id){
  if(!PROJECT_ID.test(id))throw Error('Invalid project ID');
  const response=await fetch('https://api.github.com/repos/'+REPO+'/contents/'+path(id)+'?ref=main',
    {cache:'no-store',headers:{Accept:'application/vnd.github+json'}});
  if(response.status===404)return {project:null,sha:null};
  if(!response.ok)throw Error('GitHub project read failed '+response.status);
  const body=await response.json();
  if(!/^[a-f0-9]{40}$/.test(body.sha)||body.encoding!=='base64')throw Error('Invalid project blob');
  const bytes=Uint8Array.from(atob(body.content.replace(/\s/g,'')),c=>c.charCodeAt(0));
  const project=validateProject(JSON.parse(new TextDecoder().decode(bytes)));
  if(project.id!==id)throw Error('Project path and ID differ');
  return {project,sha:body.sha};
}
export const readRemoteProject=readFile;
export async function discoverProjects(){
  const url='https://api.github.com/repos/'+REPO+'/contents/'+ROOT.slice(0,-1)+'?ref=main';
  const response=await fetch(url,{cache:'no-store'});
  if(response.status===404)return {imported:0,conflicts:0};
  if(!response.ok)throw Error('GitHub project listing failed '+response.status);
  const list=await response.json(),local=localProjects();
  let imported=0,conflicts=0;
  for(const entry of list){
    const id=entry.name?.replace(/\.json$/,'');
    if(!PROJECT_ID.test(id)||entry.name!==id+'.json')continue;
    const remote=await readFile(id);
    if(!local[id]){persistProject(remote.project);recordProjectSha(id,remote.sha);imported++;}
    else if(projectSha(id)!==remote.sha)conflicts++;
  }
  return {imported,conflicts};
}
export async function prepareProjectSave(project){
  validateProject(project);
  const remote=await readFile(project.id),known=projectSha(project.id);
  if(remote.sha!==known)throw Error('NEEDS RELOAD: GitHub project changed. Device draft retained.');
  assertAppendOnly(remote.project,project);
  const packet={v:1,id:project.id,baseSha:remote.sha,project};
  try{
    const url=await issueUrl(packet,'nextnudge-project-save');
    return {url,chars:url.length,packet,manual:false};
  }catch(e){
    if(!/exceeds one-click limit/.test(e.message))throw e;
    const body=await issueBody(packet,'nextnudge-project-save');
    if(body.length>65000)throw Error('Project snapshot exceeds GitHub issue-body limit. Device draft retained; export and request a reviewed source-file save.');
    const url='https://github.com/'+REPO+'/issues/new?labels=nextnudge-save&title='+
      encodeURIComponent('NextNudge project '+packet.id);
    return {url,chars:url.length,packet,manual:true,body};
  }
}
