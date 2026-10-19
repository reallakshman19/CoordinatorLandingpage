// CLI adapter for authenticated hosts. JSON requests use the host's connector;
// this process never receives or persists a GitHub token.
import fs from 'node:fs';
import readline from 'node:readline';
import {gzipSync} from 'node:zlib';
import {parse,serialize} from '../site/nextnudge/revamp/thread.mjs';
import {delta} from '../site/nextnudge/revamp/save.mjs';
import {sendNudge,fetchReturn} from '../site/nextnudge/revamp/transport.mjs';
const config=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const before=parse(fs.readFileSync(config.threadFile,'utf8'));
const thread=structuredClone(before),input=readline.createInterface({input:process.stdin});
let pending=null,sequence=0;
input.on('line',line=>{
  if(!pending)return;
  try{const result=JSON.parse(line);if(result.id!==pending.id)throw Error('Host response ID mismatch');
    const waiter=pending;pending=null;
    result.ok?waiter.resolve(result.value):waiter.reject(Error(result.error||'Host operation failed'));
  }catch(e){const waiter=pending;pending=null;waiter.reject(e);}
});
function rpc(method,target,body){
  return new Promise((resolve,reject)=>{
    pending={id:++sequence,resolve,reject};console.log('NEXTNUDGE_RPC '+JSON.stringify({id:sequence,method,target,...(body?{body}:{})}));
  });
}
try{
  const api={listComments:target=>rpc('listComments',target),postComment:(target,body)=>rpc('postComment',target,body)};
  const move=config.operation==='send'?await sendNudge(thread,config.move,config.target,api):
    await fetchReturn(thread,config.moveId,api);
  if(move){
    thread.moves.push(move);
    fs.writeFileSync(config.output,serialize(thread));
    const payload=delta(thread,before,config.baseSha);
    const tick=String.fromCharCode(96).repeat(3);
    fs.writeFileSync(config.output+'.save.txt',tick+'nextnudge-thread-save\n'+gzipSync(JSON.stringify(payload)).toString('base64')+'\n'+tick+'\n');
    console.log('NEXTNUDGE_RESULT '+JSON.stringify({status:'RECORDED_LOCALLY',moveId:move.id,evidence:move.evidence,
      output:config.output,saveRequest:config.output+'.save.txt',limit:'Publish and read back the Owner save before claiming durable recording.'}));
  }else console.log('NEXTNUDGE_RESULT '+JSON.stringify({status:'WAITING',limit:'No new matching named-agent return.'}));
}catch(e){console.error('NEXTNUDGE_ERROR '+e.message);process.exitCode=1;}
finally{input.close();}
