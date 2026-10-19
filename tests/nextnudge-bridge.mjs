import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {newThread,serialize} from '../site/nextnudge/revamp/thread.mjs';

test('NN110 CLI: a real terminal accepts connector responses larger than its canonical line buffer',
  {skip:process.platform==='win32'},()=>{
  const dir=fs.mkdtempSync(path.join(process.cwd(),'tests/.bridge-'));
  try{
    const thread=newThread({id:'NN-20261019-173500-a110',title:'Terminal transport',goal:'Retain actual large responses'});
    const threadFile=path.join(dir,'source.md'),output=path.join(dir,'sent.md');
    fs.writeFileSync(threadFile,serialize(thread));
    const move={id:'PTY-PILOT',kind:'task',delivery:'sent',packet:'Read-only terminal pilot',returnLine:'',
      digest:'',evidence:'',gap:'',decision:'',archive:'',note:''};
    const config=path.join(dir,'config.json');
    fs.writeFileSync(config,JSON.stringify({operation:'send',threadFile,output,baseSha:'a'.repeat(40),move,
      target:{repository:'reallakshman19/CoordinatorLandingpage',issue:110,agent:'terminal-pilot'}}));
    const python=String.raw`
import os,pty,subprocess,select,json,time,sys
master,slave=pty.openpty()
p=subprocess.Popen(['node','scripts/nextnudge_agent_bridge.mjs',sys.argv[1]],stdin=slave,stdout=slave,stderr=slave)
os.close(slave)
pending=b'';result=False;errors=[];deadline=time.monotonic()+12
while time.monotonic()<deadline:
 ready,_,_=select.select([master],[],[],0.1)
 if not ready:
  if p.poll() is not None:break
  continue
 try:data=os.read(master,65536)
 except OSError:break
 if not data:break
 pending+=data
 while b'\n' in pending:
  raw,pending=pending.split(b'\n',1);line=raw.decode('utf8',errors='replace').strip()
  if line.startswith('NEXTNUDGE_ERROR '):errors.append(line)
  if line.startswith('NEXTNUDGE_RESULT '):result=True
  if not line.startswith('NEXTNUDGE_RPC '):continue
  r=json.loads(line[len('NEXTNUDGE_RPC '):])
  if r['method']=='listComments':
   value=[{'body':'An unrelated real-shaped long response '+('x'*12000),'user':{'login':'reallakshman19'}}]
  else:
   value={'body':r['body'],'html_url':'https://github.com/reallakshman19/CoordinatorLandingpage/issues/110#issuecomment-987','user':{'login':'reallakshman19'}}
  reply=(json.dumps({'id':r['id'],'ok':True,'value':value})+'\n').encode()
  while reply:
   n=os.write(master,reply);reply=reply[n:]
if p.poll() is None:p.terminate()
p.wait(timeout=2);os.close(master)
if not result:print(json.dumps({'result':False,'errors':errors}));sys.exit(1)
print('PTY round-trip PASS with 12000-character connector payload')
`;
    const run=spawnSync('python3',['-c',python,config],{encoding:'utf8',timeout:20000});
    assert.equal(run.status,0,(run.stdout||'')+(run.stderr||''));
    assert.match(run.stdout,/PTY round-trip PASS/);
    assert.ok(fs.existsSync(output));assert.ok(fs.existsSync(output+'.save.txt'));
  }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
