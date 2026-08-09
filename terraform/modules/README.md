# Terraform Module Catalog

## 목적

이 디렉터리는 root module이 조립하는 재사용 가능한 Terraform module을 관리합니다. 현재 module 디렉터리는 19개이며 18개는 `.tf` 구현이 있고 `compute`는 향후 EC2 Auto Scaling/ECS runtime을 위한 예약 디렉터리입니다.

환경 이름, account ID와 배포 순서는 root가 결정합니다. reusable module은 입력값, resource lifecycle과 출력 interface만 소유합니다.

## Module 목록

| Module | 상태 | 소유 범위 | 소유하지 않는 범위 |
| --- | --- | --- | --- |
| [organization](organization/README.md) | 구현 | AWS Organization, root·child OU | account vending, Control Tower lifecycle |
| [scp-policy](scp-policy/README.md) | 구현 | SCP/Tag Policy 생성과 attachment | 정책 승인, 예외 register |
| [network](network/README.md) | 구현 | 공통 환경 private VPC, 7개 subnet tier, TGW attachment, endpoint | 중앙 ingress/egress·inspection attachment |
| [service-vpc](service-vpc/README.md) | 구현 | 서비스별 private VPC, 7개 subnet tier, TGW attachment | TGW route-table association과 east-west route |
| [transit-gateway-hub](transit-gateway-hub/README.md) | 구현 | TGW, route-table domain, RAM share | 서비스 attachment와 route association |
| [transit-gateway-routing](transit-gateway-routing/README.md) | 구현 | attachment association과 명시적 TGW route | VPC와 attachment 생성 |
| [security-group](security-group/README.md) | 구현 | 독립 ingress/egress rule과 semantic key | foundation inline rule 중복 소유 |
| [route-policy](route-policy/README.md) | 구현 | 기존 route table의 추가 route | workload VPC의 TGW 기본 route |
| [workload-environment](workload-environment/README.md) | 구현 | network/security/IAM/관측성/운영/비용/EKS composition | Kubernetes Helm/platform state |
| [security](security/README.md) | 구현 | KMS, EBS/S3 baseline, GuardDuty/Security Hub/Inspector | organization CloudTrail/Config aggregator |
| [waf](waf/README.md) | 구현 | WAF rule, logging, 선택적 association | ingress resource 생성과 application exclusion 승인 |
| [iam](iam/README.md) | 구현 | deployment/audit/workload/break-glass role | 사람 SSO와 Identity Center assignment |
| [observability](observability/README.md) | 구현 | VPC Flow Logs, CloudWatch, SNS, dashboard/alarm | EKS logs, Prometheus, 중앙 archive |
| [monitoring-agent-access](monitoring-agent-access/README.md) | 구현 | short-lived read-only diagnostic IAM role | Kubernetes RBAC와 Agent Runtime |
| [operations](operations/README.md) | 구현 | Backup, scheduler, patch baseline, Inspector integration | EKS composite restore 완료와 node in-place patch 주장 |
| [cost](cost/README.md) | 구현 | Budget, Cost Anomaly, SNS 연결 | payer-level CUR/Athena와 실현 절감 검증 |
| [eks](eks/README.md) | 구현 | EKS, cluster/node subnet 분리, managed add-on, VPC CNI custom networking, KMS/log, Pod Identity와 Access Entry | Kubernetes workload, HPA/node autoscaler, 중앙 archive |
| [kubernetes-platform](kubernetes-platform/README.md) | 구현 | VPC CNI ENIConfig, 내부 Istio ingress, namespace baseline, quota/LimitRange/PriorityClass, Prometheus/Grafana | application workload와 실제 PDB instance, autoscaler |
| [compute](compute/README.md) | 예약 | 향후 EC2 ASG/ECS runtime boundary | 현재 resource 없음, EKS와 Helm 중복 소유 금지 |

## Composition과 State Ownership

```text
organization root
  -> organization + scp-policy

environment root
  -> workload-environment
       -> network + security + iam + observability
       -> operations + cost + eks + monitoring-agent-access

environment/platform root
  -> kubernetes-platform

landing-zone and service roots
  -> service-vpc + transit-gateway-hub + transit-gateway-routing
  -> security-group + route-policy where lifecycle ownership is separate
```

하나의 AWS resource, route destination, security-group rule 또는 Kubernetes object는 한 state만 소유합니다. `workload-environment`는 조립 module이며 하위 module resource를 다시 선언하지 않습니다. `kubernetes-platform`은 private EKS API 연결이 필요하므로 AWS foundation과 별도 root/state에서 실행합니다.

## Module README 기준

각 module README에는 최소한 다음 내용을 유지합니다.

- 목적과 현재 구현 상태
- 생성하거나 관리하는 resource 범위
- 명시적으로 소유하지 않는 범위
- 중요한 input/output과 보수적 기본값
- root/state owner와 적용 전 조건
- 검증 명령과 관련 canonical 운영 문서

변수의 전체 schema는 `variables.tf`, machine-readable output은 `outputs.tf`가 source of truth입니다. README는 모든 변수를 복사하지 않고 설계 판단과 위험한 입력만 설명합니다.

## 검증

저장소 루트에서 실행합니다.

```bash
terraform fmt -check -recursive
./scripts/validation/validate-terraform.sh
```

`validate-terraform.sh`는 28개 target을 순회하도록 정의되어 있지만 provider 초기화나 schema handshake 실패도 전체 검증 실패입니다. 일부 정적 검사만 통과한 상태를 module 배포 완료로 표현하지 않습니다.
