import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date, datetime, timedelta

np.random.seed(42)

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

SIMULATION_DATE = date(2026, 5, 4)   # Today's date in the simulation
CHARGE_OFF_DAYS = 120                 # Aligned with Affirm standard


def generate_loan_transactions(n=None):
    """
    Generate ~3 loans per day from 2025-01-01 to 2026-04-30.
    Total: ~1,455 loans.
    Loan status is determined naturally by time elapsed and borrower profile.
    """
    start = date(2025, 1, 1)
    end = date(2026, 4, 30)

    records = []
    loan_counter = 1

    current_date = start
    while current_date <= end:
        # 每天随机 2-4 笔，均值约3笔
        daily_count = np.random.choice([2, 3, 3, 3, 4])

        for _ in range(daily_count):
            loan_id = f"LN{loan_counter:06d}"
            customer_id = f"CUST{np.random.randint(1, 500):06d}"

            transaction_date = current_date
            disbursement_id = f"DISB{transaction_date.strftime('%Y%m%d')}{loan_counter:06d}"

            disbursement_amount = int(np.random.choice([5000, 8000, 10000, 15000, 20000, 30000]))
            interest_rate = round(np.random.uniform(0.06, 0.24), 4)
            term_months = int(np.random.choice([6, 12, 18, 24, 36]))
            region = np.random.choice(["CA", "NY", "TX", "FL", "WA"])
            source_system = np.random.choice(["internal_core", "partner_platform"])

            # Bad borrower probability increases with interest rate
            # At 6%: ~8% bad; at 24%: ~30% bad
            bad_borrower_prob = 0.08 + (interest_rate - 0.06) / (0.24 - 0.06) * 0.22
            is_bad_borrower = np.random.rand() < bad_borrower_prob

            records.append({
                "loan_id": loan_id,
                "disbursement_id": disbursement_id,
                "customer_id": customer_id,
                "source_system": source_system,
                "transaction_date": transaction_date,
                "accounting_date": transaction_date,
                "disbursement_amount": disbursement_amount,
                "interest_rate": interest_rate,
                "term_months": term_months,
                "loan_status": "active",
                "region": region,
                "is_bad_borrower": is_bad_borrower,
                "charge_off_date": None,
                "charge_off_amount": None,
            })

            loan_counter += 1

        current_date += timedelta(days=1)

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
                "paid_interest": 0.00,
                "overdue_days": 0,
                "overdue_interest_due": 0.00,
                "overdue_interest_paid": 0.00,
            })

    return pd.DataFrame(records)


def generate_repayment_transactions(loan_df, schedule_df):
    """
    Payment behavior is driven by time and borrower profile:
    - Good borrowers: pay every installment that is due as of SIMULATION_DATE
    - Bad borrowers: pay 20-40% of installments then stop
    Failed payment attempts are added for bad borrowers after they stop.
    """
    records = []

    for _, loan in loan_df.iterrows():
        loan_id = loan["loan_id"]
        is_bad = loan["is_bad_borrower"]
        loan_schedule = schedule_df[
            schedule_df["loan_id"] == loan_id
        ].sort_values("installment_no").reset_index(drop=True)

        # Installments due as of simulation date
        due_installments = loan_schedule[
            loan_schedule["due_date"] <= SIMULATION_DATE
        ]

        if len(due_installments) == 0:
            continue

        if is_bad:
            # Bad borrower: pay 20-40% then stop
            num_paid = max(1, int(len(loan_schedule) * np.random.uniform(0.2, 0.4)))
            paid_installments = loan_schedule.head(num_paid)
        else:
            # Good borrower: pay all installments due so far
            paid_installments = due_installments

        for _, installment in paid_installments.iterrows():
            repayment_principal = float(installment["due_principal"])
            repayment_interest = float(installment["due_interest"])
            repayment_total = round(repayment_principal + repayment_interest, 2)
            transaction_date = pd.to_datetime(installment["due_date"]) + pd.Timedelta(
                days=np.random.randint(0, 3)
            )
            records.append({
                "repayment_transaction_id": f"REPAY_{loan_id}_{int(installment['installment_no']):02d}",
                "loan_id": loan_id,
                "transaction_date": transaction_date.date(),
                "accounting_date": transaction_date.date(),
                "repayment_total_amount": repayment_total,
                "repayment_principal": repayment_principal,
                "repayment_interest": repayment_interest,
                "repayment_overdue_interest": 0.00,
                "payment_status": "successful",
            })

        # Bad borrower: add 1-2 failed attempts after stopping
        if is_bad:
            failed_installments = loan_schedule.iloc[
                len(paid_installments): len(paid_installments) + 2
            ]
            for _, installment in failed_installments.iterrows():
                if pd.to_datetime(installment["due_date"]).date() > SIMULATION_DATE:
                    break
                repayment_principal = float(installment["due_principal"])
                repayment_interest = float(installment["due_interest"])
                repayment_total = round(repayment_principal + repayment_interest, 2)
                transaction_date = pd.to_datetime(installment["due_date"]) + pd.Timedelta(
                    days=np.random.randint(1, 5)
                )
                records.append({
                    "repayment_transaction_id": f"REPAY_{loan_id}_{int(installment['installment_no']):02d}_FAIL",
                    "loan_id": loan_id,
                    "transaction_date": transaction_date.date(),
                    "accounting_date": transaction_date.date(),
                    "repayment_total_amount": repayment_total,
                    "repayment_principal": repayment_principal,
                    "repayment_interest": repayment_interest,
                    "repayment_overdue_interest": 0.00,
                    "payment_status": "failed",
                })

    return pd.DataFrame(records)


