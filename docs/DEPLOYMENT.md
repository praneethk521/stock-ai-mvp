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

## Kubernetes

Portable application manifests live in `infra/k8s/base`. They assume managed PostgreSQL and Redis services and do not install stateful dependencies into the application cluster.

The base includes two-replica deployments, services, ingress, health probes, resource requests/limits, horizontal autoscaling, disruption budgets, and hardened pod/container security contexts. The backend image runs only the API process; `infra/k8s/base/migration-job.yaml` runs Alembic as a release step before application rollout.

Production setup must replace the example hostname, identity provider values, and image versions. Create the `stock-ai-runtime` Secret outside Git using the platform's secret manager integration; `infra/k8s/base/secret.example.yaml` lists its required keys.

Render the application resources locally with:

```bash
kubectl kustomize infra/k8s/base
```

See `infra/k8s/README.md` for deployment order and rollout checks.

## Observability

The backend exposes Prometheus metrics on its internal `/metrics` endpoint, emits structured JSON request logs, and supports optional OTLP/HTTP tracing. Kubernetes pods include Prometheus scrape annotations. Configure `OTEL_EXPORTER_OTLP_ENDPOINT` and set `TRACING_ENABLED=true` in an environment overlay when a collector is available. See `docs/OBSERVABILITY.md` for metric names and operational guidance.

## Production Checklist
- Runtime secrets configured
- Auth enabled
- HTTPS enabled
- Observability enabled
- Dependency/container scans passing
- Database migrations automated
- Immutable container image references configured
- Kubernetes migration job completed before application rollout
- Published image provenance and SBOM verified
