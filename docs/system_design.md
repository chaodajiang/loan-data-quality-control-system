# System Design

## 1. Project Scope

This project simulates a production-style data quality control and monitoring system for financial loan lifecycle management.

The system focuses on:

1. Pre-ingestion validation
2. Real-time loan transaction processing
3. Real-time accounting entry generation
4. Real-time repayment schedule updates
5. Monthly batch monitoring and reporting

## 2. Business Context

Loan data may be generated from two sources:

### Internal Loan Origination

The company directly disburses loans. Loan transactions, repayment schedules, and accounting entries are generated internally.

### External Partner Loan Origination

External partner platforms send loan disbursement data to the company. The company validates the incoming data before generating repayment schedules and accounting entries.

## 3. Validation Strategy

The project uses a two-level validation strategy.

### Strong Validation

Strong validation is applied to critical fields. Records failing strong validation are rejected before entering core processing.

Examples:

- Missing loan contract ID
- Missing disbursement transaction ID
- Missing transaction date
- Missing accounting date
- Invalid disbursement amount
- Duplicate transaction ID

### Soft Validation

Soft validation is applied to non-critical fields. Records failing soft validation may still be accepted, but warning flags are generated.

Examples:

- Missing region
- Unusual but non-blocking customer attributes
- Optional descriptive fields

## 4. Real-time Processing Logic

Every financial transaction triggers real-time updates to:

- Accounting entries
- Repayment schedule

A single loan may have multiple transactions on the same day, so processing is designed at the transaction level rather than only at the loan level.

## 5. Monthly Monitoring Logic

On the first day of each month, the system simulates a batch monitoring process using data as of the prior month-end.

Monitoring outputs include:

- Missing rate
- Duplicate rate
- Rejected record rate
- Accounting mismatch rate
- Repayment schedule mismatch rate
- Overall data quality score

## 6. Architecture

Data Sources
→ Validation Pipeline
→ Accepted / Rejected Data
→ Core Processing
→ Accounting Entries & Repayment Schedule
→ Monthly Monitoring
→ Reports / Dashboard