def update_repayment_schedule(loan_df, schedule_df, repayment_df):
    updated = schedule_df.copy()
    successful = repayment_df[repayment_df["payment_status"] == "successful"]

    # Apply successful payments
    for _, repayment in successful.iterrows():
        loan_id = repayment["loan_id"]
        rem_principal = float(repayment["repayment_principal"])
        rem_interest = float(repayment["repayment_interest"])

        unsettled = updated[
            (updated["loan_id"] == loan_id) &
            (updated["installment_settled_flag"] == 0)
        ].sort_values("installment_no")

        for idx, inst in unsettled.iterrows():
            unpaid_p = float(inst["due_principal"]) - float(inst["paid_principal"])
            unpaid_i = float(inst["due_interest"]) - float(inst["paid_interest"])

            pp = min(rem_principal, unpaid_p)
            ip = min(rem_interest, unpaid_i)

            updated.loc[idx, "paid_principal"] = round(float(updated.loc[idx, "paid_principal"]) + pp, 2)
            updated.loc[idx, "paid_interest"] = round(float(updated.loc[idx, "paid_interest"]) + ip, 2)

            rem_principal = round(rem_principal - pp, 2)
            rem_interest = round(rem_interest - ip, 2)

            fully_paid = (
                round(float(updated.loc[idx, "paid_principal"]), 2) >= round(float(inst["due_principal"]), 2) and
                round(float(updated.loc[idx, "paid_interest"]), 2) >= round(float(inst["due_interest"]), 2)
            )
            if fully_paid:
                updated.loc[idx, "installment_settled_flag"] = 1

            if rem_principal <= 0 and rem_interest <= 0:
                break

    # Compute overdue days and overdue interest for unsettled past-due installments
    loan_rate_map = loan_df.set_index("loan_id")["interest_rate"].to_dict()

    for idx, row in updated.iterrows():
        if row["installment_settled_flag"] == 1:
            continue
        due_date = pd.to_datetime(row["due_date"]).date()
        if due_date >= SIMULATION_DATE:
            continue

        overdue_days = (SIMULATION_DATE - due_date).days
        unpaid_principal = round(float(row["due_principal"]) - float(row["paid_principal"]), 2)

        if unpaid_principal > 0 and overdue_days > 0:
            annual_rate = float(loan_rate_map[row["loan_id"]])
            overdue_interest = round(
                unpaid_principal * (annual_rate * 1.5) / 365 * overdue_days, 2
            )
            updated.loc[idx, "overdue_days"] = overdue_days
            updated.loc[idx, "overdue_interest_due"] = overdue_interest
            updated.loc[idx, "installment_overdue_flag"] = 1

    # Set loan-level overdue flag
    overdue_loans = set(updated[updated["installment_overdue_flag"] == 1]["loan_id"])
    for loan_id in overdue_loans:
        updated.loc[updated["loan_id"] == loan_id, "loan_overdue_flag"] = 1

    return updated


