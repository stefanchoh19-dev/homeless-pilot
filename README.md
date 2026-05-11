# Homeless Anxiety Data pipline 
Thie project demonstrates an event driven ETL and analytics plaform build on AWS. it ingests Homelessnes-related anxirty and demographics dataset from Amazon s3, processes and merges the data using a containerized AWS Lambda funtion , and visiualizes the processed results through streamlit dashboard running on EC2

The project demonstrates 
- Event-driven severless processing 
- Infrastructure as code with terraform 
- Containerized AWS Lambda deployments using ECR 
- Data cleaning an normalization with pandas 
- Automated S3-triggered ETL workflows
- Dashboard visualization using streamlit 
- AWS IAM, ECR, EC2,Lambda, and S3 intergration 

## Architecture
                +----------------------+
                |   Raw CSV Uploads    |
                |      Amazon S3       |
                +----------+-----------+
                           |
                           | S3 Event Notification
                           v
                +----------------------+
                | AWS Lambda (Docker)  |
                |   pandas ETL Job     |
                +----------+-----------+
                           |
                           | Writes processed data
                           v
                +----------------------+
                |   Processed S3 Data  |
                +----------+-----------+
                           |
                           | Reads processed CSV
                           v
                +----------------------+
                | Streamlit Dashboard  |
                |      EC2 + Docker    |
                +----------------------+

## Features
- ETL Processing
- Loads anxiety and demographic datasets from S3
- Cleans and normalizes data
- Merges datasets using homeless identifiers
- Generates summary statistics
- Writes processed CSV output back to S3
## AWS Lambda
- Containerized Lambda deployment using Docker + ECR
- Triggered automatically on S3 uploads
- Uses environment variables for runtime configuration
- CloudWatch logging for observability
## Streamlit Dashboard
- Reads processed data directly from S3
- Displays:
  - Total encounters
  - Average anxiety score
  - Shelter statistics
  - Anxiety trends over time
  - Interactive merged dataset preview

## Infrastructure as Code
Terraform provisions:
  - S3 buckets
  - Lambda functions
  - ECR repositories
  - IAM roles and policies
  - EC2 instance
  - Security groups
  - S3 event notifications

## Technologies Used
  - Python
  - pandas
  - Streamlit
  - Terraform
  - AWS Lambda
  - Amazon S3
  - Amazon EC2
  - Amazon ECR
  - Docker
  - boto3
## Project Structure
  homeless-pilot/
  │
  ├── app/
  │   ├── config.py
  │   ├── dashboard.py
  │   ├── etl.py
  │   ├── lambda_handler.py
  │   └── __init__.py
  │
  ├── data/
  |   ├──SF_HOMELESS_ANXIETY.csv
  |   ├──SF_HOMELESS_DEMOGRAPHICS.csv
  |   ├──processed.csv
  │
  │
  │
  ├── tests/
  │   └── test_etl.py
  │
  ├── terraform/
  │   └── main.tf
  |   └──output.tf
  |   └──variable.tf
  │
  ├── Dockerfile.lambda
  ├── Dockerfile
  ├── requirements.txt
  └── README.md

s3://homeless-demo-pilot/
│
├── raw/
│   ├── SF_HOMELESS_ANXIETY.csv
│   └── SF_HOMELESS_DEMOGRAPHICS.csv
│
└── processed/
    └── merged.csv

## Local Development

  ```Bash
  # Create Virtual Environment
  python -m venv venv

  # activate venv Windows 
  venv\Scripts\activate

  # Activate venv if linux or mac 
  source venv/bin/activate

  # install dependencies 
  cd  app 
  pip install -r requirements.txt
  ```

## Running the Dashboard Locally
```Bash
cd  app 
streamlit run app/dashboard.py
```

# run test cases




# Terraform Deployment
```Bash
# initialize Terraform 
cd terraform 
terraform init

# Plan 
terraform plan

# apply 
terraform apply
```

# Building and pushing Lambda Container
```Bash
docker build -f Dockerfile.lambda -t homeless-etl:latest .

# Authenticate to ECR 
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# tag docker image 
docker tag homeless-etl:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/homeless-etl:latest

# push image to ECR 

docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/homeless-etl:latest


```

AWS Lambda Environment Variables
| Variable | Description|
|----------|------------|




# Challenges Solved
- Lambda zip deployment size limits solution was to migrate to containrized lambda 
- ECR authentication from EC2 mad use of iam roles 
- S3- triggered  event processing 
- Data normalization inconsistencies 
- Cloud watch debugging 
