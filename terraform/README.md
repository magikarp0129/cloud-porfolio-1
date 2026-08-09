# Terraform Structure

이 디렉터리는 엔터프라이즈 클라우드 포트폴리오의 Terraform 코드를 담습니다.

## 문서와 현재 상태

| 확인 대상 | 기준 문서 |
| --- | --- |
| Root/state, 적용 순서와 검증 | 이 문서 |
| 19개 module의 상태와 소유 범위 | [Module Catalog](modules/README.md) |
| Landing Zone IPAM/TGW | [Landing Zone](landing-zone/README.md) |
| 서비스 5종·환경 3종 VPC | [Service Terraform Roots](services/README.md) |
| Terraform 기반 AWS 구성도 | [Diagram Guide](diagrams/README.md) |
| 변경 승인, plan과 rollback | [Terraform Change Management](../docs/terraform-change-management.md) |
| EKS Day-2 운영 경계 | [EKS 운영 표준](../docs/eks-operations.md) |

현재 저장소 상태:

| 항목 | 현재 값 | 증거 경계 |
| --- | --- | --- |
| Reusable module | 19개 디렉터리, 18개 `.tf` 구현 | `compute`는 resource 없는 예약 디렉터리 |
| Validation target | 28개 | organization 1, environment/platform 6, standalone module 3, Landing Zone 3, service VPC 15 |
| 공통 환경 | dev, stg, prod | AWS foundation과 Kubernetes platform state 분리 |
| 서비스 VPC | 5 services × 3 environments = 15 roots | TGW attachment까지만 service state가 소유 |
| EKS | 1.35 minor pin, private API, AL2023 node | latest 자동 추종이 아니라 검증된 minor 승격 방식 |
| 검증 상태 | fmt, diagram, service CIDR 검사는 통과 | 최신 전체 validate는 local provider schema handshake에서 중단; 28/28 통과 아님 |

`main.tf`나 module이 존재하는 것과 AWS 배포 완료는 다릅니다. 이 저장소에는 실제 account별 plan/apply, restore와 운영 KPI 증적이 없으므로 코드 구현·로컬 검증·production 적용을 구분합니다.

## AWS 구성도

현재 Terraform 구현을 그림처럼 확인하는 기본 문서는 [`diagrams/aws-infrastructure-diagram.md`](diagrams/aws-infrastructure-diagram.md)입니다. GitHub Markdown에서 Mermaid 도형과 연결선으로 렌더링됩니다. 세부 항목 검색에는 [`diagrams/aws-infrastructure-tree.md`](diagrams/aws-infrastructure-tree.md), 도형 편집에는 [`diagrams/aws-infrastructure.drawio`](diagrams/aws-infrastructure.drawio) 원본을 사용하며, 표현 범위와 갱신 방법은 [`diagrams/README.md`](diagrams/README.md)를 따릅니다.

Terraform의 환경 입력이나 module 연결을 변경할 때는 구성도를 함께 갱신하고 다음 검증으로 VPC, AZ, TGW, 7개 subnet tier, EKS, 로그 보존, Prometheus와 운영 값을 대조합니다.

```bash
python3 scripts/validation/verify-architecture-diagram.py
```

## Root Modules

| Path | Purpose |
| --- | --- |
| `organization/` | AWS Organizations, OU, SCP 등 계정 거버넌스 계층 |
| `landing-zone/ipam/` | 중앙 IPAM과 서비스별 address pool |
| `landing-zone/network-hub/` | Network account의 TGW, RAM share, route table |
| `landing-zone/connectivity/` | 서비스·공통 EKS 환경 attachment association과 중앙 route policy |
| `services/<service>/<env>/` | 서비스 이름과 dev/stg/prod로 분리된 VPC·TGW attachment state |
| `environments/dev/` | 개발 환경 AWS foundation |
| `environments/stg/` | 스테이징 환경 AWS foundation |
| `environments/prod/` | 운영 환경 AWS foundation |
| `environments/<env>/platform/` | EKS 이후 Helm, Istio, Prometheus/Grafana layer |

각 root의 직접 사용법은 [Organization Root](organization/README.md), [Landing Zone](landing-zone/README.md), [Service Roots](services/README.md), [Common Workload Environments](environments/README.md)를 따릅니다.

### 환경별 입력 차이

