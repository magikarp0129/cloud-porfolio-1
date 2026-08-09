---
title: "엔터프라이즈 AWS 클라우드 아키텍처 포트폴리오"
subtitle: "멀티계정 랜딩 존 · Terraform · EKS · 관측성"
author: "아키텍처 구성: 작성자 · 작성 보조: OpenAI Codex GPT-5.6-Sol (xhigh)"
date: "2026-08-09"
lang: ko-KR
toc: true
toc-title: "목차"
toc-depth: 1
numbersections: true
papersize: a4
fontsize: 10pt
geometry:
  - top=21mm
  - bottom=19mm
  - left=20mm
  - right=20mm
---

\newpage

# 프로젝트 개요

## 구성 범위

AWS Organizations 기반 멀티계정 구조, 중앙 네트워크, 서비스별 VPC, 공통 환경과 EKS 플랫폼을 Terraform으로 구성한 엔터프라이즈 클라우드 아키텍처입니다.

```text
AWS Organizations
  → 중앙 랜딩 존: IPAM · Transit Gateway · RAM
  → 서비스 네트워크: 5개 서비스 × dev/stg/prod
  → 공통 환경: network · security · IAM · operations · cost
  → EKS: private cluster · managed node group · Istio · Prometheus
  → 관측성: CloudWatch Logs · VPC Flow Logs · Grafana · SNS
```

| 항목 | 현재 구성 |
|---|---|
| AWS 리전 | 서울 `ap-northeast-2`, 조직 정책 예외용 `us-east-1` |
| 환경 | `dev`, `stg`, `prod` |
| 서비스 네트워크 | commerce, payments, analytics, customer-profile, internal-admin |
| 서비스 VPC | 5개 서비스 × 3개 환경 = 총 15개 VPC와 독립 Terraform root |
| 중앙 네트워크 | IPAM `10.64.0.0/10`, TGW ASN `64520`, 4개 route table |
| 공통 EKS | Kubernetes `1.35`, private API, AL2023 managed node group |
| Terraform | 19개 module 디렉터리 중 18개 구현, 28개 검증 대상 |
| 운영 도구 | Linux 5개, EKS 1개, AWS 1개 읽기 전용 스크립트 |

## 문서 기준

표와 구성도는 저장소의 현재 Terraform 코드를 기준으로 작성했습니다. `구현`은 코드가 존재한다는 뜻이며 실제 AWS 계정의 배포 완료를 의미하지 않습니다. 코드에 없는 항목은 `미구현`으로 표시합니다.

\newpage

# 프로젝트 배경

## 구축 대상

개발·검증·운영 환경을 분리하고, 여러 업무 서비스를 공통 정책 아래 배치할 수 있는 AWS 플랫폼을 구성합니다.

| 영역 | 구성 요구사항 | 저장소의 구현 위치 |
|---|---|---|
| 조직 | OU, SCP, Tag Policy | `terraform/organization` |
| 중앙 네트워크 | IPAM, TGW, RAM, routing domain | `terraform/landing-zone` |
| 서비스 네트워크 | 서비스별·환경별 독립 VPC | `terraform/services` |
| 공통 환경 | VPC, IAM, 보안, 운영, 비용, EKS | `terraform/environments` |
| Kubernetes | Istio, namespace policy, Prometheus/Grafana | 환경별 `platform` root |
| 관측성 | CloudWatch Logs, VPC Flow Logs, Prometheus | `observability`, `eks`, `kubernetes-platform` |
| 운영 | 백업, scheduler, patch, 장애 점검 | `operations`, `scripts/operations` |

## 현재 코드 범위

| 포함 | 포함하지 않음 |
|---|---|
| Organization, OU, SCP, Tag Policy | AWS 계정 생성과 계정 vending |
| IPAM, TGW, 서비스 VPC 15개 | 중앙 방화벽과 inspection VPC |
| 공통 환경 VPC와 EKS foundation | 서비스별 애플리케이션 배포 |
| Istio, namespace quota, Prometheus/Grafana | 서비스별 RDS, ALB와 데이터 계층 |
| CloudWatch와 SNS 알림 기반 | 중앙 불변 로그 아카이브와 Mimir |
| EKS managed node group | Karpenter, Cluster Autoscaler, 애플리케이션 HPA/KEDA |

작성자는 전체 아키텍처와 최종 구성을 정의했고, Codex GPT-5.6-Sol `xhigh`를 코드 분석, 문서 작성, 일관성 확인과 PDF 제작에 사용했습니다.

