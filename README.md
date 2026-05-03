Loan Data Quality Control & Monitoring System
📌 Overview

A production-style data quality framework for financial loan systems, designed to ensure data integrity across the full loan lifecycle.

Key capabilities:

Pre-ingestion validation (data quality control)
Real-time financial data processing (loan / repayment / accounting)
Post-ingestion monitoring and anomaly detection
🎯 Business Problem

Loan data flows across multiple systems (internal + external), often leading to:

Invalid or inconsistent data entering core systems
Mismatch between loan, repayment, and accounting data
Errors only discovered during month-end reporting

These issues increase operational risk and reconciliation costs.

💡 Solution

This project implements a two-layer data quality system:

1. Validation Layer (Pre-ingestion)
Strong & soft validation rules
Data split into accepted vs rejected
Prevents bad data from entering core systems
2. Monitoring Layer (Post-ingestion)
Data quality metrics (missing, duplicate, mismatch)
Monthly reporting & anomaly detection
🏗️ System Architecture
Data Sources
   ↓
Validation Pipeline
   ↓
Accepted / Rejected Data
   ↓
Core Processing (Loan / Repayment / Accounting)
   ↓
Monitoring & Reporting
🧩 Key Features
Data validation framework (schema + business rules)
Financial data consistency checks
Real-time transaction simulation
Data quality monitoring & reporting
🗂️ Project Structure
src/        core pipeline logic
data/       staged data layers
sql/        data models & validation rules
docs/       system design & details
⚙️ Tech Stack

Python · SQL · Pandas · Streamlit (optional)

📊 Why This Project Matters

This project demonstrates:

End-to-end data pipeline design
Financial system understanding
Data quality & governance expertise
Strong business + technical integration
👤 Author

Chaoda Jiang
MSBA @ UC San Diego
