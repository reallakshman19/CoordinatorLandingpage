/** Same-origin isolation keeps workbench styles out of the dashboard. */
export function renderNextNudge(app, benchmarkMode, version) {
  app.replaceChildren();
  if (benchmarkMode) {
    const note = document.createElement('p');
    note.textContent = 'NextNudge is unavailable in frozen benchmark mode. Exit benchmark mode to open your browser-local task runs.';
    app.appendChild(note);
    return;
  }
  const frame = document.createElement('iframe');
  frame.id = 'nextnudge-frame';
  frame.title = 'NextNudge task workbench';
  const url = new URL('nextnudge/index.html', document.baseURI);
  if (version) url.searchParams.set('v', version);
  frame.src = url.href;
  frame.style.cssText = 'width:100%;height:85vh;min-height:640px;border:0;border-radius:12px;background:#f5f6f1';
  app.appendChild(frame);
}
