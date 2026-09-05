/**
 * RazorRecover AI - Recovery Rules Controller
 */
const RecoveryRules = {
  rules: [],

  init() {
    this.loadRules();
    this.setupCreateModal();
  },

  async loadRules() {
    const container = document.getElementById('rules-list-container');
    if (!container) return;

    try {
      const data = await API.get('/api/rules');
      if (!data || !data.rules) return;
      this.rules = data.rules;

      container.innerHTML = data.rules.map(rule => `
        <div class="card" style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: flex-start; gap: 20px;">
          <div style="flex: 1;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
              <h3 style="font-size: 16px; font-weight: 700; color: #101828;">${rule.rule_name}</h3>
              <span class="badge ${rule.is_active ? 'badge-success' : 'badge-neutral'}">
                ${rule.is_active ? 'ACTIVE' : 'INACTIVE'}
              </span>
              <span class="badge badge-info">${rule.rule_type.replace(/_/g, ' ').toUpperCase()}</span>
            </div>
            <p style="font-size: 13px; color: #475467; line-height: 1.5; max-width: 800px;">
              ${rule.description}
            </p>
            <div style="margin-top: 10px; display: flex; gap: 14px; font-size: 11.5px; color: #64748b;">
              <span><strong>Action:</strong> ${rule.action_type}</span>
              <span><strong>Rule ID:</strong> ${rule.rule_id}</span>
            </div>
          </div>

          <!-- Controls -->
          <div style="display: flex; align-items: center; gap: 14px;">
            <label class="toggle-switch" title="Toggle active status">
              <input type="checkbox" ${rule.is_active ? 'checked' : ''} onchange="RecoveryRules.toggleRule('${rule.rule_id}')">
              <span class="toggle-slider"></span>
            </label>
            <button class="btn btn-secondary btn-sm" onclick="RecoveryRules.showRuleInfo('${rule.rule_id}')">
              Info
            </button>
          </div>
        </div>
      `).join('');
    } catch (err) {
      container.innerHTML = '<div style="color: #ef4444;">Failed to load rules.</div>';
    }
  },

  showRuleInfo(ruleId) {
    const rule = (this.rules || []).find(r => r.rule_id === ruleId);
    if (rule) {
      alert('Rule Details:\n' + JSON.stringify(rule, null, 2));
    }
  },

  async toggleRule(ruleId) {
    try {
      const res = await API.post(`/api/rules/${ruleId}/toggle`);
      if (res.success) {
        this.loadRules();
        if (window.RecoveryHistory) {
          window.RecoveryHistory.loadHistory();
        }
      }
    } catch (err) {
      alert('Failed to update rule status.');
    }
  },

  setupCreateModal() {
    const openBtn = document.getElementById('btn-open-create-rule-modal');
    const closeBtn = document.getElementById('btn-close-create-rule-modal');
    const modal = document.getElementById('create-rule-modal');
    const form = document.getElementById('create-rule-form');

    if (openBtn && modal) {
      openBtn.addEventListener('click', () => modal.classList.add('active'));
    }
    if (closeBtn && modal) {
      closeBtn.addEventListener('click', () => modal.classList.remove('active'));
    }
    if (form && modal) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const rule_name = document.getElementById('rule-name-input').value;
        const description = document.getElementById('rule-desc-input').value;
        const rule_type = document.getElementById('rule-type-select').value;
        const action_type = document.getElementById('rule-action-select').value;

        try {
          const res = await API.post('/api/rules', {
            rule_name,
            description,
            rule_type,
            action_type,
            condition_json: '{}'
          });
          if (res.success) {
            modal.classList.remove('active');
            form.reset();
            this.loadRules();
            if (window.RecoveryHistory) {
              window.RecoveryHistory.loadHistory();
            }
          }
        } catch (err) {
          alert('Failed to create rule.');
        }
      });
    }
  }
};

window.RecoveryRules = RecoveryRules;
