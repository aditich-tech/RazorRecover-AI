# RazorRecover AI — Autonomous Revenue Recovery Agent
**Razorpay Buildathon — Track 03: AI Revenue Recovery**

> *“Detect revenue at risk, determine the right intervention, and execute a bounded recovery workflow.”*

RazorRecover AI is an enterprise-grade AI Revenue Recovery web application engineered for merchants on Razorpay. It replaces static dashboards with a live, 10,000+ transaction **Supabase PostgreSQL** ledger, an explainable recovery scoring engine, configurable stopping rules, merchant approval gates, simulated bounded executions, and verifiable audit trails.

---

## 🚀 Quick Start (Supabase PostgreSQL)

RazorRecover AI is powered by **Supabase PostgreSQL**. Persistent application data is hosted in Supabase, with automatic schema initialization and migration tooling.

### 1. Install Dependencies
```bash
pip install flask psycopg2-binary python-dotenv
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and set your Supabase PostgreSQL connection string:
```env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
```
*(Or use Supabase Connection Pooler URI: `postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres`)*

#### Where to find your credentials in Supabase:
1. Log in to [Supabase](https://supabase.com).
2. Open your project &rarr; **Project Settings** (gear icon) &rarr; **Database**.
3. Under **Connection string**, select **URI** (or **Pooler** URI).
4. Copy the URI and replace `[YOUR-PASSWORD]` with your actual database password.

### 3. Migrate Existing Data (SQLite → Supabase PostgreSQL)
To migrate all 10,500 transactions, 6 recovery rules, audit logs, and demo user from the local SQLite database into Supabase:
```bash
python database/migrate_sqlite_to_pg.py
```

*Alternatively, to generate and seed fresh 10,500 records directly into Supabase:*
```bash
python database/seeder.py
```

### 4. Run the Application
```bash
python app.py
```

### 5. Open in Browser
Navigate to:
```
http://127.0.0.1:5000/
```

### Demo Login Credentials
- **Instant Login**: Click the green **"Instant Merchant Demo Access"** button on the `/login` page.
- **Manual Credentials**:
  - Email: `merchant@razorpay.com`
  - Password: `demo123`

---

## 🎯 Track 03 Requirements & Key Features

| Requirement | Implementation in RazorRecover AI |
|---|---|
| **Supabase PostgreSQL Database** | Modular database layer in `database/db.py` powered by Supabase PostgreSQL via `psycopg2` with automatic connection pooling and SQL abstraction. |
| **10,000+ Realistic Dataset** | 10,500 realistic records spanning 750 unique customers over 90 days with multi-attempt customer histories. |
| **Zero Hardcoded Numbers** | All KPIs (Potential Loss, Recovered Revenue, Recovery Rate, Risk Level) are aggregated live via SQL queries against Supabase PostgreSQL. |
| **Explainable AI Scoring** | `engine/recovery_engine.py` evaluates customer historical success rate, failure reason category, payment method, retry decay, and transaction amount to output confidence percentages and human-readable rationale. |
| **Dedicated Recovery Analysis** | Clicking **"Start Recovery"** triggers an AI scanning radar animation, followed by a failure reason breakdown table and action recommendations. |
| **Merchant Approval Flow** | Explicit **"Approve Recovery"** CTA before executing bounded workflows against the database. |
| **Stopping Rules & Guardrails** | `engine/stopping_rules.py` halts endless retries when retry ceiling (3 attempts) or minimum probability (25%) thresholds are hit. |
| **Verified Audit Trail** | Every single action (`AI_IDENTIFIED`, `RECOMMENDED_ACTION`, `MERCHANT_APPROVED`, `WORKFLOW_EXECUTED`, `PAYMENT_RECOVERED`, `STOPPING_RULE_APPLIED`) is logged with exact timestamps in Supabase `audit_logs` table. |
| **Before / After Financial Impact** | Visual transformation card on the dashboard showing before vs. after metrics and recovery rates. |
| **Scalable Customers Table** | Customer-level aggregation table with search, pagination, and sorting (default: highest transaction volume first). Clicking any row opens a Customer Profile drawer with payment history and tailored AI insights. |
| **Recovery Rules Management** | Toggleable rules (Smart Retry, Intelligent UPI Timing, High-Value Payment Guard, Stopping Rules, Trust Customers) that dynamically control the recovery engine. |
| **Numbers & Trends** | Analytics dashboard with dynamic Canvas charts: weekly recovery progress, recovery by method, failure reason distribution, and best retry hour. |
| **AI Analyst Insights** | Proactive machine learning insights (UPI peak PSP congestion, retry #2 sweet spots, high-value recovery) with 1-click **"Apply Recommendation"** triggers. |
| **Demo Data Transparency** | Subtly labeled in top banners and footer as: `Demo environment · Synthetic transaction dataset`. |
| **Session Security & Logout** | Working session authentication with a prominent **Logout** button that terminates the session and protects dashboard routes. |

---

## 🧪 Running Automated Tests

Run the engine test suite:
```bash
python tests/test_engine.py
```

Run the complete 16-point end-to-end verification suite:
```bash
python tests/verify_app.py
```

---

## 📁 Repository Structure

```
RazorRecover AI/
├── app.py                             # Main Flask web server & REST endpoints
├── config.py                          # Supabase PostgreSQL configuration & env loader
├── .env.example                       # Environment variables template
├── README.md                          # Project documentation & setup guide
├── database/
│   ├── db.py                          # Supabase PostgreSQL connection & query helpers
│   ├── schema_pg.sql                  # PostgreSQL schema (transactions, rules, audit, users)
│   ├── migrate_sqlite_to_pg.py        # Streamed data migration from SQLite to Supabase
│   └── seeder.py                      # 10,500 transaction records synthesizer for Supabase
├── engine/
│   ├── recovery_engine.py             # AI recovery probability scoring & explainability
│   ├── stopping_rules.py              # Bounded stopping rules (max retries, min prob, trust rules)
│   └── workflow_executor.py           # Transactional recovery execution & audit logging
├── static/
│   ├── css/
│   │   ├── style.css                  # Design tokens, typography, buttons, tables
│   │   └── dashboard.css              # Dashboard layout, radar animations, drawers, charts
│   └── js/
│       ├── api.js                     # Fetch wrapper & INR currency formatting
│       ├── auth.js                    # Authentication & session handlers
│       ├── dashboard.js               # Live KPI & impact transformation controller
│       ├── recovery_modal.js          # Dedicated AI analysis, scanning radar, and approval flow
│       ├── customers.js               # Customer table, search, sort, and detail drawer
│       ├── rules.js                   # Recovery rules toggles and creation modal
│       ├── analytics.js               # Numbers & Trends Canvas charts
│       ├── insights.js                # AI Analyst insights & recommendation triggers
│       └── landing.js                 # Landing page interactions & preview modal
├── templates/
│   ├── index.html                     # Homepage / Landing page
│   ├── auth.html                      # Merchant Login / Signup
│   └── app.html                       # Enterprise Single-Page Application
└── tests/
    ├── test_engine.py                 # Unit tests for scoring, rules, and aggregations
    ├── test_recovery_history.py       # Tests for dynamic recovery decision history
    ├── test_trust_rule.py             # Tests for Trust Customers recovery rule
    └── verify_app.py                  # 16-point automated end-to-end verification suite
```
