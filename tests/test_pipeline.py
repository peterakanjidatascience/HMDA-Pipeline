import csv

import pytest

from src.pipeline import (
    REQUIRED_COLUMNS,
    process_file,
    validate_headers,
    validate_row,
)


def sample_row():
    return {
        "action_taken": "1",
        "state_abb": "CA",
        "respondent_id": "10001",
        "loan_amount_000s": "250",
        "applicant_income_000s": "75",
    }


def write_csv(path, headers, rows):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)


def test_valid_headers():
    validate_headers(REQUIRED_COLUMNS)


def test_missing_headers():
    with pytest.raises(ValueError, match="Missing required columns"):
        validate_headers(["action_taken", "state_abb"])


def test_valid_row():
    validate_row(sample_row(), 2)


def test_invalid_state():
    row = sample_row()
    row["state_abb"] = "California"

    with pytest.raises(ValueError, match="state abbreviation"):
        validate_row(row, 2)


def test_invalid_loan_amount():
    row = sample_row()
    row["loan_amount_000s"] = "unknown"

    with pytest.raises(ValueError, match="loan amount"):
        validate_row(row, 2)


def test_missing_income_allowed():
    row = sample_row()
    row["applicant_income_000s"] = ""

    validate_row(row, 2)


def test_pipeline_output(tmp_path):
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"

    headers = REQUIRED_COLUMNS + ["loan_type"]

    rows = [
        ["1", "CA", "10001", "250", "75", "1"],
        ["3", "NY", "10002", "180", "60", "2"],
    ]

    write_csv(input_file, headers, rows)

    count = process_file(input_file, output_file)

    assert count == 2
    assert output_file.exists()

    with output_file.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        results = list(reader)

        assert reader.fieldnames == REQUIRED_COLUMNS

    assert len(results) == 2
    assert results[0]["state_abb"] == "CA"
    assert "loan_type" not in results[0]


def test_missing_input_file(tmp_path):
    input_file = tmp_path / "missing.csv"
    output_file = tmp_path / "output.csv"

    with pytest.raises(FileNotFoundError):
        process_file(input_file, output_file)


def test_invalid_file_creates_no_output(tmp_path):
    input_file = tmp_path / "invalid.csv"
    output_file = tmp_path / "output.csv"

    rows = [
        ["1", "CA", "10001", "250", "75"],
        ["1", "NY", "10002", "invalid", "60"],
    ]

    write_csv(input_file, REQUIRED_COLUMNS, rows)

    with pytest.raises(ValueError):
        process_file(input_file, output_file)

    assert not output_file.exists()
    assert not (tmp_path / "output.csv.tmp").exists()
