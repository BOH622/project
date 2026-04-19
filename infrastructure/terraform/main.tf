###############################################################################
# UserCue Projects Portal — AWS infrastructure
#
# NOT APPLIED by CI. Someone with AWS credentials and IAM admin on the
# UserCue account must run `terraform init && terraform apply` from this
# directory.
#
# Resources:
#   - VPC + 2 public + 2 private subnets across 2 AZs
#   - RDS Postgres 16 (single-AZ in staging, Multi-AZ in prod via var)
#   - ECS Fargate cluster + backend service behind ALB
#   - S3 bucket for attachments
#   - S3 bucket + CloudFront for frontend static hosting
#   - ACM cert (DNS-validated) for projects.tryusercue.com
#   - Route 53 A alias
#   - SES domain identity + MAIL FROM
###############################################################################

terraform {
  required_version = ">= 1.7"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
  }

  # Uncomment after provisioning an S3 backend + DynamoDB lock table.
  # backend "s3" {
  #   bucket         = "usercue-terraform-state"
  #   key            = "projects-portal/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "usercue-terraform-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "projects-portal"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# ---- Data sources --------------------------------------------------------

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_route53_zone" "root" {
  name         = var.root_domain
  private_zone = false
}

# ---- VPC -----------------------------------------------------------------

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.13"

  name = "${var.environment}-projects-portal"
  cidr = var.vpc_cidr

  azs             = slice(data.aws_availability_zones.available.names, 0, 2)
  private_subnets = [cidrsubnet(var.vpc_cidr, 4, 0), cidrsubnet(var.vpc_cidr, 4, 1)]
  public_subnets  = [cidrsubnet(var.vpc_cidr, 4, 2), cidrsubnet(var.vpc_cidr, 4, 3)]

  enable_nat_gateway = true
  single_nat_gateway = var.environment != "prod"
  enable_dns_hostnames = true
}

# ---- RDS Postgres --------------------------------------------------------

resource "aws_security_group" "rds" {
  name   = "${var.environment}-portal-rds"
  vpc_id = module.vpc.vpc_id
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_service.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_subnet_group" "portal" {
  name       = "${var.environment}-portal"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_db_instance" "portal" {
  identifier             = "${var.environment}-portal"
  engine                 = "postgres"
  engine_version         = "16.4"
  instance_class         = var.environment == "prod" ? "db.t3.small" : "db.t3.micro"
  allocated_storage      = 20
  max_allocated_storage  = 100
  db_name                = "portal"
  username               = "portal_admin"
  password               = var.db_master_password
  db_subnet_group_name   = aws_db_subnet_group.portal.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  multi_az               = var.environment == "prod"
  backup_retention_period = var.environment == "prod" ? 14 : 7
  skip_final_snapshot    = var.environment != "prod"
  deletion_protection    = var.environment == "prod"
  storage_encrypted      = true
}

# ---- ECS Fargate (backend) ----------------------------------------------

resource "aws_ecs_cluster" "portal" {
  name = "${var.environment}-portal"
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.environment}-portal-backend"
  retention_in_days = 30
}

resource "aws_security_group" "ecs_service" {
  name   = "${var.environment}-portal-ecs"
  vpc_id = module.vpc.vpc_id
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_iam_role" "task_execution" {
  name = "${var.environment}-portal-task-execution"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "task_execution" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.environment}-portal-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.task_execution.arn
  container_definitions = jsonencode([{
    name      = "backend"
    image     = var.backend_image
    essential = true
    portMappings = [{ containerPort = 8000, protocol = "tcp" }]
    environment = [
      { name = "DATABASE_URL", value = "postgresql+asyncpg://portal_admin:${var.db_master_password}@${aws_db_instance.portal.address}:5432/portal" },
      { name = "PORTAL_BASE_URL", value = "https://${var.portal_subdomain}.${var.root_domain}" },
      { name = "BACKEND_BASE_URL", value = "https://api.${var.portal_subdomain}.${var.root_domain}" },
      { name = "CORS_ALLOWED_ORIGINS", value = "https://${var.portal_subdomain}.${var.root_domain}" },
      { name = "AUTH_SIGNING_KEY", value = var.auth_signing_key },
      { name = "EMAIL_BACKEND", value = "ses" },
      { name = "EMAIL_SENDER", value = "noreply@${var.portal_subdomain}.${var.root_domain}" },
      { name = "INBOUND_EMAIL_DOMAIN", value = "threads.${var.portal_subdomain}.${var.root_domain}" },
      { name = "INBOUND_EMAIL_HMAC_SECRET", value = var.inbound_email_hmac_secret },
      { name = "WEBHOOK_HMAC_SECRET", value = var.webhook_hmac_secret },
      { name = "S3_ATTACHMENTS_BUCKET", value = aws_s3_bucket.attachments.id },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.backend.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "backend"
      }
    }
  }])
}

