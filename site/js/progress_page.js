/** SPA adapter only: all Progress rendering resides in portable site/progress/. */
'use strict';
let progressUnmount;
async function renderProgressPage(app, pageKey, topic, view) {
  if (progressUnmount) { progressUnmount(); progressUnmount=null; }
  const siteVersion = document.querySelector('meta[name="site-version"]')?.content || 'unstamped';
  const moduleUrl = new URL('progress/viewer.mjs', document.baseURI);
  moduleUrl.searchParams.set('v', siteVersion);
  const {mountProgress} = await import(moduleUrl.href);
  const route = '#progress-page' + (pageKey ? '/'+pageKey : '') +
    (topic ? '/'+topic : '') + (view ? '/'+view : '');
  progressUnmount = await mountProgress(app, {
    base: new URL('progress-data', document.baseURI).href,
    route, navigate
  });
}
