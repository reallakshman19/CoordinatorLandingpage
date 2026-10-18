export const $=selector=>document.querySelector(selector);
export const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({
  '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
}[c]));
export const labels={ready:'Ready',sent:'Sent',submitted:'Review needed',accepted:'Accepted',revision:'Needs correction'};
export function notice(message){$('#notice').textContent=message;}
export function options(items,value){return items.map(([id,label])=>`<option value="${esc(id)}" ${id===value?'selected':''}>${esc(label)}</option>`).join('');}
export const button=(action,label,attrs='')=>`<button data-action="${action}" ${attrs}>${label}</button>`;
export const link=url=>url?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">Open source ↗</a>`:'';
