# Releasing

Backend and frontend images are published to GitHub Container Registry by `.github/workflows/release-containers.yml`.

## Release Contract

- A semantic version tag such as `v0.1.0` publishes both images.
- Manual dispatch accepts a version such as `0.1.0-rc.1` for controlled pre-releases.
- Each image is built for Linux AMD64 and ARM64.
- Published tags include the full semantic version, major/minor version, and source commit SHA.
- Build provenance and an SBOM are attached to each image.
- Application deployment is intentionally separate from image publication.

Published image names:

```text
ghcr.io/praneethk521/stock-ai-backend
ghcr.io/praneethk521/stock-ai-frontend
```

## Create A Release

Run the complete local validation suite, then create and push an annotated semantic version tag:

```bash
git tag -a v0.1.0 -m "Stock AI Platform v0.1.0"
git push origin v0.1.0
```

The GitHub Actions run must complete successfully before either image digest is promoted into a deployment environment.

## Promote Images

Use immutable digests for production. Update the Kubernetes image references through a deployment-specific Kustomize overlay or deployment workflow, run the migration job using the matching backend digest, wait for migration success, and then roll out both deployments.

Do not use mutable `latest` tags in staging or production.
