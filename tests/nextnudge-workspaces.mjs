import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {newThread,activeIntent,freshId,parse,serialize,currentState} from '../site/nextnudge/revamp/thread.mjs';
import {packet} from '../site/nextnudge/revamp/screens.mjs';
import {workspaceMove,savedWorkspace,defaults,buildWorkspacePacket,workspaceBasis} from '../site/nextnudge/revamp/workspace.mjs';
import {workspaceAction,workspaceMarkup,installWorkspaces,checkWorkspacePacket} from '../site/nextnudge/revamp/workspace-ui.mjs';
import {readWorkspaceDraft,writeWorkspaceDraft} from '../site/nextnudge/revamp/workspace-drafts.mjs';
import {persistMove} from '../site/nextnudge/revamp/save.mjs';
const make=()=>newThread({id:'NN-20261020-000000-ab12',title:'Distinct workspaces',goal:'Deliver useful steering',doneWhen:['Actual result verified']});
const sent={id:'TASK-1',kind:'task',delivery:'sent',packet:'Existing task',returnLine:'',digest:'',evidence:'',gap:'',decision:'',archive:'',note:''};
const reply={...sent,id:'REPLY-1',kind:'reply',delivery:'draft',packet:'',answers:'TASK-1',returnLine:'ACK TASK-1',replyText:'ACK TASK-1\nActual agent result',evidence:'https://github.com/example/repo/issues/1#issuecomment-1'};
function harness(thread=make()){
  const previous=Object.fromEntries(['document','localStorage','FormData'].map(k=>[k,globalThis[k]]));
  const storage=new Map(),handlers={};
  globalThis.localStorage={getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)};
  const state={threads:{[thread.id]:thread},active:thread.id,view:'thread',draft:null,editor:null};
  const form={id:'workspace-form'};let html='',message='';
  globalThis.FormData=class{constructor(){return new Map(Object.entries(form.values||state.workspaceValues||{}));}};
  const $=q=>q==='#workspace-form'?form:q==='#workspace-title'?{focus(){}}:null;
  globalThis.document={querySelector:$,addEventListener:(key,fn)=>{handlers[key]=fn;}};
  const ctx={state,t:()=>state.threads[state.active],notice:s=>{message=s;},
    render:()=>{if(state.view==='workspace')html=workspaceMarkup(ctx);},
    append:m=>{state.threads[state.active]=persistMove(ctx.t(),m);state.draft=null;ctx.render();}};
  const app=fs.readFileSync(new URL('../site/nextnudge/revamp/app.mjs',import.meta.url),'utf8');
  const action=app.slice(app.indexOf('async function onAction('),app.indexOf("\ndocument.addEventListener('click'"));
  const run=new Function('workspaceAction','featureAction','state','t','append','render','notice','intent','$','v','freshId','packet',
    'return ('+action+');')(workspaceAction,async()=>false,state,ctx.t,ctx.append,ctx.render,ctx.notice,()=>activeIntent(ctx.t()),$,()=>'',freshId,
      (id,kind,body)=>packet(id,kind,body,activeIntent(ctx.t())));
  installWorkspaces(ctx);
  return {ctx,state,storage,handlers,form,run,html:()=>html,message:()=>message,
    input:()=>handlers.input({target:{id:'field',closest:()=>form}}),
    save:()=>handlers.submit({target:form,preventDefault(){}}),restore:()=>Object.assign(globalThis,previous)};
}
test('Workspace UI: Ground has editable source fields, context fields, its own save and a tab link',async()=>{
  const h=harness();try{
    await h.run('workspace-ground');
    assert.equal(h.state.view,'workspace');assert.equal(h.state.workspaceMode,'ground');
    for(const name of ['repository','issue','pullRequest','roadmap','brief'])assert.ok(h.html().includes('name="'+name+'"'));
    assert.match(h.html(),/Save Ground context/);assert.match(h.html(),/workspace=ground/);
  }finally{h.restore();}
});
test('Workspace UI: Task is a deliverable form with a selectable Ground version, not an automatic generic packet',async()=>{
  const h=harness();try{
    await h.run('workspace-task');
    assert.match(h.html(),/name="deliverable"/);assert.match(h.html(),/name="success"/);
    assert.match(h.html(),/name="groundId"/);assert.match(h.html(),/Save Task/);
    assert.equal(h.state.draft,null);
  }finally{h.restore();}
});
test('Workspace UI: Correction opens linked-error and redo fields without inventing an earlier exchange',async()=>{
  const h=harness();try{
    await h.run('compose-correction');
    assert.equal(h.state.draft,null,'opening Correction must not create a context-free instruction');
    assert.match(h.html(),/No recorded instruction or response/);assert.match(h.html(),/name="expected"/);
    assert.match(h.html(),/name="redo"/);assert.match(h.html(),/Save Correction/);
  }finally{h.restore();}
});
test('Workspace UI: Reconcile selects an actual response, preserves check verdicts and saves independently',async()=>{
  const t=make();t.moves.push(sent,reply);const h=harness(t);try{
    await h.run('workspace-reconcile');
    assert.match(h.html(),/name="target"/);assert.match(h.html(),/name="check0"/);assert.match(h.html(),/Save Review/);
    Object.assign(h.state.workspaceValues,{target:'REPLY-1',check0:'met',nextTask:'Return verified artifact'});h.input();h.save();
    assert.equal(savedWorkspace(h.ctx.t(),'reconcile').values.check0,'met');
    assert.equal(currentState(h.ctx.t()),'Your move');
  }finally{h.restore();}
});
test('Workspace UI: each tab restores its own fields after navigation and reload, without typing history',async()=>{
  const h=harness();try{
    await h.run('workspace-ground');h.state.workspaceValues.brief='Saved device context';h.input();
    await h.run('workspace-task');h.state.workspaceValues.task='Separate task draft';h.input();
    await h.run('workspace-ground');assert.equal(h.state.workspaceValues.brief,'Saved device context');
    assert.equal(h.ctx.t().moves.length,0);
    h.state.view='thread';await h.run('workspace-task');assert.equal(h.state.workspaceValues.task,'Separate task draft');
    h.save();h.save();assert.equal(h.ctx.t().moves.length,1,'unchanged save creates no extra record');
  }finally{h.restore();}
});
test('Workspace model: immutable Ground versions link into Task packets and survive Markdown round-trip',()=>{
  const t=make();t.moves.push(workspaceMove(t,'ground',{brief:'Original context',issue:'https://github.com/example/repo/issues/7'},'GROUND-1'));
  t.moves.push(workspaceMove(t,'ground',{brief:'New context'},'GROUND-2'));
  const v={groundId:'GROUND-1',task:'Repair parser',deliverable:'A reviewable PR',success:'Known input converts'};
  t.moves.push(workspaceMove(t,'task',v,'TASK-CONTEXT'));
  const text=buildWorkspacePacket(parse(serialize(t)),'task',v,'OUT-1').packet;
  assert.match(text,/GROUND-1/);assert.match(text,/Original context/);assert.doesNotMatch(text,/New context/);
  assert.match(text,/issues\/7/);assert.match(text,/A reviewable PR/);assert.match(text,/Known input converts/);
});
test('Workspace UI: saving fields preserves an edited packet and does not make unchanged context stale',async()=>{
  const h=harness();try{
    await h.run('workspace-ground');h.state.workspaceValues.brief='Context with a saved packet';h.input();
    await h.run('workspace-build');const id=h.state.draft.id;
    h.state.draft.packet+='\nOwner manual refinement';h.input();h.save();
    assert.equal(h.state.draft.id,id);assert.match(h.state.draft.packet,/Owner manual refinement/);
    assert.doesNotThrow(()=>checkWorkspacePacket(h.ctx));
    assert.equal(h.ctx.t().moves.length,1);h.save();assert.equal(h.ctx.t().moves.length,1);
    await h.run('workspace-task');await h.run('workspace-ground');
    assert.equal(h.state.draft.id,id);assert.match(h.state.draft.packet,/Owner manual refinement/);
  }finally{h.restore();}
});
test('Workspace UI: a failed snapshot save retains fields and the last committed thread for reload',async()=>{
  const h=harness();try{
    await h.run('workspace-ground');h.state.workspaceValues.brief='Keep recoverable context';h.input();
    const write=globalThis.localStorage.setItem;
    globalThis.localStorage.setItem=(key,value)=>{if(key==='nextnudge.threads.v3')throw Error('Snapshot quota');write(key,value);};
    h.save();
    assert.equal(h.ctx.t().moves.length,0);
    assert.equal(readWorkspaceDraft(h.ctx.t().id,'ground').values.brief,'Keep recoverable context');
    assert.match(h.message(),/not saved: Snapshot quota/);
    globalThis.localStorage.setItem=write;h.save();h.save();assert.equal(h.ctx.t().moves.length,1);
  }finally{h.restore();}
});
test('Workspace model: amended Owner context stays bounded and unrelated history does not invalidate a packet',()=>{
  const t=make();
  t.moves.push({...sent,id:'OWNER-1',kind:'amendment',delivery:'draft',packet:'',note:'OWNER_INTENT_CHANGE:'+JSON.stringify({goal:'Updated goal',doneWhen:['Verify'],inScope:'UI',outScope:'Other projects',hold:''})});
  const values={brief:'Ground the actual source'},basis=workspaceBasis(t,'ground',values);
  t.moves.push(workspaceMove(t,'ground',values,'GROUND-1'));
  assert.equal(workspaceBasis(t,'ground',values),basis);
  assert.equal(savedWorkspace(t,'ground').owner.moves,undefined);
  assert.equal(workspaceMove(t,'ground',values),null);
});
test('Workspace UI: changing the reviewed response resets prior verdicts through the actual select event sequence',async()=>{
  const t=make();t.moves.push(sent,reply,{...reply,id:'REPLY-2'});const h=harness(t);try{
    await h.run('workspace-reconcile');
    Object.assign(h.state.workspaceValues,{target:'REPLY-1',check0:'met'});
    h.form.values={...h.state.workspaceValues,target:'REPLY-2'};
    const target={id:'',name:'target',tagName:'SELECT',closest:()=>h.form};
    h.handlers.input({target});h.handlers.change({target});
    assert.equal(h.state.workspaceValues.target,'REPLY-2');
    assert.equal(h.state.workspaceValues.check0,'unknown');
    assert.equal(readWorkspaceDraft(t.id,'reconcile').values.check0,'unknown');
  }finally{h.restore();}
});
test('Workspace UI: save links, packet edits and independent thread drafts survive navigation; stale packets are blocked',async()=>{
  const h=harness();try{
    await h.run('workspace-ground');Object.assign(h.state.workspaceValues,{brief:'Project source',issue:'https://github.com/example/repo/issues/8'});
    h.input();h.save();assert.match(h.html(),/href="https:\/\/github.com\/example\/repo\/issues\/8"/);
    await h.run('workspace-build');const id=h.state.draft.id;
    h.state.draft.packet+='\nManual clarification';h.input();
    await h.run('workspace-task');await h.run('workspace-ground');
    assert.equal(h.state.draft.id,id);assert.match(h.state.draft.packet,/Manual clarification/);
    h.state.workspaceValues.brief='Changed source';h.input();
    await assert.rejects(()=>h.run('copy-packet'),/updated packet/);
    const other=make();other.id='NN-20261020-000000-ab13';
    assert.equal(readWorkspaceDraft(other.id,'ground'),null);
  }finally{h.restore();}
});
test('Workspace model: correction needs a real target and includes its ID and bounded redo',()=>{
  const t=make(),v={target:'REPLY-1',claim:'Wrong source used',expected:'Read original input',redo:'Re-run only this comparison'};
  assert.throws(()=>buildWorkspacePacket(t,'correction',v),/recorded/);
  t.moves.push(sent,reply);const d=buildWorkspacePacket(t,'correction',v,'OUT-2');
  assert.match(d.packet,/REPLY-1/);assert.match(d.packet,/Wrong source used/);assert.match(d.packet,/Re-run only this comparison/);
});
test('Workspace model: Reconcile respects selected response, unknown checks, current criteria and close proof',()=>{
  const t=make();t.moves.push(sent,reply);const v={...defaults(t,'reconcile'),target:'REPLY-1',decision:'close',nextTask:'Final artifact'};
  assert.throws(()=>buildWorkspacePacket(t,'reconcile',v),/cannot close/);
  v.check0='met';const d=buildWorkspacePacket(t,'reconcile',v,'CLOSE-1');
  assert.equal(d.kind,'close');assert.deepEqual(d.closure.checks,['met']);assert.match(d.packet,/REPLY-1/);
  v.basis='[]';assert.throws(()=>buildWorkspacePacket(t,'reconcile',v),/checks changed/);
});
test('Workspace model: private sources, stale Owner context and HOLD cannot become deliverable packets',()=>{
  const t=make();assert.throws(()=>workspaceMove(t,'ground',{brief:'https://chatgpt.com/c/private'}),/Private chat/);
  t.moves.push(workspaceMove(t,'ground',{brief:'Source context'},'GROUND-1'));
  t.goal='Amended goal';assert.throws(()=>buildWorkspacePacket(t,'task',{groundId:'GROUND-1',task:'A',deliverable:'B',success:'C'}),/intent changed/);
  t.hold='Owner HOLD';for(const mode of ['ground','task','correction','reconcile'])assert.throws(()=>buildWorkspacePacket(t,mode,{}),/HOLD/);
});
test('Workspace drafts: failed storage and changed fields cannot silently replace or deliver an old packet',()=>{
  const t=make(),storage=new Map(),s={getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)};
  writeWorkspaceDraft(t.id,'ground',{values:{brief:'Keep me'},draft:null},s);
  const bad={getItem:s.getItem,setItem(){throw Error('Quota');}};
  assert.throws(()=>writeWorkspaceDraft(t.id,'ground',{values:{brief:'Other'}},bad),/Quota/);
  assert.equal(readWorkspaceDraft(t.id,'ground',s).values.brief,'Keep me');
  const values={brief:'Original'};const draft={workspaceMode:'ground',workspaceBasis:workspaceBasis(t,'ground',values)};
  assert.throws(()=>checkWorkspacePacket({t:()=>t,state:{view:'workspace',workspaceMode:'ground',workspaceValues:{brief:'Edited'},draft}}),/updated packet/);
});
