import * as model from './model.mjs';
import {migrate} from './migrate.mjs';
import {validate,validateProfiles} from './schema.mjs';
import {packet} from './model.mjs';
import {prepareSave,prepareIssueSave,readRepository,fingerprint,download} from './repository.mjs';
import {$,notice} from './util.mjs';
export async function action(name,target,ctx) {
  const {s,run:r,node:n,save,render}=ctx;
  const db=s.db;
  if(s.conflict&&!['export','tab','phase','select-step','github-reload'].includes(name)) {
    throw Error('Another tab changed this draft. Export your copy, then reload the page.');
  }
  if(name==='tab'){s.tab=target.dataset.id;return render();}
  if(name==='phase'){s.phase=target.dataset.id;return render();}
  if(name==='select-step'){r.selected=target.dataset.id;return render();}
  if(name==='export')return download(db);
  if(name==='restore')return $('#restore-file').click();
  if(name==='import-profiles')return $('#profile-file').click();
  if(name==='export-profiles')return download(db.profiles);
  async function manualEditor(prepared,reason='') {
    s.prepared=prepared.digest;save(false);
    $('#github-editor').hidden=false;
    try {
      await navigator.clipboard.writeText(prepared.text);
      notice(reason+'Snapshot copied. Open GitHub editor, replace JSON, commit, then verify.');
    } catch {
      const field=$('#github-manual-json');
      field.hidden=false;field.value=prepared.text;
      notice(reason+'Clipboard permission denied. Select and copy the JSON below manually, or use Export, then commit through GitHub editor.');
    }
  }
  if(name==='github-prepare')return manualEditor(await prepareSave(db,s.baseSha));
  if(name==='github-save') {
    // Reserve a tab during the original click: async fetch would lose popup permission.
    const popup=window.open('about:blank','_blank');
    try {
      const prepared=await prepareSave(db,s.baseSha);
      let result;
      try {result=await prepareIssueSave(db,prepared,s.baseSha);}
      catch(e) {
        if(!/manual GitHub editor|cannot gzip/.test(e.message))throw e;
        popup?.close();await manualEditor(prepared,e.message+'. ');return;
      }
      if(result.url.length>7500) {
        popup?.close();await manualEditor(prepared,'Save packet exceeds the 7,500-character URL limit. ');return;
      }
      s.prepared=prepared.digest;save(false);
      if(popup) {
        popup.opener=null;popup.location.replace(result.url);
        notice('Review and Submit the prefilled GitHub issue. Wait for SAVED receipt, then Verify GitHub save.');
      } else {
        const link=$('#github-save-link');link.href=result.url;link.hidden=false;
        notice('Popup blocked. Click the Save issue link, Submit on GitHub, then Verify GitHub save.');
      }
      return;
    } catch(e) {popup?.close();throw e;}
  }
  if(name==='github-verify') {
    if(!s.prepared)throw Error('Prepare a snapshot before verifying its save.');
    const remote=await readRepository(),hash=await fingerprint(remote.db);
    if(hash!==s.prepared)throw Error('GitHub does not contain the prepared snapshot yet. Nothing is marked saved.');
    s.baseSha=remote.sha;s.dirty=(await fingerprint(db))!==hash;s.prepared=null;save(false);
    render();notice(s.dirty?'Prepared snapshot verified; newer browser changes remain unsaved.':'GitHub snapshot verified.');return;
  }
  if(name==='github-reload') {
    if(s.dirty&&!confirm('Replace this browser draft with GitHub? Export it first if needed.'))return;
    const remote=await readRepository();s.db=remote.db;s.baseSha=remote.sha;s.dirty=false;
    s.prepared=null;s.conflict=false;save(false);render();return;
  }
  if(s.conflict)throw Error('Another tab changed this draft. Reload the page before editing.');
  if(name==='new-project'){openDialog('project');return;}
  if(name==='new-run'){openDialog('run');return;}
  if(name==='add-step'){model.editable(r);openDialog('step');return;}
  if(name==='copy-step') {
    await navigator.clipboard.writeText(packet(r,n));model.copied(db,r,n,packet(r,n));
    notice('Copied. Paste into the agent chat yourself, then Mark sent.');
  }
  if(name==='send-step')model.markSent(db,r,n);
  if(name==='accept-step')model.accept(db,r,n,r.drafts[n.id]?.text||'');
  if(name==='correction') {
    const text=r.drafts[n.id]?.text||'';
    const child=model.correction(db,r,n,'Correction · '+n.label,text);r.selected=child.id;
  }
  if(name==='pause'||name==='archive')model.lifecycle(db,r,name);
  if(name==='delete-run') {
    if(!confirm('Delete this run from the working list? Its history remains in the snapshot.'))return;
    model.lifecycle(db,r,'delete');s.runId=null;
  }
  if(name==='delete-step')model.removeStep(db,r,r.nodes.find(x=>x.id===target.dataset.id));
  if(name==='delete-fixture') {
    if(!confirm('Remove this item from the current heading? History is retained.'))return;
    model.removeFixture(db,r,target.dataset.key,target.dataset.id);
  }
  if(name==='pull-fixtures') {
    const key=target.dataset.key,source=$(`[data-source="${key}"]`).value;
    const count=model.pull(db,r,key,source);notice(`${count} item(s) copied with provenance. Review before relying on them.`);
  }
  save();render();
}
function openDialog(mode) {
  const form=$('#create-form');form.reset();form.dataset.mode=mode;
  $('#create-title').textContent={project:'Create project',run:'Create NextNudge',step:'Add nudge'}[mode];
  $('#create-detail').hidden=mode==='project';$('#create-dialog').showModal();
}
export async function importFile(file,kind,ctx) {
  if(!file)return;
  if(file.size>5e6)throw Error('Maximum file size is 5 MB.');
  const value=JSON.parse(await file.text()),{s,save,render}=ctx;
  if(s.conflict)throw Error('Reload the page before importing.');
  if(kind==='profiles') {
    validateProfiles(value);
    if(s.db.runs.some(r=>r.profiles.some(p=>!Object.hasOwn(value.profiles,p)))) {
      throw Error('Imported profiles omit a profile used by a run. Retain those names.');
    }
    const before=s.db.profiles;s.db.profiles=value;
    model.event(s.db,null,null,'PROFILES_IMPORTED','', '',{before,after:value});
  } else {
    const imported=migrate(value,s.db.profiles);
    if(!confirm('Replace local data with this backup? Export current work first. GitHub is unchanged.'))return;
    s.db=imported;s.runId=null;s.projectId=null;s.prepared=null;
    model.event(s.db,null,null,'BACKUP_RESTORED','Imported claims are not verified proof.');
  }
  save();render();
}
