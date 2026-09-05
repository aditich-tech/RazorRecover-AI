/**
 * RazorRecover AI - Numbers & Trends (Analytics) Controller (High-DPI Sharp Responsive Charts)
 */
const Analytics = {
  cachedData: null,
  resizeAttached: false,

  init() {
    this.setupResizeListener();
    this.loadTrends();
  },

  setupResizeListener() {
    if (this.resizeAttached) return;
    this.resizeAttached = true;
    let resizeTimer;

    const debouncedRender = () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        const trendsView = document.getElementById('view-trends');
        if (trendsView && trendsView.style.display !== 'none' && this.cachedData) {
          this.renderTrendChart(this.cachedData.trend_data);
          this.renderHourChart(this.cachedData.by_hour);
        }
      }, 80);
    };

    window.addEventListener('resize', debouncedRender);

    if (window.ResizeObserver) {
      const trendCanvas = document.getElementById('chart-trend-canvas');
      if (trendCanvas && trendCanvas.parentElement) {
        new ResizeObserver(debouncedRender).observe(trendCanvas.parentElement);
      }
    }
  },

  renderAll(data) {
    if (!data) return;
    const monthRecoveredEl = document.getElementById('analytics-this-month-recovered');
    const monthGrowthEl = document.getElementById('analytics-growth-badge');

    if (monthRecoveredEl) monthRecoveredEl.textContent = API.formatCurrency(data.this_month_recovered);
    if (monthGrowthEl) {
      monthGrowthEl.textContent = `+${data.growth_vs_previous_month}% vs previous month`;
    }

    // Update KPIs
    const kpis = data.kpis;
    const recRevEl = document.getElementById('analytics-kpi-recovered-rev');
    const lostRevEl = document.getElementById('analytics-kpi-lost-rev');
    const recRateEl = document.getElementById('analytics-kpi-recovery-rate');
    const failVolEl = document.getElementById('analytics-kpi-failed-vol');

    if (recRevEl) recRevEl.textContent = API.formatCurrency(kpis.revenue_recovered);
    if (lostRevEl) lostRevEl.textContent = API.formatCurrency(kpis.revenue_lost);
    if (recRateEl) recRateEl.textContent = `${kpis.recovery_rate}%`;
    if (failVolEl) failVolEl.textContent = API.formatNumber(kpis.failed_payment_volume);

    // Render Sharp Charts
    this.renderTrendChart(data.trend_data);
    this.renderMethodChart(data.by_method);
    this.renderReasonChart(data.by_reason);
    this.renderHourChart(data.by_hour);
  },

  async loadTrends() {
    // If cached data exists, render immediately to avoid waiting
    if (this.cachedData) {
      this.renderAll(this.cachedData);
    } else {
      const kpiEls = [
        document.getElementById('analytics-kpi-recovered-rev'),
        document.getElementById('analytics-kpi-lost-rev'),
        document.getElementById('analytics-kpi-recovery-rate'),
        document.getElementById('analytics-kpi-failed-vol'),
        document.getElementById('analytics-this-month-recovered')
      ].filter(Boolean);
      kpiEls.forEach(el => el.classList.add('skeleton-text'));
    }

    try {
      const data = await API.get('/api/analytics/trends');
      if (!data) return;
      this.cachedData = data;
      this.renderAll(data);
    } catch (err) {
      console.error('Failed to load analytics trends:', err);
    } finally {
      const kpiEls = [
        document.getElementById('analytics-kpi-recovered-rev'),
        document.getElementById('analytics-kpi-lost-rev'),
        document.getElementById('analytics-kpi-recovery-rate'),
        document.getElementById('analytics-kpi-failed-vol'),
        document.getElementById('analytics-this-month-recovered')
      ].filter(Boolean);
      kpiEls.forEach(el => el.classList.remove('skeleton-text'));
    }
  },

  // 1. Weekly Recovery Progress Trend Graph (High-DPI Sharp Responsive Canvas)
  renderTrendChart(trendData) {
    const canvas = document.getElementById('chart-trend-canvas');
    if (!canvas || !trendData || trendData.length === 0) return;

    const parentW = canvas.parentElement ? canvas.parentElement.clientWidth : 600;
    const width = Math.max(320, parentW);
    const height = 240;
    const dpr = window.devicePixelRatio || 1;

    // Retina / High-DPI crisp buffer
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';

    const ctx = canvas.getContext('2d');
    ctx.resetTransform ? ctx.resetTransform() : ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    const padding = { top: 20, right: 30, bottom: 32, left: 60 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    const maxVal = Math.max(...trendData.map(d => Math.max(d.recovered_revenue, d.lost_revenue)), 100000);

    // Draw grid lines
    ctx.strokeStyle = '#eaecf0';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padding.top + (chartH / 4) * i;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      // Y-Axis Label
      const val = maxVal - (maxVal / 4) * i;
      ctx.fillStyle = '#64748b';
      ctx.font = '500 11px Inter, sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(API.formatLakhs(val), padding.left - 10, y + 3.5);
    }

    const stepX = chartW / (trendData.length - 1 || 1);

    // Draw week period labels on X-axis
    ctx.fillStyle = '#64748b';
    ctx.font = '500 10.5px Inter, sans-serif';
    ctx.textAlign = 'center';
    trendData.forEach((d, idx) => {
      if (idx % 2 === 0 || idx === trendData.length - 1) {
        const x = padding.left + idx * stepX;
        const shortWeek = d.week_period ? d.week_period.split('-')[1] || d.week_period : `W${idx+1}`;
        ctx.fillText(shortWeek, x, height - 10);
      }
    });

    // Helper to draw smooth line
    const drawLine = (dataKey, strokeColor, fillColor) => {
      ctx.beginPath();
      trendData.forEach((d, idx) => {
        const x = padding.left + idx * stepX;
        const y = padding.top + chartH - (d[dataKey] / maxVal) * chartH;
        if (idx === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });

      // Fill area under curve
      ctx.lineTo(padding.left + (trendData.length - 1) * stepX, padding.top + chartH);
      ctx.lineTo(padding.left, padding.top + chartH);
      ctx.closePath();
      ctx.fillStyle = fillColor;
      ctx.fill();

      // Stroke line
      ctx.beginPath();
      trendData.forEach((d, idx) => {
        const x = padding.left + idx * stepX;
        const y = padding.top + chartH - (d[dataKey] / maxVal) * chartH;
        if (idx === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = 2.5;
      ctx.stroke();

      // Sharp Points
      trendData.forEach((d, idx) => {
        const x = padding.left + idx * stepX;
        const y = padding.top + chartH - (d[dataKey] / maxVal) * chartH;
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fillStyle = strokeColor;
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = '#ffffff';
        ctx.stroke();
      });
    };

    drawLine('lost_revenue', '#b42318', 'rgba(180, 35, 24, 0.05)');
    drawLine('recovered_revenue', '#027a48', 'rgba(2, 122, 72, 0.08)');
  },

  // 2. Recovery by Payment Method (Horizontal Bars)
  renderMethodChart(methods) {
    const container = document.getElementById('chart-method-list');
    if (!container || !methods) return;

    const maxAmt = Math.max(...methods.map(m => m.recovered_amount), 1);

    container.innerHTML = methods.map(m => {
      const pct = Math.round((m.recovered_amount / maxAmt) * 100);
      const successPct = m.total_attempts > 0 ? Math.round((m.recovered_attempts / m.total_attempts) * 100) : 0;

      return `
        <div style="margin-bottom: 14px;">
          <div style="display: flex; justify-content: space-between; font-size: 12.5px; margin-bottom: 6px;">
            <span style="font-weight: 600; color: #101828;">${m.payment_method}</span>
            <span style="color: #027a48; font-weight: 600;">
              ${API.formatCurrency(m.recovered_amount)} (${successPct}% recovered)
            </span>
          </div>
          <div style="width: 100%; height: 8px; background: #f2f4f7; border-radius: 4px; overflow: hidden;">
            <div style="width: ${pct}%; height: 100%; background: linear-gradient(90deg, #0052ff, #027a48); border-radius: 4px;"></div>
          </div>
        </div>
      `;
    }).join('');
  },

  // 3. Recovery by Failure Reason
  renderReasonChart(reasons) {
    const container = document.getElementById('chart-reason-list');
    if (!container || !reasons) return;

    const maxAmt = Math.max(...reasons.map(r => r.recovered_amount), 1);

    container.innerHTML = reasons.slice(0, 6).map(r => {
      const pct = Math.round((r.recovered_amount / maxAmt) * 100);
      return `
        <div style="margin-bottom: 12px;">
          <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
            <span style="color: #475467;">${r.failure_reason}</span>
            <span style="color: #0052ff; font-weight: 600;">${API.formatCurrency(r.recovered_amount)}</span>
          </div>
          <div style="width: 100%; height: 6px; background: #f2f4f7; border-radius: 3px; overflow: hidden;">
            <div style="width: ${pct}%; height: 100%; background: #0052ff; border-radius: 3px;"></div>
          </div>
        </div>
      `;
    }).join('');
  },

  // 4. Best-Performing Retry Time (High-DPI Sharp Responsive Hourly Distribution)
  renderHourChart(hours) {
    const canvas = document.getElementById('chart-hour-canvas');
    if (!canvas || !hours || hours.length === 0) return;

    const parentW = canvas.parentElement ? canvas.parentElement.clientWidth : 320;
    const width = Math.max(280, parentW);
    const height = 140;
    const dpr = window.devicePixelRatio || 1;

    // Retina / High-DPI crisp buffer
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';

    const ctx = canvas.getContext('2d');
    ctx.resetTransform ? ctx.resetTransform() : ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    const maxRecovered = Math.max(...hours.map(h => h.recovered_count), 1);
    const sideMargin = 16;
    const availableW = width - (sideMargin * 2);
    const slotW = availableW / 24;
    const barWidth = Math.max(4, slotW - 3);

    hours.forEach(h => {
      const x = sideMargin + h.hour * slotW + (slotW - barWidth) / 2;
      const barH = (h.recovered_count / maxRecovered) * (height - 35);
      const y = height - 25 - barH;

      // Draw bar
      ctx.fillStyle = h.hour >= 13 && h.hour <= 15 ? '#b54708' : '#0052ff';
      ctx.beginPath();
      if (ctx.roundRect) {
        ctx.roundRect(x, y, barWidth, barH, [2, 2, 0, 0]);
      } else {
        ctx.rect(x, y, barWidth, barH);
      }
      ctx.fill();

      // X Axis Label
      if (h.hour % 4 === 0) {
        ctx.fillStyle = '#64748b';
        ctx.font = '500 10px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(`${h.hour}h`, x + barWidth / 2, height - 8);
      }
    });
  }
};

window.Analytics = Analytics;