def assign_loan_status(loan_df, schedule_df):
    """
    Determine final loan_status based on repayment outcomes and time:
    - All installments settled → closed
    - Bad borrower, max overdue >= 120 days → written_off
    - Bad borrower, overdue but < 120 days → defaulted
    - Good borrower, installments not yet due → active
    """
    updated_loans = loan_df.copy()

    for idx, loan in loan_df.iterrows():
        loan_id = loan["loan_id"]
        loan_schedule = schedule_df[schedule_df["loan_id"] == loan_id]

        all_settled = loan_schedule["installment_settled_flag"].all()
        max_overdue = loan_schedule["overdue_days"].max()

        if all_settled:
            status = "closed"
        elif max_overdue >= CHARGE_OFF_DAYS:
            status = "written_off"
            # Charge-off amount = unpaid principal + overdue interest
            unpaid_principal = round(
                (loan_schedule["due_principal"] - loan_schedule["paid_principal"]).clip(lower=0).sum(), 2
            )
            unpaid_od_interest = round(loan_schedule["overdue_interest_due"].sum(), 2)
            charge_off_amount = round(unpaid_principal + unpaid_od_interest, 2)

            first_120_due = loan_schedule[
                loan_schedule["overdue_days"] >= CHARGE_OFF_DAYS
            ]["due_date"].min()
            charge_off_date = pd.to_datetime(first_120_due).date() + timedelta(days=CHARGE_OFF_DAYS)

            updated_loans.loc[idx, "charge_off_date"] = charge_off_date
            updated_loans.loc[idx, "charge_off_amount"] = charge_off_amount
        elif max_overdue > 0:
            status = "defaulted"
        else:
            status = "active"

        updated_loans.loc[idx, "loan_status"] = status

    return updated_loans


def generate_loan_transfers(loan_df):
    records = []
    transfer_counter = 1

    npl_counterparties = ["Cerberus Capital", "Lone Star Funds", "CarVal Investors"]
    abs_counterparties = ["Goldman Sachs ABS Trust", "JP Morgan Securitization"]

    eligible = loan_df[loan_df["loan_status"].isin(["written_off", "defaulted"])]

    for _, loan in eligible.iterrows():
        loan_id = loan["loan_id"]
        disbursement_amount = float(loan["disbursement_amount"])

        if loan["loan_status"] == "written_off":
            transfer_type = "NPL"
            discount_rate = round(np.random.uniform(0.70, 0.90), 4)
            face_value = float(loan["charge_off_amount"]) if loan["charge_off_amount"] else disbursement_amount
            charge_off_dt = loan["charge_off_date"]
            if charge_off_dt is not None:
                transfer_date = pd.to_datetime(charge_off_dt).date() + timedelta(
                    days=np.random.randint(30, 90)
                )
            else:
                continue
            counterparty = np.random.choice(npl_counterparties)

        else:  # defaulted — 50% chance of ABS
            if np.random.rand() > 0.5:
                continue
            transfer_type = "ABS"
            discount_rate = round(np.random.uniform(0.05, 0.20), 4)
            face_value = disbursement_amount
            transfer_date = pd.to_datetime(loan["transaction_date"]).date() + timedelta(
                days=np.random.randint(60, 180)
            )
            counterparty = np.random.choice(abs_counterparties)

        transfer_price = round(face_value * (1 - discount_rate), 2)

        records.append({
            "transfer_id": f"TRF{transfer_counter:06d}",
            "loan_id": loan_id,
            "transfer_date": transfer_date,
            "transfer_type": transfer_type,
            "face_value": face_value,
            "transfer_price": transfer_price,
            "discount_rate": discount_rate,
            "counterparty": counterparty,
        })
        transfer_counter += 1

    return pd.DataFrame(records)


