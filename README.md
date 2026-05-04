# Loan Data Quality Control & Monitoring System

## 🚀 Project Value

This project simulates a **production-grade data quality control and risk monitoring system** for financial loan operations, focusing on ensuring data integrity at the point of ingestion and throughout downstream processing.

It addresses a critical real-world problem:

> In financial systems, **bad data is more expensive to fix downstream than to block at ingestion.**

This system demonstrates how to **prevent, detect, monitor, and analyze** data quality issues before they impact financial reporting, risk models, and regulatory outputs.

---

## 🎯 Business Impact

This solution is designed to:

* Block invalid loan records before they corrupt core financial systems
* Detect duplicate transactions that cause double-counting in portfolio balances
* Enforce regulatory-aligned business rules (e.g., interest rate caps under U.S. lending law)
* Score and stratify portfolio risk by loan characteristics, region, and source system
* Generate automated monthly reports with business-ready interpretation and recommended actions

---

## 🧠 What This Project Demonstrates

* End-to-end data pipeline design
* Financial data modeling (loan transactions, repayment schedules, double-entry accounting)
* Data quality control — two-tier validation (hard reject + soft warning)
* SQL schema design with constraints, indexes, and audit-ready validation queries
* Exploratory data analysis — portfolio distribution, regional exposure, repayment behavior
* Credit risk modeling — logistic regression scorecard using origination-time features (no data leakage), with ROC curve, feature coefficients, risk grade assignment, and model calibration
* Business storytelling — every output includes interpretation, not just numbers

---

## 🏗️ System Overview

The system is structured around a three-layer architecture:

### 1. Data Ingestion Control (Pre-validation)

Incoming data is validated using:

* Strong validation rules (reject invalid records)
* Soft validation rules (flag warnings)
* Duplicate detection (batch-level + historical)

### 2. Data Quality Monitoring (Post-validation)

Validated data is monitored through:

* Quality metrics (acceptance rate, rejection rate, error distribution)
* Issue classification by rule type, field, and error code
* Automated monthly report with executive summary and recommended actions

### 3. Portfolio Risk Analysis (Notebooks)

Accepted loan data is analyzed through:

* EDA covering loan amount, interest rate, term, and regional distribution
* Origination-based risk scoring across four factors: rate, size, term, source system
* Risk grade assignment (A–D) with portfolio exposure breakdown

---

## 🔄 End-to-End Workflow

```text
Incoming Data (External / Internal)
        ↓
Validation Pipeline  →  Rejected Records + Error Log
        ↓
Accepted Data
        ↓
Monitoring & Metrics
        ↓
Monthly Data Quality Report
        ↓
EDA + Risk Scoring (Notebooks)
```

---

## 📊 Sample Output

**Monthly Data Quality Report — May 2026**

| Metric | Value |
|---|---|
| Total incoming records | 100 |
| Accepted | 90 (90.0%) |
| Rejected | 10 (10.0%) |
| Data Quality Score | **92.9 / 100** |

Top issues flagged: duplicate disbursement IDs, missing required fields, invalid interest rates — each linked to a concrete business risk in the full report.

---

## 🗂️ Project Structure

```text
src/          core data pipeline logic
notebooks/    EDA and portfolio risk analysis
data/         raw / incoming / accepted / rejected
docs/         system design, business context & data dictionary
reports/      generated quality reports and risk-scored portfolio output
sql/          full DDL schema and validation rule queries
```

---

## 👤 Author

**Chaoda Jiang**
MS in Business Analytics, UC San Diego

---

## 💡 Key Takeaway

This project reflects how modern data teams operate in financial services:

> Move from "fixing bad data" to **preventing bad data from entering the system in the first place** — and from reporting numbers to **turning data into risk decisions.**
