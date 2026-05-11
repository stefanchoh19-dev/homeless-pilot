resource "aws_ecr_repository" "lambda_repo" {
  name = "homeless-etl"

  image_scanning_configuration {
    scan_on_push = true
  }
}


output "ecr_repository_url" {
  value = aws_ecr_repository.lambda_repo.repository_url
}