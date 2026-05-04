# Monthly Data Quality Report

**Report Date:** 2026-05-04

## 1. Executive Summary

This report summarizes the data quality results for the latest incoming loan transaction batch. The validation process applies strong validation rules to block critical data issues and soft validation rules to flag non-critical issues.

## 2. Key Metrics

- Total incoming records: 100
- Accepted records: 90
- Rejected records: 10
- Acceptance rate: 90.00%
- Rejection rate: 10.00%
- Strong error count: 10
- Soft warning count: 1
- Overall data quality score: 92.9

## 3. Issue Summary

### Key Observations

- DUPLICATE_IN_BATCH on `disbursement_id` occurred 2 time(s).
- MISSING_OPTIONAL_FIELD on `region` occurred 1 time(s).
- MISSING_REQUIRED_FIELD on `accounting_date` occurred 1 time(s).
- Duplicate disbursement ID issues indicate potential transaction-level control or idempotency risks.
- Missing required fields suggest upstream data capture or interface validation gaps.

| Rule Type | Field | Error Code | Issue Count |
|---|---|---|---:|
| strong | disbursement_id | DUPLICATE_IN_BATCH | 2 |
| soft | region | MISSING_OPTIONAL_FIELD | 1 |
| strong | accounting_date | MISSING_REQUIRED_FIELD | 1 |
| strong | disbursement_amount | INVALID_AMOUNT | 1 |
| strong | disbursement_id | DUPLICATE_WITH_HISTORY | 1 |
| strong | disbursement_id | INVALID_DISBURSEMENT_ID_FORMAT | 1 |
| strong | disbursement_id | MISSING_REQUIRED_FIELD | 1 |
| strong | interest_rate | INVALID_INTEREST_RATE | 1 |
| strong | loan_id | MISSING_REQUIRED_FIELD | 1 |
| strong | source_system | MISSING_REQUIRED_FIELD | 1 |

## 4. Business Interpretation

The overall data quality score for this batch is 92.9, with a rejection rate of 10.00%.

The rejection rate is relatively high and should be reviewed before downstream financial processing.

The main risks are related to transaction integrity, including duplicate disbursement IDs, missing required fields, invalid transaction amounts, or invalid interest rates.

Soft warnings do not block processing, but they should be monitored because incomplete optional fields can reduce downstream analytics and reporting quality.

## 5. Recommended Actions

- Review rejected records before re-submission.
- Strengthen upstream controls for required fields.
- Monitor duplicate disbursement IDs across both incoming and historical data.
- Track soft warning trends to improve optional field completeness.