\newpage

# 랜딩 존 아키텍처

## 중앙 네트워크 구성

```text
Network Account
├── IPAM regional pool: 10.64.0.0/10
├── Transit Gateway: ASN 64520
│   ├── nonprod route table
│   ├── prod route table
│   ├── shared route table
│   └── inspection route table
└── AWS RAM: Organization 내부 TGW 공유
        ↓
Service Accounts
└── 서비스 VPC attachment → 환경별 TGW route table association
```

TGW의 기본 association과 propagation은 비활성화되어 있습니다. `dev`와 `stg` attachment는 `nonprod`, `prod` attachment는 `prod` route table에 연결됩니다. 서비스 간 route는 `connectivity` root의 허용 목록으로 생성됩니다.

## 공통 환경 VPC

| 환경 | VPC | AZ | 네트워크 경로 | Interface Endpoint | Backup |
|---|---|---:|---|---|---|
| dev | `10.10.0.0/16` | 2 | Landing Zone TGW | 없음 | 14일 |
| stg | `10.15.0.0/16` | 2 | Landing Zone TGW | ECR, Logs, SSM 5종 | 35일 |
| prod | `10.20.0.0/16` | 3 | Landing Zone TGW | EC2, ECR, Logs, SSM, STS 등 8종 | 35일 + Vault Lock |

## 서비스 VPC subnet

```text
서비스 VPC / AZ
├── LB subnet               내부 ALB/NLB ENI
├── AP subnet               일반 애플리케이션 ENI
├── DB subnet               기업 CIDR 외 기본 route 없음
├── EKS Node subnet         Managed Node Group primary ENI
├── VPC CNI Pod subnet      Pod secondary ENI
├── TGW subnet /28          Transit Gateway attachment
└── EKS Cluster subnet /28  control plane x-ENI
```

Workload VPC에는 Public Subnet, Internet Gateway와 NAT Gateway가 없습니다. LB/AP/Node/Pod/EKS Cluster의 기본 route는 Landing Zone TGW로 전달되며 DB subnet은 기업 CIDR만 TGW로 전달합니다.

\newpage

# Terraform 아키텍처

## 디렉터리와 상태 분리

```text
terraform/
├── organization/                  Organization · OU · SCP · Tag Policy
├── landing-zone/
│   ├── ipam/                      IPAM pool
│   ├── network-hub/               TGW · RAM · route table
│   └── connectivity/              association · 허용 route
├── services/{service}/{env}/      15개 서비스 VPC state
├── environments/{env}/            AWS 공통 foundation state
│   └── platform/                  Kubernetes · Helm state
└── modules/                       재사용 module
```

| Terraform state | 생성 항목 |
|---|---|
| `organization` | AWS Organizations, OU, SCP, Tag Policy |
| `landing-zone/ipam` | Enterprise pool과 서비스별 address pool |
| `landing-zone/network-hub` | TGW, RAM share, 4개 route table |
| `services/*/*` | 서비스 private VPC, 7개 subnet tier, TGW attachment |
| `landing-zone/connectivity` | attachment association과 route |
| `environments/{env}` | 공통 VPC, IAM, security, operations, cost, EKS |
| `environments/{env}/platform` | Istio, namespace policy, Prometheus/Grafana |

## Module 구성

| 구분 | 주요 module |
|---|---|
| 조직 | `organization`, `scp-policy` |
| 네트워크 | `network`, `service-vpc`, `transit-gateway-hub`, `transit-gateway-routing` |
| 보안·접근 | `security`, `iam`, `security-group`, `route-policy`, `waf` |
| 플랫폼 | `workload-environment`, `eks`, `kubernetes-platform` |
| 운영·관측 | `observability`, `monitoring-agent-access`, `operations`, `cost` |

배포 순서는 `organization → ipam → network-hub → service VPC → connectivity → environment foundation → Kubernetes platform`입니다. 전체 검증 진입점은 `scripts/validation/validate-terraform.sh`입니다.

\newpage

# 모니터링 및 관측성 아키텍처

## 신호 수집 구조

```text
VPC Flow Logs ───────────────→ CloudWatch Logs → Metric Filter → Alarm
EKS control plane 5종 ───────→ CloudWatch Logs ────────────────→ SNS
Container Insights 4종 ──────→ CloudWatch Logs ────────────────→ Email

Node · Pod · Istio metric ───→ Prometheus → Grafana
                                         └→ Alertmanager

Monitoring Agent ────────────→ Logs Insights · EKS Describe · Kubernetes read-only
```

