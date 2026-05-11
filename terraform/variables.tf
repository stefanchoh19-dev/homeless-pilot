variable "aws_region" {
  default = "us-east-1"
}

variable "environment" {
  default = "dev"
}

variable "bucket_name" {
  default = "homeless-data-pilot-demo"
}

variable "instance_type" {
  default = "t3.micro"
}

variable "key_name" {
  description = "EC2 SSH key pair"
  default = "test-keypair"
}