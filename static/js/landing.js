/**
 * RazorRecover AI - Landing Page Interactions
 */
document.addEventListener('DOMContentLoaded', () => {
  const howItWorksBtn = document.getElementById('btn-how-it-works');
  const howModal = document.getElementById('how-it-works-modal');
  const closeHowModal = document.getElementById('btn-close-how-modal');

  if (howItWorksBtn && howModal) {
    howItWorksBtn.addEventListener('click', () => {
      howModal.classList.add('active');
    });
  }

  if (closeHowModal && howModal) {
    closeHowModal.addEventListener('click', () => {
      howModal.classList.remove('active');
    });
  }

  // Active state synchronization on scroll
  const navLinks = document.querySelectorAll('.landing-nav a');
  const sections = document.querySelectorAll('main[id], section[id]');

  function updateActiveNav() {
    let currentId = '';
    const scrollPos = window.scrollY + 120;

    sections.forEach(section => {
      const top = section.offsetTop;
      const height = section.offsetHeight;
      if (scrollPos >= top && scrollPos < top + height) {
        currentId = section.getAttribute('id');
      }
    });

    navLinks.forEach(link => {
      const href = link.getAttribute('href');
      if (href === `#${currentId}`) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });
  }

  window.addEventListener('scroll', updateActiveNav, { passive: true });
  updateActiveNav();
});
