-- ============================================================
-- Loan Data Quality Control System
-- Validation Rule Queries
-- Author: Chaoda Jiang | UC San Diego, MS Business Analytics
--
-- These queries mirror the Python validation pipeline logic
-- and can be run directly against the database for auditing.
-- ============================================================


-- ============================================================
-- STRONG VALIDATION RULES (failures cause record rejection)
-- ============================================================

-- ------------------------------------------------------------
-- V-001: Missing Required Fields
-- ------------------------------------------------------------
SELECT
    loan_id,
    disbursement_id,
    'MISSING_REQUIRED_FIELD'    AS error_code,
    'strong'                    AS rule_type,
    CASE
        WHEN loan_id             IS NULL OR loan_id = ''           THEN 'loan_id'
        WHEN disbursement_id     IS NULL OR disbursement_id = ''   THEN 'disbursement_id'
        WHEN customer_id         IS NULL OR customer_id = ''       THEN 'customer_id'
        WHEN source_system       IS NULL OR source_system = ''     THEN 'source_system'
        WHEN transaction_date    IS NULL                           THEN 'transaction_date'
        WHEN accounting_date     IS NULL                           THEN 'accounting_date'
        WHEN disbursement_amount IS NULL                           THEN 'disbursement_amount'
        WHEN interest_rate       IS NULL                           THEN 'interest_rate'
        WHEN term_months         IS NULL                           THEN 'term_months'
        WHEN loan_status         IS NULL OR loan_status = ''       THEN 'loan_status'
    END AS field
FROM loan_transactions_incoming
WHERE
    loan_id            IS NULL OR loan_id = ''
    OR disbursement_id IS NULL OR disbursement_id = ''
    OR customer_id     IS NULL OR customer_id = ''
    OR source_system   IS NULL OR source_system = ''
    OR transaction_date  IS NULL
    OR accounting_date   IS NULL
    OR disbursement_amount IS NULL
    OR interest_rate     IS NULL
    OR term_months       IS NULL
    OR loan_status       IS NULL OR loan_status = '';


-- ------------------------------------------------------------
-- V-002: Invalid Disbursement Amount (must be > 0)
-- ------------------------------------------------------------
SELECT
    loan_id,
    disbursement_id,
    disbursement_amount,
    'INVALID_AMOUNT'        AS error_code,
    'strong'                AS rule_type,
    'disbursement_amount'   AS field
FROM loan_transactions_incoming
WHERE disbursement_amount <= 0;


-- ------------------------------------------------------------
-- V-003: Invalid Interest Rate (must be > 0 and <= 36%)
-- ------------------------------------------------------------
SELECT
    loan_id,
    disbursement_id,
    interest_rate,
    'INVALID_INTEREST_RATE' AS error_code,
    'strong'                AS rule_type,
    'interest_rate'         AS field
FROM loan_transactions_incoming
WHERE interest_rate <= 0 OR interest_rate > 0.36;


-- ------------------------------------------------------------
-- V-004: Invalid Disbursement ID Format (DISBYYYYMMDDNNNNNN)
-- ------------------------------------------------------------
SELECT
    loan_id,
    disbursement_id,
    'INVALID_DISBURSEMENT_ID_FORMAT'    AS error_code,
    'strong'                            AS rule_type,
    'disbursement_id'                   AS field
FROM loan_transactions_incoming
WHERE disbursement_id NOT REGEXP '^DISB[0-9]{14}$';
-- PostgreSQL: WHERE disbursement_id !~ '^DISB[0-9]{14}$'


-- ------------------------------------------------------------
-- V-005: Duplicate Disbursement ID within Incoming Batch
-- ------------------------------------------------------------
SELECT
    disbursement_id,
    COUNT(*)                AS occurrence_count,
    'DUPLICATE_IN_BATCH'    AS error_code,
    'strong'                AS rule_type,
    'disbursement_id'       AS field
FROM loan_transactions_incoming
GROUP BY disbursement_id
HAVING COUNT(*) > 1;


