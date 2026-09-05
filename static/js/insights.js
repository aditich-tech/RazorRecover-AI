/**
 * RazorRecover AI - AI Insights (Analyst) Controller
 */
const AIInsights = {
  init() {
    this.loadInsights();
  },

  async loadInsights() {
    const container = document.getElementById('ai-insights-container');
    if (!container) return;

    try {
      const data = await API.get('/api/insights');
      if (!data || !data.insights) return;

      container.innerHTML = data.insights.map(item => {
        let typeBadge = 'badge-info';
        if (item.type === 'surge') typeBadge = 'badge-warning';
        if (item.type === 'financial') typeBadge = 'badge-success';

        return `
          <div class="card" style="margin-bottom: 20px; border-left: 4px solid var(--razorpay-blue); display: flex; flex-direction: column; gap: 14px; background: #ffffff;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 16px;">
              <div>
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                  <span class="badge ${typeBadge}">${item.type.toUpperCase()}</span>
                  <h3 style="font-size: 16px; font-weight: 700; color: #101828;">${item.title}</h3>
                </div>
                <p style="font-size: 13.5px; color: #475467; line-height: 1.6; max-width: 850px;">
                  ${item.description}
                </p>
              </div>
              <div style="text-align: right; background: #f8fafc; padding: 8px 14px; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle); white-space: nowrap;">
                <div style="font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600;">Projected Impact</div>
                <div style="font-size: 13px; font-weight: 700; color: #027a48; margin-top: 2px;">${item.impact}</div>
              </div>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 12px; border-top: 1px solid var(--border-subtle);">
              <span style="font-size: 12px; color: #64748b;">
                Identified by RazorRecover ML Diagnostic Engine
              </span>
              <button class="btn btn-primary btn-sm" onclick="AIInsights.applyRecommendation('${item.action_rule_id}')">
                ✨ Apply Recommendation
              </button>
            </div>
          </div>
        `;
      }).join('');
    } catch (err) {
      container.innerHTML = '<div style="color: #ef4444;">Failed to load AI insights.</div>';
    }
  },

  async applyRecommendation(ruleId) {
    try {
      const res = await API.post(`/api/rules/${ruleId}/toggle`);
      const isApplied = res && res.is_active === 1;
      const ruleName = res && res.rule_name ? res.rule_name : ruleId;

      this.showRuleDialog({
        ruleId: ruleId,
        ruleName: ruleName,
        isApplied: isApplied,
        message: isApplied
          ? `Rule ${ruleId} (${ruleName}) has been applied and activated in the recovery engine.`
          : `Rule ${ruleId} (${ruleName}) has been turned off.`
      });

      // Keep rules view in sync if loaded
      if (window.RecoveryRules && typeof window.RecoveryRules.loadRules === 'function') {
        window.RecoveryRules.loadRules();
      }
    } catch (err) {
      console.error('Failed to toggle rule recommendation:', err);
      this.showRuleDialog({
        ruleId: ruleId,
        ruleName: ruleId,
        isApplied: false,
        message: `Failed to update Rule ${ruleId}. Please verify your connection.`
      });
    }
  },

  showRuleDialog({ ruleId, ruleName, isApplied, message }) {
    const dialog = document.getElementById('rule-action-dialog');
    if (!dialog) {
      alert(message);
      return;
    }

    const titleEl = document.getElementById('rule-dialog-title');
    const msgEl = document.getElementById('rule-dialog-message');
    const badgeEl = document.getElementById('rule-dialog-badge');
    const iconWrap = document.getElementById('rule-dialog-icon-wrap');
    const iconApplied = document.getElementById('rule-dialog-icon-applied');
    const iconOff = document.getElementById('rule-dialog-icon-off');

    if (titleEl) {
      titleEl.textContent = isApplied ? 'Recommendation Applied' : 'Rule Deactivated';
    }

    if (msgEl) {
      msgEl.textContent = message;
    }

    if (badgeEl) {
      badgeEl.className = isApplied ? 'badge badge-success' : 'badge badge-neutral';
      badgeEl.textContent = isApplied ? 'RULE ACTIVE' : 'RULE INACTIVE';
    }

    if (iconWrap && iconApplied && iconOff) {
      if (isApplied) {
        iconWrap.style.background = '#ecfdf3';
        iconWrap.style.color = '#027a48';
        iconApplied.style.display = 'block';
        iconOff.style.display = 'none';
      } else {
        iconWrap.style.background = '#fffaeb';
        iconWrap.style.color = '#b54708';
        iconApplied.style.display = 'none';
        iconOff.style.display = 'block';
      }
    }

    dialog.classList.add('active');

    const closeDialog = () => {
      dialog.classList.remove('active');
    };

    const closeBtn = document.getElementById('btn-close-rule-dialog');
    const dismissBtn = document.getElementById('btn-rule-dialog-dismiss');
    const viewRulesBtn = document.getElementById('btn-rule-dialog-view-rules');

    if (closeBtn) closeBtn.onclick = closeDialog;
    if (dismissBtn) dismissBtn.onclick = closeDialog;
    dialog.onclick = (e) => {
      if (e.target === dialog) closeDialog();
    };

    if (viewRulesBtn) {
      viewRulesBtn.onclick = () => {
        closeDialog();
        if (window.switchView) {
          window.switchView('rules');
        }
      };
    }
  }
};

window.AIInsights = AIInsights;
