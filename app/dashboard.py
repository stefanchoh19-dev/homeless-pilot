import streamlit as st
import pandas as pd
import boto3
from io import StringIO

from config import (
    ENV,
    AWS_REGION,
    S3_BUCKET,
    PROCESSED_KEY,
    PROCESSED_OUTPUT
)

from etl import run_etl

st.set_page_config(layout="wide")

st.title("Homeless Anxiety Dashboard")

st.caption(f"Environment: {ENV}")

s3 = boto3.client("s3", region_name=AWS_REGION)


@st.cache_data(ttl=60)
def load_processed_data():
    if ENV == "prod":
        response = s3.get_object(
            Bucket=S3_BUCKET,
            Key=PROCESSED_KEY
        )

        csv_content = response["Body"].read().decode("utf-8")

        return pd.read_csv(StringIO(csv_content))

    run_etl()
    return pd.read_csv(PROCESSED_OUTPUT)


df = load_processed_data()


# perform basic validation 
df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

df["encounter_date"] = pd.to_datetime(
    df["encounter_date"],
    errors="coerce"
)

df["anxiety_lvl"] = pd.to_numeric(
    df["anxiety_lvl"],
    errors="coerce"
)

df["shelter"] = (
    df["shelter"]
    .astype(str)
    .str.strip()
    .str.replace("’", "'", regex=False)
    .str.replace(r"\s+", " ", regex=True)
    .str.title()
)

df = df.dropna(subset=["encounter_date", "anxiety_lvl", "shelter"])


# kpi's
c1, c2, c3 = st.columns(3)

c1.metric("Total Encounters", len(df))

c2.metric(
    "Average Anxiety",
    round(df["anxiety_lvl"].mean(), 2)
)

c3.metric(
    "Unique Shelters",
    df["shelter"].nunique()
)

st.divider()

#chart for anxiety over time 
monthly = (
    df.groupby(
        pd.Grouper(
            key="encounter_date",
            freq="ME"
        )
    )["anxiety_lvl"]
    .mean()
)

st.subheader("Average Anxiety Over Time")
st.line_chart(monthly)

st.divider()


#generate axiety by shelter

shelter = (
    df.groupby("shelter")["anxiety_lvl"]
    .mean()
    .sort_values(ascending=False)
)

st.subheader("Average Anxiety by Shelter")
st.bar_chart(shelter)

st.divider()

#create a chart for the merged dataset 
st.subheader("Merged Dataset")
st.dataframe(df.head(100), use_container_width=True)