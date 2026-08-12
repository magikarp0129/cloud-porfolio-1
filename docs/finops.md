# FinOps Strategy

## Objective

클라우드 비용을 사후 정산 대상이 아니라 설계, 배포, 운영 단계에서 지속적으로 관리되는 품질 지표로 취급합니다.

## Governance

- 모든 Terraform 리소스에 공통 태그를 적용합니다.
- 환경별 예산을 분리합니다.
- 월간 비용 리포트를 생성합니다.
- 비용 이상 징후를 알람으로 연결합니다.

## Tagging Strategy

| Tag | Purpose | Example |
| --- | --- | --- |
| `Environment` | 환경 구분 | `dev`, `stg`, `prod` |
| `Owner` | 책임 조직 | `platform-team` |
| `Service` | 서비스 식별 | `cloud-portfolio` |
| `CostCenter` | 비용 배부 | `cloud-platform` |
| `ManagedBy` | 관리 방식 | `terraform` |
| `Schedule` | 자동 시작/중지 정책 | `office-hours`, `always-on` |
| `BackupPolicy` | 백업 정책 연결 | `daily-30d`, `none` |

## Cost Controls

| Area | Control |
| --- | --- |
| Tagging | Required tags enforced by Terraform variables |
| Budget | Environment-level AWS Budgets |
| Anomaly | Cost anomaly detection |
| Optimization | Right sizing and unused resource review |
| Reporting | Monthly service and owner cost report |

## Review Cadence

- Daily: budget and anomaly alerts
- Weekly: unused resource review
- Monthly: cost report and optimization backlog

## Commitment Strategy

- `prod`의 24x7 baseline workload는 Savings Plans 또는 RI 후보로 검토합니다.
- `dev`와 `stg`는 스케줄링과 right sizing을 우선 적용합니다.
- 30일 이상 안정적인 사용량을 확인한 뒤 약정 구매를 검토합니다.
- Compute Savings Plans는 유연성이 필요한 compute workload에 우선 적용합니다.
- Standard RI는 장기 고정 database workload에만 제한적으로 검토합니다.
