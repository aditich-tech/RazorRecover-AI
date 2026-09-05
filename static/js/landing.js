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

  if (howModal) {
    howModal.addEventListener('click', (e) => {
      if (e.target === howModal) howModal.classList.remove('active');
    });
  }
});
