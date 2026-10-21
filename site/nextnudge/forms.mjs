import * as model from './model.mjs';
import {setPrivateChat} from './storage.mjs';
import {$} from './util.mjs';
export function submitForm(form,ctx) {
  const {s,run:r,node:n,save,render}=ctx,db=s.db;
  if(s.conflict)throw Error('Reload the page before editing.');
  const values=Object.fromEntries(new FormData(form));
  if(form.id==='create-form') {
    const mode=form.dataset.mode;
    if(mode==='project')s.projectId=model.newProject(db,values.name).id;
    if(mode==='run') {
      const run=model.newRun(db,s.projectId,values.name,values.detail);s.runId=run.id;s.tab='work';
    }
    if(mode==='step')r.selected=model.newStep(db,r,values.name,values.detail).id;
    $('#create-dialog').close();
  } else if(form.id==='reply-form') {
    model.reply(db,r,n,values);r.drafts[n.id]={};
  } else if(form.id==='session-change-form') {
    model.sessionChanged(db,r,values.newSessionId,values.reason);
  } else if(form.dataset.replyVerify) {
    model.verifyReply(db,r,n,Number(form.dataset.replyVerify),values);
  } else if(form.id==='run-settings') {
    model.editable(r);
    if(values.chatId8&&!/^[a-f0-9]{8}$/i.test(values.chatId8))throw Error('Chat ID must be eight hex characters.');
    setPrivateChat(r.id,values.privateChat);
    const sentBy=values.sentBy||'Owner';
    if(!['Owner','TeamCoordinator'].includes(sentBy))throw Error('Invalid sender.');
    const before={title:r.title,aim:r.aim,chatId8:r.chatId8,sentBy:r.sentBy||'Owner'};
    Object.assign(r,{title:values.title.trim(),aim:values.aim.trim(),chatId8:values.chatId8,sentBy});
    model.event(db,r,null,'RUN_SETTINGS_UPDATED','', '',{before,after:{title:r.title,aim:r.aim,chatId8:r.chatId8,sentBy:r.sentBy}});
  } else if(form.dataset.stepEdit) {
    model.editStep(db,r,r.nodes.find(x=>x.id===form.dataset.stepEdit),values);
  } else if(form.dataset.fixture) {
    model.fixture(db,r,form.dataset.fixture,values,form.dataset.row||null,values.approvalNote||'');
  }
  save();render();
}
export function changed(target,ctx) {
  const {s,run:r,node:n,save,render}=ctx;
  if(s.conflict)throw Error('Reload the page before editing.');
  if(target.id==='project-select'){s.projectId=target.value;s.runId=null;return render();}
  if(target.id==='run-select'){s.runId=target.value;return render();}
  if(target.id==='show-archived'){s.showArchived=target.checked;return render();}
  if(target.dataset.profile) {
    model.editable(r);const before=[...r.profiles],name=target.dataset.profile;
    r.profiles=target.checked?[...new Set([...r.profiles,name])]:r.profiles.filter(x=>x!==name);
    model.event(s.db,r,null,'PROFILES_SELECTED','', '',{before,after:r.profiles});
  }
  if(target.dataset.check) {
    model.editable(r,n);const key=target.dataset.check,before=n.checks[key]||'';
    n.checks[key]=target.value;model.event(s.db,r,n,'CHECKLIST_UPDATED',key,'',{before,after:target.value});
  }
  save();render();
}