| 환경 | 공통 VPC | AZ/연결 | EKS log 보존 | Container log 보존 | Prometheus | 운영 차이 |
| --- | --- | --- | ---: | ---: | ---: | --- |
| dev | `10.10.0.0/16` | 2 AZ, Landing Zone TGW | 90일 | 30일 | 7일 | Scheduler, Spot node, backup plan 14일·selection tag `none` |
| stg | `10.15.0.0/16` | 2 AZ, Landing Zone TGW | 90일 | 90일 | 15일 | Scheduler, On-Demand node, backup plan 35일·selection tag `none` |
| prod | `10.20.0.0/16` | 3 AZ, Landing Zone TGW | 365일 | 365일 | 30일 | Scheduler 금지, Vault Lock, On-Demand node |

이 표는 environment root 입력의 요약입니다. node size, budget, quota와 세부 lifecycle은 각 root code 및 [구성도](diagrams/aws-infrastructure-diagram.md)와 함께 확인합니다.

## Reusable Modules

전체 상태, 소유 범위와 제외 범위는 [Terraform Module Catalog](modules/README.md)가 canonical source입니다. 아래 표는 빠른 경로 검색용입니다.

| Path | Purpose |
| --- | --- |
| `modules/organization/` | AWS Organization과 OU 생성 |
| `modules/scp-policy/` | SCP policy 생성 및 OU/account attachment |
| `modules/network/` | 공통 private VPC, 7개 subnet tier, TGW attachment와 endpoint |
| `modules/service-vpc/` | 서비스별 private VPC, 7개 subnet tier와 TGW attachment |
| `modules/transit-gateway-hub/` | 중앙 TGW, route-table domain, RAM share |
| `modules/transit-gateway-routing/` | attachment association과 명시적 TGW route |
| `modules/security-group/` | 변경이 잦은 security group과 독립 ingress/egress rule |
| `modules/route-policy/` | 기존 route table에 추가하는 TGW, peering, inspection route |
| `modules/workload-environment/` | 환경별 foundation composition |
| `modules/security/` | Security group, KMS, audit/security baseline |
| `modules/waf/` | WAF managed rules, rate limit, logging |
| `modules/iam/` | Workload, deployment, audit IAM role |
| `modules/observability/` | CloudWatch, SNS, dashboard, alarms |
| `modules/monitoring-agent-access/` | 전용 read-only diagnostic role, approved log/metric query와 mutation deny guardrail |
| `modules/operations/` | Backup, scheduling, patch, vulnerability operations |
| `modules/cost/` | Budget, anomaly detection, cost reporting |
| `modules/eks/` | EKS, managed node groups, control/Container Insights logs, add-ons, Access Entry, Pod Identity |
| `modules/kubernetes-platform/` | Helm, Istio, Prometheus, namespace quota/LimitRange, PriorityClass, optional PDB |
| `modules/compute/` | Future EC2 Auto Scaling and ECS runtime layer |

## Change Frequency and Ownership

변경 빈도만으로 state를 나누지 않습니다. 리소스 수명주기, 소유 팀, 승인 권한 중 하나 이상이 실제로 다를 때 별도 root/state를 사용합니다.

| Layer | Examples | Change rate | Recommended owner/state |
| --- | --- | --- | --- |
| Foundation | Private VPC, 7개 subnet tier, TGW attachment와 기본 route | Low | Platform/Network team, foundation state |
| Network policy | TGW, peering, inspection, endpoint 추가 route | Medium/High | Network team, foundation 또는 별도 network-policy state |
| Service policy | Application security group and rules | High | Service owner, service/workload state |
| Cluster platform policy | PriorityClass, shared namespace template | Medium | Platform owner, platform state |
| Namespace platform policy | LimitRange, ResourceQuota, PSS baseline | Medium | Platform owner, platform state |
| Workload policy | requests/limits, probes, HPA/KEDA, PDB, topology, service NetworkPolicy | High | Service owner, application release state |

운영 원칙:

- 한 리소스와 한 rule/destination은 하나의 Terraform state만 소유합니다.
- 변경이 잦은 security group rule과 추가 route는 inline block 대신 독립 resource로 관리합니다.
- `for_each`의 key는 `alb_https`, `app_to_db`, `private_a_to_tgw`처럼 의미가 유지되는 이름을 사용합니다.
- 순서가 바뀌면 주소가 변하는 `count`와 list index를 정책 리소스에 사용하지 않습니다.
- 별도 state가 필요하면 foundation output을 승인된 CI input, SSM Parameter Store 등 좁은 interface로 전달합니다. broad `terraform_remote_state` 접근은 최소화합니다.
- Console 긴급 변경은 ticket과 만료 시간을 남기고, 다음 영업일에 import 또는 코드 반영 후 plan으로 drift를 제거합니다.

