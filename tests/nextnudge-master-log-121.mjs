import test from 'node:test';
import assert from 'node:assert/strict';
import {HEADINGS,PROJECT_HEADINGS,PROJECT_PHASES,RETIRED_MIDCYCLE,projectHeadingNumber} from '../site/nextnudge/fixtures.mjs';
import {newProject,addThread,updateFixtures,validateProject} from '../site/nextnudge/revamp/project-model.mjs';
import {newThread,serialize,parse} from '../site/nextnudge/revamp/thread.mjs';
import {groundingPanel,projectGroundingText} from '../site/nextnudge/revamp/grounding.mjs';
import {masterLogEntries,masterLogMarkup} from '../site/nextnudge/revamp/master-log.mjs';
import {projectMarkup} from '../site/nextnudge/revamp/screens.mjs';
import {moveMarkup} from '../site/nextnudge/revamp/move-view.mjs';
import {createProjectUI} from '../site/nextnudge/revamp/project-ui.mjs';

const id=i=>'NN-20261020-120000-'+i;
const thread=(n,agent)=>newThread({id:id(n),title:'Thread '+agent,agent,goal:'Keep Owner intent'});
const project=(n,name)=>newProject(name,'NP-20261020-120000-'+n);
const move=(n,kind='task',extra={})=>({id:n,kind,delivery:'sent',
  packet:'Exact immutable task for '+n,returnLine:'',digest:'',evidence:'',gap:'',decision:'',
  archive:'',note:'',...extra});

test('NN121 active grounding has no Midcycle 1/2, renames Exit and preserves v2 headings',()=>{
  assert.equal(HEADINGS.length,25,'historic v2 data model must retain all 25');
  assert.equal(PROJECT_HEADINGS.length,17);
  assert.equal(RETIRED_MIDCYCLE.length,8);
  assert.deepEqual(Object.keys(PROJECT_PHASES),['onboarding','exit','improvements']);
  assert.equal(PROJECT_PHASES.exit,'Master Log');
  assert.deepEqual(['8','8a','8b','8c','9','10'].map(projectHeadingNumber),['6','6a','6b','6c','7','8']);
  const html=groundingPanel(null,{},false,project('a001','Alpha'));
  assert.equal((html.match(/<textarea /g)||[]).length,17);
  assert.match(html,/Master Log/);
  assert.match(html,/6\. Reconciliation against/);
  assert.doesNotMatch(html,/>Midcycle 1|>Midcycle 2|name="ground-6"|name="ground-7a"/);
  assert.match(html,/name="ground-8"/,'storage key remains unchanged for historical data');
});

test('NN121 archived 6/7 values survive active project edits, snapshots and owner packets',()=>{
  let p=project('a001','ALPHA');
  p=updateFixtures(p,{'6':'Earlier Midcycle 1','7b':'Earlier Midcycle 2',
    '8':'Old Exit reconciliation','1f':'Original Owner context'},'2026-10-20T12:00:00Z');
  const before=JSON.stringify(p.snapshots[0]);
  p=updateFixtures(p,{'8':'Old Exit reconciliation','1f':'Updated current Owner context'},
    '2026-10-20T13:00:00Z');
  assert.equal(validateProject(p),p);
  assert.equal(p.fixtures['6'],'Earlier Midcycle 1');
  assert.equal(p.fixtures['7b'],'Earlier Midcycle 2');
  assert.equal(JSON.stringify(p.snapshots[0]),before);
  assert.equal(p.snapshots.length,2);
  const html=groundingPanel(null,p.fixtures,false,p);
  assert.match(html,/Historical retired Midcycle context \(2\)/);
  assert.match(html,/Earlier Midcycle 1/);
  assert.match(html,/Old Exit reconciliation/);
  assert.doesNotMatch(projectGroundingText(p),/Earlier Midcycle 1|Earlier Midcycle 2/);
  assert.match(projectGroundingText(p),/6\. Reconciliation against/);
});

