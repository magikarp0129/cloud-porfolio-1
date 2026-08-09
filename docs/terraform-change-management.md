# Terraform Change Management

## 1. Purpose

Security group rule과 route는 application 연계, 신규 CIDR, inspection 경로, 장애 대응 때문에 foundation보다 자주 변경됩니다. 이 문서는 변경이 잦은 정책을 독립적으로 수정하면서도 state 분산, rule 충돌, 대규모 plan churn을 막는 운영 기준을 정의합니다.

## 2. Resource Ownership Boundary

| Resource | Owner | State | Change examples |
| --- | --- | --- | --- |
| VPC, subnet, route table, association | Platform/Network | Foundation | CIDR expansion, AZ addition |
| Workload TGW default route | Platform/Network | Foundation | Central ingress/egress path change |
| TGW/peering/inspection route | Network | Foundation or network-policy | New connected network |
| Foundation endpoint security group | Platform | Foundation | Endpoint service addition |
| Service security group and rules | Service owner | Service/workload | New application dependency |
| NetworkPolicy/AuthorizationPolicy | Platform/Service | Platform/application | Namespace communication change |

다음 질문 중 하나라도 `yes`이면 별도 policy root/state를 검토합니다.

1. 변경 승인자가 foundation 변경 승인자와 다른가?
2. 배포 주기가 foundation보다 훨씬 빠른가?
3. 실행 role의 AWS 권한을 더 좁게 제한해야 하는가?
4. 장애 시 foundation과 독립적으로 rollback해야 하는가?

모두 `no`이면 같은 root/state를 유지하되 독립 resource와 module boundary만 분리합니다.

## 3. Repository Pattern

기본 구조:

```text
terraform/
├── environments/<env>/             # foundation root/state
├── environments/<env>/platform/    # Kubernetes platform root/state
└── modules/
    ├── network/                     # VPC, RT, association, default route
    ├── security-group/              # mutable SG and standalone rules
    └── route-policy/                # additional standalone routes
```

권한과 lifecycle이 실제로 분리되는 조직에서는 다음 root를 추가할 수 있습니다.

```text
terraform/environments/<env>/network-policy/   # optional state
terraform/environments/<env>/services/orders/ # optional service state
```

별도 root는 state 수를 늘리므로 단순한 파일 정리 목적으로 만들지 않습니다. Route table ID와 VPC ID는 승인된 pipeline input 또는 SSM Parameter Store 등 명시적인 contract로 전달하고, foundation state 전체를 읽는 권한은 피합니다.

## 4. Security Group Rules

규칙은 `aws_security_group`의 inline `ingress`/`egress` 대신 `aws_vpc_security_group_ingress_rule`과 `aws_vpc_security_group_egress_rule`로 관리합니다.

```hcl
module "orders_sg" {
  source = "../../../modules/security-group"

  name   = "orders-api"
  vpc_id = var.vpc_id

  ingress_rules = {
    alb_to_orders_https = {
      description                  = "TLS from ALB"
      ip_protocol                  = "tcp"
      from_port                    = 8443
      to_port                      = 8443
      referenced_security_group_id = var.alb_security_group_id
    }
  }

  egress_rules = {
    orders_to_database = {
      description                  = "PostgreSQL to orders database"
      ip_protocol                  = "tcp"
      from_port                    = 5432
      to_port                      = 5432
      referenced_security_group_id = var.database_security_group_id
    }
  }
}
```

Map key는 rule의 업무 목적을 나타내며 CIDR이나 port가 바뀌어도 유지합니다. 한 security group의 rule ownership을 Console, CloudFormation, 다른 Terraform state와 섞지 않습니다. Egress는 명시적으로 선언하며 module이 `0.0.0.0/0` allow-all을 자동 추가하지 않습니다.

## 5. Route Policy

Foundation network module은 route table, association과 workload TGW default route를 소유합니다. 추가 경로는 독립 `aws_route` resource로 관리합니다.

