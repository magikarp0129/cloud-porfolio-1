# Terraform Structure

이 디렉터리는 AWS Organizations, Landing Zone, 서비스 VPC와 Private EKS 기반을 분리된 root/state와 reusable module로 구성합니다.

## 현재 범위

| 항목 | 코드에 정의된 범위 | Evidence boundary |
| --- | --- | --- |
| Module | `.tf`가 있는 reusable module 17개 | 실제 account plan/apply 증거 없음 |
| Common environment | dev, stg, prod | foundation과 Kubernetes platform state 분리 |
| Service VPC | 5 services × 3 environments = 15 roots | VPC와 TGW attachment까지 소유 |
| EKS | 1.35 pin, private API, AL2023 node와 managed add-on | 실제 cluster runtime 검증 없음 |

## Root와 state

| Path | Purpose |
| --- | --- |
| `organization/` | Organizations, OU, SCP와 Tag Policy |
| `landing-zone/ipam/` | 기업 `10.64.0.0/10`과 서비스별 address pool |
| `landing-zone/network-hub/` | TGW, RAM share와 route-table domain |
| `services/<service>/<env>/` | 서비스 private VPC와 TGW attachment |
| `landing-zone/connectivity/` | attachment association과 허용 TGW route |
| `environments/<env>/` | 공통 AWS foundation |
| `environments/<env>/platform/` | EKS 이후 Kubernetes/Helm layer |

Organization, Landing Zone, service, environment foundation과 platform은 blast radius, owner, provider, 접근 경로와 rollback이 다르므로 분리합니다. 한 resource나 policy object를 두 state가 동시에 소유하지 않습니다.

## 환경별 입력

| 환경 | VPC/AZ | Log retention | Prometheus | 운영 차이 |
| --- | --- | --- | --- | --- |
| dev | `10.10.0.0/16`, 2 AZ | control 90일, container 30일 | 7일 | Spot node, scheduler, backup 14일 |
| stg | `10.15.0.0/16`, 2 AZ | 90일, 90일 | 15일 | On-Demand node, scheduler, backup 35일 |
| prod | `10.20.0.0/16`, 3 AZ | 365일, 365일 | 30일 | node group 분리, Vault Lock, scheduler 금지 |

## Reusable modules

| Group | Modules |
| --- | --- |
| Organization | `organization`, `scp-policy` |
| Network | `network`, `service-vpc`, `transit-gateway-hub`, `transit-gateway-routing`, `security-group`, `route-policy` |
| Composition/Security | `workload-environment`, `security`, `iam`, `waf` |
| Platform | `eks`, `kubernetes-platform`, `observability` |
| Operations/Cost | `operations`, `cost` |

상세 소유 범위는 [Module Catalog](modules/README.md)를 기준으로 합니다.

## Apply order

```text
organization
  → landing-zone/ipam
  → landing-zone/network-hub
  → services/<service>/<environment>
  → landing-zone/connectivity

environments/<environment>
  → environments/<environment>/platform
```

Kubernetes/Helm state는 private EKS API에 접근 가능한 runner에서만 적용합니다.

## Root 작업 절차

```text
ticket과 owner 확인
  → 정확한 root/state 선택
  → backend와 provider lock 확인
  → terraform fmt
  → terraform init -backend=false
  → terraform validate
  → 실제 account/backend가 고정된 plan
  → replace/destroy, 보안과 비용 검토
  → plan hash와 사람 승인
  → protected CI/CD apply
  → health/log/metric/backup/cost 확인
```

예시:

```bash
cd terraform/environments/dev
terraform fmt -check
terraform init -backend=false
terraform validate
```

이 저장소는 현재 project-specific validation wrapper나 CI workflow를 포함하지 않습니다. 깨끗한 sandbox에서 위 표준 절차와 실제 plan을 재현한 뒤 필요한 최소 CI를 다시 설계합니다.

## Backend와 secret

각 root의 `backend.hcl.example`은 구조 예시입니다. 실제 `backend.hcl`, `.tfvars`, state, plan과 credential은 commit하지 않습니다. `.terraform.lock.hcl`은 provider dependency lock이므로 유지합니다.

## Design rules

- root module은 provider, backend, 환경 값과 module 조립만 소유합니다.
- reusable module은 입력, 출력과 하나의 resource lifecycle을 소유합니다.
- 변경 빈도만으로 state를 나누지 않고 owner, 권한 또는 lifecycle이 다를 때 분리합니다.
- route와 security-group rule의 `for_each` key는 의미가 유지되는 이름을 사용합니다.
- Console 긴급 변경은 ticket과 만료 시간을 남기고 import 또는 코드 반영으로 drift를 제거합니다.
- application workload의 HPA, PDB, topology와 NetworkPolicy는 platform state와 중복 관리하지 않습니다.

## Related documents

- [AWS 구성도](diagrams/README.md)
- [Service network](../docs/service-network-architecture.md)
- [Terraform change management](../docs/terraform-change-management.md)
- [EKS operations](../docs/eks-operations.md)
- [Security review](../docs/security-review.md)