| 신호 | 저장 위치 | dev / stg / prod | 암호화 |
|---|---|---|---|
| VPC Flow Logs | CloudWatch Logs | 90 / 90 / 365일 | Platform KMS |
| EKS control plane | CloudWatch Logs | 90 / 90 / 365일 | EKS Logs KMS |
| Container 로그 4종 | CloudWatch Logs | 30 / 90 / 365일 | EKS Logs KMS |
| Kubernetes metric | Prometheus 50Gi PVC | 7 / 15 / 30일 | StorageClass 기준 |
| Grafana | 10Gi PVC | 환경별 동일 | StorageClass 기준 |

## 주요 알람 기준

| 지표 | Warning | Critical |
|---|---|---|
| Host CPU | 80% 이상 10분 | 90% 이상 5분 |
| Host memory | 80% 이상 10분 | 90% 이상 5분 또는 OOM |
| Disk·inode | 80% 이상 15분 | 90% 이상 10분 |
| Pod CPU request | 80% 이상 10분 | 95% 이상 5분 |
| Container memory limit | 80% 이상 10분 | 90% 이상 5분 또는 OOMKilled |
| Target 5xx | 2% 이상 5분 | 5% 이상 5분 |
| Node NotReady | 1개 이상 2분 | 1개 이상 5분 |

현재 구현된 AWS 알람은 VPC rejected flow filter와 SNS 흐름입니다. Grafana ingress는 비활성화되어 있습니다. Prometheus, Grafana와 Alertmanager는 설치되지만 Alertmanager receiver·route는 비어 있습니다. 중앙 로그 아카이브와 Mimir 장기 저장은 미구현입니다.

\newpage

# EKS 아키텍처

## Cluster와 Node 구성

```text
Private EKS 1.35
├── EKS Cluster subnet: control plane x-ENI
├── Node subnet: managed node group primary ENI
├── Pod subnet: VPC CNI secondary ENI
├── Access Entry: cluster admin · Monitoring Agent
├── KMS: Kubernetes Secret · node EBS · CloudWatch Logs
├── Managed Add-on 6종
├── Managed Node Group
└── Kubernetes Platform State
    ├── Istio
    ├── application namespace
    └── Prometheus · Grafana · Alertmanager
```

| 항목 | 현재 구성 |
|---|---|
| API endpoint | Private access 사용, public access 비활성 |
| 인증 모드 | `API_AND_CONFIG_MAP`, bootstrap creator admin 비활성 |
| 관리자 | EKS Access Entry + `AmazonEKSClusterAdminPolicy` |
| Secret 암호화 | EKS 전용 KMS key, rotation 사용 |
| Node OS | EKS AL2023 managed node group |
| Node volume | 암호화 gp3, IMDSv2 필수, detailed monitoring |
| Add-on | VPC CNI, CoreDNS, kube-proxy, Pod Identity Agent, EBS CSI, CloudWatch Observability |
| VPC CNI | Custom networking, prefix delegation, AZ별 ENIConfig |

## 환경별 Node Group

| 환경·그룹 | Instance | Capacity | min / desired / max | Disk | Update |
|---|---|---|---|---:|---:|
| dev general | `t3.large` | Spot | 1 / 1 / 3 | 30Gi | 최대 50% |
| stg general | `m6i.large` | On-Demand | 2 / 2 / 5 | 50Gi | 최대 25% |
| prod system | `m7i.large` | On-Demand | 3 / 3 / 6 | 80Gi | 최대 25% |
| prod application | `m7i.large`, `m6i.large` | On-Demand | 3 / 3 / 12 | 80Gi | 최대 25% |

prod `system` 그룹은 `CriticalAddonsOnly=true:NoSchedule` taint를 사용하며, `application` 그룹과 분리되어 있습니다.

## 자동 확장 상태

| 계층 | 현재 상태 |
|---|---|
| Node 공급 | EKS Managed Node Group |
| Karpenter | 미설치 |
| Cluster Autoscaler | 미설치 |
| 애플리케이션 HPA/KEDA | 미구현 |
| Istiod | chart 내부 autoscale 사용, 2~5 replica |
| Terraform `desired_size` | drift 무시 설정, 자동 확장 controller를 의미하지 않음 |

\newpage

## Kubernetes Platform 구성

