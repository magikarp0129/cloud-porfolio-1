# Service VPC Module

서비스·환경별 private VPC를 만들고 Landing Zone TGW에 연결합니다. Public subnet, Internet Gateway와 NAT Gateway는 생성하지 않습니다.

| Tier | CIDR 계산 | 용도 | 기본 경로 |
| --- | --- | --- | --- |
| Pod | VPC의 1/8씩, AZ별 | VPC CNI secondary ENI와 Pod IP | TGW |
| Node | VPC의 1/16씩, AZ별 | EKS managed node group | TGW |
| AP | VPC의 1/32씩, AZ별 | 일반 application ENI | TGW |
| DB | VPC의 1/64씩, AZ별 | RDS, cache, stateful data | 기업 CIDR만 TGW |
| LB | VPC의 1/64씩, AZ별 | 내부 ALB/NLB ENI | TGW |
| TGW | AZ별 고정 `/28` | TGW attachment | local |
| EKS Cluster | AZ별 고정 `/28` | EKS control-plane x-ENI | TGW |

`LB` subnet은 `kubernetes.io/role/internal-elb=1` tag를 갖습니다. `Node`와 `Pod` subnet을 분리해 node primary ENI 주소와 Pod secondary ENI 주소가 같은 subnet pool을 경쟁하지 않도록 합니다.

계정마다 AZ 이름이 다른 물리 zone을 가리킬 수 있으므로 service root는 `apne2-az1`, `apne2-az2`, `apne2-az3` 같은 stable AZ ID를 전달합니다. `transit_gateway_id`는 승인된 Landing Zone 배포 artifact에서 주입합니다.