def generate_accounting_entries(loan_df, schedule_df, repayment_df, transfer_df):
    records = []

    # 1. Disbursement
    for _, row in loan_df.iterrows():
        txn_id = row["disbursement_id"]
        amt = float(row["disbursement_amount"])
        base = dict(transaction_id=txn_id, loan_id=row["loan_id"],
                    transaction_type="disbursement",
                    transaction_date=row["transaction_date"],
                    accounting_date=row["accounting_date"])
        records += [
            {**base, "entry_id": f"AE_{txn_id}_DR", "account_code": "1301",
             "account_name": "Loans Receivable", "debit_amount": amt, "credit_amount": 0.00, "signed_amount": amt},
            {**base, "entry_id": f"AE_{txn_id}_CR", "account_code": "1002",
             "account_name": "Cash and Bank Deposits", "debit_amount": 0.00, "credit_amount": amt, "signed_amount": -amt},
        ]

    # 2. Normal interest accrual
    for _, row in schedule_df.iterrows():
        txn_id = f"ACCRUAL_{row['loan_id']}_{int(row['installment_no']):02d}"
        amt = float(row["due_interest"])
        base = dict(transaction_id=txn_id, loan_id=row["loan_id"],
                    transaction_type="interest_accrual",
                    transaction_date=row["due_date"], accounting_date=row["due_date"])
        records += [
            {**base, "entry_id": f"AE_{txn_id}_DR", "account_code": "1320",
             "account_name": "Interest Receivable", "debit_amount": amt, "credit_amount": 0.00, "signed_amount": amt},
            {**base, "entry_id": f"AE_{txn_id}_CR", "account_code": "4610",
             "account_name": "Interest Income", "debit_amount": 0.00, "credit_amount": amt, "signed_amount": -amt},
        ]

    # 3. Overdue interest accrual
    for _, row in schedule_df[schedule_df["overdue_interest_due"] > 0].iterrows():
        txn_id = f"OD_ACCRUAL_{row['loan_id']}_{int(row['installment_no']):02d}"
        amt = float(row["overdue_interest_due"])
        base = dict(transaction_id=txn_id, loan_id=row["loan_id"],
                    transaction_type="overdue_interest_accrual",
                    transaction_date=row["due_date"], accounting_date=row["due_date"])
        records += [
            {**base, "entry_id": f"AE_{txn_id}_DR", "account_code": "1321",
             "account_name": "Overdue Interest Receivable", "debit_amount": amt, "credit_amount": 0.00, "signed_amount": amt},
            {**base, "entry_id": f"AE_{txn_id}_CR", "account_code": "4611",
             "account_name": "Overdue Interest Income", "debit_amount": 0.00, "credit_amount": amt, "signed_amount": -amt},
        ]

    # 4. Repayment (successful only)
    for _, row in repayment_df[repayment_df["payment_status"] == "successful"].iterrows():
        txn_id = row["repayment_transaction_id"]
        base = dict(transaction_id=txn_id, loan_id=row["loan_id"],
                    transaction_type="repayment",
                    transaction_date=row["transaction_date"],
                    accounting_date=row["accounting_date"])
        records += [
            {**base, "entry_id": f"AE_{txn_id}_DR_BANK", "account_code": "1002",
             "account_name": "Cash and Bank Deposits",
             "debit_amount": row["repayment_total_amount"], "credit_amount": 0.00,
             "signed_amount": row["repayment_total_amount"]},
            {**base, "entry_id": f"AE_{txn_id}_CR_PRINCIPAL", "account_code": "1301",
             "account_name": "Loans Receivable",
             "debit_amount": 0.00, "credit_amount": row["repayment_principal"],
             "signed_amount": -row["repayment_principal"]},
            {**base, "entry_id": f"AE_{txn_id}_CR_INTEREST", "account_code": "1320",
             "account_name": "Interest Receivable",
             "debit_amount": 0.00, "credit_amount": row["repayment_interest"],
             "signed_amount": -row["repayment_interest"]},
        ]

    # 5. Charge-off
    for _, row in loan_df[loan_df["loan_status"] == "written_off"].iterrows():
        txn_id = f"CHARGEOFF_{row['loan_id']}"
        amt = float(row["charge_off_amount"])
        base = dict(transaction_id=txn_id, loan_id=row["loan_id"],
                    transaction_type="charge_off",
                    transaction_date=row["charge_off_date"],
                    accounting_date=row["charge_off_date"])
        records += [
            {**base, "entry_id": f"AE_{txn_id}_DR", "account_code": "7111",
             "account_name": "Bad Debt Expense – Charge-off",
             "debit_amount": amt, "credit_amount": 0.00, "signed_amount": amt},
            {**base, "entry_id": f"AE_{txn_id}_CR", "account_code": "1301",
             "account_name": "Loans Receivable",
             "debit_amount": 0.00, "credit_amount": amt, "signed_amount": -amt},
        ]

    # 6. Loan transfer
    for _, row in transfer_df.iterrows():
        txn_id = row["transfer_id"]
        face = float(row["face_value"])
        price = float(row["transfer_price"])
        gain_loss = round(price - face, 2)
        base = dict(transaction_id=txn_id, loan_id=row["loan_id"],
                    transaction_type="loan_transfer",
                    transaction_date=row["transfer_date"],
                    accounting_date=row["transfer_date"])
        records.append({**base, "entry_id": f"AE_{txn_id}_DR_BANK", "account_code": "1002",
                        "account_name": "Cash and Bank Deposits",
                        "debit_amount": price, "credit_amount": 0.00, "signed_amount": price})
        records.append({**base, "entry_id": f"AE_{txn_id}_CR_LOAN", "account_code": "1301",
                        "account_name": "Loans Receivable",
                        "debit_amount": 0.00, "credit_amount": face, "signed_amount": -face})
        if gain_loss < 0:
            records.append({**base, "entry_id": f"AE_{txn_id}_DR_LOSS", "account_code": "7120",
                            "account_name": "Loss on Loan Transfer",
                            "debit_amount": abs(gain_loss), "credit_amount": 0.00, "signed_amount": abs(gain_loss)})
        elif gain_loss > 0:
            records.append({**base, "entry_id": f"AE_{txn_id}_CR_GAIN", "account_code": "6013",
                            "account_name": "Gain on Loan Transfer",
                            "debit_amount": 0.00, "credit_amount": gain_loss, "signed_amount": -gain_loss})

    return pd.DataFrame(records)


