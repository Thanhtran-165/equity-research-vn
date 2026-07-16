(() => {
  const button = document.querySelector('.menu-button');
  const mobile = document.querySelector('#mobile-nav');
  const nav = document.querySelector('.chapter-nav');
  if (button && mobile && nav) {
    mobile.innerHTML = nav.innerHTML;
    button.addEventListener('click', () => {
      const open = button.getAttribute('aria-expanded') === 'true';
      button.setAttribute('aria-expanded', String(!open));
      mobile.hidden = open;
    });
    mobile.addEventListener('click', () => {
      button.setAttribute('aria-expanded', 'false');
      mobile.hidden = true;
    });
  }

  const tocLinks = [...document.querySelectorAll('.page-toc a')];
  const sections = tocLinks
    .map((link) => document.getElementById(decodeURIComponent(link.hash.slice(1))))
    .filter(Boolean);
  if ('IntersectionObserver' in window && sections.length) {
    const observer = new IntersectionObserver((entries) => {
      const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
      if (!visible) return;
      tocLinks.forEach((link) => link.classList.toggle('active', link.hash === `#${visible.target.id}`));
    }, { rootMargin: '-18% 0px -68% 0px', threshold: 0 });
    sections.forEach((section) => observer.observe(section));
  }
})();
