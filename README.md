# Enterprise Cloud Portfolio

Terraform으로 AWS Landing Zone, 서비스 네트워크와 Private EKS 플랫폼을 설계한 엔터프라이즈 클라우드 포트폴리오입니다.

이 저장소는 많은 기능을 나열하기보다 다음 질문에 명확히 답하는 것을 목표로 합니다.

- 여러 AWS account와 환경을 어떤 경계로 나눌 것인가?
- IP 충돌 없이 서비스별 VPC와 subnet을 어떻게 확장할 것인가?
- Terraform root, module과 state를 어떻게 분리할 것인가?
- EKS의 네트워크, 보안, 관측성, 백업과 변경을 어떻게 운영할 것인가?
- 코드가 있는 상태와 실제 production 검증 완료를 어떻게 구분할 것인가?

## 목차

1. [포트폴리오 범위](#1-포트폴리오-범위)
2. [숫자를 읽는 방법](#2-숫자를-읽는-방법)
3. [전체 아키텍처](#3-전체-아키텍처)
4. [서비스 네트워크와 IP 설계](#4-서비스-네트워크와-ip-설계)
5. [Terraform 구조](#5-terraform-구조)
6. [EKS와 Kubernetes Platform](#6-eks와-kubernetes-platform)
7. [보안·운영·비용](#7-보안운영비용)
8. [문서형 협업 모델](#8-문서형-협업-모델)
9. [저장소 구조와 탐색 순서](#9-저장소-구조와-탐색-순서)
10. [현재 구현과 증거 경계](#10-현재-구현과-증거-경계)
11. [다음 설계 단계](#11-다음-설계-단계)
12. [PDF 포트폴리오](#12-pdf-포트폴리오)

## 1. 포트폴리오 범위

### 중심 범위

| 영역 | 저장소에서 보여주는 내용 | 아직 포함되지 않은 내용 |
| --- | --- | --- |
| Organization | OU, SCP, Tag Policy와 정책 승격 경계 | 실제 account vending과 Control Tower lifecycle |
| Landing Zone | IPAM, TGW, RAM share와 route-table domain | 실제 Network account와 중앙 inspection 배포 |
| Service Network | 5개 서비스의 dev/stg/prod VPC와 7개 subnet tier | application, database와 실제 traffic |
| Terraform | module/root/state 분리와 적용 순서 | 승인된 AWS account별 plan/apply 결과 |
| EKS | private API, managed node/add-on, 로그, Kubernetes platform | 실제 cluster health, load, upgrade와 restore 결과 |
| Operations | backup, scheduler, patch, alert, budget 코드와 기준 | 실제 복구 RPO/RTO, on-call 통지와 billing actual |

### 의도적으로 단순화한 범위

2026-08-12 정리에서 다음 실행형 보조 자산을 제거했습니다.

- Agent Runtime과 장애 분석 simulation
- `config/`, `schemas/`, `examples/`
- 프로젝트 전용 validation·운영 script와 GitHub Actions
- 비교용·구버전 PDF builder
- AI Gateway, Mimir와 Agent 성과 측정 중심의 확장 문서

Agent는 별도 실행 시스템이 아니라 설계·검토 책임을 나누는 문서형 협업 모델로만 남겼습니다. Terraform 검증과 CI/CD는 실제 sandbox 실행 흐름이 결정된 뒤 작게 다시 설계합니다.

## 2. 숫자를 읽는 방법

| 숫자 | 의미 | 주의할 점 |
| ---: | --- | --- |
| 환경 3개 | 공통 platform 환경 `dev`, `stg`, `prod` | AWS account 3개가 실제 생성되었다는 뜻이 아님 |
| 서비스 5개 | commerce, payments, analytics, customer-profile, internal-admin | 서로 다른 주소 요구량 예시 |
| 서비스 VPC 15개 | 서비스 5개 × 환경 3개 Terraform root | 실제 배포 VPC 수가 아니라 코드에 정의된 root 수 |
| subnet tier 7개 | LB, AP, DB, Node, Pod, TGW, EKS Cluster | 각 AZ에 용도별 private subnet을 계산 |
| module 17개 | 현재 `.tf`가 있는 reusable module 디렉터리 | module 수 자체가 품질이나 배포 완료를 의미하지 않음 |
| PDF 1개 | 최종 제출본 `enterprise-cloud-portfolio.pdf` | 비교안과 중간 PDF는 저장소에 보관하지 않음 |

숫자는 설계 범위를 설명합니다. 자동 시험 통과 수나 module 수보다 실제 plan, 배포 후 health와 복구 증거가 더 중요합니다.

## 3. 전체 아키텍처

```text
AWS Organizations
├── Security OU
├── Infrastructure OU
│   ├── Network account
│   │   ├── IPAM 10.64.0.0/10
│   │   ├── Transit Gateway
│   │   └── nonprod / prod / shared / inspection route table
│   └── Log Archive account                [Target]
└── Workloads OU
    ├── 공통 dev/stg/prod platform VPC
    └── 5 services × dev/stg/prod VPC
```

서비스 VPC는 public subnet, Internet Gateway와 NAT Gateway를 직접 갖지 않는 private spoke로 설계했습니다. ingress, egress와 다른 account 통신은 Landing Zone의 TGW와 명시적인 route-table association을 통과합니다.

구성도는 다음 세 형식으로 제공합니다.

- [Mermaid 구성도](terraform/diagrams/aws-infrastructure-diagram.md): GitHub에서 바로 보는 기본 그림
- [검색용 구성 트리](terraform/diagrams/aws-infrastructure-tree.md): 텍스트로 세부 항목 탐색
- [draw.io 원본](terraform/diagrams/aws-infrastructure.drawio): 도형 편집용 원본

## 4. 서비스 네트워크와 IP 설계

기업 서비스 주소 영역은 `10.64.0.0/10`으로 두고 서비스 성장률에 따라 서로 다른 supernet과 환경 VPC 크기를 배정했습니다.

| Service | Supernet | Dev | Stg | Prod | 설계 의도 |
| --- | --- | --- | --- | --- | --- |
| commerce | `10.64.0.0/13` | `10.64.0.0/20` | `10.64.32.0/19` | `10.65.0.0/16` | 주문·상품 traffic과 Pod 확장 여유 |
| payments | `10.72.0.0/14` | `10.72.0.0/22` | `10.72.8.0/21` | `10.73.0.0/18` | 중요하지만 제한된 workload 범위 |
| analytics | `10.76.0.0/14` | `10.76.0.0/20` | `10.76.64.0/18` | `10.77.0.0/16` | batch·worker·data 처리 확장 여유 |
| customer-profile | `10.80.0.0/14` | `10.80.0.0/22` | `10.80.8.0/21` | `10.81.0.0/19` | API와 개인정보 처리 계층 분리 |
| internal-admin | `10.84.0.0/16` | `10.84.0.0/22` | `10.84.4.0/22` | `10.84.16.0/20` | 내부 사용자 중심의 작은 주소 수요 |

모든 VPC는 AZ마다 다음 7개 private tier를 갖습니다.

| Tier | 기본 크기 원칙 | 용도 |
| --- | --- | --- |
| Pod | VPC prefix `+3` | VPC CNI secondary ENI, 가장 큰 주소 pool |
| Node | `+4` | EKS managed node primary ENI |
| AP | `+5` | application ENI |
| DB | `+6` | database, cache와 stateful data |
| LB | `+6` | 내부 ALB/NLB ENI |
| TGW | 고정 `/28` | TGW attachment 전용 |
| EKS Cluster | 고정 `/28` | control-plane x-ENI 전용 |

### Routing 원칙

- LB/AP/Node/Pod/EKS Cluster: `0.0.0.0/0 → Landing Zone TGW`
- DB: `10.64.0.0/10 → TGW`, 인터넷 default route 없음
- TGW attachment subnet: VPC local route만 사용
- TGW default association과 propagation: 비활성
- `dev/stg`와 `prod`: 서로 다른 TGW route-table domain

상세 주소와 commerce-prod의 AZ별 계산 예시는 [서비스 네트워크 설계](docs/service-network-architecture.md)에서 확인할 수 있습니다.

## 5. Terraform 구조

```text
terraform/
├── organization/                 Organizations, OU, SCP와 Tag Policy
├── landing-zone/
│   ├── ipam/                     기업·서비스 address pool
│   ├── network-hub/              TGW, RAM과 route-table domain
│   └── connectivity/             attachment association과 route
├── services/
│   └── <service>/<dev|stg|prod>/ 서비스 VPC 독립 state
├── environments/
│   ├── dev|stg|prod/             공통 AWS foundation state
│   └── <env>/platform/           Kubernetes/Helm state
└── modules/                      17개 reusable module
```

### State 분리 기준

- Organization은 blast radius와 승인자가 다르므로 workload와 분리합니다.
- IPAM/TGW hub와 서비스 VPC는 Network team과 service lifecycle을 분리합니다.
- 공통 environment foundation과 Kubernetes platform은 provider·접근 경로·rollback이 달라 분리합니다.
- 하나의 resource, route, security-group rule 또는 Kubernetes object는 하나의 state만 소유합니다.
- 실제 `backend.hcl`, `.tfvars`, state와 credential은 Git에 저장하지 않습니다.

### 적용 순서

```text
organization
  → landing-zone/ipam
  → landing-zone/network-hub
  → services/<service>/<environment>
  → landing-zone/connectivity

environments/<environment>
  → environments/<environment>/platform
```

실제 배포 전 각 root에서 `terraform fmt`, `terraform init -backend=false`, `terraform validate`를 수행하고, account·backend가 고정된 plan artifact를 별도로 검토해야 합니다. 자세한 변경·승인 기준은 [Terraform Change Management](docs/terraform-change-management.md)를 따릅니다.

## 6. EKS와 Kubernetes Platform

### Foundation state

- EKS `1.35` minor version 명시
- public API endpoint 비활성
- EKS Cluster subnet과 Node subnet 분리
- AL2023 managed node group
- VPC CNI custom networking과 prefix delegation
- VPC CNI, EBS CSI Pod Identity
- API, audit, authenticator, controller manager, scheduler log 활성화
- Container Insights application, dataplane, host, performance log group
- KMS 암호화와 환경별 log retention

### Platform state

- AZ별 Pod subnet을 연결하는 `ENIConfig`
- revision 기반 Istio와 strict mTLS
- Prometheus, Alertmanager와 Grafana
- namespace별 ResourceQuota와 LimitRange
- PriorityClass catalog
- optional PDB interface

### 환경 차이

| 환경 | AZ | EKS control log | Container log | Prometheus | Node 전략 |
| --- | ---: | ---: | ---: | ---: | --- |
| dev | 2 | 90일 | 30일 | 7일 | Spot, 최소 1 |
| stg | 2 | 90일 | 90일 | 15일 | On-Demand, 최소 2 |
| prod | 3 | 365일 | 365일 | 30일 | system/application 분리, 각 최소 3 |

HPA, KEDA, Cluster Autoscaler/Karpenter, workload별 PDB·topology와 default-deny NetworkPolicy는 아직 구현하지 않았습니다. `desired_size` drift ignore는 autoscaler 설치를 의미하지 않습니다.

운영 기준과 남은 검증 항목은 [EKS Day-2 Operations](docs/eks-operations.md)를 기준으로 합니다.

## 7. 보안·운영·비용

| 영역 | 코드에 포함된 통제 | 필요한 production 증거 |
| --- | --- | --- |
| Security | KMS, EBS 기본 암호화, GuardDuty, Security Hub, Inspector | delegated admin과 실제 finding 흐름 |
| IAM | deployment/audit role, OIDC subject 제한, break-glass option | 실제 principal, IAM simulation과 접근 기록 |
| Network | private VPC, subnet 분리, VPC endpoint, TGW route | 중앙 ingress/egress와 왕복 traffic |
| Backup | 태그 기반 plan, prod Vault Lock | EKS composite restore와 RPO/RTO |
| Scheduler | dev/stg EC2·RDS 업무시간 정책, prod 차단 | 대상 tag와 실제 실행 결과 |
| Patch | SSM patch baseline과 Inspector | maintenance window와 patch compliance |
| Monitoring | VPC Flow Logs, CloudWatch alarm/dashboard, Prometheus/Grafana | baseline tuning, receiver와 test notification |
| FinOps | required tag, Budget, Cost Anomaly Detection | CUR/invoice와 실현 절감 검증 |

상세 문서:

- [Security Review](docs/security-review.md)
- [Monitoring](docs/monitoring.md)과 [Alert Policy](docs/monitoring-alert-policy.md)
- [Operations](docs/operations.md)
- [FinOps](docs/finops.md)
- [Workforce Identity](docs/identity-access.md)

## 8. 문서형 협업 모델

Architecture, Terraform, Governance, Security, Monitoring, Operations, FinOps, CI/CD, Reviewer와 Documentation 역할을 구분합니다. 이 역할은 별도 Runtime이나 AWS 권한을 뜻하지 않습니다.

```text
Architecture
  → Governance / Security 검토
  → Terraform 구현
  → Monitoring / Operations / FinOps 검토
  → CI/CD plan·승인 설계
  → Reviewer 독립 검토
  → Documentation 정합화
  → 사람 승인
```

코드 작성과 production 실행은 분리합니다. 자동화 도구 또는 에이전트가 생성한 변경도 사람의 plan 검토와 protected deployment 경계를 우회할 수 없습니다. 역할과 완료 기준은 [AGENTS.md](AGENTS.md)에 간결하게 정리했습니다.

## 9. 저장소 구조와 탐색 순서

```text
.
├── AGENTS.md
├── README.md
├── docs/                         설계·운영 기준과 PDF 원고
├── reports/templates/            월간·장애 보고서 빈 양식
├── scripts/pdf/                  최종 PDF builder와 verifier
├── terraform/                    AWS·Kubernetes IaC와 구성도
└── enterprise-cloud-portfolio.pdf
```

처음 볼 때 권장 순서:

1. 이 README에서 범위와 증거 경계를 확인합니다.
2. [AWS Mermaid 구성도](terraform/diagrams/aws-infrastructure-diagram.md)로 전체 흐름을 봅니다.
3. [서비스 네트워크](docs/service-network-architecture.md)에서 CIDR와 subnet 근거를 확인합니다.
4. [Terraform README](terraform/README.md)에서 root/state/module 경계를 확인합니다.
5. `terraform/organization`, `landing-zone`, `services`, `environments` 순으로 코드를 봅니다.
6. [EKS 운영 문서](docs/eks-operations.md)와 [Security Review](docs/security-review.md)에서 남은 위험을 확인합니다.
7. 마지막으로 최종 PDF를 읽습니다.

전체 문서 역할은 [docs/README.md](docs/README.md), 코드 탐색표는 [repository-structure.md](docs/repository-structure.md)에 있습니다.

## 10. 현재 구현과 증거 경계

### 저장소에서 확인 가능한 것

- Organizations/OU/SCP/Tag Policy 코드
- IPAM `10.64.0.0/10`, TGW hub와 routing domain
- 서비스 5종의 dev/stg/prod VPC root와 주소 설계
- 공통 dev/stg/prod foundation과 별도 Kubernetes platform state
- reusable Terraform module 17개
- Private EKS, managed add-on, Pod Identity와 환경별 로그 보존 코드
- Istio, Prometheus/Grafana, namespace quota와 PriorityClass 코드
- backup, scheduler, patch, vulnerability, budget와 anomaly detection 코드
- Mermaid, Markdown tree와 draw.io 구성도
- 월간 플랫폼 보고서와 장애 보고서 빈 양식

### 아직 주장하지 않는 것

- 실제 AWS account에서 모든 root의 plan/validate 성공
- production apply와 서비스 traffic 검증
- 중앙 ingress/egress·inspection과 immutable log archive 동작
- EKS upgrade, drain, autoscaling과 restore 성공
- 실제 availability, MTTR, 비용 절감 또는 audit 성과

2026-08-12 단순화 이후 기존 자동 검증 수치는 폐기했습니다. 다음 검증 결과는 깨끗한 sandbox와 명시적인 provider/backend 조건에서 새로 기록합니다.

## 11. 다음 설계 단계

우선순위는 새로운 문서를 늘리는 것이 아니라 실행 증거를 만드는 것입니다.

1. 깨끗한 환경에서 root별 `fmt`, `init -backend=false`, `validate` 절차를 재정의합니다.
2. sandbox account에서 Organization을 제외한 최소 root의 plan을 생성합니다.
3. dev Landing Zone과 한 개 service VPC를 적용하고 TGW route와 subnet을 확인합니다.
4. dev EKS를 적용해 private access, Pod IP, log와 add-on 상태를 확인합니다.
5. destroy 또는 격리 restore까지 수행해 rollback과 복구 증거를 남깁니다.
6. 검증 흐름이 안정된 후에만 작은 CI workflow를 다시 추가합니다.
7. 실제 결과를 기준으로 README와 PDF의 Current/Target 표기를 갱신합니다.

중앙 audit, WAF association, autoscaling, Identity Center와 장기 metric backend는 위 기본 경로가 재현된 이후의 확장 과제로 둡니다.

## 12. PDF 포트폴리오

최종 제출본은 저장소 최상위 `enterprise-cloud-portfolio.pdf` 하나입니다.

```bash
python3 scripts/pdf/build/build_portfolio_presentation_pdf.py
python3 scripts/pdf/verify/verify_portfolio_pdf.py enterprise-cloud-portfolio.pdf
```

- 본문 source: `docs/portfolio-presentation.md`
- 스타일 source: `docs/portfolio-presentation-header.tex`
- builder: `scripts/pdf/build/build_portfolio_presentation_pdf.py`
- verifier: `scripts/pdf/verify/verify_portfolio_pdf.py`

중간 렌더링 이미지는 시스템 임시 디렉터리에 생성하며 저장소 내부 `tmp/`는 사용하지 않습니다.
