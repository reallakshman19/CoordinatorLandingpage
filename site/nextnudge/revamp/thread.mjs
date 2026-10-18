// Canonical Markdown thread codec. Sent packets are length-framed to preserve exact bytes.
export const THREAD_ID=/^NN-\d{8}-\d{6}-[a-f0-9]{4}$/;
const MODES=new Set(['ground','task','correction','evidence','direction','close','amendment']);
const CHAT=/(?:https?:\/\/[^\s<>"')\]]*(?:chatgpt\.com\/c\/|chat\.openai\.com|claude\.ai\/chat|gemini\.google\.com\/app|antigravity|poe\.com\/chat|\/conversation\/|\/chats?\/))/i;
const clean=s=>typeof s==='string'&&s.length<90000;
const line=s=>s.replace(/[\r\n]+/g,' ').trim();
export function assertPublic(value) {
  const scan=typeof value==='string'?value:JSON.stringify(value);
  if(CHAT.test(scan))throw Error('Private chat URL found. Keep conversation links on this device.');
}
export function validate(t) {
  if(!t||t.version!==3||!THREAD_ID.test(t.id)||!clean(t.title)||!t.title.trim()||
     !clean(t.agent)||!clean(t.goal)||!clean(t.inScope)||!clean(t.outScope)||
     !clean(t.hold)||!Array.isArray(t.doneWhen)||t.doneWhen.length>5||
     t.doneWhen.some(x=>!clean(x)||!x.trim())||!Array.isArray(t.moves)||t.moves.length>200)
    throw Error('Invalid thread intent or limits');
  const ids=new Set();
  for(const m of t.moves) {
    if(!THREAD_ID.test(m.id)||ids.has(m.id)||!MODES.has(m.kind)||
       !['draft','sent'].includes(m.delivery)||!clean(m.packet)||!clean(m.returnLine)||
       !clean(m.digest)||!clean(m.evidence)||!clean(m.gap)||!clean(m.decision)||
       !clean(m.archive)||!clean(m.note))throw Error('Invalid move');
    ids.add(m.id);
    if(m.delivery==='sent'&&!m.packet&&!m.archive)throw Error('Sent move requires exact packet or archive reference');
    if(m.archive&&!m.archive.startsWith('site/nextnudge-data/workbench.json#'))throw Error('Invalid archive reference');
  }
  assertPublic(t);
  return t;
}
export function freshId(date=new Date(),suffix) {
  const stamp=date.toISOString().replace(/[-:]/g,'');
  const hex=suffix??Array.from(crypto.getRandomValues(new Uint8Array(2))).map(x=>x.toString(16).padStart(2,'0')).join('');
  return 'NN-'+stamp.slice(0,8)+'-'+stamp.slice(9,15)+'-'+hex;
}
export function newThread({id=freshId(),title,agent='',goal='',inScope='',outScope='',hold='',doneWhen=[]}) {
  return validate({version:3,id,title,agent,goal,inScope,outScope,hold,doneWhen,moves:[]});
}
const mark=(kind,v)=>'<!-- nn3:'+kind+'\n'+JSON.stringify(v)+'\n-->';
export function serialize(t) {
  validate(t);
  const {moves,...header}=t;
  const result=['# '+line(t.title),'',mark('header',header),'',
    '## Owner intent','',t.goal||'UNKNOWN','',
    'Done-when: '+(t.doneWhen.length?t.doneWhen.map((x,i)=>'('+ (i+1)+') '+x).join(' · '):'UNKNOWN'),'',
    'In scope: '+(t.inScope||'UNKNOWN'),'Out of scope: '+(t.outScope||'UNKNOWN'),
    'Agent: '+(t.agent||'UNKNOWN'),'Owner constraint: '+(t.hold||'None'),'',
    '## Moves'];
  for(const m of moves) {
    const {packet,...meta}=m;
    result.push('', '### '+m.kind.toUpperCase()+' · '+m.id,'',mark('move',{...meta,packetChars:packet.length}),
      '', 'Return: '+(m.returnLine||'UNKNOWN'),
      'Evidence: '+(m.evidence||m.archive||'UNKNOWN'),
      'Open gap: '+(m.gap||'None'),
      'Decision: '+(m.decision||'UNKNOWN'));
    if(packet)result.push('','#### Exact '+(m.delivery==='sent'?'sent':'draft')+' packet','', '~~~~~~text',packet,'~~~~~~');
  }
  return result.join('\n')+'\n';
}
function metadata(text,kind) {
  const pattern=new RegExp('<!-- nn3:'+kind+'\\n([^\\n]+)\\n-->','g');
  return [...text.matchAll(pattern)].map(match=>({at:match.index,end:match.index+match[0].length,
    value:JSON.parse(match[1])}));
}
export function parse(source) {
  if(typeof source!=='string'||source.length>2_000_000)throw Error('Invalid Markdown size');
  const heads=metadata(source,'header');
  if(heads.length!==1)throw Error('Thread header missing or duplicated');
  const h=heads[0].value;
  const parts=metadata(source,'move'),moves=[];
  for(let i=0;i<parts.length;i++){
    const a=parts[i],end=parts[i+1]?.at??source.length;
    if(a.at<heads[0].end)throw Error('Move preceding header');
    const v=a.value,n=v.packetChars;
    if(!Number.isSafeInteger(n)||n<0||n>90000)throw Error('Invalid packet length');
    let packet='';
    if(n){
      const start=source.indexOf('~~~~~~text\n',a.end);
      if(start<0||start>end)throw Error('Missing packet fence');
      const pos=start+'~~~~~~text\n'.length;
      packet=source.slice(pos,pos+n);
      if(source.slice(pos+n,pos+n+7)!=='\n~~~~~~')throw Error('Packet length mismatch');
    }
    const {packetChars,...meta}=v;
    moves.push({...meta,packet});
  }
  return validate({...h,moves});
}
export function archiveRun(run) {
  const t=newThread({id:run.id,title:run.title,agent:'Google Antigravity',
    goal:run.aim,inScope:'Validation only; findings, no fixes',
    outScope:'Product edits and unapproved next tasks',
    hold:run.id==='NN-20261018-171656-66d2'?'Owner HOLD':''});
  t.moves=run.nodes.filter(n=>n.sentText||n.messages?.length).map(n=>{
    const r=n.messages?.find(x=>x.by==='Agent');
    const first=(r?.text||'').split(/\r?\n/).find(x=>/\bACK\b|\bSAVED\b|rows=/.test(x))||'';
    return {id:n.id,kind:n.type==='course_correction'?'correction':n.type==='new_requirement'?'ground':'task',
      delivery:'sent',packet:'',returnLine:line(first).slice(0,300),digest:line((r?.text||'').slice(0,300)),
      evidence:(r?.proof||'').startsWith('https://github.com/')?r.proof:'',
      gap:'UNKNOWN — historical status is not evidence of Owner acceptance',
      decision:'UNKNOWN',archive:'site/nextnudge-data/workbench.json#'+n.id,note:n.label};
  });
  return validate(t);
}
export function currentState(t) {
  if(t.hold)return 'Your move';
  const last=t.moves.at(-1);
  if(last?.kind==='close'&&last.delivery==='sent'&&last.returnLine)return 'Done';
  return last?.delivery==='sent'&&!last.returnLine?'Waiting on agent':'Your move';
}
export function reconcile({checks,reply,decision,gap='',nudgeId,goal,criteria=[],agent='',method=''}) {
  if(!['continue','correct','request evidence','change direction','close'].includes(decision))throw Error('Choose a decision');
  if(!Array.isArray(checks)||checks.some(x=>!['met','not met','unknown'].includes(x)))throw Error('Invalid checks');
  const missing=criteria.filter((x,i)=>checks[i]!=='met');
  const negatives=criteria.filter((x,i)=>checks[i]==='not met');
  const unknown=criteria.filter((x,i)=>checks[i]==='unknown');
  if(decision==='close'&&(missing.length||!criteria.length))throw Error('Owner outcome cannot close with missing or UNKNOWN checks');
  if(decision==='correct'&&!negatives.length&&!gap)throw Error('Name the observed gap for correction');
  if(decision==='request evidence'&&!unknown.length&&!gap)throw Error('Name missing evidence');
  let kind={continue:'task',correct:'correction','request evidence':'evidence','change direction':'direction',close:'close'}[decision];
  const explanation=decision==='correct'?'Correct these observed gaps: '+[...negatives,gap].filter(Boolean).join('; '):
    decision==='request evidence'?'Provide evidence for these UNKNOWNs: '+[...unknown,gap].filter(Boolean).join('; '):
    decision==='close'?'Provide the final artifact or issue pointer; do not infer Owner approval from task COMPLETE.':
    decision==='change direction'?'Propose revised direction; Owner retains approval. '+gap:
    'Continue one bounded task, preserving the Owner outcome. '+gap;
  const packet=['[Owner · NextNudge '+nudgeId+']','Intent: '+goal,
    'Agent: '+agent,'Move: '+decision,'Purpose: '+goal,
    'One bounded task: '+explanation,'Authoritative inputs: '+(reply||'UNKNOWN'),
    'Boundaries: preserve Owner scope and HOLD; no unassigned edits.',
    'Success criteria: '+(criteria.length?criteria.join(' | '):'UNKNOWN — ask Owner'),
    'Uncertainty handling: UNKNOWN must be stated, not assumed.',
    'Evidence and continuation: return actual result, source and next feasible action.',
    method?'GUIDED method: '+method:'',
    'COMPLETE covers this bounded task only, not the Owner outcome.',
    'Start your reply with ACK '+nudgeId+'.'].filter(Boolean).join('\n');
  assertPublic(packet);
  return {kind,packet,gap:explanation};
}
