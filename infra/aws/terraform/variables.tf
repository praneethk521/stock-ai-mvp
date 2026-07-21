variable "aws_region" {
  description = "AWS region for the environment."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "staging"
}

variable "project_name" {
  description = "Project name used for resource naming."
  type        = string
  default     = "stock-ai"
}

variable "backend_image_tag" {
  description = "Backend container image tag to deploy."
  type        = string
  default     = "latest"
}

variable "frontend_image_tag" {
  description = "Frontend container image tag to deploy when using container hosting."
  type        = string
  default     = "latest"
}
