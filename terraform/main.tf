data "aws_caller_identity" "current" {}
# create the s3 bucket
resource "aws_s3_bucket" "data_bucket" {
  bucket = var.bucket_name

  tags = {
    Environment = var.environment
    Project     = "homeless-pilot"
  }
}

resource "aws_ecr_repository" "dashboard_repo" {
  name = "homeless-dashboard"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_iam_role" "ec2_role" {
  name = "homeless-dashboard-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRole"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ec2_ecr_readonly" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "ec2_s3_readonly" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "homeless-dashboard-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

resource "aws_s3_bucket_versioning" "versioning" {
  bucket = aws_s3_bucket.data_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Security groups to expose ec2 service 
resource "aws_security_group" "streamlit_sg" {
  name = "streamlit-sg"

  ingress {
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# create the EC2 instance 
resource "aws_instance" "streamlit_server" {
  ami                    = "ami-0c101f26f147fa7fd"
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.streamlit_sg.id]

  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name

  user_data = <<-EOF
              #!/bin/bash
              set -xe

              dnf update -y

              dnf install -y docker awscli

              systemctl enable docker
              systemctl start docker

              usermod -aG docker ec2-user

              aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com

              docker pull ${aws_ecr_repository.dashboard_repo.repository_url}:latest

              docker run -d \
                --name homeless-dashboard \
                -p 8501:8501 \
                -e ENV=prod \
                -e AWS_REGION=${var.aws_region} \
                -e S3_BUCKET=${aws_s3_bucket.data_bucket.id} \
                -e PROCESSED_KEY=processed/merged.csv \
                ${aws_ecr_repository.dashboard_repo.repository_url}:latest
              EOF

  tags = {
    Name = "homeless-dashboard"
  }
}
# create an s3 bucket to holde the lambda handler 




# create the lambda funtion 
resource "aws_iam_role" "lambda_role" {
  name = "etl_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_s3" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_lambda_function" "etl_lambda" {
  function_name = "homeless-etl"

  package_type = "Image"
  image_uri    = "${aws_ecr_repository.lambda_repo.repository_url}:latest"

  role    = aws_iam_role.lambda_role.arn
  timeout = 120
  memory_size = 1024

  environment {
    variables = {
      S3_BUCKET = aws_s3_bucket.data_bucket.id
      ENV       = "prod"
      OUTPUT_KEY = "processed/merged.csv"
    }
  }
}

# add trigger 
resource "aws_lambda_permission" "allow_s3_invoke_etl" {
  statement_id  = "AllowS3InvokeETL"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.etl_lambda.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.data_bucket.arn
}

resource "aws_s3_bucket_notification" "data_bucket_notification" {
  bucket = aws_s3_bucket.data_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.etl_lambda.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "raw/"
    filter_suffix       = ".csv"
  }

  depends_on = [
    aws_lambda_permission.allow_s3_invoke_etl
  ]
}

