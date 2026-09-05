/**
 * RazorRecover AI - Customers Scalable Table & Detail Drawer Controller (Clean Light Theme)
 */
const Customers = {
  currentPage: 1,
  currentSort: 'total_transactions',
  currentOrder: 'DESC',
  searchQuery: '',
  limit: 15,

  init() {
    this.setupSearch();
    this.setupSorting();
    this.setupPagination();
    this.loadCustomers();
    this.setupDrawerClose();
  },

  async loadCustomers() {
    const tableBody = document.getElementById('customers-table-body');
    const pageInfo = document.getElementById('customers-page-info');
    if (!tableBody) return;

    tableBody.innerHTML = `
      <tr>
        <td colspan="8" style="text-align: center; padding: 32px; color: #64748b;">
          Loading aggregated customer accounts...
        </td>
      </tr>
    `;

    try {
      const url = `/api/customers?page=${this.currentPage}&limit=${this.limit}&sort=${this.currentSort}&order=${this.currentOrder}&search=${encodeURIComponent(this.searchQuery)}`;
      const data = await API.get(url);
      if (!data) return;

      if (data.customers.length === 0) {
        tableBody.innerHTML = `
          <tr>
            <td colspan="8" style="text-align: center; padding: 32px; color: #64748b;">
              No customers found matching "${this.searchQuery}".
            </td>
          </tr>
        `;
        if (pageInfo) pageInfo.textContent = 'Page 0 of 0';
        return;
      }

      tableBody.innerHTML = data.customers.map(c => `
        <tr style="cursor: pointer;" onclick="Customers.openCustomerDetail('${c.customer_id}')">
          <td>
            <div style="font-weight: 600; color: #101828;">${c.customer_name}</div>
            <div style="font-size: 11.5px; color: #64748b; font-family: var(--font-mono);">${c.customer_id}</div>
          </td>
          <td style="font-weight: 700; color: #0052ff; text-align: center;">
            ${c.total_transactions}
          </td>
          <td style="color: #027a48; text-align: center; font-weight: 600;">${c.successful_count}</td>
          <td style="color: #b42318; text-align: center; font-weight: 600;">${c.failed_count}</td>
          <td style="color: #0052ff; font-weight: 600; text-align: center;">${c.recovered_count}</td>
          <td style="color: #b54708; text-align: center; font-weight: 600;">${c.pending_count}</td>
          <td style="color: #64748b; text-align: center;">${c.abandoned_count}</td>
          <td style="text-align: right; font-family: var(--font-mono); font-weight: 700; color: #101828;">
            ${API.formatCurrency(c.total_volume)}
          </td>
        </tr>
      `).join('');

      if (pageInfo) {
        pageInfo.textContent = `Page ${data.page} of ${data.total_pages} (${API.formatNumber(data.total)} total customers)`;
      }

      // Update button states
      const prevBtn = document.getElementById('btn-prev-customers');
      const nextBtn = document.getElementById('btn-next-customers');
      if (prevBtn) prevBtn.disabled = data.page <= 1;
      if (nextBtn) nextBtn.disabled = data.page >= data.total_pages;

    } catch (err) {
      tableBody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: #b42318; padding: 24px;">Failed to load customers.</td></tr>`;
    }
  },

  setupSearch() {
    const searchInput = document.getElementById('customers-search-input');
    if (!searchInput) return;

    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        this.searchQuery = e.target.value.trim();
        this.currentPage = 1;
        this.loadCustomers();
      }, 300);
    });
  },

  setupSorting() {
    const headers = document.querySelectorAll('th.sortable-customer');
    headers.forEach(th => {
      th.addEventListener('click', () => {
        const sortField = th.getAttribute('data-sort');
        if (this.currentSort === sortField) {
          this.currentOrder = this.currentOrder === 'ASC' ? 'DESC' : 'ASC';
        } else {
          this.currentSort = sortField;
          this.currentOrder = 'DESC';
        }
        this.loadCustomers();
      });
    });
  },

  setupPagination() {
    const prevBtn = document.getElementById('btn-prev-customers');
    const nextBtn = document.getElementById('btn-next-customers');

    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        if (this.currentPage > 1) {
          this.currentPage--;
          this.loadCustomers();
        }
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        this.currentPage++;
        this.loadCustomers();
      });
    }
  },

  setupDrawerClose() {
    const closeBtn = document.getElementById('btn-close-customer-drawer');
    const overlay = document.getElementById('customer-drawer-overlay');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.closeDrawer());
    }
    if (overlay) {
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) this.closeDrawer();
      });
    }
  },

  closeDrawer() {
    const overlay = document.getElementById('customer-drawer-overlay');
    if (overlay) overlay.classList.remove('active');
  },

  async openCustomerDetail(customerId) {
    const overlay = document.getElementById('customer-drawer-overlay');
    const drawerBody = document.getElementById('customer-drawer-body');
    const drawerName = document.getElementById('customer-drawer-name');
    const drawerEmail = document.getElementById('customer-drawer-email');

    if (!overlay || !drawerBody) return;

    overlay.classList.add('active');
    drawerBody.innerHTML = '<div style="text-align: center; padding: 40px; color: #64748b;">Loading customer profile...</div>';

    try {
      const data = await API.get(`/api/customers/${customerId}`);
      if (!data) return;

      const cust = data.customer;
      if (drawerName) drawerName.textContent = cust.name;
      if (drawerEmail) drawerEmail.textContent = `${cust.email} · ${cust.customer_id}`;

      // Build Payment History List
      const historyHtml = data.history.map(item => {
        let badgeClass = 'badge-neutral';
        let icon = '✓';
        let iconClass = 'success';

        if (item.status === 'success') {
          badgeClass = 'badge-success';
          icon = '✓';
          iconClass = 'success';
        } else if (item.status === 'recovered') {
          badgeClass = 'badge-info';
          icon = '✓';
          iconClass = 'success';
        } else {
          badgeClass = 'badge-danger';
          icon = '✕';
          iconClass = 'failed';
        }

        return `
          <div class="history-item">
            <div class="history-item-left">
              <span class="history-icon ${iconClass}">${icon}</span>
              <div>
                <div style="font-weight: 600; color: #101828;">${API.formatCurrency(item.amount)} — ${item.status_display}</div>
                <div style="font-size: 11.5px; color: #64748b;">${item.timestamp} · ${item.payment_method} ${item.failure_reason ? `(${item.failure_reason})` : ''}</div>
              </div>
            </div>
            <div style="text-align: right;">
              <span class="badge ${badgeClass}">${item.status.toUpperCase()}</span>
            </div>
          </div>
        `;
      }).join('');

      drawerBody.innerHTML = `
        <!-- Top Metrics Cards -->
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">
          <div class="card" style="padding: 14px; background: #ffffff;">
            <div style="font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600;">Total Paid</div>
            <div style="font-family: var(--font-heading); font-size: 18px; font-weight: 700; color: #027a48; margin-top: 4px;">
              ${API.formatCurrency(cust.total_paid)}
            </div>
          </div>
          <div class="card" style="padding: 14px; background: #ffffff;">
            <div style="font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600;">Total Txns</div>
            <div style="font-family: var(--font-heading); font-size: 18px; font-weight: 700; color: #101828; margin-top: 4px;">
              ${cust.total_transactions}
            </div>
          </div>
          <div class="card" style="padding: 14px; background: #ffffff;">
            <div style="font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600;">Recovery Rate</div>
            <div style="font-family: var(--font-heading); font-size: 18px; font-weight: 700; color: #0052ff; margin-top: 4px;">
              ${cust.recovery_rate}%
            </div>
          </div>
        </div>

        <!-- Customer AI Insight -->
        <div class="ai-insight-box">
          <div class="ai-insight-title">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#026aa2" stroke-width="2.5">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
            </svg>
            AI Customer Behavioral Insight
          </div>
          <p class="ai-insight-text">
            ${data.ai_insight.summary}
          </p>
          <div style="margin-top: 6px; padding-top: 8px; border-top: 1px solid #b9e6fe; font-size: 12px; color: #026aa2; display: flex; justify-content: space-between;">
            <span><strong>Recommended:</strong> ${data.ai_insight.recovery_recommendation}</span>
            <span class="badge ${data.ai_insight.recovery_probability_tier === 'High' ? 'badge-success' : 'badge-warning'}">
              ${data.ai_insight.recovery_probability_tier} Potential
            </span>
          </div>
        </div>

        <!-- Payment History Timeline -->
        <div>
          <h4 style="font-size: 14px; font-weight: 600; color: #101828; margin-bottom: 12px;">
            Payment History (${data.history.length} records)
          </h4>
          <div class="history-timeline">
            ${historyHtml}
          </div>
        </div>
      `;

    } catch (err) {
      drawerBody.innerHTML = '<div style="color: #b42318; padding: 20px;">Failed to load customer profile.</div>';
    }
  }
};

window.Customers = Customers;
