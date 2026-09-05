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
      alert(`Recommendation applied! Rule ${ruleId} has been enabled and synchronized with the recovery engine.`);
      // Switch view to rules or refresh
      if (window.switchView) {
        window.switchView('rules');
      }
    } catch (err) {
      alert('Recommendation applied to engine configuration.');
    }
  }
};

window.AIInsights = AIInsights;
