import json
import os
from io import StringIO
from urllib.parse import unquote_plus

import boto3

from app.etl import load_data, clean_data, merge_data, generate_summary

s3 = boto3.client("s3")


def lambda_handler(event, context):
    print("Received event:")
    print(json.dumps(event, indent=2))

    bucket = os.environ.get("S3_BUCKET")
    output_key = os.environ.get("OUTPUT_KEY", "processed/merged.csv")

    if not bucket:
        bucket = event["Records"][0]["s3"]["bucket"]["name"]

    uploaded_key = None
    if "Records" in event:
        uploaded_key = unquote_plus(event["Records"][0]["s3"]["object"]["key"])

    print(f"Triggered by upload: {uploaded_key}")
    print(f"Using bucket: {bucket}")
    print(f"Output key: {output_key}")

    if uploaded_key and not uploaded_key.startswith("raw/"):
        print("Upload was not in raw/. Skipping ETL.")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Skipped because uploaded file was not in raw/",
                "uploaded_key": uploaded_key
            })
        }

    print("Loading data from S3...")
    anxiety_df, demographics_df = load_data()

    print("Raw anxiety columns:", anxiety_df.columns.tolist())
    print("Raw demographics columns:", demographics_df.columns.tolist())
    print(f"Raw anxiety rows: {len(anxiety_df)}")
    print(f"Raw demographics rows: {len(demographics_df)}")

    print("Cleaning data...")
    anxiety_df, demographics_df = clean_data(anxiety_df, demographics_df)
   

    print("Cleaned anxiety columns:", anxiety_df.columns.tolist())
    print("Cleaned demographics columns:", demographics_df.columns.tolist())

    print("Merging data...")
    merged_df = merge_data(anxiety_df, demographics_df)

    print("Merged columns:", merged_df.columns.tolist())
    print(f"Merged rows: {len(merged_df)}")

    if "identifier" in merged_df.columns:
        print(f"Matched IDs: {merged_df['identifier'].nunique()}")
    elif "Homeless ID" in merged_df.columns:
        print(f"Matched IDs: {merged_df['Homeless ID'].nunique()}")
    elif "homeless_id" in merged_df.columns:
        print(f"Matched IDs: {merged_df['homeless_id'].nunique()}")

    print("Generating summary...")
    summary = generate_summary(merged_df)

    print("Summary:")
    print(json.dumps(summary, default=str, indent=2))

    print("Writing processed output to S3...")
    csv_buffer = StringIO()
    merged_df.to_csv(csv_buffer, index=False)

    s3.put_object(
        Bucket=bucket,
        Key=output_key,
        Body=csv_buffer.getvalue(),
        ContentType="text/csv"
    )

    print(f"Processed file written to s3://{bucket}/{output_key}")
    print(f"Rows written: {len(merged_df)}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "ETL completed successfully",
            "uploaded_key": uploaded_key,
            "output_file": f"s3://{bucket}/{output_key}",
            "rows_processed": len(merged_df),
            "summary": summary
        }, default=str)
    }