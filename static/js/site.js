document.querySelectorAll('[data-step]').forEach(button => {
  button.addEventListener('click', () => {
    const input = button.closest('.quantity-control').querySelector('input');
    const min = Number(input.min || 1), max = Number(input.max || 9999);
    input.value = Math.max(min, Math.min(max, Number(input.value || min) + Number(button.dataset.step)));
    input.dispatchEvent(new Event('change', { bubbles: true }));
  });
});
document.querySelectorAll('[data-gallery-src]').forEach(button => {
  button.addEventListener('click', () => {
    document.getElementById('gallery-main').src = button.dataset.gallerySrc;
    document.querySelectorAll('[data-gallery-src]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
  });
});
document.querySelectorAll('[data-confirm]').forEach(form => {
  form.addEventListener('submit', event => { if (!window.confirm(form.dataset.confirm)) event.preventDefault(); });
});
const role = document.getElementById('id_role');
if (role) {
  const shop = document.getElementById('id_shop_name');
  const syncRole = () => { if (shop) { shop.closest('.field').hidden = role.value !== 'SELLER'; shop.required = role.value === 'SELLER'; } };
  role.addEventListener('change', syncRole); syncRole();
}
document.querySelectorAll('.navbar a.nav-link').forEach(link => {
  if (link.pathname === window.location.pathname) { link.classList.add('active'); link.setAttribute('aria-current', 'page'); }
});
document.querySelectorAll('img').forEach(img => {
  img.addEventListener('error', () => {
    if (!img.dataset.fallbackApplied) { img.dataset.fallbackApplied = 'true'; img.src = '/static/images/placeholder.svg'; img.alt = 'Photograph unavailable'; }
  });
});
if (window.location.hash === '#search') {
  const filters = document.getElementById('filters');
  if (filters && window.bootstrap) {
    bootstrap.Collapse.getOrCreateInstance(filters, { toggle: false }).show();
    document.getElementById('search').focus();
  }
}
