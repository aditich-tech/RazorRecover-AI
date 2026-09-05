/**
 * RazorRecover AI - Central API Client
 */
const API = {
  async get(endpoint) {
    try {
      const res = await fetch(endpoint, {
        headers: { 'Accept': 'application/json' }
      });
      if (res.status === 401 && !endpoint.includes('/auth/')) {
        window.location.href = '/login';
        return null;
      }
      return await res.json();
    } catch (err) {
      console.error(`API GET error on ${endpoint}:`, err);
      throw err;
    }
  },

  async post(endpoint, body = {}) {
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(body)
      });
      if (res.status === 401 && !endpoint.includes('/auth/')) {
        window.location.href = '/login';
        return null;
      }
      return await res.json();
    } catch (err) {
      console.error(`API POST error on ${endpoint}:`, err);
      throw err;
    }
  },

  // Number formatting utilities for Indian Currency (INR)
  formatCurrency(amount) {
    if (amount === undefined || amount === null) return '₹0';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount);
  },

  formatLakhs(amount) {
    if (!amount) return '₹0';
    if (amount >= 10000000) {
      return `₹${(amount / 10000000).toFixed(2)} Cr`;
    }
    if (amount >= 100000) {
      return `₹${(amount / 100000).toFixed(2)} L`;
    }
    return API.formatCurrency(amount);
  },

  formatNumber(num) {
    if (num === undefined || num === null) return '0';
    return new Intl.NumberFormat('en-IN').format(num);
  }
};
