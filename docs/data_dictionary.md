# Data Dictionary

## 1. Loan Transactions (`loan_transactions`)

Core disbursement records from internal systems or external partner platforms.

| Field | Type | Required | Validation | Description |
|---|---|---|---|---|
| loan_id | VARCHAR(20) | Yes | Strong | Unique loan contract ID (e.g. LN000001) |
| disbursement_id | VARCHAR(30) | Yes | Strong | Unique disbursement transaction ID. Format: DISBYYYYMMDDNNNNNN |
| customer_id | VARCHAR(20) | Yes | Strong | Borrower ID |
| source_system | VARCHAR(30) | Yes | Strong | Data source: `internal_core` or `partner_platform` |
| transaction_date | DATE | Yes | Strong | Actual disbursement date |
| accounting_date | DATE | Yes | Strong | Accounting recognition date |
| disbursement_amount | DECIMAL(15,2) | Yes | Strong | Loan disbursement amount, must be > 0 |
| interest_rate | DECIMAL(6,4) | Yes | Strong | Annual interest rate, must be > 0 and ≤ 0.36 (36%) |
| term_months | INT | Yes | Strong | Loan term in months, must be > 0 |
| loan_status | VARCHAR(20) | Yes | Strong | Loan lifecycle status: `active`, `closed`, `defaulted`, `written_off` |
| region | VARCHAR(5) | No | Soft | Borrower state code (e.g. CA, NY). Optional but monitored |
| charge_off_date | DATE | Conditional | Strong | Date of charge-off. Required when loan_status = `written_off` |
| charge_off_amount | DECIMAL(15,2) | Conditional | Strong | Charge-off amount = unpaid principal + overdue interest. Required when loan_status = `written_off` |

**Loan Status Definitions:**

| Status | Description | Trigger |
|---|---|---|
| `active` | Loan is current and repayments are on schedule | Default at origination |
| `closed` | All installments fully settled | All installment_settled_flag = 1 |
| `defaulted` | Borrower has stopped paying; overdue but < 120 days | Overdue days > 0 and < 120 |
| `written_off` | Loan charged off per Affirm-aligned 120-day standard | Overdue days ≥ 120 |

---

## 2. Repayment Schedule (`repayment_schedule`)

Installment-level repayment obligations per loan, including overdue tracking.

| Field | Type | Required | Validation | Description |
|---|---|---|---|---|
| loan_id | VARCHAR(20) | Yes | Strong | Loan contract ID (FK → loan_transactions) |
| installment_no | INT | Yes | Strong | Installment sequence number (1, 2, 3, ...) |
| due_date | DATE | Yes | Strong | Scheduled repayment date |
| loan_overdue_flag | BOOLEAN | Yes | Strong | 1 if any installment on this loan is overdue |
| installment_overdue_flag | BOOLEAN | Yes | Strong | 1 if this specific installment is overdue |
| installment_settled_flag | BOOLEAN | Yes | Strong | 1 if this installment is fully paid |
| due_principal | DECIMAL(15,2) | Yes | Strong | Principal amount due for this installment |
| paid_principal | DECIMAL(15,2) | Yes | Strong | Principal amount actually paid |
| due_interest | DECIMAL(15,2) | Yes | Strong | Normal interest amount due |
| paid_interest | DECIMAL(15,2) | Yes | Strong | Normal interest amount actually paid |
| overdue_days | INT | Yes | Strong | Number of days past due date (0 if current) |
| overdue_interest_due | DECIMAL(15,2) | Yes | Strong | Overdue interest accrued. Formula: unpaid principal × (annual rate × 1.5) / 365 × overdue days |
| overdue_interest_paid | DECIMAL(15,2) | Yes | Strong | Overdue interest actually collected |

**Overdue Interest Formula:**

Overdue Interest = Installment Unpaid Principal × (Annual Rate × 1.5) / 365 × Overdue Days

Note: The base is the **installment-level** unpaid principal, not the total outstanding loan balance.

---

## 3. Repayment Transactions (`repayment_transactions`)

Actual payment events. A single loan may have multiple transactions.

