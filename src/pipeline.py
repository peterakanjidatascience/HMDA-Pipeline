import argparse
import csv
from pathlib import Path

REQUIRED_COLUMNS = [
    "action_taken",
    "state_abb",
    "respondent_id",
    "loan_amount_000s",
    "applicant_income_000s"]


def validate_headers(headers):
    """Check that all required columns exist."""

    if not headers:
        raise ValueError("The CSV has no header row.")

    missing = [column for column in REQUIRED_COLUMNS if column not in headers]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def validate_row(row, row_number):
    """Validate the essential values in a record."""

    for column in REQUIRED_COLUMNS:
        if row.get(column) is None:
            raise ValueError(f"Row {row_number}: missing {column}")

    if not row["respondent_id"].strip():
        raise ValueError(f"Row {row_number}: empty respondent ID")

    state = row["state_abb"].strip()

    if len(state) != 2 or not state.isalpha():
        raise ValueError(f"Row {row_number}: invalid state abbreviation")

    action = row["action_taken"].strip()

    if not action.isdigit() or int(action) < 1:
        raise ValueError(f"Row {row_number}: invalid action_taken")

    amount = row["loan_amount_000s"].strip()

    try:
        loan_amount = float(amount)
    except ValueError as exc:
        raise ValueError(f"Row {row_number}: invalid loan amount") from exc

    if not (0 < loan_amount < float("inf")):
        raise ValueError(f"Row {row_number}: invalid loan amount")

    income = row["applicant_income_000s"].strip()

    # Income can legitimately be missing in HMDA data.
    if income not in ("", "NA", "Exempt"):
        try:
            income_value = float(income)
        except ValueError as exc:
            raise ValueError(f"Row {row_number}: invalid income") from exc

        if not (float("-inf") < income_value < float("inf")):
            raise ValueError(f"Row {row_number}: invalid income")


def process_file(input_path, output_path):
    """Validate the CSV and retain required columns."""

    input_path = Path(input_path)
    output_path = Path(output_path)

    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if input_path.resolve() == output_path.resolve():
        raise ValueError("Input and output files must differ.")

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_path = output_path.with_name(output_path.name + ".tmp")

    count = 0

    try:
        with (
            input_path.open("r", encoding="utf-8-sig", newline="") as source,
            temp_path.open("w", encoding="utf-8", newline="") as destination,
        ):
            reader = csv.DictReader(source)

            validate_headers(reader.fieldnames)

            writer = csv.DictWriter(
                destination,
                fieldnames=REQUIRED_COLUMNS,
            )

            writer.writeheader()

            for row_number, row in enumerate(reader, start=2):
                validate_row(row, row_number)

                cleaned_row = {
                    column: row[column].strip() for column in REQUIRED_COLUMNS
                }

                writer.writerow(cleaned_row)
                count += 1

        temp_path.replace(output_path)

    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

    return count


def main():
    parser = argparse.ArgumentParser(description="HMDA data processing pipeline")

    parser.add_argument(
        "--input",
        default="data/raw/hmda_sample.csv",
    )

    parser.add_argument(
        "--output",
        default="data/processed/hmda_clean.csv",
    )

    args = parser.parse_args()

    count = process_file(
        args.input,
        args.output,
    )

    print("Pipeline completed successfully")
    print(f"Records processed: {count}")
    print(f"Output: {args.output}")


if __name__ == "__main__":
    main()
