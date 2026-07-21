# Deployment

## Local
`docker compose up --build`

## Secrets
- Local demo: use `SECRET_PROVIDER=env` and place local-only keys in `backend/.env`.
- Production runtime: use `SECRET_PROVIDER=file`, mount secrets into `SECRETS_DIR`, and set names such as `POLYGON_API_KEY_SECRET_NAME=polygon_api_key`.
- AWS direction: store secrets in AWS Secrets Manager, then inject or mount them through ECS/EKS runtime secret support.

## Authentication
- Local demo: use `AUTH_MODE=local`.
- Production runtime: use `AUTH_MODE=jwt`, configure issuer/audience, and provide either a mounted HMAC secret or a JWKS URL from the identity provider.

## AWS Direction
- Frontend: CloudFront + S3 or container on ECS/EKS
- Backend: ECS/Fargate or EKS
- Database: RDS PostgreSQL
- Redis: ElastiCache
- Secrets: AWS Secrets Manager
- CI/CD: GitHub Actions

## Production Checklist
- Runtime secrets configured
- Auth enabled
- HTTPS enabled
- Observability enabled
- Dependency/container scans passing
- Database migrations automated
