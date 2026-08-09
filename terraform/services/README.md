# Service Terraform Roots

서비스 이름 아래에 `dev`, `stg`, `prod` 독립 root/state를 둡니다. 저장소의 기존 환경 표기와 맞추기 위해 `prd`가 아니라 `prod`를 사용합니다.

```text
services/
├── commerce/{dev,stg,prod}
├── payments/{dev,stg,prod}
├── analytics/{dev,stg,prod}
├── customer-profile/{dev,stg,prod}
└── internal-admin/{dev,stg,prod}
```

각 root는 `modules/service-vpc`를 호출해 private VPC, AZ별 `LB/AP/DB/Node/Pod/TGW/EKS Cluster` 7개 subnet tier, route table과 TGW attachment를 만듭니다. Public subnet, Internet Gateway와 NAT Gateway는 만들지 않습니다. `transit_gateway_id`는 Landing Zone Network account의 승인된 배포 artifact에서 받습니다.

## VPC Sizing

| Service | Workload profile | Dev | Stg | Prod | 설계 이유 |
| --- | --- | --- | --- | --- | --- |
| commerce | High-growth EKS/API | `10.64.0.0/20` | `10.64.32.0/19` | `10.65.0.0/16` | Pod, ALB, peak campaign scale 여유 |
| payments | Regulated transactional | `10.72.0.0/22` | `10.72.8.0/21` | `10.73.0.0/18` | 격리된 API·data 계층과 DR 여유 |
| analytics | High-IP batch/EKS | `10.76.0.0/20` | `10.76.64.0/18` | `10.77.0.0/16` | 짧은 시간의 대규모 node/Pod scale-out |
| customer-profile | Medium API/data | `10.80.0.0/22` | `10.80.8.0/21` | `10.81.0.0/19` | API·cache·database 확장 |
| internal-admin | Small internal | `10.84.0.0/22` | `10.84.4.0/22` | `10.84.16.0/20` | 소규모지만 3 AZ와 migration 여유 유지 |

## State Keys

state key는 `services/<service>/<environment>/terraform.tfstate` 형식을 사용합니다. 예: `services/commerce/prod/terraform.tfstate`.

서비스 root는 TGW attachment 생성까지만 소유합니다. TGW route table association과 서비스 간 route는 `landing-zone/connectivity` state가 소유합니다.