| 구성 | 현재 내용 |
|---|---|
| Service Mesh | Istio revision 배포, application namespace injection |
| 통신 보안 | namespace 기본 `STRICT` mTLS |
| Ingress | Istio ingress `LoadBalancer`, internal annotation |
| Namespace | `application-dev`, `application-stg`, `application-prod` |
| 자원 정책 | namespace별 ResourceQuota와 container LimitRange |
| PriorityClass | `platform-critical`, `application-high`, `batch-low` |
| Metrics | kube-prometheus-stack, Grafana, Alertmanager |
| Monitoring RBAC | Node, Event, Pod, Deployment, HPA, PDB 읽기 전용 |

## Namespace 자원 한도

| 환경 | CPU requests / limits | Memory requests / limits | Pod | Storage |
|---|---|---|---:|---:|
| dev | 4 / 8 | 8Gi / 16Gi | 50 | 100Gi |
| stg | 12 / 24 | 24Gi / 48Gi | 150 | 250Gi |
| prod | 40 / 80 | 80Gi / 160Gi | 400 | 1Ti |

| Workload 구성 항목 | 현재 상태 |
|---|---|
| PDB | module interface 존재, 환경별 resource 0개 |
| Deployment·StatefulSet | 서비스 애플리케이션 저장소 범위, 현재 없음 |
| Probe·topology spread | 현재 없음 |
| NetworkPolicy | 현재 없음 |
| QoS class | LimitRange 기본값 제공, 최종 class는 실제 Pod requests/limits로 결정 |
| AWS Load Balancer Controller | 미설치 |

EKS control plane 로그 5종과 Container Insights 로그 4종은 앞 장의 관측성 구조로 전달됩니다.

\newpage

# 보안 아키텍처

## 보안 계층

```text
Organization SCP
  → IAM deployment / audit / break-glass role
  → VPC private subnet · endpoint · flow log
  → EKS private API · Access Entry · Pod Identity
  → KMS Secret · EBS · CloudWatch Logs 암호화
  → GuardDuty · Security Hub · Inspector
```

| 영역 | 현재 구성 |
|---|---|
| 계정 기본 | S3 Account Public Access Block, IAM password policy 16자 |
| 암호화 | Platform KMS, EKS KMS, EKS Logs KMS, EBS 기본 암호화 |
| 위협 탐지 | GuardDuty, Security Hub, Inspector v2 |
| 배포 권한 | 지정 principal 또는 GitHub OIDC subject 기반 deployment role |
| 감사 권한 | ReadOnlyAccess + SecurityAudit 기반 audit role |
| 비상 권한 | MFA 조건이 있는 break-glass role interface |
| EKS 접근 | Admin Access Entry와 Monitoring Agent group 분리 |
| Pod AWS 권한 | VPC CNI, EBS CSI, CloudWatch에 Pod Identity 적용 |
| Network | Private EKS API, LB/AP/DB/Node/Pod subnet 분리, TGW 중앙 경로, VPC Flow Logs |

## Edge 보안 상태

WAF module에는 rate limit, AWS Common, Known Bad Inputs, IP Reputation, SQLi managed rule과 Authorization header redaction이 구현되어 있습니다. 현재 환경 root에는 WAF resource ARN 연결이 없으며, AWS Load Balancer Controller도 설치되어 있지 않습니다.

Corporate IdP와 IAM Identity Center permission set은 문서화된 아키텍처이며 Terraform 배포 코드는 현재 없습니다.

\newpage

# 서비스 아키텍처

## 서비스별 네트워크

| 서비스 | Workload | dev | stg | prod |
|---|---|---|---|---|
| commerce | 대규모 EKS/API | `10.64.0.0/20` | `10.64.32.0/19` | `10.65.0.0/16` |
| payments | Transaction | `10.72.0.0/22` | `10.72.8.0/21` | `10.73.0.0/18` |
| analytics | Batch/EKS | `10.76.0.0/20` | `10.76.64.0/18` | `10.77.0.0/16` |
| customer-profile | API/Data | `10.80.0.0/22` | `10.80.8.0/21` | `10.81.0.0/19` |
| internal-admin | 내부 업무 | `10.84.0.0/22` | `10.84.4.0/22` | `10.84.16.0/20` |

## 서비스 VPC 구성

```text
Landing Zone 중앙 ingress
    ↓ Transit Gateway
LB subnet: 내부 ALB/NLB
    ↓
AP subnet: 일반 application
    └ EKS Node subnet: Managed Node Group
         └ VPC CNI Pod subnet: Pod secondary ENI
DB subnet: database, 기업 CIDR 외 기본 route 없음

Service VPC ── TGW subnet ── Enterprise Transit Gateway
            └ EKS Cluster subnet: control plane x-ENI
```

