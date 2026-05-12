import os
from io import StringIO

import boto3
import pandas as pd
import streamlit as st

from app.config import (
    ENV,
    AWS_REGION,
    S3_BUCKET,
    PROCESSED_KEY,
    PROCESSED_OUTPUT,
)

from etl import run_etl


st.set_page_config(
    page_title="Homeless Anxiety Dashboard",
    layout="wide",
)

st.title("Homeless Anxiety Dashboard")
st.caption(f"Environment: {ENV}")


s3 = boto3.client("s3", region_name=AWS_REGION)


RAW_ANXIETY_KEY = os.getenv(
    "ANXIETY_KEY",
    "raw/SF_HOMELESS_ANXIETY.csv"
)

RAW_DEMOGRAPHICS_KEY = os.getenv(
    "DEMOGRAPHICS_KEY",
    "raw/SF_HOMELESS_DEMOGRAPHICS.csv"
)


def s3_object_exists(bucket: str, key: str) -> bool:
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except Exception:
        return False


def get_s3_last_modified(bucket: str, key: str):
    try:
        response = s3.head_object(Bucket=bucket, Key=key)
        return response.get("LastModified")
    except Exception:
        return None


@st.cache_data(ttl=60)
def load_processed_data():
    if ENV == "prod":
        response = s3.get_object(
            Bucket=S3_BUCKET,
            Key=PROCESSED_KEY,
        )

        csv_content = response["Body"].read().decode("utf-8")

        return pd.read_csv(StringIO(csv_content))

    run_etl()
    return pd.read_csv(PROCESSED_OUTPUT)


def normalize_dashboard_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    if "encounter_date" in df.columns:
        df["encounter_date"] = pd.to_datetime(
            df["encounter_date"],
            errors="coerce",
        )

    if "anxiety_lvl" in df.columns:
        df["anxiety_lvl"] = pd.to_numeric(
            df["anxiety_lvl"],
            errors="coerce",
        )

    if "shelter" in df.columns:
        df["shelter"] = (
            df["shelter"]
            .astype(str)
            .str.replace("â€™", "'", regex=False)
            .str.replace("’", "'", regex=False)
            .str.strip()
            .str.replace(r"\s+", " ", regex=True)
            .str.title()
        )

    return df


if st.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()


if ENV == "prod":
    if not S3_BUCKET:
        st.error("S3_BUCKET environment variable is not set.")
        st.stop()

    required_raw_files = [
        RAW_ANXIETY_KEY,
        RAW_DEMOGRAPHICS_KEY,
    ]

    missing_files = [
        key for key in required_raw_files
        if not s3_object_exists(S3_BUCKET, key)
    ]

    if missing_files:
        st.error("Raw source files are missing. Dashboard cannot refresh safely.")
        st.write("Missing files:")
        st.write(missing_files)
        st.info(
            "Upload the required raw files to S3, then rerun the ETL or upload a new file to trigger Lambda."
        )
        st.stop()

    if not s3_object_exists(S3_BUCKET, PROCESSED_KEY):
        st.warning("Processed dataset does not exist yet.")
        st.info(
            f"Expected processed file: s3://{S3_BUCKET}/{PROCESSED_KEY}"
        )
        st.stop()

    processed_last_modified = get_s3_last_modified(
        S3_BUCKET,
        PROCESSED_KEY,
    )

    st.caption(
        f"Reading processed data from s3://{S3_BUCKET}/{PROCESSED_KEY}"
    )

    if processed_last_modified:
        st.caption(f"Processed data last updated: {processed_last_modified}")


try:
    df = load_processed_data()
except Exception as e:
    st.error("Failed to load processed data.")
    st.exception(e)
    st.stop()


df = normalize_dashboard_data(df)

required_columns = [
    "encounter_date",
    "anxiety_lvl",
    "shelter",
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    st.error("Processed dataset is missing required columns.")
    st.write("Missing columns:")
    st.write(missing_columns)
    st.write("Available columns:")
    st.write(df.columns.tolist())
    st.stop()


df = df.dropna(
    subset=[
        "encounter_date",
        "anxiety_lvl",
        "shelter",
    ]
)


if df.empty:
    st.warning("Processed dataset is empty after cleaning.")
    st.stop()


# Identify KPI's
c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Encounters", len(df))

c2.metric(
    "Average Anxiety",
    round(df["anxiety_lvl"].mean(), 2),
)

c3.metric(
    "Unique Shelters",
    df["shelter"].nunique(),
)

if "canonical_id" in df.columns:
    unique_people = df["canonical_id"].nunique()
elif "identifier" in df.columns:
    unique_people = df["identifier"].nunique()
else:
    unique_people = "N/A"

c4.metric("Matched Individuals", unique_people)

st.divider()



# data Coversge 
st.subheader("Matched Data Coverage")

coverage_col = None

if "canonical_id" in df.columns:
    coverage_col = "canonical_id"
elif "identifier" in df.columns:
    coverage_col = "identifier"

if coverage_col:
    coverage = (
        df.groupby("shelter")[coverage_col]
        .nunique()
        .sort_values(ascending=False)
    )

    st.bar_chart(coverage)

    st.caption(
        "This chart shows shelters represented in the merged dataset. "
        "Shelters that exist only in demographics but have no matching anxiety encounters "
        "will not appear in the dashboard."
    )
else:
    st.info("No identifier column found for coverage analysis.")

st.divider()


# Visualize anxiety over time 
monthly = (
    df.groupby(
        pd.Grouper(
            key="encounter_date",
            freq="ME",
        )
    )["anxiety_lvl"]
    .mean()
    .dropna()
)

st.subheader("Average Anxiety Over Time")
st.line_chart(monthly)

st.divider()


# Generate anxiety by shelter 
shelter = (
    df.groupby("shelter")["anxiety_lvl"]
    .mean()
    .sort_values(ascending=False)
)

st.subheader("Average Anxiety by Shelter")
st.bar_chart(shelter)

st.divider()


# filtered data view 
st.subheader("Merged Dataset")

shelter_options = sorted(df["shelter"].dropna().unique())

selected_shelters = st.multiselect(
    "Filter by shelter",
    options=shelter_options,
    default=shelter_options,
)

filtered_df = df[df["shelter"].isin(selected_shelters)]

st.dataframe(
    filtered_df.head(100),
    use_container_width=True,
)

st.caption(f"Showing {len(filtered_df)} records after filters.")