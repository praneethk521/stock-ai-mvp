# Kubernetes Deployment

The `base` directory is a provider-neutral Kustomize package for the application tier. PostgreSQL, Redis, TLS, DNS, the ingress controller, and the identity provider are expected to be managed outside this package.

## Included Resources

- Two-replica backend and frontend deployments
- ClusterIP services and host-based ingress
- Startup, readiness, and liveness probes
- CPU-based horizontal pod autoscaling
- Pod disruption budgets
- Non-root containers, read-only root filesystems, and dropped Linux capabilities
- A one-shot Alembic migration job template

## Required Configuration

Before deployment, customize `base/configmap.yaml` for the public hostname and JWT identity provider. Use immutable image tags or digests in the deployment and migration manifests.

Create `stock-ai-runtime` in the `stock-ai` namespace through the cluster's secret manager integration. `base/secret.example.yaml` documents the required keys and must never contain real credentials in Git.

## Deployment Order

```bash
kubectl apply -f infra/k8s/base/namespace.yaml
kubectl apply -f /secure/path/stock-ai-runtime-secret.yaml
kubectl apply -f infra/k8s/base/migration-job.yaml
kubectl wait --namespace stock-ai --for=condition=complete job/stock-ai-migrate --timeout=300s
kubectl apply -k infra/k8s/base
kubectl rollout status --namespace stock-ai deployment/stock-ai-backend
kubectl rollout status --namespace stock-ai deployment/stock-ai-frontend
```

The migration job name must be unique for each release, or the completed prior job must be removed before applying a new migration. A deployment workflow should generate that release-specific name and wait for success before updating application deployments.

## Local Validation

```bash
kubectl kustomize infra/k8s/base >/dev/null
ruby -e "require 'yaml'; YAML.load_stream(File.read('infra/k8s/base/migration-job.yaml'))"
```
