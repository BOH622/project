variable "environment" {
  description = "Deployment environment: staging | prod"
  type        = string
  validation {
    condition     = contains(["staging", "prod"], var.environment)
    error_message = "environment must be staging or prod."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.20.0.0/16"
}

variable "root_domain" {
  description = "Root domain (e.g. tryusercue.com)"
  type        = string
  default     = "tryusercue.com"
}

variable "portal_subdomain" {
  description = "Portal subdomain (e.g. projects or projects-staging)"
  type        = string
}

variable "backend_image" {
  description = "ECR image URI for the backend service"
  type        = string
}

variable "db_master_password" {
  description = "RDS master password"
  type        = string
  sensitive   = true
}

variable "auth_signing_key" {
  description = "Magic-link token signing key"
  type        = string
  sensitive   = true
}

variable "inbound_email_hmac_secret" {
  description = "HMAC secret for validating inbound email webhook"
  type        = string
  sensitive   = true
}

variable "webhook_hmac_secret" {
  description = "HMAC secret for signing outbound webhooks and validating inbound"
  type        = string
  sensitive   = true
}
