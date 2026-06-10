# Bullet 6 — AWS serverless portability slice as IaC.
# Declares the two serverless services the openFDA contract lands/serves on. No RDS/OpenSearch/ECS.
# `terraform apply` to provision, `terraform destroy` to tear down (the teardown proof).
# Cost: S3 (tiny object) + DynamoDB PAY_PER_REQUEST = effectively $0.

terraform {
  required_providers { aws = { source = "hashicorp/aws", version = "~> 5.0" } }
}

variable "region"  { default = "us-east-1" }
variable "account" { description = "AWS account id (for globally-unique bucket name)" }

provider "aws" { region = var.region }   # creds from ~/.aws default profile (per /aws-auth-hell)

# ── serverless service #1: S3 landing for the openFDA fact (shared contract) ──
resource "aws_s3_bucket" "openfda_landing" {
  bucket = "openfda-portability-${var.account}"
  tags   = { project = "openfda-portability", bullet = "6", lane = "multicloud" }
}

resource "aws_s3_bucket_lifecycle_configuration" "expire" {
  bucket = aws_s3_bucket.openfda_landing.id
  rule {
    id     = "expire-bounded-sample"
    status = "Enabled"
    expiration { days = 30 }   # bounded sample — auto-expire, no lingering cost
  }
}

# ── serverless service #2: DynamoDB serving (on-demand, no always-on capacity) ──
resource "aws_dynamodb_table" "openfda_events" {
  name         = "openfda-adverse-events"
  billing_mode = "PAY_PER_REQUEST"          # serverless: $0 idle, pay per request only
  hash_key     = "safetyreportid"
  attribute {
    name = "safetyreportid"
    type = "S"
  }
  tags = { project = "openfda-portability", bullet = "6", lane = "multicloud" }
}

output "s3_landing_bucket" { value = aws_s3_bucket.openfda_landing.bucket }
output "dynamodb_table"    { value = aws_dynamodb_table.openfda_events.name }
output "teardown"          { value = "terraform destroy -var account=${var.account}" }
