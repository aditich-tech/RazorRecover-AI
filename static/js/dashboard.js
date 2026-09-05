/**
 * RazorRecover AI - Main Dashboard Controller
 */
const Dashboard = {
  init() {
    this.loadStats();
    this.loadImpact();
    this.setupReseedHandler();
  },

  async loadStats() {
    const lossEl = document.getElementById('stat-potential-loss');
    const recoverableEl = document.getElementById('stat-potentially-recoverable');
    const failedCountEl = document.getElementById('stat-failed-attempts');
    const pendingEl = document.getElementById('stat-pending-recoveries');
    const recoveredEl = document.getElementById('stat-recovered-revenue');
    const rateEl = document.getElementById('stat-recovery-rate');
    const kpiEls = [lossEl, recoverableEl, failedCountEl, pendingEl, recoveredEl, rateEl].filter(Boolean);

    kpiEls.forEach(el => el.classList.add('skeleton-text'));

    try {
      const data = await API.get('/api/dashboard/stats');
      if (!data) return;

      if (lossEl) lossEl.textContent = API.formatCurrency(data.total_potential_loss);
      if (recoverableEl) recoverableEl.textContent = API.formatCurrency(data.potentially_recoverable_revenue);
      if (failedCountEl) failedCountEl.textContent = API.formatNumber(data.failed_payment_attempts);
      if (pendingEl) pendingEl.textContent = API.formatNumber(data.pending_recoveries);
      if (recoveredEl) recoveredEl.textContent = API.formatCurrency(data.revenue_already_recovered);
      if (rateEl) rateEl.textContent = `${data.recovery_rate}%`;

      // Update Risk Zone Banner
      const riskCard = document.getElementById('risk-zone-card');
      const riskTitle = document.getElementById('risk-zone-title');
      const riskDesc = document.getElementById('risk-zone-desc');

      if (riskCard && riskTitle && riskDesc) {
        riskCard.className = `risk-zone-card ${data.risk_level}`;
        riskTitle.textContent = data.risk_zone;
        riskDesc.textContent = data.risk_summary;
      }

      // Render Recent Audit Logs Feed
      const logsContainer = document.getElementById('recent-audit-logs-list');
      if (logsContainer && data.recent_logs) {
        if (data.recent_logs.length === 0) {
          logsContainer.innerHTML = '<div style="color: #64748b; font-size: 13px;">No audit trail events recorded yet.</div>';
        } else {
          logsContainer.innerHTML = data.recent_logs.map(log => `
            <div style="padding: 10px 14px; background: #f8fafc; border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); font-size: 12.5px; display: flex; justify-content: space-between; align-items: center;">
              <div>
                <span style="font-family: var(--font-mono); color: #0052ff; font-size: 11px; margin-right: 8px;">${log.timestamp}</span>
                <span style="color: #101828; font-weight: 500;">${log.description}</span>
              </div>
              <span class="badge ${log.event_type === 'PAYMENT_RECOVERED' ? 'badge-success' : 'badge-neutral'}">
                ${log.event_type.replace(/_/g, ' ')}
              </span>
            </div>
          `).join('');
        }
      }
    } catch (err) {
      console.error('Failed to load dashboard stats:', err);
    } finally {
      kpiEls.forEach(el => el.classList.remove('skeleton-text'));
    }
  },

  async loadImpact() {
    const beforeLossEl = document.getElementById('impact-before-loss');
    const beforeRecoverableEl = document.getElementById('impact-before-recoverable');
    const beforeAttemptsEl = document.getElementById('impact-before-attempts');

    const afterRecoveredEl = document.getElementById('impact-after-recovered');
    const afterRemainingEl = document.getElementById('impact-after-remaining');
    const afterRateEl = document.getElementById('impact-after-rate');
    const impactBar = document.getElementById('impact-progress-fill');
    const impactEls = [beforeLossEl, beforeRecoverableEl, beforeAttemptsEl, afterRecoveredEl, afterRemainingEl, afterRateEl].filter(Boolean);

    impactEls.forEach(el => el.classList.add('skeleton-text'));

    try {
      const data = await API.get('/api/dashboard/impact');
      if (!data) return;

      if (beforeLossEl) beforeLossEl.textContent = API.formatCurrency(data.before.potential_loss);
      if (beforeRecoverableEl) beforeRecoverableEl.textContent = API.formatCurrency(data.before.potentially_recoverable);
      if (beforeAttemptsEl) beforeAttemptsEl.textContent = API.formatNumber(data.before.failed_attempts);

      if (afterRecoveredEl) afterRecoveredEl.textContent = API.formatCurrency(data.after.recovered_revenue);
      if (afterRemainingEl) afterRemainingEl.textContent = API.formatCurrency(data.after.remaining_potential_loss);
      if (afterRateEl) afterRateEl.textContent = `${data.after.recovery_rate}%`;

      if (impactBar) {
        impactBar.style.width = `${Math.min(100, Math.max(0, data.after.recovery_rate))}%`;
      }
    } catch (err) {
      console.error('Failed to load impact stats:', err);
    } finally {
      impactEls.forEach(el => el.classList.remove('skeleton-text'));
    }
  },

  setupReseedHandler() {
    const reseedBtn = document.getElementById('btn-reseed-data');
    if (reseedBtn) {
      reseedBtn.addEventListener('click', async () => {
        if (!confirm('Reset transaction database back to initial state with 10,000+ demo transactions?')) return;
        reseedBtn.disabled = true;
        reseedBtn.textContent = 'Resetting & Seeding...';
        try {
          const res = await API.post('/api/admin/reseed');
          alert(res.message);
          window.location.reload();
        } catch (err) {
          alert('Failed to reset dataset.');
          reseedBtn.disabled = false;
          reseedBtn.textContent = 'Reset Demo Data';
        }
      });
    }
  }
};

window.Dashboard = Dashboard;