resource "aws_ecs_service" "backend" {
  name            = "${var.environment}-portal-backend"
  cluster         = aws_ecs_cluster.portal.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.environment == "prod" ? 2 : 1
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = module.vpc.private_subnets
    security_groups  = [aws_security_group.ecs_service.id]
    assign_public_ip = false
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }
  depends_on = [aws_lb_listener.https]
}

# ---- ALB ----------------------------------------------------------------

resource "aws_security_group" "alb" {
  name   = "${var.environment}-portal-alb"
  vpc_id = module.vpc.vpc_id
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 80
    to_port     = 80
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

resource "aws_lb" "portal" {
  name               = "${var.environment}-portal-alb"
  load_balancer_type = "application"
  subnets            = module.vpc.public_subnets
  security_groups    = [aws_security_group.alb.id]
}

resource "aws_lb_target_group" "backend" {
  name        = "${var.environment}-portal-backend"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = module.vpc.vpc_id
  target_type = "ip"
  health_check {
    path                = "/healthz"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

resource "aws_acm_certificate" "api" {
  domain_name       = "api.${var.portal_subdomain}.${var.root_domain}"
  validation_method = "DNS"
  lifecycle { create_before_destroy = true }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.portal.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.api.arn
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}

# ---- S3: attachments ----------------------------------------------------

resource "aws_s3_bucket" "attachments" {
  bucket = "usercue-portal-attachments-${var.environment}"
}

resource "aws_s3_bucket_public_access_block" "attachments" {
  bucket                  = aws_s3_bucket.attachments.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ---- S3 + CloudFront: frontend hosting ----------------------------------

resource "aws_s3_bucket" "frontend" {
  bucket = "usercue-portal-frontend-${var.environment}"
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket                  = aws_s3_bucket.frontend.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${var.environment}-portal-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  default_root_object = "index.html"
  aliases             = ["${var.portal_subdomain}.${var.root_domain}"]
  price_class         = "PriceClass_100"

  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "s3-frontend"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  default_cache_behavior {
    target_origin_id       = "s3-frontend"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }
    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.frontend.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }
}

resource "aws_acm_certificate" "frontend" {
  provider          = aws.us_east_1
  domain_name       = "${var.portal_subdomain}.${var.root_domain}"
  validation_method = "DNS"
  lifecycle { create_before_destroy = true }
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"  # CloudFront ACM certs must live in us-east-1
}

# ---- Route53 ------------------------------------------------------------

resource "aws_route53_record" "frontend" {
  zone_id = data.aws_route53_zone.root.zone_id
  name    = "${var.portal_subdomain}.${var.root_domain}"
  type    = "A"
  alias {
    name                   = aws_cloudfront_distribution.frontend.domain_name
    zone_id                = aws_cloudfront_distribution.frontend.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "api" {
  zone_id = data.aws_route53_zone.root.zone_id
  name    = "api.${var.portal_subdomain}.${var.root_domain}"
  type    = "A"
  alias {
    name                   = aws_lb.portal.dns_name
    zone_id                = aws_lb.portal.zone_id
    evaluate_target_health = true
  }
}

# ---- SES ----------------------------------------------------------------

resource "aws_ses_domain_identity" "portal" {
  domain = "${var.portal_subdomain}.${var.root_domain}"
}

resource "aws_ses_domain_dkim" "portal" {
  domain = aws_ses_domain_identity.portal.domain
}

resource "aws_route53_record" "dkim" {
  count   = 3
  zone_id = data.aws_route53_zone.root.zone_id
  name    = "${aws_ses_domain_dkim.portal.dkim_tokens[count.index]}._domainkey.${var.portal_subdomain}.${var.root_domain}"
  type    = "CNAME"
  ttl     = 600
  records = ["${aws_ses_domain_dkim.portal.dkim_tokens[count.index]}.dkim.amazonses.com"]
}
