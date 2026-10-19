import {summary,replyWarnings,replyAcks} from './reply.mjs';
import {sealHtml} from './seal.mjs';
export function moveMarkup(thread,move,esc) {
  if(move.kind==='sealed')return sealHtml(thread,move,esc);
  const first=move.kind==='reply'?replyAcks(move.replyText||move.returnLine||'').primary:'';
  const warnings=move.kind==='reply'?replyWarnings(move.replyText||move.digest||'',first,
    !first||!!move.answers):[];
  const info=summary(move,thread);
  return '<div class="move-summary"><strong>'+esc(info)+'</strong> · '+
    esc(move.returnLine||move.note||'No reply')+
    warnings.map(w=>'<p class="hold">'+esc(w)+'</p>').join('')+'</div>';
}
