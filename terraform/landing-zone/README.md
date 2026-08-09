# Enterprise Landing Zone

이 디렉터리는 workload VPC보다 먼저 배포되는 중앙 계층입니다. Network account가 IPAM과 Transit Gateway를 소유하고, 서비스 계정과 공통 EKS 환경 root는 RAM으로 공유된 TGW에 attachment를 생성합니다.

## Roots

| Root | State owner | Purpose |
| --- | --- | --- |
| `ipam/` | Network/IPAM account | `10.64.0.0/10` regional pool과 서비스별 pool 예약 |
| `network-hub/` | Network account | TGW, RAM share, prod/nonprod/shared/inspection route table |
| `connectivity/` | Network account | workload attachment association, return route, 허용된 east-west route |

AWS Organizations, OU와 SCP는 기존 `terraform/organization` root가 계속 소유합니다. Organization resource와 Network resource를 한 state에 합치지 않습니다.

## Apply Order

```text
terraform/organization
  -> landing-zone/ipam
  -> landing-zone/network-hub
  -> services/<service>/<environment>
  -> landing-zone/connectivity
```

`network-hub` output의 TGW ID를 승인된 CI variable 또는 SSM Parameter Store로 서비스 root에 전달합니다. 서비스 root output의 attachment ID와 VPC CIDR은 Network 팀이 검증한 artifact로 `connectivity` root에 전달합니다. 광범위한 cross-account `terraform_remote_state` 읽기는 기본 경로로 사용하지 않습니다.

## Routing Policy

- `dev`, `stg` attachment는 `nonprod` route table에 association합니다.
- `prod` attachment는 `prod` route table에 association합니다.
- 기본 route propagation과 service full mesh는 사용하지 않습니다.
- 서비스 간 연결은 `connectivity.allowed_routes`에 목적 CIDR과 target attachment를 명시합니다.
- 중앙 방화벽이 준비되면 prod/nonprod default route를 `inspection` attachment로 전환합니다.
