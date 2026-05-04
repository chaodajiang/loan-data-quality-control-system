import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
INCOMING_DIR = BASE_DIR / "data" / "incoming"
INCOMING_DIR.mkdir(parents=True, exist_ok=True)


def inject_loan_transaction_issues(loan_df):
    """
    Inject realistic data quality issues into loan transaction data.

    The purpose is to simulate incoming data from internal systems
    and external partner platforms before validation.
    """

    corrupted_df = loan_df.copy()

    # 1. Missing loan_id - strong validation failure
    corrupted_df.loc[0, "loan_id"] = None

    # 2. Missing disbursement_id - strong validation failure
    corrupted_df.loc[1, "disbursement_id"] = None

    # 3. Duplicate disbursement_id - strong validation failure
    corrupted_df.loc[2, "disbursement_id"] = corrupted_df.loc[3, "disbursement_id"]

    # 4. Negative disbursement amount - strong validation failure
    corrupted_df.loc[4, "disbursement_amount"] = -10000

    # 5. Interest rate out of business range - strong validation failure
    corrupted_df.loc[5, "interest_rate"] = 0.55

    # 6. Missing accounting_date - strong validation failure
    corrupted_df.loc[6, "accounting_date"] = None

    # 7. Missing source_system - strong validation failure
    corrupted_df.loc[7, "source_system"] = None

    # 8. Missing region - soft validation warning
    corrupted_df.loc[8, "region"] = None

    return corrupted_df


def main():
    loan_df = pd.read_csv(RAW_DIR / "loan_transactions.csv")

    corrupted_loan_df = inject_loan_transaction_issues(loan_df)

    corrupted_loan_df.to_csv(
        INCOMING_DIR / "loan_transactions_incoming.csv",
        index=False
    )

    print("Incoming loan transaction data with injected issues generated successfully.")
    print(f"Original records: {len(loan_df)}")
    print(f"Incoming records: {len(corrupted_loan_df)}")
    print("Output file: data/incoming/loan_transactions_incoming.csv")


if __name__ == "__main__":
    main()
