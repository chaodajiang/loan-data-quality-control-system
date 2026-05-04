import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"


def check_principal_balance(loan_df, schedule_df):
    """
    Check whether total scheduled principal equals disbursement amount for each loan.
    """

    principal_sum = (
        schedule_df
        .groupby("loan_id", as_index=False)["due_principal"]
        .sum()
        .rename(columns={"due_principal": "scheduled_principal_total"})
    )

    check_df = loan_df.merge(principal_sum, on="loan_id", how="left")

    check_df["principal_difference"] = (
        check_df["scheduled_principal_total"] - check_df["disbursement_amount"]
    ).round(2)

    failed = check_df[check_df["principal_difference"] != 0]

    return failed[[
        "loan_id",
        "disbursement_amount",
        "scheduled_principal_total",
        "principal_difference"
    ]]


def check_accounting_balance(accounting_df):
    """
    Check whether debit equals credit for each transaction.
    """

    balance_df = (
        accounting_df
        .groupby("transaction_id", as_index=False)
        .agg(
            total_debit=("debit_amount", "sum"),
            total_credit=("credit_amount", "sum"),
            net_signed_amount=("signed_amount", "sum")
        )
    )

    balance_df["debit_credit_difference"] = (
        balance_df["total_debit"] - balance_df["total_credit"]
    ).round(2)

    balance_df["net_signed_amount"] = balance_df["net_signed_amount"].round(2)

    failed = balance_df[
        (balance_df["debit_credit_difference"] != 0)
        | (balance_df["net_signed_amount"] != 0)
    ]

    return failed


def check_repayment_amount(repayment_df):
    """
    Check whether repayment_total_amount equals repayment_principal + repayment_interest.
    """

    repayment_df = repayment_df.copy()

    repayment_df["calculated_total"] = (
        repayment_df["repayment_principal"] + repayment_df["repayment_interest"]
    ).round(2)

    repayment_df["repayment_difference"] = (
        repayment_df["repayment_total_amount"] - repayment_df["calculated_total"]
    ).round(2)

    failed = repayment_df[repayment_df["repayment_difference"] != 0]

    return failed[[
        "repayment_transaction_id",
        "loan_id",
        "repayment_total_amount",
        "repayment_principal",
        "repayment_interest",
        "calculated_total",
        "repayment_difference"
    ]]


def check_repayment_schedule_payment(schedule_df):
    """
    Check whether paid principal/interest exceeds due principal/interest.
    """

    schedule_df = schedule_df.copy()

    failed = schedule_df[
        (schedule_df["paid_principal"] > schedule_df["due_principal"])
        | (schedule_df["paid_interest"] > schedule_df["due_interest"])
    ]

    return failed[[
        "loan_id",
        "installment_no",
        "due_principal",
        "paid_principal",
        "due_interest",
        "paid_interest"
    ]]


def run_all_checks():
    loan_df = pd.read_csv(RAW_DIR / "loan_transactions.csv")
    schedule_df = pd.read_csv(RAW_DIR / "repayment_schedule.csv")
    repayment_df = pd.read_csv(RAW_DIR / "repayment_transactions.csv")
    accounting_df = pd.read_csv(RAW_DIR / "accounting_entries.csv")

    checks = {
        "Principal Balance Check": check_principal_balance(loan_df, schedule_df),
        "Accounting Balance Check": check_accounting_balance(accounting_df),
        "Repayment Amount Check": check_repayment_amount(repayment_df),
        "Repayment Schedule Payment Check": check_repayment_schedule_payment(schedule_df),
    }

    print("\nData Quality Self-Check Results")
    print("=" * 40)

    all_passed = True

    for check_name, failed_df in checks.items():
        if failed_df.empty:
            print(f"[PASS] {check_name}")
        else:
            all_passed = False
            print(f"[FAIL] {check_name}: {len(failed_df)} issue(s) found")
            print(failed_df.head(10).to_string(index=False))
            print("-" * 40)

    print("=" * 40)

    if all_passed:
        print("All self-checks passed. Normal business data is internally consistent.")
    else:
        print("Some checks failed. Please review the failed records above.")


if __name__ == "__main__":
    run_all_checks()
