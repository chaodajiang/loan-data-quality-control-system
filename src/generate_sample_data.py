import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

np.random.seed(42)

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def generate_loan_transactions(n=100):
    records = []
    start_date = datetime(2026, 1, 1)

    for i in range(1, n + 1):
        loan_id = f"LN{i:06d}"
        disbursement_id = f"DISB{i:06d}"
        customer_id = f"CUST{np.random.randint(1, 80):06d}"

        transaction_date = start_date + timedelta(days=np.random.randint(0, 90))

        if np.random.rand() < 0.15:
            accounting_date = transaction_date - timedelta(days=1)
        else:
            accounting_date = transaction_date

        disbursement_amount = int(np.random.choice([5000, 8000, 10000, 15000, 20000, 30000]))
        interest_rate = round(np.random.uniform(0.06, 0.24), 4)
        term_months = int(np.random.choice([6, 12, 18, 24, 36]))

        records.append({
            "loan_id": loan_id,
            "disbursement_id": disbursement_id,
            "customer_id": customer_id,
            "source_system": np.random.choice(["internal_core", "partner_platform"]),
            "transaction_date": transaction_date.date(),
            "accounting_date": accounting_date.date(),
            "disbursement_amount": disbursement_amount,
            "interest_rate": interest_rate,
            "term_months": term_months,
            "loan_status": "active",
            "region": np.random.choice(["CA", "NY", "TX", "FL", "WA"])
        })

    return pd.DataFrame(records)


def generate_repayment_schedule(loan_df):
    records = []

    for _, row in loan_df.iterrows():
        loan_amount = float(row["disbursement_amount"])
        term_months = int(row["term_months"])
        monthly_principal = round(loan_amount / term_months, 2)

        principal_values = [monthly_principal] * (term_months - 1)
        final_principal = round(loan_amount - sum(principal_values), 2)
        principal_values.append(final_principal)

        monthly_interest = round(loan_amount * float(row["interest_rate"]) / 12, 2)

        for installment_no in range(1, term_months + 1):
            due_date = pd.to_datetime(row["accounting_date"]) + pd.DateOffset(months=installment_no)

            records.append({
                "loan_id": row["loan_id"],
                "installment_no": installment_no,
                "due_date": due_date.date(),
                "loan_overdue_flag": 0,
                "installment_overdue_flag": 0,
                "installment_settled_flag": 0,
                "due_principal": principal_values[installment_no - 1],
                "paid_principal": 0.00,
                "due_interest": monthly_interest,
                "paid_interest": 0.00
            })

    return pd.DataFrame(records)


def generate_repayment_transactions(loan_df, schedule_df):
    records = []

    for _, loan in loan_df.iterrows():
        if np.random.rand() > 0.70:
            continue

        loan_schedule = schedule_df[schedule_df["loan_id"] == loan["loan_id"]].sort_values("installment_no")
        num_paid_installments = np.random.randint(1, min(4, len(loan_schedule) + 1))

        for _, installment in loan_schedule.head(num_paid_installments).iterrows():
            repayment_principal = float(installment["due_principal"])
            repayment_interest = float(installment["due_interest"])
            repayment_total = round(repayment_principal + repayment_interest, 2)

            transaction_date = pd.to_datetime(installment["due_date"]) + pd.Timedelta(days=np.random.randint(0, 3))
            accounting_date = transaction_date

            records.append({
                "repayment_transaction_id": f"REPAY_{loan['loan_id']}_{int(installment['installment_no']):02d}",
                "loan_id": loan["loan_id"],
                "transaction_date": transaction_date.date(),
                "accounting_date": accounting_date.date(),
                "repayment_total_amount": repayment_total,
                "repayment_principal": repayment_principal,
                "repayment_interest": repayment_interest,
                "payment_status": "successful"
            })

    return pd.DataFrame(records)


def update_repayment_schedule(schedule_df, repayment_df):
    updated_schedule = schedule_df.copy()

    for _, repayment in repayment_df.iterrows():
        loan_id = repayment["loan_id"]
        remaining_principal = float(repayment["repayment_principal"])
        remaining_interest = float(repayment["repayment_interest"])

        loan_schedule = updated_schedule[
            (updated_schedule["loan_id"] == loan_id)
            & (updated_schedule["installment_settled_flag"] == 0)
        ].sort_values("installment_no")

        for idx, installment in loan_schedule.iterrows():
            unpaid_principal = float(installment["due_principal"]) - float(installment["paid_principal"])
            unpaid_interest = float(installment["due_interest"]) - float(installment["paid_interest"])

            principal_payment = min(remaining_principal, unpaid_principal)
            interest_payment = min(remaining_interest, unpaid_interest)

            updated_schedule.loc[idx, "paid_principal"] = round(
                float(updated_schedule.loc[idx, "paid_principal"]) + principal_payment, 2
            )
            updated_schedule.loc[idx, "paid_interest"] = round(
                float(updated_schedule.loc[idx, "paid_interest"]) + interest_payment, 2
            )

            remaining_principal = round(remaining_principal - principal_payment, 2)
            remaining_interest = round(remaining_interest - interest_payment, 2)

            principal_fully_paid = (
                round(float(updated_schedule.loc[idx, "paid_principal"]), 2)
                >= round(float(updated_schedule.loc[idx, "due_principal"]), 2)
            )
            interest_fully_paid = (
                round(float(updated_schedule.loc[idx, "paid_interest"]), 2)
                >= round(float(updated_schedule.loc[idx, "due_interest"]), 2)
            )

            if principal_fully_paid and interest_fully_paid:
                updated_schedule.loc[idx, "installment_settled_flag"] = 1

            if remaining_principal <= 0 and remaining_interest <= 0:
                break

    return updated_schedule


