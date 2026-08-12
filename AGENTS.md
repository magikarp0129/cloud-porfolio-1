# Cloud Portfolio Working Agreement

이 문서는 Terraform 기반 엔터프라이즈 AWS 포트폴리오를 설계·수정·검토할 때 지켜야 할 역할과 작업 경계를 정의합니다.

## Goal

포트폴리오의 중심은 다음 네 영역입니다.

1. AWS Organizations와 Landing Zone
2. IPAM, Transit Gateway와 서비스별 VPC/IP 설계
3. Terraform module, root, state와 변경 통제
4. Private EKS의 보안·관측성·백업·운영 준비도

AI Agent는 실제 운영 주체가 아니라 역할을 나누어 검토하는 문서형 협업 모델입니다. 이 저장소에는 Agent Runtime, AI Gateway, 자동 장애 분석기 또는 production 변경 기능이 없습니다.

## Current Evidence Boundary

| 구분 | 현재 저장소에서 확인 가능 | 포함되지 않은 증거 |
| --- | --- | --- |
| Architecture | OU, IPAM, TGW, 5개 서비스와 15개 VPC, subnet 설계 | 실제 account, RAM share, 중앙 ingress/egress 배포 |
| Terraform | root/state 분리와 reusable module 코드 | 승인된 account별 plan/apply와 runtime health |
| EKS | private endpoint, managed node/add-on, 로그, Kubernetes platform 코드 | 실제 cluster 동작, load/drain/upgrade/restore rehearsal |
| Operations | backup, scheduler, patch, budget와 alert 코드·기준 | 실제 복구 결과, billing actual, on-call 통지 결과 |
| Documentation | 구성도, domain 문서, 보고서 양식과 최종 PDF | production 운영 실적 |

`코드 존재`, `로컬 검토`, `실제 배포`, `운영 증적`을 서로 다른 완료 단계로 취급합니다. 실제 증거가 없으면 성공으로 추정하지 않습니다.

## Roles

| Role | Primary responsibility | Main outputs |
| --- | --- | --- |
| Architecture | 요구사항, account/network 경계와 Architecture Decision | target architecture, ADR |
| Terraform | module/root/state 설계와 코드 | `terraform/` |
| Governance | Organizations, OU, SCP와 승인 기준 | governance model, guardrail |
| Security | IAM, network, encryption과 residual risk | security review |
| Monitoring | metric, log, alarm과 운영 가시성 | monitoring policy |
| Operations | backup, patch, lifecycle와 장애 대응 | runbook, report |
| FinOps | tag, budget, anomaly와 비용 검토 | cost policy |
| CI/CD | plan review와 protected deployment gate | pipeline design |
| Reviewer | 코드·보안·운영 위험 독립 검토 | review findings |
| Documentation | README, 구성도와 PDF 정합성 | portfolio narrative |

역할은 관점과 책임을 구분하기 위한 것이며 별도 AWS administrator나 실행 profile을 의미하지 않습니다. 최종 결정과 production 승인은 항상 사람이 수행합니다.

## Collaboration Flow

1. Architecture가 요구사항, account, network와 state boundary를 정합니다.
2. Governance와 Security가 SCP, IAM, 암호화와 network guardrail을 검토합니다.
3. Terraform이 reusable module과 environment/service root를 구현합니다.
4. Monitoring, Operations와 FinOps가 관측성, 복구, lifecycle과 비용 기준을 연결합니다.
5. CI/CD가 plan artifact, 승인과 environment promotion 절차를 설계합니다.
6. Reviewer가 코드와 문서의 Current/Target/Evidence 구분을 독립 검토합니다.
7. Documentation이 README, 구성도와 PDF를 갱신합니다.

## Repository Ownership

| Artifact | Canonical owner |
| --- | --- |
| 프로젝트 소개와 현재 상태 | `README.md` |
| 역할과 작업 안전 경계 | `AGENTS.md` |
| Terraform root/module/state | `terraform/README.md`와 각 하위 README |
| 전체 AWS architecture | `docs/architecture.md` |
| 서비스 CIDR, subnet과 TGW | `docs/service-network-architecture.md` |
| Terraform 승인과 rollback | `docs/terraform-change-management.md` |
| EKS Day-2 운영 | `docs/eks-operations.md` |
| Monitoring, Operations, Security, FinOps | 해당 `docs/*.md` |
| 월간·장애 보고 양식 | `reports/templates/` |
| PDF 본문과 스타일 | `docs/portfolio-presentation.md`, `docs/portfolio-presentation-header.tex` |

같은 표나 수치를 여러 문서에 복사하지 않습니다. README와 PDF에는 필요한 요약만 두고 상세 기준은 canonical 문서를 링크합니다.

## Terraform Change Boundary

| 단계 | 허용 산출물 | 실제 실행 책임 |
| --- | --- | --- |
| Code | branch patch, input/output 설명과 영향 분석 | 사람 review 후 merge |
| Format/Validate | `terraform fmt`, `init -backend=false`, `validate` 결과 | 작성자와 Reviewer 확인 |
| Plan | environment, backend, provider lock이 고정된 plan과 요약 | designated approver 승인 |
| Apply | 저장소 작업 Agent의 범위가 아님 | protected CI/CD deployment role |
| Emergency | 원복안, import/code 반영안과 사후 점검 | Incident Commander와 운영자 승인·실행 |

한 resource, route destination, security-group rule 또는 Kubernetes object를 두 state가 동시에 소유하지 않도록 합니다. 실제 `.tfvars`, state, credential과 고객 데이터는 저장소에 commit하지 않습니다.

## Documentation Rules

- 현재 코드와 목표 설계를 명시적으로 구분합니다.
- module 수나 시험 수보다 어떤 기능이 코드·배포·운영 증거로 확인되는지를 설명합니다.
- 값이 없으면 `not_available`과 사유를 사용합니다.
- 구성 변경 시 Terraform, 관련 diagram, README와 PDF 원고의 인용값을 함께 검색합니다.
- 최종 PDF는 하나만 유지하며 canonical builder와 verifier만 사용합니다.
- 임시 render, provider cache와 bytecode는 소스나 증적으로 취급하지 않습니다.

## Definition of Done

### Repository artifact

- environment, service와 platform state가 분리되어 있습니다.
- module의 입력, 출력과 소유하지 않는 범위가 명확합니다.
- OU/SCP, IPAM/TGW, 서비스 VPC와 EKS 구조가 코드와 구성도에서 일치합니다.
- 보안, 관측성, 백업, patch, 비용과 변경 통제 기준이 문서화되어 있습니다.
- Current, Target, gap과 필요한 evidence가 구분되어 있습니다.
- README와 PDF의 경로·수치·구현 주장이 현재 저장소와 일치합니다.

### Production promotion

- 실제 account와 Region에 대한 승인된 `terraform plan`과 plan hash가 있습니다.
- 적용 identity, ticket, 승인자, maintenance window와 rollback owner가 연결됩니다.
- 배포 후 health, log, metric, backup과 비용 검증 결과가 있습니다.
- EKS restore, upgrade, drain/PDB와 autoscaling은 격리 환경 rehearsal을 통과합니다.
- Target이나 예시값을 실제 배포·절감·가용성 성과로 표현하지 않습니다.
