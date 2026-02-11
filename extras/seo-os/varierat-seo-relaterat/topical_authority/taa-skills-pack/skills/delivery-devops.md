---
name: "Delivery & DevOps Integration"
slug: "delivery-devops"
version: "1.0.0"
tags: ["#deployment", "#cms", "#devops", "#automation", "#ci-cd"]
summary: "Automate export, deployment, and verification of SEO deliverables to CMS, headless systems, or edge SEO environments with rollback safety."
---

## 1) Purpose

Automate export→deploy→verify with rollback for CMS/headless/edge SEO.

This skill defines:
- **CMS exporters** (WordPress, Contentful, Sanity)
- **Edge deployers** (Cloudflare, Netlify, Vercel)
- **CI/CD hooks** with validation gates
- **Rollback manifests** with file hashes

You use it to: publish briefs/pages/schema safely.

## 2) Novelty rationale

Two-way verification & deterministic manifests (hashes).

## 3) Trigger conditions

**Use** pipeline deployments; **Avoid** local protos.

## 4) Prerequisites

API creds, `/out/` artifacts.

## 5) Sources

- CMS REST APIs
- GitHub Actions/GitLab CI
- Cloudflare Workers KV

## 6) Conceptual model

```
Validate → Hash → Push → Verify → Log or Rollback
```

## 7) Procedure

1. Validate artifacts exist & schemas pass.
2. Hash manifest (SHA256) → `/out/deploy/manifest.json`.
3. Dry-run publish; verify endpoints.
4. Deploy respecting rate limits & rollback strategy.
5. Verify live vs checksums; write `/out/deploy/logs/{ts}.log`.

## 8) Artifacts produced

- `manifest.json`
- `deploy_log`
- `rollback_manifest.json`

## 9) Templates

**manifest.json**
```json
{
  "files": [
    {"path": "briefs/horapparater-pris.md", "sha256": "abc123"},
    {"path": "schema/jsonld/horapparater.json", "sha256": "def456"}
  ],
  "target": "wordpress",
  "timestamp": "2025-12-25T10:00:00Z"
}
```

## 10) Anti-patterns

- No checksum validation
- No rollback plan
- Hardcoded secrets

## 11) Integration

- **Monitoring Agent**: confirms deploy
- **Quality Harness**: final gate
- **Programmatic Factory**: pages source
