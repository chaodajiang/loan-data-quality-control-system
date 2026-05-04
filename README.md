# Loan Data Quality Control & Monitoring System

## 🚀 Project Value

This project simulates a **production-grade data quality control system** for financial loan operations, focusing on ensuring data integrity at the point of ingestion and throughout downstream processing.

It addresses a critical real-world problem:

> In financial systems, **bad data is more expensive to fix downstream than to block at ingestion**.

This system demonstrates how to **prevent, detect, and monitor data quality issues** before they impact financial reporting, risk models, and regulatory outputs.

---

## 🎯 Business Impact

This solution is designed to:

* Prevent invalid loan transactions from entering core systems
* Reduce downstream reconciliation and manual correction costs
* Improve reliability of financial reporting and KPI tracking
* Enable early detection of systemic data issues

---

## 🧠 What This Project Demonstrates

* End-to-end data pipeline design
* Financial data modeling (loan, repayment, accounting)
* Data quality control (pre-ingestion validation)
* Data observability (monitoring & metrics)
* Business + technical integration

---

## 🏗️ System Overview

The system is structured around a two-layer architecture:

### 1. Data Ingestion Control (Pre-validation)

Incoming data is validated using:

* Strong validation rules (reject invalid records)
* Soft validation rules (flag warnings)
* Duplicate detection (batch + historical)

### 2. Data Quality Monitoring (Post-validation)

Validated data is monitored through:

* Quality metrics (acceptance rate, rejection rate, error distribution)
* Issue classification
* Automated reporting

---

## 🔄 End-to-End Workflow

```text
Incoming Data (External / Internal)
        ↓
Validation Pipeline
        ↓
Accepted Data / Rejected Data
        ↓
Monitoring & Metrics
        ↓
Monthly Data Quality Report
```

---

## 📊 Sample Output

The system generates a production-style report:

```text
reports/monthly_data_quality_report.md
```

Example insights include:

* Data quality score
* Rejection rate
* Top validation issues
* Business interpretation
* Recommended actions

---

## ⚙️ How to Run

```bash
git clone https://github.com/chaodajiang/loan-data-quality-control-system.git
cd loan-data-quality-control-system

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python src/generate_sample_data.py
python src/inject_data_issues.py
python src/validation_pipeline.py
python src/quality_monitoring.py
python src/generate_monthly_report.py
```

---

## 🗂️ Project Structure

```text
src/        core data pipeline logic
data/       raw / incoming / accepted / rejected
docs/       system design & business rules
reports/    generated monitoring reports
sql/        validation rule definitions
```

---

## 👤 Author

**Chaoda Jiang**
MS in Business Analytics, UC San Diego

---

## 💡 Key Takeaway

This project reflects how modern data teams:

> Move from “fixing bad data” to **preventing bad data from entering the system in the first place**