def main():
    loan_df = generate_loan_transactions(n=100)
    schedule_df = generate_repayment_schedule(loan_df)
    repayment_df = generate_repayment_transactions(loan_df, schedule_df)
    updated_schedule_df = update_repayment_schedule(loan_df, schedule_df, repayment_df)
    loan_df = assign_loan_status(loan_df, updated_schedule_df)
    transfer_df = generate_loan_transfers(loan_df)
    accounting_df = generate_accounting_entries(
        loan_df, updated_schedule_df, repayment_df, transfer_df
    )

    # Drop internal helper column before saving
    loan_df = loan_df.drop(columns=["is_bad_borrower"])

    loan_df.to_csv(RAW_DIR / "loan_transactions.csv", index=False)
    updated_schedule_df.to_csv(RAW_DIR / "repayment_schedule.csv", index=False)
    repayment_df.to_csv(RAW_DIR / "repayment_transactions.csv", index=False)
    accounting_df.to_csv(RAW_DIR / "accounting_entries.csv", index=False)
    transfer_df.to_csv(RAW_DIR / "loan_transfers.csv", index=False)

    print("Sample data generated successfully.")
    print(f"\nLoan transactions:        {len(loan_df)} records")
    print(f"  - active:               {(loan_df['loan_status'] == 'active').sum()}")
    print(f"  - closed:               {(loan_df['loan_status'] == 'closed').sum()}")
    print(f"  - defaulted:            {(loan_df['loan_status'] == 'defaulted').sum()}")
    print(f"  - written_off:          {(loan_df['loan_status'] == 'written_off').sum()}")
    print(f"\nRepayment schedule:       {len(updated_schedule_df)} records")
    print(f"  - overdue installments: {(updated_schedule_df['installment_overdue_flag'] == 1).sum()}")
    print(f"\nRepayment transactions:   {len(repayment_df)} records")
    print(f"  - successful:           {(repayment_df['payment_status'] == 'successful').sum()}")
    print(f"  - failed:               {(repayment_df['payment_status'] == 'failed').sum()}")
    print(f"\nLoan transfers:           {len(transfer_df)} records")
    print(f"  - NPL:                  {(transfer_df['transfer_type'] == 'NPL').sum() if len(transfer_df) > 0 else 0}")
    print(f"  - ABS:                  {(transfer_df['transfer_type'] == 'ABS').sum() if len(transfer_df) > 0 else 0}")
    print(f"\nAccounting entries:       {len(accounting_df)} records")


if __name__ == "__main__":
    main()
