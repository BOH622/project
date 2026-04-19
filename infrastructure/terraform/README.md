# Infrastructure — Terraform

**Not applied by CI.** Run manually by someone with AWS admin on the UserCue account.

## First-time bootstrap (once per environment)

```sh
# 1. Pick environment
export TF_VAR_environment=staging   # or prod
export TF_VAR_portal_subdomain=projects-staging   # or projects

# 2. Create the state backend bucket + lock table (one-time, manual)
aws s3api create-bucket --bucket usercue-terraform-state --region us-east-1
aws dynamodb create-table --table-name usercue-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# 3. Uncomment the `backend "s3"` block in main.tf

# 4. Set the sensitive variables (use tfvars file, not env, for rotation)
cat > staging.tfvars <<EOF
environment               = "staging"
portal_subdomain          = "projects-staging"
backend_image             = "<account>.dkr.ecr.us-east-1.amazonaws.com/portal-backend:latest"
db_master_password        = "<rotate-me>"
auth_signing_key          = "<long-random>"
inbound_email_hmac_secret = "<long-random>"
webhook_hmac_secret       = "<long-random>"
EOF

# 5. Init + plan + apply
terraform init
terraform plan -var-file=staging.tfvars
terraform apply -var-file=staging.tfvars
```

## Outputs to feed back to app config

- `portal_url` → `PORTAL_BASE_URL`
- `api_url` → `BACKEND_BASE_URL`
- `attachments_bucket` → `S3_ATTACHMENTS_BUCKET`

## After apply

- Validate SES domain (SES console will be in sandbox mode until approved).
- Request SES production access for the domain so you can send to unverified recipients (2-3 day turnaround from AWS).
- Configure SES inbound rule set for `threads.projects.tryusercue.com` pointing to S3 + Lambda that forwards to the backend inbound-email endpoint.

## Destroying

```sh
terraform destroy -var-file=staging.tfvars
```

`deletion_protection` is ON in prod — disable manually in the RDS console first if you really mean it.
