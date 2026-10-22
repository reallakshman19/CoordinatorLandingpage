// PRG-CORE-1 Stage 2: portable logic and fail-closed link safety.
import test from 'node:test';
import assert from 'node:assert/strict';
import {ppRollup, ppSafeUrl, ppSendUrl, ppOpenActions, ppMilestones} from '../site/progress/helpers.mjs';
import {readFile} from 'node:fs/promises';
const project = {kind:'github-issue', repo:'sample/owner', template:'owner-reply.yml',
  target:'CustomReceiver', site:'https://example.org/public/'};
test('rollup and milestones preserve old badge precedence',()=>{
  assert.equal(ppRollup(['BLOCKED','VERIFIED']),'BLOCKED');
  assert.equal(ppRollup(['VERIFIED','NOT_APPLICABLE']),'VERIFIED');
  assert.equal(ppRollup(['SUBMITTED','NOT_STARTED']),'SUBMITTED');
  const topic={topic:{milestones:{M1:{name:'Check',order:1}}}, stages:{S1:{milestone:'M1',state:'VERIFIED'}}};
  assert.equal(ppMilestones(topic)[0].state,'VERIFIED');
});
test('only https links become anchors',()=>{
  assert.equal(ppSafeUrl('http://example.org'),'');
  assert.equal(ppSafeUrl('javascript:alert(1)'),'');
  assert.equal(ppSafeUrl('https://example.org'), 'https://example.org');
});
test('reply URL uses per-project repo, template, target, and site',()=>{
  const u=new URL(ppSendUrl({replyTo:project,project:'g9v35',page:'g9v35',topic:'nlm',view:'actions',card:'D1',option:'A'},'Text'));
  assert.equal(u.origin, 'https://github.com');
  assert.equal(u.pathname, '/sample/owner/issues/new');
  assert.equal(u.searchParams.get('template'), 'owner-reply.yml');
  assert.equal(u.searchParams.get('target'), 'CustomReceiver');
  assert.equal(u.searchParams.get('text'), 'Text');
  assert.equal(u.searchParams.get('evidence_link'),'https://example.org/public/#progress-page/g9v35/nlm/actions');
});
test('none or missing replyTo cannot construct a Send URL',()=>{
  assert.equal(ppSendUrl({replyTo:{kind:'none'}},'text'),'');
  assert.equal(ppSendUrl({},'text'),'');
});
test('standalone Oracle legacy receiver and data contract',async()=>{
  const pages=JSON.parse(await readFile(new URL('../site/progress-data/projects.json',import.meta.url)));
  assert.equal(pages.projects.find(p=>p.key==='ciifr').mode,'standalone-oracle');
  assert.equal(ppSendUrl({mode:'standalone-oracle',replyTo:project},'x').includes('target=Oracle'),true);
  assert.equal(ppOpenActions({actions:{D:{order:1,status:'open'},E:{status:'done'}}}).length,1);
});
test('versioned source graph never uses unversioned static imports',async()=>{
  for(const name of ['viewer','actions','progress','fixtures','overview']){
    const src=await readFile(new URL('../site/progress/'+name+'.mjs',import.meta.url),'utf8');
    assert.match(src,/new URL\(import\.meta\.url\)\.search|const v = new URL\(import\.meta\.url\)\.search/);
    assert.doesNotMatch(src,/^\s*import\s+.*from\s*['"]/m);
  }
});
