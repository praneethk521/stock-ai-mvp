# Deployment

## Local
`docker compose up --build`

## AWS Direction
- Frontend: CloudFront + S3 or container on ECS/EKS
- Backend: ECS/Fargate or EKS
- Database: RDS PostgreSQL
- Redis: ElastiCache
- Secrets: AWS Secrets Manager
- CI/CD: GitHub Actions

## Production Checklist
- Real env vars configured
- HTTPS enabled
- Auth enabled
- Observability enabled
- Dependency/container scans passing
- Database migrations automated
