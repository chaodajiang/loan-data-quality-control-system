import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

INCOMING_DIR = BASE_DIR / "data" / "incoming"
ACCEPTED_DIR = BASE_DIR / "data" / "accepted"
REJECTED_DIR = BASE_DIR / "data" / "rejected"
REPORTS_DIR = BASE_DIR / "reports"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def calculate_quality_metrics():
    incoming_df = pd.read_csv(INCOMING_DIR / "loan_transactions_incoming.csv")
    accepted_df = pd.read_csv(ACCEPTED_DIR / "loan_transactions_accepted.csv")
    rejected_df = pd.read_csv(REJECTED_DIR / "loan_transactions_rejected.csv")
    error_log_df = pd.read_csv(REJECTED_DIR / "validation_error_log.csv")

    total_records = len(incoming_df)
    accepted_records = len(accepted_df)
    rejected_records = len(rejected_df)

    strong_errors = error_log_df[error_log_df["rule_type"] == "strong"]
    soft_warnings = error_log_df[error_log_df["rule_type"] == "soft"]

    rejection_rate = rejected_records / total_records if total_records > 0 else 0
    acceptance_rate = accepted_records / total_records if total_records > 0 else 0
    soft_warning_rate = len(soft_warnings["row_index"].unique()) / total_records if total_records > 0 else 0

    issue_summary = (
        error_log_df
        .groupby(["rule_type", "field", "error_code"], as_index=False)
        .size()
        .rename(columns={"size": "issue_count"})
        .sort_values("issue_count", ascending=False)
    )

    overall_quality_score = round(
        100
        - rejection_rate * 70
        - soft_warning_rate * 10,
        2
    )

    metrics = {
        "total_records": total_records,
        "accepted_records": accepted_records,
        "rejected_records": rejected_records,
        "acceptance_rate": round(acceptance_rate, 4),
        "rejection_rate": round(rejection_rate, 4),
        "strong_error_count": len(strong_errors),
        "soft_warning_count": len(soft_warnings),
        "soft_warning_rate": round(soft_warning_rate, 4),
        "overall_quality_score": overall_quality_score,
    }

    metrics_df = pd.DataFrame([metrics])

    return metrics_df, issue_summary


def main():
    metrics_df, issue_summary = calculate_quality_metrics()

    metrics_df.to_csv(REPORTS_DIR / "data_quality_metrics.csv", index=False)
    issue_summary.to_csv(REPORTS_DIR / "issue_summary.csv", index=False)

    print("Data quality monitoring completed.")
    print("\nSummary Metrics")
    print(metrics_df.to_string(index=False))

    print("\nIssue Summary")
    print(issue_summary.to_string(index=False))

    print("\nOutputs:")
    print("- reports/data_quality_metrics.csv")
    print("- reports/issue_summary.csv")


if __name__ == "__main__":
    main()
