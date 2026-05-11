import pandas as pd
import boto3
from io import StringIO
from config import (
    ENV,
    AWS_REGION,
    S3_BUCKET,
    ANXIETY_KEY,
    DEMOGRAPHICS_KEY,
    LOCAL_ANXIETY_FILE,
    LOCAL_DEMOGRAPHICS_FILE,
    PROCESSED_OUTPUT
)

s3 = boto3.client("s3", region_name=AWS_REGION)


# load data 
def load_csv_from_s3(bucket, key):
    response = s3.get_object(Bucket=bucket, Key=key)
    csv_content = response["Body"].read().decode("utf-8")
    return pd.read_csv(StringIO(csv_content))


def load_data():
    if ENV == "prod":
        print("Loading data from S3...")
        anxiety = load_csv_from_s3(S3_BUCKET, ANXIETY_KEY)
        demographics = load_csv_from_s3(S3_BUCKET, DEMOGRAPHICS_KEY)
    else:
        print("Loading data locally...")
        anxiety = pd.read_csv(LOCAL_ANXIETY_FILE)
        demographics = pd.read_csv(LOCAL_DEMOGRAPHICS_FILE)

    return anxiety, demographics


# clean data
def clean_data(anxiety, demographics):

    for df in [anxiety, demographics]:
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    anxiety.rename(columns={"homeless_id": "hid"}, inplace=True)
    demographics.rename(columns={"homeless_id": "hid"}, inplace=True)

    anxiety = anxiety.drop_duplicates().dropna(subset=["hid"])
    demographics = demographics.drop_duplicates().dropna(subset=["hid"])

    anxiety["encounter_date"] = pd.to_datetime(anxiety["encounter_date"], errors="coerce")
    demographics["registration_date"] = pd.to_datetime(demographics["registration_date"], errors="coerce")

    return anxiety, demographics


def merge_data(anxiety, demographics):
# good to preserve the original ID 
    anxiety = anxiety.rename(columns={
        "hid": "hid_anxiety"
    })

    demographics = demographics.rename(columns={
        "hid": "hid_demo"
    })

# create new Ids
    anxiety["canonical_id"] = (
        anxiety["hid_anxiety"]
        .astype(str)
        .str.extract(r"HM15-(\d+)", expand=False)
        .astype(int)
        .astype(str)
    )


    demographics["canonical_id"] = (
        demographics["hid_demo"]
        .astype(str)
        .str.extract(r"(\d+)-15", expand=False)
        .astype(int)
        .astype(str)
    )

# validateing the Ids 
    anxiety_ids = set(anxiety["canonical_id"])
    demographics_ids = set(demographics["canonical_id"])

    matches = anxiety_ids & demographics_ids

    print(f"Anxiety IDs: {len(anxiety_ids)}")
    print(f"Demographic IDs: {len(demographics_ids)}")
    print(f"Matched IDs: {len(matches)}")

# Perform the merge on the canonical ids 
    merged = anxiety.merge(
        demographics,
        on="canonical_id",
        how="left"
    )

    return merged


# generate a summary of the new dataset
def generate_summary(merged):

    merged["encounter_date"] = pd.to_datetime(
        merged["encounter_date"],
        errors="coerce"
    )

    monthly = (
        merged.groupby(pd.Grouper(key="encounter_date", freq="M"))["anxiety_lvl"]
        .mean()
        .reset_index()
    )

    shelter_summary = (
        merged.groupby("shelter")["anxiety_lvl"]
        .mean()
        .reset_index()
        .sort_values(by="anxiety_lvl", ascending=False)
    )

    return monthly, shelter_summary


#save the generated dataset 
def save_processed_data(merged):
    merged.to_csv(PROCESSED_OUTPUT, index=False)
    print(f"Saved processed data → {PROCESSED_OUTPUT}")


# combine all methods to create a main 
def run_etl():

    anxiety, demographics = load_data()

    anxiety, demographics = clean_data(anxiety, demographics)

    # anxiety, demographics = merge_data(anxiety, demographics)

    merged = merge_data(anxiety, demographics)

    monthly, shelter_summary = generate_summary(merged)

    save_processed_data(merged)

    return merged, monthly, shelter_summary


anxiety, demographics = load_data()



anxiety_clean, demographics_clean = clean_data(anxiety, demographics)



merged = merge_data(anxiety_clean, demographics_clean)


# run the etl 
if __name__  == "__main__":
  run_etl()