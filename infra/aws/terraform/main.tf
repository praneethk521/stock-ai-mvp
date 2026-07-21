locals {
  name_prefix = "${var.project_name}-${var.environment}"

  default_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# Resource modules will be added after the hosting mode and AWS account layout are confirmed.
