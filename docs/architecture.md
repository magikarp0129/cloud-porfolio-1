# Enterprise Cloud Architecture

## Target Architecture

AWS 기반 workload VPC는 인터넷 경계를 직접 갖지 않는 private spoke로 구성합니다. 외부·사내 트래픽은 Landing Zone의 중앙 ingress/egress·inspection 계층과 Transit Gateway를 통과합니다.

## Workload VPC Subnet

- `LB`: 내부 ALB/NLB ENI
- `AP`: 일반 application ENI
- `DB`: RDS, cache와 stateful data
- `Node`: EKS managed node group
- `Pod`: VPC CNI custom networking secondary ENI
- `TGW`: Transit Gateway VPC attachment
- `EKS Cluster`: control-plane x-ENI

Public subnet, Internet Gateway와 workload VPC NAT Gateway는 생성하지 않습니다. LB/AP/Node/Pod/EKS Cluster subnet의 기본 경로는 Landing Zone TGW를 향하고, DB subnet은 기업 CIDR만 TGW로 전달합니다.

## Landing Zone Shared Services

- Network account: TGW, IPAM, RAM, 중앙 ingress/egress와 inspection
- Security account: 중앙 로그, 탐지, WAF·Firewall 정책
- Shared services: DNS, artifact/package mirror, 운영 도구
- Workload accounts: 서비스별 private VPC와 EKS

중앙 inspection VPC와 실제 north-south attachment는 target이며 현재 Terraform 코드에는 TGW hub, route-table domain과 workload attachment까지만 있습니다.

## Workforce Identity Plane

사람의 AWS 접근은 IAM user와 장기 access key 대신 `Corporate IdP → IAM Identity Center → Permission Set → AWS Account` 흐름을 사용합니다. 상세 설계는 [Enterprise Workforce Identity and AWS Account Access](identity-access.md)를 기준으로 합니다.

## AI Platform Plane

Agent 실행은 Infrastructure OU의 전용 AI Platform account에 중앙화하고, 코드 변경은 pull request와 plan으로 제출합니다. production 배포는 protected CI/CD가 수행합니다. 상세 설계는 [Enterprise AI Platform and Agent Operations](ai-platform.md)를 기준으로 합니다.

## EKS Platform Plane

EKS는 세 lifecycle로 분리합니다.

- Foundation state: cluster, KMS, control-plane 로그, Access Entry, managed node group, managed add-on
- Platform state: VPC CNI ENIConfig, Istio, Prometheus/Grafana, PriorityClass, LimitRange, ResourceQuota
- Application state: workload, requests/limits, probe, HPA/KEDA, PDB, topology와 NetworkPolicy

Control-plane x-ENI, node primary ENI, Pod secondary ENI가 각각 EKS Cluster, Node, Pod subnet을 사용합니다. 상세 Day-2 운영 기준은 [EKS 운영 표준](eks-operations.md)을 따릅니다.
