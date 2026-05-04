import pandas as pd
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = BASE_DIR / "reports"

METRICS_FILE = REPORTS_DIR / "data_quality_metrics.csv"
ISSUE_SUMMARY_FILE = REPORTS_DIR / "issue_summary.csv"
REPORT_FILE = REPORTS_DIR / "monthly_data_quality_report.md"


def generate_key_observations(issue_summary_df):
    observations = []

    if issue_summary_df.empty:
        observations.append("- No validation issues were found in this batch.")
        return observations

    top_issues = issue_summary_df.head(3)

    for _, row in top_issues.iterrows():
        observations.append(
            f"- {row['error_code']} on `{row['field']}` occurred {int(row['issue_count'])} time(s)."
        )

    duplicate_issues = issue_summary_df[
        issue_summary_df["error_code"].str.contains("DUPLICATE", na=False)
    ]

    if not duplicate_issues.empty:
        observations.append(
            "- Duplicate disbursement ID issues indicate potential transaction-level control or idempotency risks."
        )

    missing_required_issues = issue_summary_df[
        issue_summary_df["error_code"].str.contains("MISSING_REQUIRED_FIELD", na=False)
    ]

    if not missing_required_issues.empty:
        observations.append(
            "- Missing required fields suggest upstream data capture or interface validation gaps."
        )

    return observations


def generate_business_interpretation(metrics, issue_summary_df):
    interpretation = []

    quality_score = float(metrics["overall_quality_score"])
    rejection_rate = float(metrics["rejection_rate"])
    soft_warning_count = int(metrics["soft_warning_count"])

    interpretation.append(
        f"The overall data quality score for this batch is {quality_score}, "
        f"with a rejection rate of {rejection_rate:.2%}."
    )

    if rejection_rate >= 0.10:
        interpretation.append(
            "The rejection rate is relatively high and should be reviewed before downstream financial processing."
        )
    elif rejection_rate > 0:
        interpretation.append(
            "A small portion of records failed strong validation and should be corrected before re-submission."
        )
    else:
        interpretation.append(
            "No records failed strong validation, indicating strong ingestion-level data quality."
        )

    if not issue_summary_df.empty:
        interpretation.append(
            "The main risks are related to transaction integrity, including duplicate disbursement IDs, "
            "missing required fields, invalid transaction amounts, or invalid interest rates."
        )

    if soft_warning_count > 0:
        interpretation.append(
            "Soft warnings do not block processing, but they should be monitored because incomplete optional fields "
            "can reduce downstream analytics and reporting quality."
        )

    return interpretation


def generate_report():
    metrics_df = pd.read_csv(METRICS_FILE)
    issue_summary_df = pd.read_csv(ISSUE_SUMMARY_FILE)

    metrics = metrics_df.iloc[0]
    report_date = datetime.now().strftime("%Y-%m-%d")

    report_lines = []

    report_lines.append("# Monthly Data Quality Report")
    report_lines.append("")
    report_lines.append(f"**Report Date:** {report_date}")
    report_lines.append("")
    report_lines.append("## 1. Executive Summary")
    report_lines.append("")
    report_lines.append(
        "This report summarizes the data quality results for the latest incoming loan transaction batch. "
        "The validation process applies strong validation rules to block critical data issues and soft validation rules "
        "to flag non-critical issues."
    )

    report_lines.append("")
    report_lines.append("## 2. Key Metrics")
    report_lines.append("")
    report_lines.append(f"- Total incoming records: {int(metrics['total_records'])}")
    report_lines.append(f"- Accepted records: {int(metrics['accepted_records'])}")
    report_lines.append(f"- Rejected records: {int(metrics['rejected_records'])}")
    report_lines.append(f"- Acceptance rate: {metrics['acceptance_rate']:.2%}")
    report_lines.append(f"- Rejection rate: {metrics['rejection_rate']:.2%}")
    report_lines.append(f"- Strong error count: {int(metrics['strong_error_count'])}")
    report_lines.append(f"- Soft warning count: {int(metrics['soft_warning_count'])}")
    report_lines.append(f"- Overall data quality score: {metrics['overall_quality_score']}")

    report_lines.append("")
    report_lines.append("## 3. Issue Summary")
    report_lines.append("")
    report_lines.append("### Key Observations")
    report_lines.append("")

    for observation in generate_key_observations(issue_summary_df):
        report_lines.append(observation)

    report_lines.append("")

    if issue_summary_df.empty:
        report_lines.append("No validation issues were found.")
    else:
        report_lines.append("| Rule Type | Field | Error Code | Issue Count |")
        report_lines.append("|---|---|---|---:|")

        for _, row in issue_summary_df.iterrows():
            report_lines.append(
                f"| {row['rule_type']} | {row['field']} | {row['error_code']} | {int(row['issue_count'])} |"
            )

    report_lines.append("")
    report_lines.append("## 4. Business Interpretation")
    report_lines.append("")

    for paragraph in generate_business_interpretation(metrics, issue_summary_df):
        report_lines.append(paragraph)
        report_lines.append("")

    report_lines.append("## 5. Recommended Actions")
    report_lines.append("")
    report_lines.append("- Review rejected records before re-submission.")
    report_lines.append("- Strengthen upstream controls for required fields.")
    report_lines.append("- Monitor duplicate disbursement IDs across both incoming and historical data.")
    report_lines.append("- Track soft warning trends to improve optional field completeness.")
    report_lines.append("")

    REPORT_FILE.write_text("\n".join(report_lines), encoding="utf-8")

    print("Monthly data quality report generated successfully.")
    print(f"Output file: {REPORT_FILE}")


if __name__ == "__main__":
    generate_report()