test('NN121 master log is project scoped and derives links from immutable agent moves',()=>{
  const g1=thread('a001','G1'),g2=thread('a002','G2'),b=thread('a003','B');
  g1.moves.push(move('NN-20261020-120100-aaaa','task', {packet:'Owner context\nOne bounded task:\nInspect sample pipes\nEvidence'}));
  g1.moves.push(move('NN-20261020-120200-bbbb','reply',{delivery:'draft',returnLine:'ACK some earlier task'}));
  g2.moves.push(move('NN-20261020-120300-cccc','correction',{gap:'Needs rework'}));
  b.moves.push(move('NN-20261020-120400-dddd','task',{returnLine:'BETA ONLY'}));
  let a=addThread(addThread(project('b001','ALPHA'),g1),g2);
  const beta=addThread(project('b002','BETA'),b);
  const stored={[g1.id]:g1,[g2.id]:g2,[b.id]:b};
  const feed=masterLogEntries(a,stored);
  assert.equal(feed.rows.length,3);
  assert.equal(feed.unavailable.length,0);
  assert.deepEqual(feed.rows.map(x=>x.agent),['G2','G1','G1']);
  const html=masterLogMarkup(a,stored);
  assert.match(html,/Open exact thread item/);
  assert.match(html,/Inspect sample pipes/,'Task preview must be usable without opening every link');
  assert.match(html,new RegExp('thread='+g1.id+'&move=NN-20261020-120100-aaaa'));
  assert.doesNotMatch(html,/BETA ONLY|Thread B/);
  assert.equal(masterLogEntries(beta,stored).rows.length,1);
  assert.match(masterLogMarkup(a,stored),/read-only/);
  const old=serialize(g1);
  assert.equal(serialize(parse(old)),old,'deriving a project log must never mutate source thread');
  assert.match(moveMarkup(g1,g1.moves[0],x=>x),/id="move-NN-20261020-120100-aaaa"/);
});

test('NN121 missing GitHub source and divergent remote record are not misreported as complete',()=>{
  const a=thread('a001','G1'),b=thread('a002','G2');
  const p=addThread(addThread(project('b001','ALPHA'),a),b);
  a.moves.push(move('NN-20261020-120200-abcd'));
  let feed=masterLogEntries(p,{[a.id]:a},{[b.id]:{error:'GitHub read failed 403'}});
  assert.equal(feed.rows.length,1);assert.equal(feed.unavailable.length,1);
  assert.match(masterLogMarkup(p,{[a.id]:a},{[b.id]:{error:'GitHub read failed 403'}}),/Incomplete source coverage/);
  assert.match(masterLogMarkup(p,{[a.id]:a}),/device \(remote unverified\)/);
  const newer={...a,moves:[...a.moves,move('NN-20261020-120300-abcd')]};
  feed=masterLogEntries(p,{[a.id]:a},{[a.id]:{thread:newer}});
  assert.equal(feed.rows.length,1,'stale local thread must not produce a deep link to an unseen remote-only move');
  assert.match(feed.rows[0].origin,/GitHub has newer moves/);
  assert.equal(masterLogEntries(p,{}, {[a.id]:{thread:newer}}).rows.length,2,'clean Oracle device reads all remote moves');
  const incompatible={...a,moves:[move('NN-20261020-120200-abcd','correction')]};
  feed=masterLogEntries(p,{[a.id]:a},{[a.id]:{thread:incompatible}});
  assert.match(feed.rows[0].origin,/GitHub conflict/);
});

test('NN121 source preview escapes markup; sealed notes are not exposed in summary',()=>{
  const a=thread('a001','G1');
  a.moves.push(move('NN-20261020-120500-ffff','task',{returnLine:'<img src=x onerror=alert(1)>'}));
  a.moves.push(move('NN-20261020-120600-aaaa','sealed',{delivery:'draft',
    packet:'',returnLine:'PRIVATE SECRET',note:''}));
  const p=addThread(project('b001','ALPHA'),a);
  const html=masterLogMarkup(p,{[a.id]:a});
  assert.match(html,/&lt;img/);assert.doesNotMatch(html,/<img src=x/);
  assert.doesNotMatch(html,/PRIVATE SECRET/);assert.match(html,/Private contents not shown/);
});

test('NN121 duplicate-agent error stays beside Create button and focuses accessible alert',()=>{
  const p=project('b001','ALPHA'),a=thread('a001','G1'),managed=addThread(p,a);
  const rendered=projectMarkup(managed,{[a.id]:a},{[p.id]:managed});
  assert.match(rendered,/id="new-thread-error" role="alert" aria-live="assertive"/);
  assert.match(rendered,/data-action="master-log"/);
  const orig=globalThis.document;let handler;
  globalThis.document={addEventListener:(name,fn)=>{if(name==='input')handler=fn;}};
  const state={activeProject:p.id,projects:{[p.id]:managed},threads:{[a.id]:a}};
  try{
    const ui=createProjectUI({state,put:()=>{},render:()=>{},notice:()=>{}});
    let focused=0,scrolled=0;const alert={textContent:'',focus:()=>focused++,scrollIntoView:()=>scrolled++};
    ui.createError({querySelector:()=>alert},Error('Agent already has a project thread; open that thread instead'));
    assert.match(alert.textContent,/Agent already/);
    assert.equal(focused,1);assert.equal(scrolled,1);
    handler({target:{closest:q=>q==='#new-thread'?{querySelector:()=>alert}:null}});
    assert.equal(alert.textContent,'','correction clears the inline error');
  }finally{globalThis.document=orig;}
});
