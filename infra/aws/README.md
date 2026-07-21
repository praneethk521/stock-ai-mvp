# AWS Infrastructure Skeleton

This folder is the production deployment starting point. It intentionally defines variables, provider requirements, and outputs before creating paid resources.

## Planned Components
- VPC with public load-balancer subnets and private application/data subnets
- ECR repositories for backend and frontend images
- ECS Fargate services for backend and, if needed, frontend
- RDS PostgreSQL
- ElastiCache Redis
- AWS Secrets Manager entries injected into runtime tasks
- CloudWatch logs and alarms

## First Deployment Pass
1. Confirm frontend hosting mode: static S3/CloudFront or containerized Next.js.
2. Add networking and ECR resources.
3. Add backend ECS service with health checks.
4. Add RDS, Redis, secrets, and migration execution.
5. Promote from local demo to a staging environment before production.
