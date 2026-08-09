# CI/CD Agent

## Purpose

CI/CD Agent는 Terraform 코드의 품질 검증, plan 리뷰, 배포 승인, 환경별 배포 흐름을 자동화합니다.

## Responsibilities

- Terraform `fmt`, `validate`, `plan` 자동화
- Pull request 기반 인프라 변경 리뷰 설계
- `dev`, `stg`, `prod` 배포 promotion flow 정의
- OIDC 기반 CI/CD 배포 role 설계
- Terraform state backend와 lock 전략 검토
- 정책 검사 및 보안 스캔 도구 연결

## Main Outputs

- CI/CD workflow
- Terraform validation pipeline
- Plan review process
- Deployment approval strategy
- Rollback and recovery notes

## Pipeline Stages

| Stage | Purpose |
| --- | --- |
| Format | `terraform fmt -check -recursive` |
| Validate | `terraform validate` |
| Static Analysis | policy, security, lint scan |
| Plan | environment-specific `terraform plan` |
| Approval | manual review for `stg` and `prod` |
| Apply | controlled deployment |

