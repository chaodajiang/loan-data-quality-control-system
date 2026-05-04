import re
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

INCOMING_DIR = BASE_DIR / "data" / "incoming"
RAW_DIR = BASE_DIR / "data" / "raw"
ACCEPTED_DIR = BASE_DIR / "data" / "accepted"
REJECTED_DIR = BASE_DIR / "data" / "rejected"

ACCEPTED_DIR.mkdir(parents=True, exist_ok=True)
REJECTED_DIR.mkdir(parents=True, exist_ok=True)

DISBURSEMENT_ID_PATTERN = r"^DISB\d{8}\d{6}$"


def load_data():
    incoming_df = pd.read_csv(INCOMING_DIR / "loan_transactions_incoming.csv")

    # In this project, raw loan_transactions.csv simulates historical/core data.
    # In a real system, this would come from an accepted/core transaction table.
    historical_df = pd.read_csv(RAW_DIR / "loan_transactions.csv")

    return incoming_df, historical_df


def add_error(error_log, row_index, loan_id, disbursement_id, rule_type, field, error_code, error_message):
    error_log.append({
        "row_index": row_index,
        "loan_id": loan_id,
        "disbursement_id": disbursement_id,
        "rule_type": rule_type,
        "field": field,
        "error_code": error_code,
        "error_message": error_message
    })


def validate_required_fields(row, row_index, error_log):
    required_fields = [
        "loan_id",
        "disbursement_id",
        "customer_id",
        "source_system",
        "transaction_date",
        "accounting_date",
        "disbursement_amount",
        "interest_rate",
        "term_months",
        "loan_status",
    ]

    for field in required_fields:
        if pd.isna(row.get(field)) or str(row.get(field)).strip() == "":
            add_error(
                error_log=error_log,
                row_index=row_index,
                loan_id=row.get("loan_id"),
                disbursement_id=row.get("disbursement_id"),
                rule_type="strong",
                field=field,
                error_code="MISSING_REQUIRED_FIELD",
                error_message=f"{field} is required but missing."
            )


def validate_field_values(row, row_index, error_log):
    disbursement_amount = row.get("disbursement_amount")
    interest_rate = row.get("interest_rate")

    if not pd.isna(disbursement_amount):
        try:
            if float(disbursement_amount) <= 0:
                add_error(
                    error_log,
                    row_index,
                    row.get("loan_id"),
                    row.get("disbursement_id"),
                    "strong",
                    "disbursement_amount",
                    "INVALID_AMOUNT",
                    "disbursement_amount must be greater than 0."
                )
        except ValueError:
            add_error(
                error_log,
                row_index,
                row.get("loan_id"),
                row.get("disbursement_id"),
                "strong",
                "disbursement_amount",
                "INVALID_AMOUNT_TYPE",
                "disbursement_amount must be numeric."
            )

    if not pd.isna(interest_rate):
        try:
            interest_rate = float(interest_rate)
            if interest_rate <= 0 or interest_rate > 0.36:
                add_error(
                    error_log,
                    row_index,
                    row.get("loan_id"),
                    row.get("disbursement_id"),
                    "strong",
                    "interest_rate",
                    "INVALID_INTEREST_RATE",
                    "interest_rate must be greater than 0 and no more than 36%."
                )
        except ValueError:
            add_error(
                error_log,
                row_index,
                row.get("loan_id"),
                row.get("disbursement_id"),
                "strong",
                "interest_rate",
                "INVALID_INTEREST_RATE_TYPE",
                "interest_rate must be numeric."
            )


def validate_disbursement_id_format(row, row_index, error_log):
    disbursement_id = row.get("disbursement_id")

    if pd.isna(disbursement_id):
        return

    disbursement_id = str(disbursement_id)

    if not re.match(DISBURSEMENT_ID_PATTERN, disbursement_id):
        add_error(
            error_log,
            row_index,
            row.get("loan_id"),
            disbursement_id,
            "strong",
            "disbursement_id",
            "INVALID_DISBURSEMENT_ID_FORMAT",
            "disbursement_id must follow format DISBYYYYMMDDNNNNNN."
        )


