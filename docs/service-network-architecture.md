# Enterprise Service Network and Landing Zone Architecture

## 구성 경계

중앙 Landing Zone과 서비스 VPC의 state와 권한을 분리합니다.

- `terraform/landing-zone/ipam`: Network account 주소 카탈로그
- `terraform/landing-zone/network-hub`: TGW, RAM share와 route-table domain
- `terraform/services/<service>/<dev|stg|prod>`: 서비스별 private VPC와 TGW attachment
- `terraform/landing-zone/connectivity`: 중앙 TGW association과 허용 route

서비스 VPC에는 public subnet, Internet Gateway와 NAT Gateway가 없습니다. ingress와 egress는 TGW를 통해 Landing Zone의 중앙 연결 계층으로 전달합니다.

## Address Hierarchy

| Service | Supernet | Dev | Stg | Prod |
| --- | --- | --- | --- | --- |
| commerce | `10.64.0.0/13` | `10.64.0.0/20` | `10.64.32.0/19` | `10.65.0.0/16` |
| payments | `10.72.0.0/14` | `10.72.0.0/22` | `10.72.8.0/21` | `10.73.0.0/18` |
| analytics | `10.76.0.0/14` | `10.76.0.0/20` | `10.76.64.0/18` | `10.77.0.0/16` |
| customer-profile | `10.80.0.0/14` | `10.80.0.0/22` | `10.80.8.0/21` | `10.81.0.0/19` |
| internal-admin | `10.84.0.0/16` | `10.84.0.0/22` | `10.84.4.0/22` | `10.84.16.0/20` |

## Subnet Allocation

모든 VPC는 AZ별로 동일한 7개 private tier를 계산합니다.

| Tier | Prefix relative to VPC | 용도 |
| --- | --- | --- |
| Pod | `+3` | VPC CNI Pod secondary ENI, 가장 큰 주소 pool |
| Node | `+4` | EKS managed node group primary ENI |
| AP | `+5` | 일반 application ENI |
| DB | `+6` | RDS, cache와 stateful data |
| LB | `+6` | 내부 ALB/NLB ENI |
| TGW | 고정 `/28` | TGW VPC attachment |
| EKS Cluster | 고정 `/28` | EKS control-plane x-ENI |

### Commerce Prod Example

| Tier | AZ-1 | AZ-2 | AZ-3 |
| --- | --- | --- | --- |
| Pod | `10.65.0.0/19` | `10.65.32.0/19` | `10.65.64.0/19` |
| Node | `10.65.128.0/20` | `10.65.144.0/20` | `10.65.160.0/20` |
| AP | `10.65.176.0/21` | `10.65.184.0/21` | `10.65.192.0/21` |
| DB | `10.65.200.0/22` | `10.65.204.0/22` | `10.65.208.0/22` |
| LB | `10.65.212.0/22` | `10.65.216.0/22` | `10.65.220.0/22` |
| TGW | `10.65.255.160/28` | `10.65.255.176/28` | `10.65.255.192/28` |
| EKS Cluster | `10.65.255.208/28` | `10.65.255.224/28` | `10.65.255.240/28` |

AWS account마다 AZ 이름이 다른 물리 zone을 가리킬 수 있으므로 service root는 `apne2-az1`, `apne2-az2`, `apne2-az3` stable AZ ID를 전달합니다.

## Routing

- LB/AP/Node/Pod/EKS Cluster: `0.0.0.0/0 → Landing Zone TGW`
- DB: enterprise CIDR `10.64.0.0/10 → TGW`, 인터넷 default route 없음
- TGW attachment subnet: VPC local route만 사용
- 같은 VPC 내부 통신: 더 구체적인 VPC local route 사용

TGW default association과 propagation은 비활성입니다. `dev/stg`는 nonprod, `prod`는 prod route table에 연결하고, 허용된 목적지만 `connectivity` root가 생성합니다.

## EKS Network

EKS control plane은 `eks_cluster` subnet, managed node group은 `node` subnet을 사용합니다. VPC CNI managed add-on은 custom networking과 prefix delegation을 사용하고, platform state가 AZ 이름과 `pod` subnet을 연결하는 `ENIConfig`를 생성합니다.

## Evidence Boundary

Terraform은 15개 service VPC, 7개 subnet tier 계산, TGW attachment와 중앙 route policy를 정의합니다. 실제 account ID, RAM principal, 중앙 ingress/egress·inspection attachment, provider plan/apply와 runtime traffic 증적은 아직 입력되지 않았습니다.