def generate_accounting_entries(loan_df, schedule_df, repayment_df):
    records = []

    for _, row in loan_df.iterrows():
        transaction_id = row["disbursement_id"]

        records.append({
            "entry_id": f"AE_{transaction_id}_DR",
            "transaction_id": transaction_id,
            "loan_id": row["loan_id"],
            "transaction_type": "disbursement",
            "transaction_date": row["transaction_date"],
            "accounting_date": row["accounting_date"],
            "account_code": "1301",
            "account_name": "Loans Receivable",
            "debit_amount": row["disbursement_amount"],
            "credit_amount": 0.00,
            "signed_amount": row["disbursement_amount"]
        })

        records.append({
            "entry_id": f"AE_{transaction_id}_CR",
            "transaction_id": transaction_id,
            "loan_id": row["loan_id"],
            "transaction_type": "disbursement",
            "transaction_date": row["transaction_date"],
            "accounting_date": row["accounting_date"],
            "account_code": "1002",
            "account_name": "Bank Deposit",
            "debit_amount": 0.00,
            "credit_amount": row["disbursement_amount"],
            "signed_amount": -row["disbursement_amount"]
        })

    for _, row in schedule_df.iterrows():
        transaction_id = f"ACCRUAL_{row['loan_id']}_{int(row['installment_no']):02d}"
        interest_amount = float(row["due_interest"])

        records.append({
            "entry_id": f"AE_{transaction_id}_DR",
            "transaction_id": transaction_id,
            "loan_id": row["loan_id"],
            "transaction_type": "interest_accrual",
            "transaction_date": row["due_date"],
            "accounting_date": row["due_date"],
            "account_code": "1132",
            "account_name": "Interest Receivable",
            "debit_amount": interest_amount,
            "credit_amount": 0.00,
            "signed_amount": interest_amount
        })

        records.append({
            "entry_id": f"AE_{transaction_id}_CR",
            "transaction_id": transaction_id,
            "loan_id": row["loan_id"],
            "transaction_type": "interest_accrual",
            "transaction_date": row["due_date"],
            "accounting_date": row["due_date"],
            "account_code": "6011",
            "account_name": "Interest Income",
            "debit_amount": 0.00,
            "credit_amount": interest_amount,
            "signed_amount": -interest_amount
        })

    for _, row in repayment_df.iterrows():
        transaction_id = row["repayment_transaction_id"]

        records.append({
            "entry_id": f"AE_{transaction_id}_DR_BANK",
            "transaction_id": transaction_id,
            "loan_id": row["loan_id"],
            "transaction_type": "repayment",
            "transaction_date": row["transaction_date"],
            "accounting_date": row["accounting_date"],
            "account_code": "1002",
            "account_name": "Bank Deposit",
            "debit_amount": row["repayment_total_amount"],
            "credit_amount": 0.00,
            "signed_amount": row["repayment_total_amount"]
        })

        records.append({
            "entry_id": f"AE_{transaction_id}_CR_PRINCIPAL",
            "transaction_id": transaction_id,
            "loan_id": row["loan_id"],
            "transaction_type": "repayment",
            "transaction_date": row["transaction_date"],
            "accounting_date": row["accounting_date"],
            "account_code": "1301",
            "account_name": "Loans Receivable",
            "debit_amount": 0.00,
            "credit_amount": row["repayment_principal"],
            "signed_amount": -row["repayment_principal"]
        })

        records.append({
            "entry_id": f"AE_{transaction_id}_CR_INTEREST",
            "transaction_id": transaction_id,
            "loan_id": row["loan_id"],
            "transaction_type": "repayment",
            "transaction_date": row["transaction_date"],
            "accounting_date": row["accounting_date"],
            "account_code": "1132",
            "account_name": "Interest Receivable",
            "debit_amount": 0.00,
            "credit_amount": row["repayment_interest"],
            "signed_amount": -row["repayment_interest"]
        })

    return pd.DataFrame(records)


def main():
    loan_df = generate_loan_transactions(n=100)
    schedule_df = generate_repayment_schedule(loan_df)
    repayment_df = generate_repayment_transactions(loan_df, schedule_df)
    updated_schedule_df = update_repayment_schedule(schedule_df, repayment_df)
    accounting_df = generate_accounting_entries(loan_df, schedule_df, repayment_df)

    loan_df.to_csv(RAW_DIR / "loan_transactions.csv", index=False)
    updated_schedule_df.to_csv(RAW_DIR / "repayment_schedule.csv", index=False)
    repayment_df.to_csv(RAW_DIR / "repayment_transactions.csv", index=False)
    accounting_df.to_csv(RAW_DIR / "accounting_entries.csv", index=False)

    print("Sample data generated successfully.")
    print(f"Loan transactions: {len(loan_df)} records")
    print(f"Repayment schedule: {len(updated_schedule_df)} records")
    print(f"Repayment transactions: {len(repayment_df)} records")
    print(f"Accounting entries: {len(accounting_df)} records")


if __name__ == "__main__":
    main()
