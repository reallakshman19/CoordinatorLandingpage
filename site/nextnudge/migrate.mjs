import {UUID,id,now,safeURL} from './identity.mjs';
import {emptyFixtures} from './fixtures.mjs';
import {event,newProject} from './model.mjs';
import {validate} from './schema.mjs';
/** Explicit conversion of earlier prototype exports; no delivery is inferred. */
export function migrate(value,profiles) {
  if(value.formatVersion===2)return validate(value);
  if(value.schemaVersion!==1||!Array.isArray(value.runs)||!value.runs.length) {
    throw Error('Use a version 2 snapshot or a version 1 prototype export.');
  }
  const db={formatVersion:2,revision:0,profiles:structuredClone(profiles),projects:[],runs:[],events:[]};
  const p=newProject(db,'Imported prototype runs');
  for(const old of value.runs) {
    if(!UUID.test(old.id)||!Array.isArray(old.nodes)||old.nodes.length>500)throw Error('Invalid legacy run ID or nodes.');
    const mapping=new Map();
    for(const n of old.nodes) {
      if(!UUID.test(n.id)||mapping.has(n.id))throw Error('Invalid legacy step ID.');
      mapping.set(n.id,id('NN',[db,[...mapping.values()]]));
    }
    const r={id:id('NN',[db,[...mapping.values()]]),projectId:p.id,title:old.title,
      aim:old.aim,createdAt:now(),archived:false,deleted:false,paused:!!old.paused,
      chatId8:'',profiles:(old.types||[]).filter(p=>Object.hasOwn(profiles.profiles,p)),
      fixtures:emptyFixtures(),drafts:{},nodes:[]};
    for(const n of old.nodes) {
      if(n.parent&&!mapping.has(n.parent))throw Error('Missing legacy parent.');
      const messages=(n.messages||[]).map(m=>{
        if(!['agent','instructor'].includes(m.role)||typeof m.text!=='string'||
          !safeURL(m.link||'')||!Number.isFinite(Date.parse(m.at)))throw Error('Invalid legacy message.');
        return {by:m.role==='agent'?'Agent':'Owner',text:m.text,proof:m.link||'',
          at:new Date(m.at).toISOString(),repliedAt:null,relayed:m.role==='agent',recordedBy:'Owner',chatId8:null,ack:null};
      });
      r.nodes.push({id:mapping.get(n.id),label:n.title,instruction:n.instruction,
        type:n.parent?'course_correction':n.index===0?'new_requirement':n.index===1?'ground':'next_step',
        parent:n.parent?mapping.get(n.parent):null,status:{locked:'ready',available:'ready',submitted:'submitted',revision:'revision',accepted:'accepted'}[n.status],
        messages,checks:{},sentAt:null,copied:null,deleted:false});
      const draft=old.drafts?.[n.id+'instructor']||old.drafts?.[n.id+'agent'];
      if(draft)r.drafts[mapping.get(n.id)]={text:draft.text||'',proof:draft.link||''};
    }
    r.selected=mapping.get(old.selected)||r.nodes[0]?.id;db.runs.push(r);
    event(db,r,null,'LEGACY_IMPORTED','Historical statuses retained as imported claims; actual reply times and send records are UNKNOWN. Checklist dispositions require fresh review.','',
      {oldRun:old.id,nodeMap:Object.fromEntries(mapping),historicalLog:old.log||[]});
  }
  return validate(db);
}