| 구성 요소 | 현재 코드 상태 |
|---|---|
| VPC, private subnet 7개 tier, route table | 구현 |
| Public/IGW/NAT 없음, TGW attachment | 구현 |
| prod stable AZ ID 3개 | 구현 |
| TGW association·서비스 허용 route | `connectivity` root에서 입력 기반 생성 |
| 서비스별 EKS cluster | 미구현 |
| 서비스별 ALB, application, RDS | 미구현 |

`terraform/services`는 서비스 네트워크만 생성합니다. 공통 EKS `dev/stg/prod`는 `10.10.0.0/16`, `10.15.0.0/16`, `10.20.0.0/16`의 별도 reference environment에 구성되어 있습니다.

\newpage

# 거버넌스

## Organization 구조

```text
AWS Organizations Root
├── Security
├── Infrastructure
├── Workloads
│   ├── Dev
│   ├── Stg
│   └── Prod
├── Sandbox
└── Policy-Staging
```

| 정책 | 연결 대상 | 통제 내용 |
|---|---|---|
| DenyLeaveOrganization | Workloads, Infrastructure, Security, Sandbox | 조직 탈퇴 차단 |
| DenyDisableAuditServices | Workloads | CloudTrail, Config, GuardDuty, Security Hub 보호 |
| DenyUnapprovedRegions | Workloads | `ap-northeast-2`, `us-east-1` 외 workload API 제한 |
| DenyDeletePublicAccessControls | Workloads | S3 public access control 삭제 제한 |
| EnterpriseTagPolicy | Workloads, Sandbox | Environment와 ManagedBy 값 표준화 |

## 공통 태그

| Tag | 예시 값 |
|---|---|
| Environment | dev, stg, prod, shared, security, sandbox |
| Owner | platform-team |
| Service | cloud-portfolio 또는 서비스 이름 |
| CostCenter | cloud-platform |
| ManagedBy | terraform, cloudformation, manual-exception |

현재 Organization, OU와 정책 attachment 코드는 존재하지만 `aws_organizations_account`는 없습니다. 계정 생성과 Control Tower account vending은 현재 범위에 포함되지 않습니다.

\newpage

# 비용 관리

## 예산과 이상 탐지

| 환경 | 월 예산 | 비용 이상 알림 | Scheduler | 네트워크 비용 구성 |
|---|---:|---:|---|---|
| dev | USD 300 | USD 50 이상 | 평일 EC2/RDS, 기본 dry-run | TGW + S3 Gateway Endpoint |
| stg | USD 1,000 | USD 100 이상 | 평일 EC2/RDS, 기본 dry-run | TGW + Interface Endpoint 5종 |
| prod | USD 5,000 | USD 300 이상 | 사용하지 않음 | TGW + Interface Endpoint 8종 |

AWS Budgets는 `Environment` tag로 비용을 필터링합니다.

| 알림 단계 | 기준 | 채널 |
|---|---|---|
| Forecasted | 예산 50% 초과 예측 | KMS 암호화 SNS |
| Actual Warning | 실제 비용 80% 초과 | KMS 암호화 SNS |
| Actual Critical | 실제 비용 100% 초과 | KMS 암호화 SNS |
| Cost Anomaly | 서비스별 일간 절대 영향 임계값 초과 | KMS 암호화 SNS |

## 비용 통제 구성

- 세 환경 모두 workload VPC에 Public Subnet, Internet Gateway와 NAT Gateway를 생성하지 않습니다.
- 외부·사내 통신은 TGW 너머 Landing Zone 중앙 경로를 사용합니다.
- dev는 S3 Gateway Endpoint, stg는 Interface Endpoint 5종, prod는 8종을 사용합니다.
- dev와 stg의 scheduler는 `Environment`와 `Schedule=office-hours` tag가 모두 일치하는 EC2와 RDS만 조회합니다.
- prod에서 scheduler를 활성화할 수 없도록 Terraform precondition이 설정되어 있습니다.
- EKS node group은 EC2/RDS scheduler 대상에서 제외되어 있습니다.
- Budget와 Cost Anomaly 알림은 환경별 SNS topic으로 전달됩니다.

현재 저장소에는 예산과 이상 탐지 정책이 구성되어 있으며, 실제 청구 데이터와 절감 실적은 포함되어 있지 않습니다.