-- ------------------------------------------------------------
-- V-006: Duplicate Disbursement ID vs Historical Core Data
-- ------------------------------------------------------------
SELECT
    i.loan_id,
    i.disbursement_id,
    'DUPLICATE_WITH_HISTORY'    AS error_code,
    'strong'                    AS rule_type,
    'disbursement_id'           AS field
FROM loan_transactions_incoming i
INNER JOIN loan_transactions h
    ON i.disbursement_id = h.disbursement_id;


-- ------------------------------------------------------------
-- V-007: Accounting Balance Check (debit must equal credit)
-- ------------------------------------------------------------
SELECT
    transaction_id,
    loan_id,
    SUM(debit_amount)                               AS total_debit,
    SUM(credit_amount)                              AS total_credit,
    ABS(SUM(debit_amount) - SUM(credit_amount))     AS imbalance,
    'ACCOUNTING_IMBALANCE'                          AS error_code,
    'strong'                                        AS rule_type
FROM accounting_entries
GROUP BY transaction_id, loan_id
HAVING ABS(SUM(debit_amount) - SUM(credit_amount)) > 0.01;


-- ------------------------------------------------------------
-- V-008: Repayment Schedule Principal Sum vs Loan Amount
-- ------------------------------------------------------------
SELECT
    rs.loan_id,
    lt.disbursement_amount,
    SUM(rs.due_principal)                                       AS scheduled_total,
    ABS(lt.disbursement_amount - SUM(rs.due_principal))         AS discrepancy,
    'SCHEDULE_PRINCIPAL_MISMATCH'                               AS error_code,
    'strong'                                                    AS rule_type
FROM repayment_schedule rs
JOIN loan_transactions lt ON rs.loan_id = lt.loan_id
GROUP BY rs.loan_id, lt.disbursement_amount
HAVING ABS(lt.disbursement_amount - SUM(rs.due_principal)) > 0.01;


-- ------------------------------------------------------------
-- V-009: Charge-off Amount Must Exist for Written-off Loans
-- ------------------------------------------------------------
SELECT
    loan_id,
    loan_status,
    charge_off_date,
    charge_off_amount,
    'MISSING_CHARGE_OFF_AMOUNT' AS error_code,
    'strong'                    AS rule_type,
    'charge_off_amount'         AS field
FROM loan_transactions
WHERE loan_status = 'written_off'
  AND (charge_off_amount IS NULL OR charge_off_amount <= 0);


-- ------------------------------------------------------------
-- V-010: Transfer Price Must Be Less Than Face Value (NPL/ABS sold at discount)
-- ------------------------------------------------------------
SELECT
    transfer_id,
    loan_id,
    transfer_type,
    face_value,
    transfer_price,
    'TRANSFER_PRICE_EXCEEDS_FACE'   AS error_code,
    'strong'                        AS rule_type,
    'transfer_price'                AS field
FROM loan_transfers
WHERE transfer_price >= face_value;


-- ============================================================
-- SOFT VALIDATION RULES (failures generate warnings only)
-- ============================================================

-- ------------------------------------------------------------
-- V-101: Missing Optional Field: region
-- ------------------------------------------------------------
SELECT
    loan_id,
    disbursement_id,
    'MISSING_OPTIONAL_FIELD'    AS error_code,
    'soft'                      AS rule_type,
    'region'                    AS field
FROM loan_transactions_incoming
WHERE region IS NULL OR region = '';


-- ------------------------------------------------------------
-- V-102: Overdue Interest Not Computed for Overdue Installments
-- ------------------------------------------------------------
SELECT
    loan_id,
    installment_no,
    overdue_days,
    overdue_interest_due,
    'MISSING_OVERDUE_INTEREST'  AS error_code,
    'soft'                      AS rule_type,
    'overdue_interest_due'      AS field
FROM repayment_schedule
WHERE installment_overdue_flag = 1
  AND overdue_days > 0
  AND overdue_interest_due = 0;


-- ============================================================
-- MONITORING QUERIES (monthly batch reporting)
-- ============================================================

