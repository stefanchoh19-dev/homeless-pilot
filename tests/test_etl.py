import pandas as pd
from app.etl import  clean_data, merge_data, generate_summary


def test_clean_data_standardizes_columns():

    anxiety = pd.DataFrame({
        "Homeless ID": ["HM15-1"],
        "Encounter Date": ["2024-01-01"],
        "Anxiety Lvl": [5]
    })

    demographics = pd.DataFrame({
        "Homeless ID": ["001-15"],
        "Registration Date": ["2024-01-01"]
    })

    anxiety_clean, demographics_clean = clean_data(
        anxiety,
        demographics
    )

    assert "hid" in anxiety_clean.columns
    assert "encounter_date" in anxiety_clean.columns
    assert "registration_date" in demographics_clean.columns

def test_canonical_id_matching():

    anxiety = pd.DataFrame({
        "hid": ["HM15-18"],
        "encounter_date": ["2024-01-01"],
        "anxiety_lvl": [4]
    })

    demographics = pd.DataFrame({
        "hid": ["018-15"],
        "registration_date": ["2024-01-01"],
        "shelter": ["Shelter A"]
    })

    merged = merge_data(anxiety, demographics)

    assert len(merged) == 1

    assert merged.iloc[0]["canonical_id"] == "18"

    assert merged.iloc[0]["shelter"] == "Shelter A"
    
def test_duplicates_removed():

    anxiety = pd.DataFrame({
        "Homeless ID": ["HM15-1", "HM15-1"],
        "Encounter Date": ["2024-01-01", "2024-01-01"],
        "Anxiety Lvl": [5, 5]
    })

    demographics = pd.DataFrame({
        "Homeless ID": ["001-15"],
        "Registration Date": ["2024-01-01"]
    })

    anxiety_clean, _ = clean_data(
        anxiety,
        demographics
    )

    assert len(anxiety_clean) == 1

def test_generate_summary():

    merged = pd.DataFrame({
        "encounter_date": [
            "2024-01-01",
            "2024-01-15"
        ],
        "anxiety_lvl": [4, 6],
        "shelter": ["A", "A"]
    })

    monthly, shelter_summary = generate_summary(merged)

    assert len(monthly) == 1

    assert monthly.iloc[0]["anxiety_lvl"] == 5