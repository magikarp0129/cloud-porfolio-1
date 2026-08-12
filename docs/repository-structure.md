# Repository Structure and Code Map

## 전체 구조

```text
cloud-portfolio/
├── AGENTS.md
├── README.md
├── docs/
│   ├── README.md
│   ├── architecture.md
│   ├── service-network-architecture.md
│   ├── terraform-change-management.md
│   ├── eks-operations.md
│   ├── monitoring.md
│   ├── monitoring-alert-policy.md
│   ├── operations.md
│   ├── finops.md
│   ├── identity-access.md
│   ├── security-review.md
│   ├── repository-structure.md
│   ├── portfolio-outline.md
│   ├── portfolio-presentation.md
│   └── portfolio-presentation-header.tex
├── reports/
│   ├── README.md
│   └── templates/
│       ├── monthly-platform-report.md
│       └── incident-report.md
├── scripts/
│   ├── README.md
│   └── pdf/
│       ├── build/build_portfolio_presentation_pdf.py
│       └── verify/verify_portfolio_pdf.py
├── terraform/
│   ├── README.md
│   ├── diagrams/
│   ├── organization/
│   ├── landing-zone/
│   ├── services/
│   ├── environments/
│   └── modules/
└── enterprise-cloud-portfolio.pdf
```

## 디렉터리 책임

| 경로 | 책임 | 포함하지 않는 것 |
| --- | --- | --- |
| `terraform/organization/` | Organizations, OU, SCP와 Tag Policy | account vending과 Control Tower lifecycle |
| `terraform/landing-zone/` | IPAM, TGW hub, RAM과 connectivity | service application resource |
| `terraform/services/` | 서비스별 dev/stg/prod VPC와 TGW attachment | 중앙 TGW association·route |
| `terraform/environments/` | 공통 environment foundation과 Kubernetes platform | 실제 application workload |
| `terraform/modules/` | reusable AWS·Kubernetes resource logic | backend와 환경별 값 |
| `terraform/diagrams/` | Mermaid, 검색용 tree와 draw.io 원본 | live AWS inventory |
| `docs/` | 설계 판단, 운영 기준과 PDF source | state, credential과 raw 운영 데이터 |
| `reports/templates/` | 사람이 채우고 승인할 월간·장애 보고 양식 | 채워진 실제 보고서와 고객 데이터 |
| `scripts/pdf/` | 최종 PDF build와 render verification | Terraform apply와 운영 자동화 |

## Terraform roots

| Root | State ownership |
| --- | --- |
| `organization/` | Organizations와 조직 정책 |
| `landing-zone/ipam/` | 기업·서비스 address pool |
| `landing-zone/network-hub/` | TGW, RAM share와 route-table domain |
| `services/<service>/<env>/` | 서비스 private VPC와 TGW attachment |
| `landing-zone/connectivity/` | attachment association과 허용 route |
| `environments/<env>/` | 공통 VPC, security, IAM, EKS와 AWS 운영 기반 |
| `environments/<env>/platform/` | Kubernetes/Helm resource |

## 질문별 시작 위치

| 질문 | 먼저 볼 파일 | 다음 코드 |
| --- | --- | --- |
| 전체 AWS 경계는 무엇인가 | `docs/architecture.md` | `terraform/organization`, `workload-environment` |
| 다른 account와 어떻게 통신하는가 | `docs/service-network-architecture.md` | `landing-zone/network-hub`, `connectivity` |
| 서비스 CIDR는 왜 다른가 | `docs/service-network-architecture.md` | `terraform/services/*/*/main.tf` |
| Terraform state는 왜 나뉘는가 | `terraform/README.md` | 각 root README와 backend example |
| EKS network와 로그는 어떻게 구성되는가 | `docs/eks-operations.md` | `modules/eks`, `kubernetes-platform` |
| 보안상 무엇이 남았는가 | `docs/security-review.md` | IAM, security, WAF module |
| 운영 보고서는 어떻게 작성하는가 | `reports/README.md` | `reports/templates/` |
| PDF는 어떻게 만드는가 | `scripts/README.md` | PDF source, builder와 verifier |

## 생성 파일

다음 항목은 소스가 아니며 Git에서 제외합니다.

- `.terraform/`과 `.terraform-plugin-cache/`
- `.pdf-tools/`
- `__pycache__/`
- `.DS_Store`
- `tmp/`와 PDF render 이미지
- `*.tfstate*`, 실제 `.tfvars`와 plan artifact

`.terraform.lock.hcl`은 provider dependency lock이므로 각 root에 유지합니다. 생성 cache를 삭제하기 전에는 state나 증적 파일이 섞여 있지 않은지 확인합니다.
