/**
 * RazorRecover AI - Recovery History Controller (Clean Light Theme)
 * Real-time transaction history with AI Decision Explainability (Why?)
 */
const RecoveryHistory = {
  currentPage: 1,
  currentFilter: 'all',
  searchQuery: '',
  limit: 15,
  itemsMap: {},

  init() {
    this.setupFilters();
    this.setupSearch();
    this.setupPagination();
    this.setupModalClose();
  },

  setupFilters() {
    const filterBtns = document.querySelectorAll('.history-filter-btn');
    filterBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentFilter = btn.getAttribute('data-filter') || 'all';
        this.currentPage = 1;
        this.loadHistory();
      });
    });
  },

  setupSearch() {
    const searchInput = document.getElementById('history-search-input');
    if (!searchInput) return;

    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        this.searchQuery = e.target.value.trim();
        this.currentPage = 1;
        this.loadHistory();
      }, 250);
    });
  },

  setupPagination() {
    const prevBtn = document.getElementById('btn-prev-history');
    const nextBtn = document.getElementById('btn-next-history');

    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        if (this.currentPage > 1) {
          this.currentPage--;
          this.loadHistory();
        }
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        this.currentPage++;
        this.loadHistory();
      });
    }
  },

  setupModalClose() {
    const modal = document.getElementById('recovery-reasoning-modal');
    const closeBtn = document.getElementById('btn-close-reasoning-modal');
    if (closeBtn && modal) {
      closeBtn.addEventListener('click', () => {
        modal.classList.remove('active');
      });
    }
    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          modal.classList.remove('active');
        }
      });
    }
  },

  async loadHistory() {
    const tableBody = document.getElementById('history-table-body');
    const pageInfo = document.getElementById('history-page-info');
    if (!tableBody) return;

    tableBody.innerHTML = `
      <tr>
        <td colspan="9" style="text-align: center; padding: 32px; color: #64748b;">
          Loading AI recovery history...
        </td>
      </tr>
    `;

    try {
      const url = `/api/recovery/history?filter=${this.currentFilter}&search=${encodeURIComponent(this.searchQuery)}&page=${this.currentPage}&limit=${this.limit}`;
      const data = await API.get(url);
      if (!data) return;

      // Update Summary Cards at Top
      this.updateSummary(data.summary);

      // Cache items for the "Why?" popup
      this.itemsMap = {};
      data.history.forEach(item => {
        this.itemsMap[item.transaction_id] = item;
      });

      if (data.history.length === 0) {
        tableBody.innerHTML = `
          <tr>
            <td colspan="9" style="text-align: center; padding: 36px; color: #64748b;">
              No transactions found matching "${this.searchQuery || this.currentFilter}".
            </td>
          </tr>
        `;
        if (pageInfo) pageInfo.textContent = 'Page 0 of 0';
        return;
      }

      tableBody.innerHTML = data.history.map(item => {
        // AI Action Badge
        let actionBadgeClass = 'badge-info';
        if (item.ai_action === 'Resolve') actionBadgeClass = 'badge-success';
        else if (item.ai_action === 'Skip') actionBadgeClass = 'badge-neutral';

        // Status Badge
        let statusBadgeClass = 'badge-info';
        if (item.status === 'Recovered') statusBadgeClass = 'badge-success';
        else if (item.status === 'Skipped') statusBadgeClass = 'badge-warning';
        else if (item.status === 'Failed') statusBadgeClass = 'badge-danger';

        // Customer Success Rate Color
        const sr = item.customer_success_rate;
        let srColor = '#027a48';
        if (sr < 60) srColor = '#b42318';
        else if (sr < 75) srColor = '#b54708';

        return `
          <tr>
            <td>
              <span style="font-family: var(--font-mono); font-size: 12px; color: #0052ff; font-weight: 600;">
                ${item.transaction_id}
              </span>
            </td>
            <td>
              <div style="font-weight: 600; color: #101828;">${item.customer_name}</div>
              <div style="font-size: 11px; color: #64748b; font-family: var(--font-mono);">${item.customer_id}</div>
            </td>
            <td style="font-family: var(--font-mono); font-weight: 700; color: #101828;">
              ${API.formatCurrency(item.amount)}
            </td>
            <td>
              <span style="color: #475467; font-size: 12.5px;">${item.failure_reason}</span>
            </td>
            <td style="text-align: center;">
              <span style="display: inline-flex; align-items: center; gap: 4px; font-weight: 700; color: ${srColor}; font-size: 12.5px;">
                ${sr}%
              </span>
            </td>
            <td>
              <span class="badge ${actionBadgeClass}" style="font-weight: 700;">
                ${item.ai_action}
              </span>
            </td>
            <td>
              <span class="badge ${statusBadgeClass}">
                ${item.status}
              </span>
            </td>
            <td style="font-size: 11.5px; color: #64748b; font-family: var(--font-mono); white-space: nowrap;">
              ${item.timestamp}
            </td>
            <td style="text-align: center;">
              <button class="btn btn-secondary btn-xs btn-why" onclick="RecoveryHistory.openReasoningModal('${item.transaction_id}')">
                Why?
              </button>
            </td>
          </tr>
        `;
      }).join('');

      if (pageInfo) {
        pageInfo.textContent = `Page ${data.page} of ${data.total_pages} (${API.formatNumber(data.total)} records)`;
      }

      // Pagination buttons
      const prevBtn = document.getElementById('btn-prev-history');
      const nextBtn = document.getElementById('btn-next-history');
      if (prevBtn) prevBtn.disabled = data.page <= 1;
      if (nextBtn) nextBtn.disabled = data.page >= data.total_pages;

    } catch (err) {
      console.error('Failed to load recovery history:', err);
      tableBody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: #b42318; padding: 24px;">Failed to load recovery history.</td></tr>`;
    }
  },

  updateSummary(summary) {
    if (!summary) return;
    const totalEl = document.getElementById('history-stat-total');
    const recEl = document.getElementById('history-stat-recovered');
    const retEl = document.getElementById('history-stat-retried');
    const skipEl = document.getElementById('history-stat-skipped');

    if (totalEl) totalEl.textContent = API.formatNumber(summary.total_actions);
    if (recEl) recEl.textContent = API.formatNumber(summary.recovered);
    if (retEl) retEl.textContent = API.formatNumber(summary.retried);
    if (skipEl) skipEl.textContent = API.formatNumber(summary.skipped);
  },

  openReasoningModal(txnId) {
    const item = this.itemsMap[txnId];
    if (!item) return;

    const modal = document.getElementById('recovery-reasoning-modal');
    const content = document.getElementById('reasoning-modal-content');
    if (!modal || !content) return;

    // Decision badge color
    let actionBadgeClass = 'badge-info';
    if (item.ai_action === 'Resolve') actionBadgeClass = 'badge-success';
    else if (item.ai_action === 'Skip') actionBadgeClass = 'badge-neutral';

    content.innerHTML = `
      <div class="reasoning-popover-card">
        <!-- Top Decision Header -->
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid var(--border-subtle);">
          <div>
            <span style="font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px;">Transaction ${item.transaction_id}</span>
            <div style="font-family: var(--font-heading); font-size: 17px; font-weight: 700; color: #101828; margin-top: 2px;">
              AI Decision: <span class="badge ${actionBadgeClass}" style="font-size: 12px; margin-left: 6px; padding: 3px 8px;">${item.ai_action}</span>
            </div>
          </div>
          <div style="text-align: right;">
            <div style="font-size: 11px; color: #64748b;">Customer</div>
            <div style="font-size: 13px; font-weight: 600; color: #101828;">${item.customer_name}</div>
          </div>
        </div>

        <!-- Detail Attributes List -->
        <div style="display: flex; flex-direction: column; gap: 10px; font-size: 13px;">
          <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; background: #f8fafc; border: 1px solid var(--border-subtle); border-radius: var(--radius-sm);">
            <span style="color: #475467; font-weight: 500;">Customer success rate:</span>
            <span style="font-weight: 700; font-size: 14px; color: ${item.customer_success_rate >= 75 ? '#027a48' : '#b54708'};">
              ${item.customer_success_rate}%
            </span>
          </div>

          <div style="padding: 10px 14px; background: #f8fafc; border: 1px solid var(--border-subtle); border-radius: var(--radius-sm);">
            <div style="color: #64748b; font-size: 11.5px; margin-bottom: 4px;">Active recovery rule evaluated:</div>
            <div style="font-weight: 600; color: #0052ff;">
              ${item.rule_name}
            </div>
          </div>

          <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; background: #f8fafc; border: 1px solid var(--border-subtle); border-radius: var(--radius-sm);">
            <span style="color: #475467; font-weight: 500;">Rule satisfied:</span>
            <span style="font-weight: 700; display: inline-flex; align-items: center; gap: 6px; color: ${item.rule_satisfied ? '#027a48' : '#b42318'};">
              ${item.rule_satisfied ? '✓ Yes' : '✕ No'}
            </span>
          </div>

          <div style="padding: 12px 14px; background: #f8fafc; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle); border-left: 3px solid ${item.rule_satisfied ? '#027a48' : '#b54708'};">
            <div style="color: #475467; font-size: 11.5px; margin-bottom: 4px; text-transform: uppercase; font-weight: 600;">Reason:</div>
            <div style="color: #101828; line-height: 1.5; font-size: 13px;">
              ${item.reason}
            </div>
          </div>
        </div>

        <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
          <button class="btn btn-secondary btn-sm" onclick="document.getElementById('recovery-reasoning-modal').classList.remove('active')">
            Close
          </button>
        </div>
      </div>
    `;

    modal.classList.add('active');
  }
};

window.RecoveryHistory = RecoveryHistory;