```hcl
module "inspection_routes" {
  source = "../../../modules/route-policy"

  route_table_ids = var.ap_route_table_ids

  routes = {
    app_a_to_corporate = {
      route_table_key        = "ap-northeast-2a"
      destination_cidr_block = "10.0.0.0/8"
      transit_gateway_id     = var.transit_gateway_id
    }
    app_c_to_corporate = {
      route_table_key        = "ap-northeast-2c"
      destination_cidr_block = "10.0.0.0/8"
      transit_gateway_id     = var.transit_gateway_id
    }
  }
}
```

동일 route table에서 inline `route`와 독립 `aws_route`를 혼합하지 않습니다. 동일 destination은 한 state만 소유하며, foundation의 `0.0.0.0/0` default route를 policy state가 덮어쓰지 않습니다.

## 6. Change Workflow

1. 요청자는 source, destination, protocol/port, 업무 목적, owner, expiry, rollback 조건을 ticket에 기록합니다.
2. Terraform Agent는 기존 map에 semantic key로 rule 또는 route를 추가합니다.
3. CI/CD Agent는 `fmt`, `validate`, lint/security scan과 speculative plan을 생성합니다.
4. Security Agent는 least privilege, public exposure, overlapping CIDR을 검토합니다.
5. Network 또는 Service CODEOWNER가 plan의 create/update/delete를 승인합니다.
6. 동일 commit을 `dev`, `stg`, `prod` 순서로 승격하고 production environment approval을 받습니다.
7. Monitoring Agent는 reject flow, 5xx, latency, connection error를 변경 전후 비교합니다.

Plan에서 의도하지 않은 전체 rule 교체, route table 교체, 많은 address 이동이 보이면 적용을 중지합니다. 일상 배포에 `-target`을 사용하지 않습니다.

## 7. Emergency and Drift

운영 장애로 Console 변경이 불가피하면 다음 통제를 적용합니다.

- incident/change ticket, 작업자, 명령 또는 화면 증적, 만료 시간, 원복 기준 기록
- break-glass role과 MFA 사용, session logging 유지
- 임시 rule에는 owner와 expiry metadata 기록
- 다음 영업일에 Terraform code 반영 후 import 또는 state reconciliation
- refresh-only plan과 일반 plan으로 drift 제거 확인
- 원인과 permanent fix를 incident review에 연결

Console 변경을 Terraform `ignore_changes`로 영구 은폐하지 않습니다. 긴급 변경 경로는 예외 절차이지 병행 관리 방식이 아닙니다.

## 8. Migration from Inline Blocks

기존 inline rule/route를 한 번에 삭제하고 다시 만들면 통신 단절이 발생할 수 있습니다.

1. 기존 resource address와 실제 AWS rule/route ID를 inventory합니다.
2. 동일 규칙을 표현하는 새 module code를 작성합니다.
3. provider resource의 import ID 형식을 확인하고 기존 객체를 새 address로 import합니다.
4. plan이 no-op인지 확인한 뒤 기존 inline block을 제거합니다.
5. `stg`에서 연결성과 rollback을 검증하고 작은 단위로 production에 적용합니다.

Resource 유형이 달라 `moved` block만으로 이전할 수 없는 경우 import block 또는 `terraform import`를 사용합니다. State 직접 편집은 승인된 복구 절차 외에는 사용하지 않습니다.

## 9. Review Checklist

- Stable semantic map key를 사용했는가?
- Source/destination과 protocol/port가 최소 범위인가?
- `0.0.0.0/0`, `::/0`, broad RFC1918 route가 정당화되었는가?
- 동일 rule/destination을 다른 state가 관리하지 않는가?
- Default route, association, route table 교체가 plan에 나타나지 않는가?
- Owner, expiry, rollback, monitoring query가 ticket에 있는가?
- `dev`와 `stg` 연결성 검증을 통과했는가?
