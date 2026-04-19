output "portal_url" {
  value = "https://${var.portal_subdomain}.${var.root_domain}"
}

output "api_url" {
  value = "https://api.${var.portal_subdomain}.${var.root_domain}"
}

output "db_endpoint" {
  value     = aws_db_instance.portal.endpoint
  sensitive = true
}

output "frontend_bucket" {
  value = aws_s3_bucket.frontend.id
}

output "attachments_bucket" {
  value = aws_s3_bucket.attachments.id
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.frontend.id
}

output "ecs_cluster" {
  value = aws_ecs_cluster.portal.id
}

output "ecs_service" {
  value = aws_ecs_service.backend.name
}
