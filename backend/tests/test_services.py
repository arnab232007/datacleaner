"""
Unit tests for DataCleaner cleaning services.
Run: pytest tests/ -v   (from /backend directory)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
import pytest

from services.missing  import handle_missing
from services.dedup    import remove_duplicates
from services.types    import correct_types
from services.outliers import handle_outliers
from services.text     import standardize_text
from services.colnames import clean_column_names
from services.dates    import standardize_dates


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def messy_df():
    return pd.DataFrame({
        "Name":   ["Alice", "Bob", None, "  Charlie  ", "Bob"],
        "Age":    [25, None, 30, 22, None],
        "Salary": [50000, 60000, None, 999999, 60000],  # 999999 = outlier
        "Join Date": ["2020-01-15", "Jan 5 2021", "2019/11/30", None, "Jan 5 2021"],
        "Status": ["Active", "inactive", None, "ACTIVE", "inactive"],
    })


# ── Missing value tests ────────────────────────────────────────────

def test_handle_missing_numeric_median(messy_df):
    df, audit, stats = handle_missing(messy_df, "median", "mode", 0.9)
    assert df["Age"].isnull().sum() == 0
    assert stats["total_filled"] > 0

def test_handle_missing_categorical_mode(messy_df):
    df, audit, stats = handle_missing(messy_df, "median", "mode", 0.9)
    assert df["Name"].isnull().sum() == 0

def test_handle_missing_drop_threshold():
    df = pd.DataFrame({"A": [1, None, None, None], "B": [1, 2, 3, 4]})
    result, audit, stats = handle_missing(df, "mean", "mode", 0.5)
    assert "A" not in result.columns
    assert stats["cols_dropped"] == 1


# ── Deduplication tests ────────────────────────────────────────────

def test_remove_duplicates(messy_df):
    df, audit, count = remove_duplicates(messy_df)
    assert count == 1                     # one duplicate row (Bob)
    assert len(df) == len(messy_df) - 1

def test_no_duplicates():
    df = pd.DataFrame({"x": [1, 2, 3]})
    _, _, count = remove_duplicates(df)
    assert count == 0


# ── Type correction tests ──────────────────────────────────────────

def test_correct_types_numeric():
    df = pd.DataFrame({"score": ["10", "20", "30", "bad", "50"]})
    result, audit = correct_types(df)
    # 4/5 = 80% convertible → should convert
    assert pd.api.types.is_numeric_dtype(result["score"])

def test_correct_types_date():
    df = pd.DataFrame({"created_date": ["2021-01-01", "2021-02-15", "2021-03-20", "bad"]})
    result, audit = correct_types(df)
    assert pd.api.types.is_datetime64_any_dtype(result["created_date"])


# ── Outlier tests ──────────────────────────────────────────────────

def test_outlier_iqr_cap():
    df = pd.DataFrame({"Salary": [50000, 55000, 60000, 52000, 999999]})
    result, audit, stats = handle_outliers(df, "iqr", "cap", 3.0)
    assert result["Salary"].max() < 999999

def test_outlier_iqr_remove():
    df = pd.DataFrame({"val": list(range(100)) + [9999]})
    result, audit, stats = handle_outliers(df, "iqr", "remove", 3.0)
    assert len(result) == 100

def test_outlier_keep():
    df = pd.DataFrame({"val": list(range(100)) + [9999]})
    result, audit, stats = handle_outliers(df, "iqr", "keep", 3.0)
    assert len(result) == 101


# ── Text standardisation tests ─────────────────────────────────────

def test_standardize_text_strips_whitespace(messy_df):
    result, audit = standardize_text(messy_df)
    assert result["Name"].iloc[3] == "charlie"   # "  Charlie  " → "charlie"

def test_standardize_text_lowercase(messy_df):
    result, audit = standardize_text(messy_df)
    assert result["Status"].iloc[0] == "active"


# ── Column name tests ──────────────────────────────────────────────

def test_clean_column_names():
    df = pd.DataFrame({"First Name": [1], "Last-Name": [2], "AGE!!": [3]})
    result, audit = clean_column_names(df)
    assert set(result.columns) == {"first_name", "last_name", "age"}

def test_clean_column_names_already_clean():
    df = pd.DataFrame({"name": [1], "age": [2]})
    result, audit = clean_column_names(df)
    assert "already clean" in audit[0]


# ── Date standardisation tests ─────────────────────────────────────

def test_standardize_dates_iso():
    df = pd.DataFrame({"join_date": ["Jan 5 2021", "2021/11/30", "2020-01-15"]})
    result, audit = standardize_dates(df)
    assert result["join_date"].iloc[0] == "2021-01-05"
    assert result["join_date"].iloc[2] == "2020-01-15"