def validate_batch_duplicate(incoming_df, error_log):
    duplicated_mask = (
        incoming_df["disbursement_id"].notna()
        & incoming_df["disbursement_id"].duplicated(keep=False)
    )

    duplicated_rows = incoming_df[duplicated_mask]

    for row_index, row in duplicated_rows.iterrows():
        add_error(
            error_log,
            row_index,
            row.get("loan_id"),
            row.get("disbursement_id"),
            "strong",
            "disbursement_id",
            "DUPLICATE_IN_BATCH",
            "disbursement_id is duplicated within the incoming batch."
        )


def validate_historical_duplicate(incoming_df, historical_df, error_log):
    historical_ids = set(historical_df["disbursement_id"].dropna().astype(str))

    duplicate_history_rows = incoming_df[
        incoming_df["disbursement_id"].notna()
        & incoming_df["disbursement_id"].astype(str).isin(historical_ids)
    ]

    for row_index, row in duplicate_history_rows.iterrows():
        add_error(
            error_log,
            row_index,
            row.get("loan_id"),
            row.get("disbursement_id"),
            "strong",
            "disbursement_id",
            "DUPLICATE_WITH_HISTORY",
            "disbursement_id already exists in historical/core data."
        )


def validate_soft_rules(row, row_index, error_log):
    if pd.isna(row.get("region")) or str(row.get("region")).strip() == "":
        add_error(
            error_log,
            row_index,
            row.get("loan_id"),
            row.get("disbursement_id"),
            "soft",
            "region",
            "MISSING_OPTIONAL_FIELD",
            "region is missing but record can still be accepted."
        )


def run_validation():
    incoming_df, historical_df = load_data()

    error_log = []

    for row_index, row in incoming_df.iterrows():
        validate_required_fields(row, row_index, error_log)
        validate_field_values(row, row_index, error_log)
        validate_disbursement_id_format(row, row_index, error_log)
        validate_soft_rules(row, row_index, error_log)

    validate_batch_duplicate(incoming_df, error_log)
    validate_historical_duplicate(incoming_df, historical_df, error_log)

    error_log_df = pd.DataFrame(error_log)

    if error_log_df.empty:
        rejected_indices = set()
        warning_indices = set()
    else:
        strong_errors = error_log_df[error_log_df["rule_type"] == "strong"]
        soft_warnings = error_log_df[error_log_df["rule_type"] == "soft"]

        rejected_indices = set(strong_errors["row_index"].unique())
        warning_indices = set(soft_warnings["row_index"].unique())

    accepted_df = incoming_df[~incoming_df.index.isin(rejected_indices)].copy()
    rejected_df = incoming_df[incoming_df.index.isin(rejected_indices)].copy()

    accepted_df["validation_status"] = "accepted"
    accepted_df["has_soft_warning"] = accepted_df.index.isin(warning_indices)

    rejected_df["validation_status"] = "rejected"

    accepted_df.to_csv(ACCEPTED_DIR / "loan_transactions_accepted.csv", index=False)
    rejected_df.to_csv(REJECTED_DIR / "loan_transactions_rejected.csv", index=False)
    error_log_df.to_csv(REJECTED_DIR / "validation_error_log.csv", index=False)

    print("Validation pipeline completed.")
    print(f"Incoming records: {len(incoming_df)}")
    print(f"Accepted records: {len(accepted_df)}")
    print(f"Rejected records: {len(rejected_df)}")
    print(f"Validation issues logged: {len(error_log_df)}")
    print("Outputs:")
    print("- data/accepted/loan_transactions_accepted.csv")
    print("- data/rejected/loan_transactions_rejected.csv")
    print("- data/rejected/validation_error_log.csv")


if __name__ == "__main__":
    run_validation()
