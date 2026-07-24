(() => {
  document.querySelectorAll('#interop-outlet').forEach((e) => {
    e.style.pointerEvents = 'none';
    e.style.display = 'none';
  });
  const el = [...document.querySelectorAll('a,button,[role=button]')].find((e) =>
    ((e.innerText || '') + (e.getAttribute('aria-label') || '')).includes('Start a post')
  );
  if (!el) return 'NOT_FOUND';
  el.click();
  return 'CLICKED';
})()
