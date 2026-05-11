from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

ENV = os.getenv("ENV", "dev")

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

S3_BUCKET = os.getenv("S3_BUCKET", "homeless-data-pilot")

ANXIETY_KEY = os.getenv(
    "ANXIETY_KEY",
    "raw/SF_HOMELESS_ANXIETY.csv"
)

DEMOGRAPHICS_KEY = os.getenv(
    "DEMOGRAPHICS_KEY",
    "raw/SF_HOMELESS_DEMOGRAPHICS.csv"
)

LOCAL_ANXIETY_FILE = BASE_DIR / "data" / "SF_HOMELESS_ANXIETY.csv"

LOCAL_DEMOGRAPHICS_FILE = (
    BASE_DIR / "data" / "SF_HOMELESS_DEMOGRAPHICS.csv"
)

PROCESSED_OUTPUT = BASE_DIR / "data" / "processed.csv"

PROCESSED_KEY = os.getenv("PROCESSED_KEY", "processed/merged.csv")