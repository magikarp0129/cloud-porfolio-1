# Network Module

## 목적과 상태

공통 `dev`, `stg`, `prod` 환경에 인터넷 경계가 없는 private VPC를 만드는 구현 module입니다. Workload VPC의 ingress·egress는 Landing Zone Transit Gateway를 통과합니다.

## 소유 범위

- VPC와 DNS 설정
- AZ별 `LB`, `AP`, `DB`, `Node`, `Pod`, `TGW`, `EKS Cluster` 전용 subnet
- 각 subnet tier의 route table과 association
- TGW attachment
- LB/AP/Node/Pod/EKS Cluster의 `0.0.0.0/0 → TGW` 중앙 경로
- 인터넷 기본 경로가 없는 DB subnet
- S3 Gateway Endpoint와 선택형 Interface Endpoint

이 module은 Internet Gateway, NAT Gateway, public subnet을 생성하지 않습니다. `LB` subnet은 내부 ALB/NLB용이며 `kubernetes.io/role/internal-elb=1` tag를 갖습니다. `Node` subnet은 managed node group, `Pod` subnet은 VPC CNI secondary ENI, `EKS Cluster` subnet은 control-plane x-ENI 전용입니다.

| 구분 | 항목 |
| --- | --- |
| Input | `name`, `cidr_block`, `az_count`, `transit_gateway_id`, endpoint 목록 |
| Output | VPC, 7개 subnet tier, route table, TGW attachment |

실제 외부 연결은 TGW 너머의 Landing Zone ingress/egress·inspection attachment와 중앙 route가 준비되어야 동작합니다. 이 module은 중앙 방화벽, 중앙 NAT와 TGW route-table association을 소유하지 않습니다.
