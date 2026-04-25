// page-fold.js — page entrance animation.
// Reads sessionStorage 'nav-direction' set by the previous page's exit transition.
// (No-op when navigating directly via URL.)

(function () {
  const dir = sessionStorage.getItem('nav-direction');
  sessionStorage.removeItem('nav-direction');
  if (!dir) return;
  const el = document.getElementById('page-content');
  if (!el) return;

  document.documentElement.style.overflow = 'hidden';

  el.style.transition = 'none';
  el.style.transformOrigin = 'top center';
  if (dir === 'forward') {
    el.style.transform = 'translateY(100%)';
  } else {
    el.style.transform = 'perspective(900px) rotateX(-90deg) translateY(-55px)';
    el.style.opacity = '0';
  }

  void el.offsetHeight;
  requestAnimationFrame(() => {
    el.style.transition = 'transform 0.5s cubic-bezier(0.4,0,0.2,1), opacity 0.5s ease';
    el.style.transform = '';
    el.style.opacity = '';

    const cleanup = () => {
      el.style.transition = '';
      el.style.transformOrigin = '';
      document.documentElement.style.overflow = '';
    };
    const fallback = setTimeout(cleanup, 600);
    el.addEventListener('transitionend', function done() {
      clearTimeout(fallback);
      cleanup();
      el.removeEventListener('transitionend', done);
    });
  });
})();
