import {id,now,utc,safeURL} from './identity.mjs';
import {emptyFixtures,fixtureChange,pullFixtures} from './fixtures.mjs';
export const STATES=['ready','sent','submitted','accepted','revision'];
export const TYPES=['new_requirement','ground','next_step','course_correction'];
export const children=(r,n)=>r.nodes.filter(x=>x.parent===n&&!x.deleted);
export function event(db,run,step,state,note='',proof='',data=null,by='Owner') {
  const row={id:id('EV',db),project:run?.projectId||null,run:run?.id||null,
    step:step?.id||null,state,by,at:now(),proof,note,data};
  db.events.push(row);db.revision++;return row;
}
export function newProject(db,name) {
  if (!name.trim()) throw Error('Enter a project name.');
  const p={id:id('PRJ',db),name:name.trim(),createdAt:now()};db.projects.push(p);
  event(db,null,null,'PROJECT_CREATED',p.name,'',p);return p;
}
export function newStep(db,run,label,instruction='',type='next_step',parent=null) {
  if (!label.trim()||!TYPES.includes(type)) throw Error('Enter a label and valid type.');
  const n={id:id('NN',db),label:label.trim(),instruction,type,parent,status:'ready',
    messages:[],checks:{},sentAt:null,copied:null,deleted:false};
  run.nodes.push(n);event(db,run,n,'CREATED',label);return n;
}
export function newRun(db,projectId,title,aim) {
  if (!db.projects.some(p=>p.id===projectId)||!title.trim()||!aim.trim()) {
    throw Error('Select a project and enter a task title and aim.');
  }
  const r={id:id('NN',db),projectId,title:title.trim(),aim:aim.trim(),createdAt:now(),
    archived:false,deleted:false,paused:false,sentBy:'Owner',chatId8:'',profiles:Object.hasOwn(db.profiles.profiles,'Coding')
      ? ['Coding'] : [Object.keys(db.profiles.profiles)[0]],
    nodes:[],fixtures:emptyFixtures(),drafts:{}};
  db.runs.push(r);event(db,r,null,'RUN_CREATED',r.title);
  newStep(db,r,'Initial prompt',aim+'\nReply with your understanding and fill the On boarding fixtures.','new_requirement');
  newStep(db,r,'Grounding','Confirm or correct understanding; record unresolved inputs.','ground');
  return r;
}
export function editable(run,node) {
  if(run.archived||run.deleted||run.paused||node?.deleted) throw Error('Resume the active run before editing.');
}
export function editStep(db,r,n,values) {
  editable(r,n);
  if(n.sentAt||n.messages.length) throw Error('Sent or answered instructions are frozen. Add a correction.');
  if(!values.label.trim()||!TYPES.includes(values.type)) throw Error('Invalid step details.');
  const before={label:n.label,instruction:n.instruction,type:n.type};
  Object.assign(n,values,{copied:null});event(db,r,n,'INSTRUCTION_REVISED','', '',{before,after:values});
}
export function packet(r,n) {
  if(n.sentText)return n.sentText;
  const context=['1a','1b','1c','1d','1e','1f','2','3','4','5'].map(key => {
    const rows=r.fixtures[key].filter(row=>!row.deleted);
    return key+': '+(rows.length?rows.map(row=>`${row.text} [${row.status}] ${row.url}`).join(' | '):'UNKNOWN');
  }).join('\n');
  const grounding=n.type==='new_requirement'||n.type==='ground'
    ? '\n\nGrounding inputs (fill missing headings from sources; do not infer proof):\n'+context : '';
  return `[${r.sentBy||'Owner'} · NextNudge ${n.id}]\nProject: ${r.projectId}\nRun: ${r.id}\nAim: ${r.aim}\nStep: ${n.label}\n\n${n.instruction}${grounding}\n\nStart your reply with ACK ${n.id}. Record missing information explicitly. Supporting evidence is optional.`;
}
export async function packetSha256(r,n) {
  return fingerprintText(packet(r,n));
}
export async function fingerprintText(text) {
  const hash=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));
  return [...new Uint8Array(hash)].map(x=>x.toString(16).padStart(2,'0')).join('');
}
export function statusChange(db,r,n,to,note='',by=r.sentBy||'Owner') {
  if(n.status===to)return;
  const from=n.status;n.status=to;
  event(db,r,n,'STATUS_CHANGED',note,'',{from,to},by);
}
export function copied(db,r,n,text,sha256=null) {
  editable(r,n);n.copied={text,at:now(),sha256};event(db,r,n,'COPIED','Copied for manual delivery; not sent.');
}
export function markSent(db,r,n) {
  editable(r,n);
  if(n.sentAt) throw Error('Already marked sent. Use a correction for a new instruction.');
  if(!/^[a-f0-9]{8}$/i.test(r.chatId8)) throw Error('Record the destination chat’s 8-character ID first.');
  if(n.copied?.text!==packet(r,n)) throw Error('Copy the current instruction before marking it sent.');
  n.sentAt=now();n.sentText=n.copied.text;n.sentChatId8=r.chatId8;
  n.sentPacketSha256=n.copied.sha256||null;
  if(n.status==='ready')statusChange(db,r,n,'sent','Marked manually sent');
  event(db,r,n,'SENT','Owner records manual delivery; not independently verified.','',
    {text:n.sentText,chatId8:r.chatId8,sentAt:n.sentAt});
}
export function parseSavedLine(value) {
  const line=value.split(/\r?\n/).find(x=>/^SAVED-[A-Za-z0-9_-]+\b/.test(x.trim()))?.trim()||'';
  if(!line)return null;
  const tag=line.match(/^(SAVED-[A-Za-z0-9_-]+)/)[1],fields={};
  for(const pair of line.matchAll(/(?:^|[\s·])([A-Za-z][A-Za-z0-9_-]{0,59})=([^\s·]+)/g)){
    if(Object.hasOwn(fields,pair[1]))throw Error('Duplicate SAVED field: '+pair[1]);
    fields[pair[1]]=pair[2];
  }
  return {tag,fields};
}
export function reply(db,r,n,{by,text,proof='',repliedAt='',source='chat_words',
  returnPath='',returnBytes='',returnSha256=''}) {
  editable(r,n);
  if(!text.trim()||!['Owner','Agent'].includes(by)||!safeURL(proof)) throw Error('Enter a reply and a valid optional evidence URL.');
  if(n.status==='accepted') throw Error('Add a correction to reopen a reviewed step.');
  const ack=text.match(/\bACK\s+(NN-\d{8}-\d{6}-[a-f0-9]{4})\b/);
  if(ack&&ack[1]!==n.id) throw Error('ACK belongs to a different step. Select the matching step.');
  if(!['chat_words','return_file','relayed_summary'].includes(source))throw Error('Invalid reply source.');
  let returnFile=null;
  if(source==='return_file') {
    const size=Number(returnBytes);
    if(!returnPath||returnPath.length>1000||/[\r\n]/.test(returnPath)||
      !Number.isSafeInteger(size)||size<0||!/^[a-f0-9]{64}$/i.test(returnSha256))
      throw Error('Return file requires path, byte size and SHA-256.');
    returnFile={path:returnPath,bytes:size,sha256:returnSha256.toLowerCase()};
  }
  const m={by,text,proof,source,returnFile,savedLine:parseSavedLine(text),at:now(),recordedBy:r.sentBy||'Owner',relayed:by==='Agent',
    repliedAt:by==='Agent'?utc(repliedAt):null,chatId8:r.chatId8||null,ack:ack?.[1]||null};
  n.messages.push(m);
  if(by==='Agent'||n.type==='ground')statusChange(db,r,n,children(r,n.id).some(c=>c.status!=='accepted')?'revision':'submitted','Reply recorded');
  event(db,r,n,by==='Agent'?'REPLY_RECORDED':'FEEDBACK_RECORDED',text,proof,m,by);
}
export function checklist(db,r) {
  return r.profiles.flatMap(p=>(db.profiles.profiles[p]||[]).map(q=>({...q,key:p+':'+q.id,profile:p})));
}
export function accept(db,r,n,note='') {
  editable(r,n);
  if(n.status!=='submitted') throw Error('Record a result before reviewing.');
  if(children(r,n.id).some(c=>c.status!=='accepted')) throw Error('Resolve blocking children before rechecking the parent.');
  const qs=checklist(db,r);
  if(qs.some(q=>n.checks[q.key]==='Needs correction')) throw Error('Resolve checklist items marked Needs correction.');
  const gaps=qs.filter(q=>!n.checks[q.key]||n.checks[q.key]==='Proceed with gap').map(q=>q.question);
  if(!n.messages.some(m=>m.proof)) gaps.push('No supporting evidence link supplied');
  if(gaps.length&&!note.trim()) throw Error('Record a note to proceed with the listed gaps.');
  statusChange(db,r,n,'accepted',note);
  n.acceptance={note,at:now(),by:r.sentBy||'Owner',gaps};
  event(db,r,n,'ACCEPTED',note,'',{gaps});
  if(n.parent) {
    const p=r.nodes.find(x=>x.id===n.parent);
    if(children(r,p.id).every(c=>c.status==='accepted')) {
      statusChange(db,r,p,p.messages.length?'submitted':p.sentAt?'sent':'ready','Parent re-review required');
      event(db,r,p,'PARENT_RECHECK_REQUIRED','Children resolved; parent still needs review.');
    }
  }
}
export function correction(db,r,n,label,instruction) {
  editable(r,n);
  if(!instruction.trim()) throw Error('Describe the correction.');
  const child=newStep(db,r,label,instruction,'course_correction',n.id);
  statusChange(db,r,n,'revision',instruction);event(db,r,n,'NEEDS_CORRECTION',instruction,'',{child:child.id});return child;
}
export function removeStep(db,r,n) {
  editable(r,n);
  if(children(r,n.id).length) throw Error('Remove or resolve child entries first.');
  if(n.sentAt||n.messages.length) throw Error('Delivered or answered steps are retained. Use a correction.');
  n.deleted=true;event(db,r,n,'STEP_REMOVED','Removed from ladder; history retained.');
  if(n.parent) {
    const p=r.nodes.find(x=>x.id===n.parent);
    if(children(r,p.id).every(c=>c.status==='accepted'))statusChange(db,r,p,p.messages.length?'submitted':p.sentAt?'sent':'ready','Child removed');
  }
}
export function sessionChanged(db,r,newId,reason) {
  editable(r);
  if(!/^[a-f0-9]{8}$/i.test(newId)||!reason?.trim())throw Error('New session ID (eight hex characters) and reason required.');
  const old=r.chatId8||'';if(old.toLowerCase()===newId.toLowerCase())throw Error('New session must differ from old.');
  r.chatId8=newId.toLowerCase();
  event(db,r,null,'AGENT_SESSION_CHANGED',reason,'',{from:old,to:r.chatId8});
}
export function verifyReply(db,r,n,index,{checkedBy,recomputed,result,note=''}) {
  editable(r,n);
  const message=n.messages[index];
  if(!message||!checkedBy?.trim()||!recomputed?.trim()||!['MATCH','MISMATCH'].includes(result))
    throw Error('Verified by, recomputed check and MATCH/MISMATCH are required.');
  message.verification={checkedBy:checkedBy.trim(),recomputed:recomputed.trim(),result,note,at:now()};
  event(db,r,n,'REPLY_VERIFIED',note,'',{index,verification:message.verification});
}
export function revertStatus(db,r,n,reason) {
  editable(r,n);
  if(!reason?.trim())throw Error('A reason is required to revert status.');
  const last=db.events.filter(e=>e.run===r.id&&e.step===n.id&&
    ['STATUS_CHANGED','STATUS_REVERTED'].includes(e.state)).at(-1);
  if(!last||last.state!=='STATUS_CHANGED'||last.data.to!==n.status)
    throw Error('No unreverted last status transition.');
  const from=last.data.from;
  if(from==='ready'&&(n.sentAt||n.messages.length)||from==='sent'&&!n.sentAt||
    from==='submitted'&&!n.messages.length)
    throw Error('Reverting would contradict delivery or reply evidence.');
  const previous=n.status;n.status=from;
  event(db,r,n,'STATUS_REVERTED',reason,'',{from:previous,to:from,source:last.id},r.sentBy||'Owner');
}
export function waitingOn(r,at=Date.now()) {
  return r.nodes.filter(n=>!n.deleted&&n.sentAt&&n.status==='sent'&&
    !n.messages.some(m=>m.by==='Agent'&&Date.parse(m.at)>=Date.parse(n.sentAt)))
    .map(n=>({id:n.id,label:n.label,elapsedMinutes:Math.max(0,Math.floor((at-Date.parse(n.sentAt))/60000)),
      quiet:at-Date.parse(n.sentAt)>30*60000}));
}
export async function runSummary(db,r,at=Date.now()) {
  const steps=[];
  for(const n of r.nodes) {
    const replyDigests=[];
    for(const message of n.messages)replyDigests.push(await fingerprintText(message.text));
    steps.push({id:n.id,label:n.label,status:n.status,sentAt:n.sentAt,
      packetSha256:n.sentPacketSha256|| (n.sentText?await fingerprintText(n.sentText):null),
      replySha256s:replyDigests,replySources:n.messages.map(m=>m.source||'chat_words'),
      lastStatusEvent:db.events.filter(e=>e.run===r.id&&e.step===n.id&&
        ['STATUS_CHANGED','STATUS_REVERTED'].includes(e.state)).at(-1)||null});
  }
  return {format:'nextnudge-run-summary-v1',runId:r.id,projectId:r.projectId,
    generatedAt:new Date(at).toISOString(),steps,waitingOn:waitingOn(r,at)};
}
export function lifecycle(db,r,action) {
  if(!['pause','archive','delete'].includes(action)) throw Error('Unknown action.');
  const key={pause:'paused',archive:'archived',delete:'deleted'}[action];r[key]=!r[key];
  event(db,r,null,action.toUpperCase(),`${key}: ${r[key]}`);
}
export function fixture(db,r,key,values,rowId,approvalNote) {
  editable(r);const change=fixtureChange(db,r,key,values,rowId,approvalNote);
  event(db,r,null,'FIXTURE_RECORDED',key,values.url,change);
}
export function removeFixture(db,r,key,rowId) {
  editable(r);const row=r.fixtures[key].find(x=>x.id===rowId);
  if(!row) throw Error('Item not found.');
  row.deleted=true;event(db,r,null,'FIXTURE_REMOVED',key,'',structuredClone(row));
}
export function pull(db,r,key,sourceId) {
  editable(r);const rows=pullFixtures(db,r,key,sourceId);
  event(db,r,null,'FIXTURES_PULLED',key,'',{sourceId,rows});return rows.length;
}
