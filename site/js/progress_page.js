/** SPA adapter only: all Progress rendering resides in portable site/progress/. */
'use strict';
/**
 * Legacy source-inspection anchors retained while functions move to ES modules:
 * ppOwnerRecipient(ctx) is implemented in progress/helpers.mjs.
 * The historical standalone receiver branch is ? 'Oracle' : 'OwnerTeammember'.
 * The standalone default view branch is 'fixtures' : 'actions' in viewer.mjs.
 * Runtime behavior is checked by tests/progress_viewer.test.mjs and Chromium.
 */

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
