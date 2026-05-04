import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

np.random.seed(99)

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
INCOMING_DIR = BASE_DIR / "data" / "incoming"
INCOMING_DIR.mkdir(parents=True, exist_ok=True)


def generate_new_incoming_loan_transactions(n=100):
    """
    Generate a new incoming loan transaction batch.

    This simulates new data received from internal systems or external partner platforms.
    The batch is separate from historical/core data.
    """

    records = []
    start_date = datetime(2026, 5, 1)

    for i in range(1, n + 1):
        loan_id = f"LN_NEW{i:06d}"
        customer_id = f"CUST{np.random.randint(1, 120):06d}"

        transaction_date = start_date + timedelta(days=np.random.randint(0, 10))
        disbursement_id = f"DISB{transaction_date.strftime('%Y%m%d')}{i:06d}"

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


def inject_loan_transaction_issues(incoming_df, historical_df):
    """
    Inject realistic data quality issues into the new incoming batch.
    """

    corrupted_df = incoming_df.copy()

    # 1. Missing loan_id - strong validation failure
    corrupted_df.loc[0, "loan_id"] = None

    # 2. Missing disbursement_id - strong validation failure
    corrupted_df.loc[1, "disbursement_id"] = None

    # 3. Duplicate disbursement_id within the same incoming batch - strong validation failure
    corrupted_df.loc[2, "disbursement_id"] = corrupted_df.loc[3, "disbursement_id"]

    # 4. Duplicate disbursement_id with historical/core data - strong validation failure
    historical_disbursement_id = historical_df.loc[0, "disbursement_id"]
    corrupted_df.loc[4, "disbursement_id"] = historical_disbursement_id

    # 5. Negative disbursement amount - strong validation failure
    corrupted_df.loc[5, "disbursement_amount"] = -10000

    # 6. Interest rate out of business range - strong validation failure
    corrupted_df.loc[6, "interest_rate"] = 0.55

    # 7. Missing accounting_date - strong validation failure
    corrupted_df.loc[7, "accounting_date"] = None

    # 8. Missing source_system - strong validation failure
    corrupted_df.loc[8, "source_system"] = None

    # 9. Invalid disbursement_id format - strong validation failure
    corrupted_df.loc[9, "disbursement_id"] = "BAD_ID_000009"

    # 10. Missing region - soft validation warning only
    corrupted_df.loc[10, "region"] = None

    return corrupted_df


def main():
    historical_df = pd.read_csv(RAW_DIR / "loan_transactions.csv")

    incoming_df = generate_new_incoming_loan_transactions(n=100)
    corrupted_incoming_df = inject_loan_transaction_issues(incoming_df, historical_df)

    corrupted_incoming_df.to_csv(
        INCOMING_DIR / "loan_transactions_incoming.csv",
        index=False
    )

    print("New incoming loan transaction data with injected issues generated successfully.")
    print(f"Incoming records: {len(corrupted_incoming_df)}")
    print("Expected outcome after validation:")
    print("- Most records should be accepted")
    print("- Strong validation failures should be rejected")
    print("- Missing region should be accepted with soft warning")
    print("Output file: data/incoming/loan_transactions_incoming.csv")


if __name__ == "__main__":
    main()
