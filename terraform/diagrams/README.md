# AWS 인프라 구성도

이 디렉터리는 Terraform 코드에서 확인되는 현재 AWS 구성을 diagrams.net(draw.io) 원본으로 관리합니다.

## 파일

- [`aws-infrastructure-diagram.md`](aws-infrastructure-diagram.md): Mermaid가 도형과 연결선으로 렌더링되는 기본 구성도
- [`aws-infrastructure-tree.md`](aws-infrastructure-tree.md): GitHub와 일반 Markdown viewer에서 바로 읽는 기본 구성도
- [`aws-infrastructure.drawio`](aws-infrastructure.drawio): draw.io에서 직접 열고 수정할 수 있는 원본

빠른 검토와 면접 포트폴리오 열람에는 Mermaid 구성도를 사용하고, 세부 항목 검색에는 Markdown 트리, 도형을 직접 편집할 때는 draw.io 원본을 사용합니다.

Mermaid 문서는 조직과 기존 환경, 환경별 VPC, EKS, 운영 흐름, 서비스 Landing Zone, IPAM/VPC 크기와 AZ별 subnet의 일곱 개 구성도로 나뉩니다. GitHub에서 파일을 열면 각 `mermaid` code block이 그림으로 렌더링됩니다.

draw.io 구성도는 다음 여섯 페이지로 나뉩니다.

1. `01 조직과 환경 경계`: AWS Organizations, OU, SCP, 환경별 Terraform root와 상태 경계
2. `02 환경별 AWS 상세 구성`: VPC, subnet, EKS, 관측성, 보안, 백업, 패치, 비용 자원
3. `03 EKS 플랫폼과 운영 흐름`: EKS foundation, Kubernetes platform, application state와 Day-2 운영 흐름
4. `04 서비스 Landing Zone과 TGW`: 중앙 IPAM/TGW와 5개 서비스의 dev·stg·prod attachment 구조
5. `05 서비스 IPAM과 VPC 크기`: `10.64.0.0/10` 기업 대역, 서비스 supernet, 환경별 VPC 크기와 sizing 근거
6. `06 서비스 VPC Subnet 상세`: commerce-prod의 3개 AZ, app·data·public·TGW·EKS cluster subnet과 reserve

## 표현 기준

- 실선과 채워진 상자는 현재 Terraform 코드에 구현되었거나 환경 root에 연결된 항목입니다.
- 점선 상자는 모듈만 존재하고 환경 root에 연결되지 않았거나, 별도 application 저장소와 운영 증적이 필요한 항목입니다.
- `terraform/organization`은 Organization과 OU를 만들지만 AWS 계정을 생성하지 않습니다. 따라서 Dev, Stg, Prod는 계정 자체가 아니라 지정된 workload 계정에 배포되는 환경별 root/state로 표시합니다.
- Kubernetes `Service(type=LoadBalancer)`로 요청되는 Istio 진입점은 Helm이 생성하는 자원임을 표시하며, Terraform AWS 리소스로 직접 선언된 Load Balancer로 표현하지 않습니다.
- 중앙 로그 아카이브, HPA/KEDA, Cluster Autoscaler/Karpenter, application workload는 현재 코드에 구현된 것으로 표시하지 않습니다.

## 코드 기준

| 구성도 항목 | Terraform 기준 파일 |
| --- | --- |
| Organization, OU, SCP | `terraform/organization/main.tf`, `terraform/modules/organization`, `terraform/modules/scp-policy` |
| 환경 차이 | `terraform/environments/dev/main.tf`, `stg/main.tf`, `prod/main.tf` |
| VPC와 subnet | `terraform/modules/network` |
| 보안과 IAM | `terraform/modules/security`, `terraform/modules/iam` |
| EKS와 로그 | `terraform/modules/eks` |
| Kubernetes platform | `terraform/environments/*/platform`, `terraform/modules/kubernetes-platform` |
| 관측성 | `terraform/modules/observability`, `terraform/modules/kubernetes-platform` |
| 백업·일정·패치 | `terraform/modules/operations` |
| 예산·비용 이상 탐지 | `terraform/modules/cost` |
| 중앙 IPAM | `terraform/landing-zone/ipam` |
| 중앙 TGW와 route table | `terraform/landing-zone/network-hub`, `terraform/modules/transit-gateway-hub` |
| 중앙 attachment association/route | `terraform/landing-zone/connectivity`, `terraform/modules/transit-gateway-routing` |
| 서비스 VPC와 TGW attachment | `terraform/services/*/*`, `terraform/modules/service-vpc` |

## 열기와 수정

diagrams.net 데스크톱 또는 웹 편집기에서 `aws-infrastructure.drawio`를 엽니다. 원본은 압축되지 않은 XML 형식이므로 코드 리뷰에서 label과 연결 변경을 확인할 수 있습니다.

Terraform의 환경 값이나 모듈 연결을 바꿀 때는 Mermaid, Markdown tree와 draw.io 원본을 함께 수정합니다. 환경별 VPC·AZ·TGW·EKS 버전·로그 보존·Prometheus·백업·Scheduler 값과 서비스 VPC의 7개 subnet tier를 Terraform diff와 대조합니다. 자동 동기화 검증기는 단순화 과정에서 제거했으며, 새 CI 설계 시 코드에서 값을 추출하는 방식으로 다시 추가합니다.