| Field | Type | Required | Validation | Description |
|---|---|---|---|---|
| repayment_transaction_id | VARCHAR(40) | Yes | Strong | Unique repayment transaction ID |
| loan_id | VARCHAR(20) | Yes | Strong | Loan contract ID (FK → loan_transactions) |
| transaction_date | DATE | Yes | Strong | Actual repayment transaction date |
| accounting_date | DATE | Yes | Strong | Accounting recognition date |
| repayment_total_amount | DECIMAL(15,2) | Yes | Strong | Total repayment amount (principal + interest) |
| repayment_principal | DECIMAL(15,2) | Yes | Strong | Principal component of repayment |
| repayment_interest | DECIMAL(15,2) | Yes | Strong | Normal interest component of repayment |
| repayment_overdue_interest | DECIMAL(15,2) | Yes | Strong | Overdue interest component of repayment (0 if none) |
| payment_status | VARCHAR(20) | Yes | Strong | `successful`, `failed`, or `reversed` |

---

## 4. Accounting Entries (`accounting_entries`)

Double-entry bookkeeping records for every financial event.

| Field | Type | Required | Validation | Description |
|---|---|---|---|---|
| entry_id | VARCHAR(60) | Yes | Strong | Unique accounting entry ID |
| transaction_id | VARCHAR(50) | Yes | Strong | Related transaction ID |
| loan_id | VARCHAR(20) | Yes | Strong | Loan contract ID (FK → loan_transactions) |
| transaction_type | VARCHAR(30) | Yes | Strong | Event type (see below) |
| transaction_date | DATE | Yes | Strong | Actual event date |
| accounting_date | DATE | Yes | Strong | Accounting recognition date |
| account_code | VARCHAR(10) | Yes | Strong | GL account code (see chart of accounts below) |
| account_name | VARCHAR(60) | Yes | Strong | GL account name |
| debit_amount | DECIMAL(15,2) | Yes | Strong | Debit amount (≥ 0) |
| credit_amount | DECIMAL(15,2) | Yes | Strong | Credit amount (≥ 0) |
| signed_amount | DECIMAL(15,2) | Yes | Strong | Signed net amount for system calculation |

**Transaction Types:**

| transaction_type | Description |
|---|---|
| `disbursement` | Loan funded to borrower |
| `interest_accrual` | Normal monthly interest recognized |
| `overdue_interest_accrual` | Penalty interest on overdue installments |
| `repayment` | Borrower payment received |
| `charge_off` | Written-off loan removed from books |
| `loan_transfer` | Asset sold via NPL sale or ABS securitization |

**Chart of Accounts:**

| Account Code | Account Name | Type | Description |
|---|---|---|---|
| 1002 | Cash and Bank Deposits | Asset | Cash received or paid |
| 1301 | Loans Receivable | Asset | Outstanding loan principal |
| 1311 | Allowance for Credit Losses | Asset (Contra) | Reserve against expected losses |
| 1320 | Interest Receivable | Asset | Normal interest earned but not yet collected |
| 1321 | Overdue Interest Receivable | Asset | Penalty interest earned but not yet collected |
| 4610 | Interest Income | Revenue | Normal interest income recognized |
| 4611 | Overdue Interest Income | Revenue | Penalty interest income recognized |
| 6013 | Gain on Loan Transfer | Other Income | Gain when transfer price > face value |
| 7111 | Bad Debt Expense – Charge-off | Expense | Loss recognized on written-off loans |
| 7120 | Loss on Loan Transfer | Expense | Loss when transfer price < face value |

---

## 5. Loan Transfers (`loan_transfers`)

Asset transfer records for non-performing and securitized loans.

| Field | Type | Required | Validation | Description |
|---|---|---|---|---|
| transfer_id | VARCHAR(20) | Yes | Strong | Unique transfer ID (e.g. TRF000001) |
| loan_id | VARCHAR(20) | Yes | Strong | Loan contract ID (FK → loan_transactions) |
| transfer_date | DATE | Yes | Strong | Date of asset transfer |
| transfer_type | VARCHAR(10) | Yes | Strong | `NPL` or `ABS` |
| face_value | DECIMAL(15,2) | Yes | Strong | Book value of loan at time of transfer |
| transfer_price | DECIMAL(15,2) | Yes | Strong | Actual price received from buyer |
| discount_rate | DECIMAL(6,4) | Yes | Strong | Discount applied: (face_value - transfer_price) / face_value |
| counterparty | VARCHAR(60) | Yes | Strong | Name of purchasing institution |

**Transfer Type Definitions:**

| Type | Eligible Loan Status | Typical Discount | Description |
|---|---|---|---|
| `NPL` | `written_off` | 70–90% | Non-performing loan sale to distressed debt buyer |
| `ABS` | `defaulted` | 5–20% | Asset-backed securitization to capital markets investor |
