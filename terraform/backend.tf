terraform {
  backend "s3" {
    bucket = "e84-terraform-backend"
    key    = "homeless-pilot/terraform.tfstate"
    region = "us-east-1"
  }
}