/**
 * RazorRecover AI - Dedicated AI Recovery Flow & Approval Workflow (Clean Light Theme)
 */
const RecoveryModal = {
  currentAnalysis: null,

  init() {
    const startBtn = document.getElementById('btn-start-recovery-main');
    const modalOverlay = document.getElementById('recovery-modal-overlay');
    const closeBtn = document.getElementById('btn-close-recovery-modal');

    if (startBtn) {
      startBtn.addEventListener('click', () => this.openModal());
    }
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.closeModal());
    }
  },

  openModal() {
    const modal = document.getElementById('recovery-modal-overlay');
    modal.classList.add('active');
    this.showScanningPhase();
  },

  closeModal() {
    const modal = document.getElementById('recovery-modal-overlay');
    modal.classList.remove('active');
  },

  // PHASE 1: Clean AI Scanning Animation
  async showScanningPhase() {
    const content = document.getElementById('recovery-modal-body');
    content.innerHTML = `
      <div class="ai-radar-container">
        <div class="radar-circle">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#0052ff" stroke-width="2">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
          </svg>
        </div>
        <div class="radar-status-text">Analyzing payment failures...</div>
        <p style="color: #64748b; font-size: 13px; max-width: 480px;">
          Querying transaction database, computing customer recovery probabilities, and screening against stopping rules.
        </p>

        <div class="analysis-steps-list" id="scan-steps-list">
          <div class="step-item" id="step-1">
            <span class="step-icon">⏳</span>
            <span>Querying unrecovered transaction records from Supabase...</span>
          </div>
          <div class="step-item" id="step-2">
            <span class="step-icon">⏳</span>
            <span>Evaluating customer historical reliability & retry decay...</span>
          </div>
          <div class="step-item" id="step-3">
            <span class="step-icon">⏳</span>
            <span>Applying stopping rules & calculating priority scores...</span>
          </div>
        </div>
      </div>
    `;

    // Progressive step animations
    setTimeout(() => {
      const s1 = document.getElementById('step-1');
      if (s1) { s1.classList.add('completed'); s1.querySelector('.step-icon').textContent = '✓'; }
    }, 600);

    setTimeout(() => {
      const s2 = document.getElementById('step-2');
      if (s2) { s2.classList.add('completed'); s2.querySelector('.step-icon').textContent = '✓'; }
    }, 1200);

    setTimeout(() => {
      const s3 = document.getElementById('step-3');
      if (s3) { s3.classList.add('completed'); s3.querySelector('.step-icon').textContent = '✓'; }
    }, 1800);

    // Call live analysis endpoint
    try {
      const data = await API.get('/api/recovery/analyze');
      this.currentAnalysis = data;
      // Reveal results after short animation delay
      setTimeout(() => {
        this.showAnalysisResults(data);
      }, 2100);
    } catch (err) {
      content.innerHTML = `
        <div style="padding: 40px; text-align: center; color: #b42318;">
          <h3>Analysis Failed</h3>
          <p style="margin: 12px 0;">Unable to query transaction database.</p>
          <button class="btn btn-secondary" onclick="RecoveryModal.closeModal()">Close</button>
        </div>
      `;
    }
  },

  // PHASE 2: Detailed Failure Breakdown & AI Recommendations
  showAnalysisResults(data) {
    const content = document.getElementById('recovery-modal-body');
    const breakdownRows = data.breakdown.map(b => `
      <tr>
        <td style="font-weight: 600; color: #101828;">${b.reason}</td>
        <td style="text-align: right; color: #475467;">${API.formatNumber(b.attempts)}</td>
        <td style="text-align: right; font-family: var(--font-mono); font-weight: 700; color: #b42318;">
          ${API.formatCurrency(b.potential_loss)}
        </td>
      </tr>
    `).join('');

    const recCards = data.recommendations.map(r => `
      <div class="rec-card">
        <div class="rec-title">
          <span style="color: #0052ff;">✦</span> ${r.action}
        </div>
        <p style="font-size: 12px; color: #64748b; line-height: 1.4;">${r.description}</p>
        <div class="rec-meta">
          <span>${API.formatNumber(r.count)} transactions</span>
          <span>${API.formatCurrency(r.amount)}</span>
        </div>
      </div>
    `).join('');

    content.innerHTML = `
      <div style="padding: 28px 32px;">
        <!-- Header Summary -->
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; padding-bottom: 18px; border-bottom: 1px solid var(--border-subtle);">
          <div>
            <div class="badge badge-info" style="margin-bottom: 8px;">AI Diagnosis Complete</div>
            <h2 style="font-family: var(--font-heading); font-size: 22px; color: #101828;">
              ${API.formatNumber(data.total_failures_analyzed)} failed payment attempts analyzed
            </h2>
            <p style="color: #64748b; font-size: 13px; margin-top: 4px;">
              Live dataset processed from Supabase. Revenue at risk: <strong style="color: #b42318;">${API.formatCurrency(data.total_potential_loss)}</strong>
            </p>
          </div>
          <div style="text-align: right; background: #ecfdf3; border: 1px solid #abefc6; padding: 12px 18px; border-radius: var(--radius-md);">
            <div style="font-size: 11px; color: #027a48; font-weight: 600; text-transform: uppercase;">Estimated Recoverable</div>
            <div style="font-family: var(--font-heading); font-size: 24px; font-weight: 800; color: #027a48;">
              ${API.formatCurrency(data.estimated_recoverable_revenue)}
            </div>
            <div style="font-size: 11px; color: #64748b;">
              Across ${API.formatNumber(data.recommended_for_recovery_count)} eligible payments
            </div>
          </div>
        </div>

        <!-- Failure Breakdown Table -->
        <h3 style="font-size: 14px; font-weight: 600; color: #101828; margin-bottom: 10px;">
          Failure Reason Breakdown
        </h3>
        <div class="table-container" style="margin-bottom: 24px;">
          <table class="data-table">
            <thead>
              <tr>
                <th>Failure Reason</th>
                <th style="text-align: right;">Attempts</th>
                <th style="text-align: right;">Potential Loss</th>
              </tr>
            </thead>
            <tbody>
              ${breakdownRows}
            </tbody>
          </table>
        </div>

        <!-- AI Recommendations -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <h3 style="font-size: 14px; font-weight: 600; color: #101828;">
            AI Recovery Recommendations
          </h3>
          <span style="font-size: 11.5px; color: #64748b;">
            Stopping rules enforced: Max 3 retries · Min 25% prob threshold
          </span>
        </div>
        <div class="recommendations-grid">
          ${recCards}
        </div>

        <!-- Merchant Approval CTA Bar -->
        <div style="margin-top: 28px; padding-top: 18px; border-top: 1px solid var(--border-subtle); display: flex; align-items: center; justify-content: space-between;">
          <div style="display: flex; align-items: center; gap: 8px; color: #475467; font-size: 12.5px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#b54708" stroke-width="2">
              <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
            <span>Requires merchant approval before automated workflow execution.</span>
          </div>

          <div style="display: flex; gap: 12px;">
            <button class="btn btn-secondary" onclick="RecoveryModal.closeModal()">Cancel</button>
            <button class="btn btn-accent btn-lg" id="btn-approve-recovery" onclick="RecoveryModal.executeWorkflow()">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M20 6L9 17l-5-5"/>
              </svg>
              Approve Recovery
            </button>
          </div>
        </div>
      </div>
    `;
  },

  // PHASE 3: Simulated Bounded Workflow Execution
  async executeWorkflow() {
    const content = document.getElementById('recovery-modal-body');
    content.innerHTML = `
      <div style="padding: 48px 32px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 18px;">
        <div class="radar-circle" style="border-color: #abefc6; border-top-color: #027a48;">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#027a48" stroke-width="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
        </div>
        <h2 style="font-family: var(--font-heading); font-size: 22px; color: #101828;">
          Recovery in progress...
        </h2>
        <p style="color: #64748b; font-size: 13.5px; max-width: 500px;">
          Executing bounded recovery workflows, applying routing adjustments, and updating transaction ledger.
        </p>

        <div style="width: 100%; max-width: 500px; height: 8px; background: #eaecf0; border-radius: 4px; overflow: hidden; margin-top: 8px;">
          <div id="progress-bar-fill" style="width: 0%; height: 100%; background: linear-gradient(90deg, #0052ff, #027a48); transition: width 0.4s ease;"></div>
        </div>

        <div id="execution-live-feed" style="margin-top: 10px; font-family: var(--font-mono); font-size: 11.5px; color: #64748b; height: 32px;">
          Dispatching intelligent retry payloads...
        </div>
      </div>
    `;

    const progressFill = document.getElementById('progress-bar-fill');
    const liveFeed = document.getElementById('execution-live-feed');

    setTimeout(() => {
      if (progressFill) progressFill.style.width = '35%';
      if (liveFeed) liveFeed.textContent = 'Enforcing stopping rules: 3 max retry boundaries checked...';
    }, 500);

    setTimeout(() => {
      if (progressFill) progressFill.style.width = '70%';
      if (liveFeed) liveFeed.textContent = 'Recording recovery confirmations to Supabase audit trail...';
    }, 1100);

    try {
      const result = await API.post('/api/recovery/execute');
      setTimeout(() => {
        if (progressFill) progressFill.style.width = '100%';
        if (liveFeed) liveFeed.textContent = 'Batch execution complete! Finalizing metrics...';
        setTimeout(() => {
          this.showOutcomeScreen(result);
        }, 600);
      }, 1600);
    } catch (err) {
      alert('Execution failed. Please retry.');
      this.closeModal();
    }
  },

  // PHASE 4: Recovery Outcome Screen
  showOutcomeScreen(res) {
    const content = document.getElementById('recovery-modal-body');
    content.innerHTML = `
      <div style="padding: 36px 32px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 20px;">
        <div style="width: 56px; height: 56px; border-radius: 50%; background: #ecfdf3; border: 1px solid #abefc6; display: flex; align-items: center; justify-content: center;">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#027a48" stroke-width="2.5">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        </div>

        <div>
          <div class="badge badge-success" style="margin-bottom: 8px;">Execution Successful</div>
          <h2 style="font-family: var(--font-heading); font-size: 24px; font-weight: 800; color: #101828;">
            Recovery Complete
          </h2>
          <p style="color: #64748b; font-size: 13.5px; margin-top: 4px;">
            Simulated bounded workflow executed against the database and logged to audit trail.
          </p>
        </div>

        <!-- Outcome Highlights -->
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; width: 100%; max-width: 560px; text-align: left;">
          <div class="card" style="padding: 18px; border-color: #abefc6; background: #ecfdf3;">
            <div style="font-size: 11.5px; color: #027a48; text-transform: uppercase; font-weight: 600;">Revenue Recovered</div>
            <div style="font-family: var(--font-heading); font-size: 26px; font-weight: 800; color: #027a48; margin-top: 4px;">
              ${API.formatCurrency(res.recovered_amount)}
            </div>
            <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Added to verified merchant ledger</div>
          </div>

          <div class="card" style="padding: 18px; background: #ffffff;">
            <div style="font-size: 11.5px; color: #0052ff; text-transform: uppercase; font-weight: 600;">Success Rate</div>
            <div style="font-family: var(--font-heading); font-size: 26px; font-weight: 800; color: #0052ff; margin-top: 4px;">
              ${res.recovery_success_percentage}%
            </div>
            <div style="font-size: 11px; color: #64748b; margin-top: 4px;">
              ${API.formatNumber(res.payments_successfully_recovered)} payments recovered
            </div>
          </div>

          <div class="card" style="padding: 18px; background: #ffffff;">
            <div style="font-size: 11.5px; color: #64748b; text-transform: uppercase; font-weight: 600;">Failures Analyzed</div>
            <div style="font-family: var(--font-heading); font-size: 22px; font-weight: 700; color: #101828; margin-top: 4px;">
              ${API.formatNumber(res.failures_analyzed)}
            </div>
            <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Live query from Supabase</div>
          </div>

          <div class="card" style="padding: 18px; background: #ffffff;">
            <div style="font-size: 11.5px; color: #b54708; text-transform: uppercase; font-weight: 600;">Stopped by Guardrails</div>
            <div style="font-family: var(--font-heading); font-size: 22px; font-weight: 700; color: #b54708; margin-top: 4px;">
              ${API.formatNumber(res.stopped_by_rules_count)}
            </div>
            <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Protected from endless retries</div>
          </div>
        </div>

        <button class="btn btn-primary btn-lg" style="margin-top: 8px; width: 100%; max-width: 280px;" onclick="RecoveryModal.finishAndRefreshDashboard()">
          Back to Dashboard
        </button>
      </div>
    `;
  },

  finishAndRefreshDashboard() {
    this.closeModal();
    if (window.Dashboard) {
      window.Dashboard.loadStats();
      window.Dashboard.loadImpact();
    }
  }
};

window.RecoveryModal = RecoveryModal;
