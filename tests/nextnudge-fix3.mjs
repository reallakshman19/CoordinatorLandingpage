import test from 'node:test';
import assert from 'node:assert/strict';
import {gzipSync} from 'node:zlib';
import {newThread,validate,assertPublic} from '../site/nextnudge/revamp/thread.mjs';
import {applyIssue,unpack} from '../scripts/nextnudge_thread_apply.mjs';

const ID='NN-20261019-010101-ab12',M='NN-20261019-010102-cd34';
const example=()=>newThread({id:ID,title:'Owner decision',agent:'Validator',
  goal:'Evaluate evidence',inScope:'Read-only',outScope:'No repairs',
  doneWhen:['Evidence reviewed']});
const move=()=>({id:M,kind:'task',delivery:'sent',packet:'One bounded task',
  returnLine:'',digest:'',evidence:'',gap:'',decision:'',archive:'',note:''});
const fence=String.fromCharCode(96).repeat(3);
const encode=packet=>'Issue body\n'+fence+'nextnudge-thread-save\n'+
  gzipSync(JSON.stringify(packet)).toString('base64')+'\n'+fence;
const refused=[
  'chatgpt.com/c/x',
  'claude.ai/chat/x',
  'https%3A%2F%2Fchatgpt.com%2Fc%2Fx',
  'aistudio.google.com/prompts/example',
  '100% sure https%3A%2F%2Fchatgpt.com%2Fc%2Fx',
  'https%3A%2F%2Fchatgpt.com%2Fc%2Fx 100%',
  '50% confident https%253A%252F%252Fchatgpt.com%252Fc%252Fx',
  'https://chatgpt.com/g/g-p-123-name/c/68f0',
  'chatgpt.com/g/g-p-123-name/c/68f0',
  'https://chat.openai.com/g/g-p-123-name/c/68f0',
  'chat.openai.com/g/g-p-123-name/c/68f0',
  'https://chatgpt.com/share/id',
  'HTTPS://CHATGPT.COM/C/X',
  'https://chatg\u200Bpt.com/c/x',
  'https://chatgpt.com/\u200Bc/x',
  'https://claude.ai/chat/x',
  'https://gemini.google.com/app/x',
  'https://aistudio.google.com/prompts/x',
  'https://antigravity.google.com/chat/x',
  'https://copilot.microsoft.com/chat/x',
  'https://chat.mistral.ai/chat/x',
  'https://grok.com/chat/x',
  'https://chat.deepseek.com/chat/x',
  'https://poe.com/chat/x',
  'https://character.ai/chat/x',
  'https://perplexity.ai/search/x',
  'foo.chatgpt.com/c/x',
  'chatgpt.com:443/c/x',
  'u@chatgpt.com/c/x',
  'chatgpt.com/?q=x',
  'chatgpt.com/#session',
  'Link:\nhttps://chatgpt.com/c/x',
  'Link:https://chatgpt.com/c/x',
  'here,https://claude.ai/chat/x',
  'a;https://gemini.google.com/app/x',
  'url=https://chatgpt.com/share/x'
];
const allowed=[
  'chatgpt.com','chatgpt.com.',
  'github.com/o/r/pull/1',
  'https://github.com/o/r/blob/main/docs/chat/readme.md',
  'https://github.com/o/r/blob/main/conversations/answer.md',
  'https://github.com/o/r/blob/main/docs/antigravity-notes.md',
  '100% sure','%','%zz'
];
const prefixes=['',' ','\n','\t',...Array.from(',;:=|>*/\\!@#&"'),String.fromCharCode(96)];
const cases=refused.length*prefixes.length*3;

function payloadFor(field,value) {
  const header=example();delete header.moves;
  const item=move();
  if(field==='header')header.goal=value;
  else item[field]=value;
  return {v:3,id:ID,baseSha:null,expectedCount:0,header,moves:[item]};
}
async function exercise(field,value,shouldRefuse) {
  const packet=payloadFor(field,value);
  const thread={...packet.header,moves:packet.moves};
  const label=field+' '+JSON.stringify(value);
  if(shouldRefuse)assert.throws(()=>validate(thread),/Private chat URL/,label);
  else assert.doesNotThrow(()=>validate(thread),label);
  // The same issue-body bytes must be checked by the actual server unpacker and writer.
  const issue={state:'open',user:{login:'reallakshman19'},
    labels:[{name:'nextnudge-save'}],body:encode(packet)};
  if(shouldRefuse)assert.throws(()=>unpack(issue.body),/Private chat URL/,label);
  else assert.doesNotThrow(()=>unpack(issue.body),label);
  let writes=0,receipt='';
  const status=await applyIssue({issue,owner:'reallakshman19',read:async()=>null,
    write:async()=>{writes++;},comment:async text=>{receipt=text;},close:async()=>{}});
  assert.equal(status,shouldRefuse?'REJECTED':'SAVED',label);
  assert.equal(writes,shouldRefuse?0:1,label);
  if(shouldRefuse)assert.match(receipt,/Private chat URL/,label);
}
test('FIX3: all punctuation-prefix × URL × packet/digest/header cases use shared client/server filter',async()=>{
  for(const url of refused)for(const prefix of prefixes)for(const field of ['packet','digest','header'])
    await exercise(field,prefix+url,true);
  console.log('CROSS_PRODUCT_CASES='+cases);
});
test('FIX3: harmless mentions and GitHub evidence remain allowed in all three fields',async()=>{
  for(const text of allowed)for(const field of ['packet','digest','header'])
    await exercise(field,text,false);
});
test('FIX4: long non-chat input is checked in under 250 ms without backtracking',()=>{
  const samples=[
    'a.'.repeat(100000),
    '1.'.repeat(100000),
    'a-b.'.repeat(50000),
    'lorem.ipsum.dolor.'.repeat(11200)
  ];
  let max=0;
  for(const sample of samples){
    const started=performance.now();
    assert.doesNotThrow(()=>assertPublic(sample));
    const elapsed=performance.now()-started;
    max=Math.max(max,elapsed);
    assert.ok(elapsed<250,'Non-chat input '+sample.length+' chars took '+elapsed.toFixed(1)+' ms');
  }
  console.log('MAX_MS_200KB='+Math.ceil(max));
});
test('FIX3: recursive string scanning handles nested arrays, raw newlines and stray percent',()=>{
  const secrets={packet:'100% sure',reply:['Link:\nhttps://chatgpt.com/c/x']};
  assert.throws(()=>assertPublic(secrets),/Private chat URL/);
  assert.throws(()=>assertPublic({nested:[{value:'50% https%253A%252F%252Fchatgpt.com%252Fc%252Fx'}]}),
    /Private chat URL/);
  assert.doesNotThrow(()=>assertPublic({nested:[{value:'100% sure'}],links:[
    'github.com/o/r/blob/main/docs/chat/readme.md','%zz']}));
});