-- ------------------------------------------------------------
-- M-001: Overall Data Quality Summary
-- ------------------------------------------------------------
SELECT
    COUNT(*)                                                                AS total_records,
    SUM(CASE WHEN validation_status = 'accepted' THEN 1 ELSE 0 END)        AS accepted_records,
    SUM(CASE WHEN validation_status = 'rejected' THEN 1 ELSE 0 END)        AS rejected_records,
    ROUND(
        SUM(CASE WHEN validation_status = 'rejected' THEN 1 ELSE 0 END)
        * 100.0 / COUNT(*), 2
    )                                                                       AS rejection_rate_pct
FROM loan_transactions_incoming;


-- ------------------------------------------------------------
-- M-002: Error Distribution by Field and Error Code
-- ------------------------------------------------------------
SELECT
    rule_type,
    field,
    error_code,
    COUNT(*) AS issue_count
FROM validation_error_log
GROUP BY rule_type, field, error_code
ORDER BY issue_count DESC;


-- ------------------------------------------------------------
-- M-003: Rejection Rate by Source System
-- ------------------------------------------------------------
SELECT
    source_system,
    COUNT(*)                                                                    AS total_records,
    SUM(CASE WHEN validation_status = 'rejected' THEN 1 ELSE 0 END)            AS rejected_records,
    ROUND(
        SUM(CASE WHEN validation_status = 'rejected' THEN 1 ELSE 0 END)
        * 100.0 / COUNT(*), 2
    )                                                                           AS rejection_rate_pct
FROM loan_transactions_incoming
GROUP BY source_system
ORDER BY rejection_rate_pct DESC;


-- ------------------------------------------------------------
-- M-004: Portfolio Status Distribution
-- ------------------------------------------------------------
SELECT
    loan_status,
    COUNT(*)                                            AS loan_count,
    SUM(disbursement_amount)                            AS total_exposure,
    ROUND(AVG(interest_rate) * 100, 2)                  AS avg_interest_rate_pct,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2)  AS portfolio_share_pct
FROM loan_transactions
GROUP BY loan_status
ORDER BY loan_count DESC;


-- ------------------------------------------------------------
-- M-005: Overdue Portfolio Aging Buckets
-- ------------------------------------------------------------
SELECT
    CASE
        WHEN overdue_days = 0           THEN 'Current'
        WHEN overdue_days <= 30         THEN '1-30 DPD'
        WHEN overdue_days <= 60         THEN '31-60 DPD'
        WHEN overdue_days <= 90         THEN '61-90 DPD'
        WHEN overdue_days <= 120        THEN '91-120 DPD'
        ELSE                                 '120+ DPD (Charge-off)'
    END                                 AS aging_bucket,
    COUNT(*)                            AS installment_count,
    SUM(due_principal - paid_principal) AS unpaid_principal,
    SUM(overdue_interest_due)           AS total_overdue_interest
FROM repayment_schedule
GROUP BY aging_bucket
ORDER BY MIN(overdue_days);


-- ------------------------------------------------------------
-- M-006: Loan Transfer Summary
-- ------------------------------------------------------------
SELECT
    transfer_type,
    COUNT(*)                            AS transfer_count,
    SUM(face_value)                     AS total_face_value,
    SUM(transfer_price)                 AS total_transfer_price,
    ROUND(AVG(discount_rate) * 100, 2)  AS avg_discount_rate_pct,
    SUM(face_value - transfer_price)    AS total_loss_on_transfer
FROM loan_transfers
GROUP BY transfer_type;


-- ------------------------------------------------------------
-- M-007: Collection Rate by Loan Status
-- ------------------------------------------------------------
SELECT
    lt.loan_status,
    COUNT(DISTINCT rs.loan_id)                                      AS loan_count,
    SUM(rs.paid_principal + rs.paid_interest)                       AS total_collected,
    SUM(rs.due_principal + rs.due_interest)                         AS total_due,
    ROUND(
        SUM(rs.paid_principal + rs.paid_interest) * 100.0
        / NULLIF(SUM(rs.due_principal + rs.due_interest), 0), 2
    )                                                               AS collection_rate_pct
FROM repayment_schedule rs
JOIN loan_transactions lt ON rs.loan_id = lt.loan_id
GROUP BY lt.loan_status
ORDER BY collection_rate_pct DESC;
