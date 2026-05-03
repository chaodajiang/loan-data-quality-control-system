# Data Dictionary

## 1. Loan Transactions

Represents loan disbursement records from internal systems or external partner platforms.

| Field | Description | Required | Validation Type |
|---|---|---:|---|
| loan_id | Unique loan contract ID | Yes | Strong |
| disbursement_id | Unique disbursement transaction ID | Yes | Strong |
| customer_id | Borrower ID | Yes | Strong |
| source_system | Internal or external data source | Yes | Strong |
| transaction_date | Actual transaction date | Yes | Strong |
| accounting_date | Accounting recognition date | Yes | Strong |
| disbursement_amount | Loan disbursement amount | Yes | Strong |
| interest_rate | Annual interest rate | Yes | Strong |
| term_months | Loan term in months | Yes | Strong |
| loan_status | Loan status | Yes | Strong |
| region | Borrower region | No | Soft |

## 2. Repayment Schedule

Each loan contract has a repayment schedule showing installment-level repayment obligations and repayment status.

| Field | Description | Required | Validation Type |
|---|---|---:|---|
| loan_id | Loan contract ID | Yes | Strong |
| installment_no | Installment number | Yes | Strong |
| due_date | Scheduled repayment date | Yes | Strong |
| loan_overdue_flag | Whether the overall loan is overdue | Yes | Strong |
| installment_overdue_flag | Whether this installment is overdue | Yes | Strong |
| installment_settled_flag | Whether this installment is fully settled | Yes | Strong |
| due_principal | Principal amount due | Yes | Strong |
| paid_principal | Principal amount paid | Yes | Strong |
| due_interest | Interest amount due | Yes | Strong |
| paid_interest | Interest amount paid | Yes | Strong |

## 3. Repayment Transactions

Represents repayment transactions. A single loan may have multiple transactions on the same day.

| Field | Description | Required | Validation Type |
|---|---|---:|---|
| repayment_transaction_id | Unique repayment transaction ID | Yes | Strong |
| loan_id | Loan contract ID | Yes | Strong |
| transaction_date | Actual repayment transaction date | Yes | Strong |
| accounting_date | Accounting recognition date | Yes | Strong |
| repayment_total_amount | Total repayment amount | Yes | Strong |
| repayment_principal | Principal component | Yes | Strong |
| repayment_interest | Interest component | Yes | Strong |
| payment_status | Payment status | Yes | Strong |

## 4. Accounting Entries

Accounting entries are generated in real time for loan disbursement, interest accrual, repayment, and other financial transactions.

| Field | Description | Required | Validation Type |
|---|---|---:|---|
| entry_id | Unique accounting entry ID | Yes | Strong |
| transaction_id | Related transaction ID | Yes | Strong |
| loan_id | Loan contract ID | Yes | Strong |
| transaction_type | Disbursement / interest accrual / repayment | Yes | Strong |
| transaction_date | Actual transaction date | Yes | Strong |
| accounting_date | Accounting recognition date | Yes | Strong |
| account_code | Accounting account code | Yes | Strong |
| account_name | Accounting account name | Yes | Strong |
| debit_amount | Debit amount, shown as positive number | Yes | Strong |
| credit_amount | Credit amount, shown as positive number | Yes | Strong |
| signed_amount | Signed amount for system calculation | Yes | Strong |