자세한 구조, 예제, 변경 절차는 [Terraform Change Management](../docs/terraform-change-management.md)를 따릅니다.

## Design Rule

Root module은 조립 계층입니다. 실제 리소스 구현은 재사용 가능한 module 안에 둡니다.

좋은 root module:

- Provider와 backend 설정
- 환경별 locals
- 모듈 호출
- 환경별 변수값

좋은 reusable module:

- 명확한 입력 변수
- 명확한 출력값
- 단일 책임
- 환경 이름에 의존하지 않는 구현
- 기본값은 보수적으로 설정

## Apply Order

```text
organization
  -> landing-zone/ipam
  -> landing-zone/network-hub
  -> services/<service>/<environment>
  -> landing-zone/connectivity

environments/<environment> foundation
  -> environments/<environment>/platform
```

foundation과 platform은 state를 분리합니다. Helm/Kubernetes provider는 EKS API가 준비되고 private endpoint에 접근할 network path가 확보된 이후에만 사용합니다.

EKS log retention, QoS, backup/restore, upgrade와 incident 운영 기준은 [EKS Day-2 Operations](../docs/eks-operations.md)를 따릅니다. 같은 PDB, NetworkPolicy 또는 namespace policy를 platform state와 application release가 동시에 소유하지 않습니다.

Organization, Landing Zone과 공통 environment root는 각 root의 `backend.hcl.example`을 사용합니다. 서비스 root는 `terraform/services/backend.hcl.example`을 복사해 service/environment별 state key를 설정합니다. 실제 `backend.hcl`, `.tfvars`, state와 credential은 repository에 commit하지 않습니다.

```bash
terraform init -backend-config=backend.hcl
```

전체 module 검증은 repository root에서 실행합니다.

```bash
./scripts/validation/validate-terraform.sh
```

검증 단계:

1. `terraform fmt -check -recursive`
2. Mermaid/draw.io/tree와 Terraform 환경 값 동기화 검사
3. 기업 CIDR, 서비스 VPC와 AZ별 subnet 중복 검사
4. 28개 target의 `init -backend=false`와 `validate`
5. Operations scheduler Python 구문 검사

Provider 다운로드, plugin 실행 또는 schema handshake가 실패하면 해당 이후 target은 검증되지 않은 것입니다. CI에서는 provider cache, architecture와 lock file을 고정하고, 실제 변경은 account별 `plan`을 별도 artifact로 생성합니다.

## Root 작업 절차

```text
ticket과 owner 확인
  -> 정확한 root/state 선택
  -> backend와 provider lock 확인
  -> fmt / validate / 정적 정책 검사
  -> 환경별 plan과 replace/destroy 검토
  -> Security·Operations·FinOps·Reviewer handoff
  -> plan hash와 사람 승인
  -> protected CI/CD apply
  -> health/log/metric/cost post-check와 rollback 판단
```

Agent는 patch, validation, plan 분석까지 수행할 수 있지만 `apply` mode는 없습니다. production 배포는 승인된 CI/CD role만 수행합니다.

## Planned Enterprise Extensions

다음 root와 module은 설계 문서 검토 후 단계적으로 구현합니다.

| Path | Purpose |
| --- | --- |
| `identity-center/` | IAM Identity Center permission set과 account assignment root |
| `ai-platform/dev/` | AI Gateway와 Agent Runtime 검증 환경 |
| `ai-platform/prod/` | 승인된 production AI Platform 환경 |
| `modules/identity-center/` | Permission set, policy attachment, group-to-account assignment |
| `modules/ai-gateway/` | Private ingress, runtime, Bedrock VPC endpoint, policy boundary |
| `modules/ai-observability/` | Token metric, usage lake, dashboard, quota와 비용 알람 |
| `observability-platform/` | 중앙 Mimir S3/KMS/private ingress와 Grafana data source root |
| `modules/mimir/` | Mimir distributed topology, tenant limit, retention과 object storage |
| `modules/otel-collector/` | OTel Collector gateway, ServiceAccount, pipeline과 self-monitoring |
| `modules/metrics-autoscaling/` | Prometheus Adapter와 선택적 KEDA platform component |

관측성 확장 module은 아직 생성되지 않은 Target이며 상세 경계는 [Advanced Metrics and Telemetry Platform](../docs/observability-platform.md)을 따릅니다. SCIM user/group membership은 Corporate IdP를 source of truth로 유지하고 Terraform에서 중복 관리하지 않습니다. AI Agent도 Terraform `apply`를 직접 실행하지 않으며 protected CI/CD role과 environment approval을 사용합니다.
