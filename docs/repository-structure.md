# 저장소 구조와 코드 탐색 가이드

## 목적

이 문서는 포트폴리오의 설계 설명이 실제 코드, 운영 기준, 데이터 계약과 검증 증적으로 어디에 연결되는지 보여주는 저장소 구조의 기준 문서입니다. 디렉터리는 파일 종류보다 변경 책임과 실행 권한을 기준으로 분리합니다.

## 전체 구조

```text
cloud-portfolio/
|-- AGENTS.md
|-- README.md
|-- .github/
|   `-- workflows/
|       |-- terraform-validate.yml
|       |-- agent-runtime-test.yml
|       `-- operations-scripts-test.yml
|-- agents/
|   |-- README.md
|   |-- operator-guide.md
|   |-- adoption-scenarios.md
|   |-- request-templates/
|   `-- *-agent.md
|-- agent-runtime/
|   |-- pyproject.toml
|   |-- src/cloud_portfolio_agents/
|   |   |-- adapters/
|   |   |-- cli.py
|   |   |-- contracts.py
|   |   |-- redaction.py
|   |   `-- triage.py
|   `-- tests/
|-- config/
|   `-- monitoring/
|-- examples/
|   `-- incidents/
|-- schemas/
|-- reports/
|   |-- README.md
|   |-- templates/
|   `-- examples/
|-- scripts/
|   |-- README.md
|   |-- agent/
|   |-- validation/
|   |-- operations/
|   |   |-- linux/
|   |   |-- kubernetes/
|   |   `-- aws/
|   |-- pdf/
|   |   |-- build/
|   |   `-- verify/
|   |-- lib/
|   `-- tests/
|-- docs/
|   |-- README.md
|   |-- repository-structure.md
|   |-- architecture.md
|   |-- identity-access.md
|   |-- ai-platform.md
|   |-- terraform-change-management.md
|   |-- monitoring.md
|   |-- monitoring-alert-policy.md
|   |-- observability-platform.md
|   |-- operations.md
|   |-- eks-operations.md
|   |-- finops.md
|   |-- security-review.md
|   |-- agent-incident-triage.md
|   |-- agent-value/
|   |-- portfolio-outline.md
|   |-- portfolio-presentation.md
|   `-- portfolio-presentation-header.tex
|-- terraform/
|   |-- README.md
|   |-- diagrams/
|   |   |-- README.md
|   |   |-- aws-infrastructure-diagram.md
|   |   |-- aws-infrastructure-tree.md
|   |   `-- aws-infrastructure.drawio
|   |-- organization/
|   |   `-- README.md
|   |-- landing-zone/
|   |   |-- ipam/
|   |   |-- network-hub/
|   |   `-- connectivity/
|   |-- services/
|   |   |-- README.md
|   |   `-- {commerce,payments,analytics,customer-profile,internal-admin}/{dev,stg,prod}/
|   |-- environments/
|   |   |-- README.md
|   |   |-- dev/
|   |   |   `-- platform/
|   |   |-- stg/
|   |   |   `-- platform/
|   |   `-- prod/
|   |       `-- platform/
|   `-- modules/
|       `-- README.md
`-- enterprise-cloud-portfolio.pdf
```

`.pdf-tools/`, `.terraform/`, `.terraform-plugin-cache/`, `__pycache__/`, `artifacts/incidents/`는 소스 구조가 아니라 로컬 실행 중 생성되는 임시 또는 민감 산출물입니다. Git에 포함하지 않으며 필요할 때 생성하고 검증 후 정리합니다. 저장소 내부 `tmp/`와 `output/` 디렉터리는 사용하지 않습니다.

## 최상위 파일

| 경로 | 역할 | 변경 시 확인할 내용 |
| --- | --- | --- |
| `README.md` | 프로젝트 전체 설명과 주요 진입점 | 세부 문서·코드와 현재 상태가 일치하는지 확인 |
| `AGENTS.md` | 에이전트 역할, 협업 순서, 실행 경계 | 운영 환경 직접 변경 금지와 승인 책임 확인 |
| `enterprise-cloud-portfolio.pdf` | 최종 제출용 한국어 포트폴리오 | 본문 source, 페이지 검수와 현재 구현 경계 확인 |
| `.gitignore` | 상태, 캐시, PDF, 장애 산출물 제외 | 민감 정보와 생성 파일이 추적되지 않는지 확인 |

## `.github/workflows`

코드 변경을 사람이 검토하기 전에 반복 가능한 자동 검증을 수행합니다.

| 파일 | 검증 대상 | 현재 경계 |
| --- | --- | --- |
| `terraform-validate.yml` | Terraform 형식과 28개 검증 대상 | 계정별 plan/apply는 수행하지 않음 |
| `agent-runtime-test.yml` | 요청 계약, 보안 경계, 읽기 전용 장애 분석 | 고정 모의 입력을 사용하며 실제 운영 조회가 아님 |
| `operations-scripts-test.yml` | 운영 스크립트 Bash 구문, 도움말, 금지 패턴 | 실제 서버·EKS·AWS 통합 시험은 별도 필요 |

## `agents`

AI 에이전트의 역할과 운영자가 요청하는 방식을 정의합니다.

- `*-agent.md`: Platform Manager와 Architecture, Terraform, Governance, Security, Monitoring, Operations, FinOps, CI/CD, Reviewer, Documentation 역할의 책임과 산출물
- `operator-guide.md`: 요청, 승인, 인계, 세션 재개와 보고 절차
- `adoption-scenarios.md`: 읽기 전용 자문에서 제한 위임까지의 단계적 도입 조건
- `request-templates/`: 운영자가 역할별 질문과 범위를 빠짐없이 작성하도록 돕는 YAML 양식

이 디렉터리는 실행 코드가 아니라 역할·승인·성과 기준입니다. 실제로 실행되는 모니터링 에이전트 최소 기능은 `agent-runtime/`에 있습니다.

## `agent-runtime`

읽기 전용 장애 분석 최소 기능을 구현합니다.

| 경로 | 책임 |
| --- | --- |
| `src/cloud_portfolio_agents/contracts.py` | 요청과 실행 설정의 환경·티켓·비용·조회 범위 검증 |
| `src/cloud_portfolio_agents/adapters/` | CloudWatch, Kubernetes, Prometheus, Grafana의 허용된 조회 실행 |
| `src/cloud_portfolio_agents/redaction.py` | 비밀·개인정보 패턴 마스킹 |
| `src/cloud_portfolio_agents/triage.py` | 사실, 가설, 누락 증적, 복구 후보 보고서 생성 |
| `src/cloud_portfolio_agents/cli.py` | validate와 run 명령 진입점 |
| `tests/` | 요청 계약, 보안 경계, Terraform 권한 경계, 보고서 시험 |

운영 환경 변경 기능은 없으며 보고서의 `executed_mutations`는 빈 배열이어야 합니다.

## `config`, `examples`, `schemas`, `reports`

네 디렉터리는 실행 정책, 테스트 입력, machine contract와 사람용 보고서를 분리합니다.

- `config/monitoring/runtime.example.json`: 도구, 시간 제한, 대상 범위와 읽기 전용 조회 목록 예시
- `config/monitoring/metric-catalog.example.json`: 지표 이름, 단위, 소유자와 사용 목적 예시
- `examples/incidents/`: 운영 정보가 아닌 모의 장애 요청과 증적
- `schemas/incident-request.schema.json`: 포털 또는 AI Gateway가 생성할 장애 요청 계약
- `schemas/incident-report.schema.json`: 후속 시스템과 담당자에게 전달할 보고서 계약
- `reports/templates/`: 월간 플랫폼 운영 보고서와 장애 보고서 발행 양식
- `reports/examples/`: fixture 결과를 사람이 검토할 수 있게 정리한 sanitized simulation 예시

`examples/`는 CI가 실행하는 입력이고 `reports/examples/`는 포트폴리오에서 읽는 출력 예시입니다. 둘 다 운영 자격 증명이나 실제 고객 식별자를 포함하지 않으며 live KPI나 장애 증적으로 합산하지 않습니다. 보고 종류, cadence, 보존과 승인 기준은 `docs/agent-value/measurement-reporting.md`가 소유합니다.

## `scripts`

사람과 CI가 실행하는 검증·운영 도구입니다. 상세 사용법과 안전 원칙은 [운영 및 검증 스크립트](../scripts/README.md)를 기준으로 합니다.

| 하위 경로 | 책임 | 변경 여부 |
| --- | --- | --- |
| `agent/agentctl.py` | 모니터링 에이전트 요청 검증과 모의 실행 | 보고서 파일 생성, 인프라 변경 없음 |
| `validation/` | Terraform, 구성도, CIDR, 알람 정책 검증 | 로컬 캐시는 만들 수 있으나 AWS 자원은 변경하지 않음 |
| `operations/linux/` | 호스트, traffic·socket queue, CPU·memory·FD·disk, systemd와 패치 증적 수집 | 읽기 전용 |
| `operations/kubernetes/` | 명시한 context의 EKS/Kubernetes 상태 수집 | 읽기 전용 |
| `operations/aws/` | CloudWatch Logs 보존과 KMS 구성 감사 | 읽기 전용 |
| `pdf/build/` | 현재 문서와 선택적 비교 자료를 PDF로 생성 | 최종 또는 로컬 비교 PDF 생성 |
| `pdf/verify/` | PDF 텍스트, 페이지와 전체 렌더링 확인 | 임시 PNG 생성 후 정리 가능 |
| `lib/` | 명령, Linux, 정수, 출력 파일 공통 검증 | 실행 보조 |
| `tests/` | 운영 스크립트 구문·도움말·금지 패턴 검증 | 로컬·CI 검증 |

## `docs`

코드만으로 설명하기 어려운 설계 판단과 운영 조건의 기준 문서입니다.

| 문서 | 주요 내용 |
| --- | --- |
| `README.md` | 문서 전체 목록, 상태, canonical scope와 추가 규칙 |
| `architecture.md` | 목표 계정, 네트워크, 보안과 플랫폼 구조 |
| `service-network-architecture.md` | IPAM, TGW, 서비스 VPC와 네트워크 state ownership |
| `identity-access.md` | Corporate IdP, IAM Identity Center, 계정 접근과 비상 권한 |
| `ai-platform.md` | AI Gateway, Agent Runtime, 도구 중개, 추적과 비용 통제 |
| `terraform-change-management.md` | 상태 소유권, plan 검토, 승인과 원복 |
| `monitoring.md` | 신호, 알람 심각도, 담당자와 운영 절차 |
| `monitoring-alert-policy.md` | metric query, 지속 시간, Warning/Critical과 missing-data 기준 |
| `observability-platform.md` | Mimir, OpenTelemetry, 지표 카탈로그와 확장 경계 |
| `operations.md` | 백업, 일정, 패치, 취약점, 지원 종료와 공통 운영 |
| `eks-operations.md` | EKS 로그, 자원 품질, 가용성, 확장, 업그레이드와 복구 |
| `finops.md` | 태그, 예산, 이상 탐지와 비용 최적화 |
| `security-review.md` | 구현 통제, 잔여 위험과 운영 적용 조건 |
| `agent-incident-triage.md` | 읽기 전용 장애 분석 실행과 보고서 |
| `agent-value/` | 비즈니스·엔지니어링 성과, 측정과 보고 기준 |
| `portfolio-outline.md` | PDF 작성 원칙과 서사 계획 |
| `portfolio-presentation.md` | 현재 포트폴리오 PDF 본문 source |
| `portfolio-presentation-header.tex` | 현재 포트폴리오 PDF LaTeX 스타일 |

## `terraform`

AWS와 Kubernetes 기반을 코드로 구성합니다. `terraform/README.md`가 Terraform 사용법의 기준 문서입니다.

`terraform/diagrams/aws-infrastructure-diagram.md`는 Terraform 코드의 현재 구성을 Mermaid 도형으로 보여주며, `aws-infrastructure-tree.md`는 검색 가능한 상세 트리, `aws-infrastructure.drawio`는 도형 편집용 원본입니다. 환경 값 변경은 `scripts/validation/verify-architecture-diagram.py`가 세 파일을 자동 대조하며, module 연결이나 서비스 흐름 변경은 Terraform diff와 구성도를 함께 검토합니다.

### `terraform/organization`

AWS Organizations, OU, SCP와 조직 정책을 조립하는 독립 상태입니다. 조직 전체에 영향을 주므로 workload 환경보다 별도 승인과 상태를 사용합니다.

### `terraform/environments`

| 경로 | 소유 상태 | 차이 |
| --- | --- | --- |
| `dev/` | 개발 AWS 공통 기반 | 2개 가용 영역, 낮은 비용, 짧은 보존과 업무 시간 운영 |
| `stg/` | 검증 AWS 공통 기반 | 운영 전 승격과 장애·복구 검증 |
| `prod/` | 운영 AWS 공통 기반 | 3개 가용 영역, 강화된 보존, 고가용성과 운영 보호 |
| `*/platform/` | Kubernetes와 Helm 상태 | 사설 Kubernetes API 접근과 별도 원복이 필요해 AWS 상태에서 분리 |

각 환경 root는 자원 구현을 복제하지 않고 `workload-environment` 모듈을 조립하며 환경 차이는 입력값으로 표현합니다.

### `terraform/modules`

하위 디렉터리는 19개이며 18개에 Terraform 구현이 있습니다. `compute`는 EC2 Auto Scaling 또는 ECS 같은 향후 실행 계층을 위한 예약 디렉터리입니다. 전체 module별 현재 상태, 소유 범위와 명시적 제외는 `terraform/modules/README.md`에서 관리합니다.

| 그룹 | 모듈 |
| --- | --- |
| 조직·정책 | `organization`, `scp-policy` |
| 공통·서비스 네트워크 | `network`, `service-vpc`, `transit-gateway-hub`, `transit-gateway-routing`, `security-group`, `route-policy` |
| 환경 조립과 보안 | `workload-environment`, `security`, `iam`, `waf` |
| 운영·관측·비용 | `observability`, `monitoring-agent-access`, `operations`, `cost` |
| EKS·Kubernetes | `eks`, `kubernetes-platform` |
| 예약 | `compute` |

## PDF와 생성 디렉터리

- `enterprise-cloud-portfolio.pdf`: README, AGENTS.md와 같은 최상위에 두는 최종 포트폴리오
- 시스템 임시 경로의 `cloud-portfolio-pdf-review/`: PDF 페이지 PNG와 전체 검수 이미지를 생성하는 기본 검수 경로
- `.pdf-tools/samples/`, `.pdf-tools/review/`: 선택형 sample builder와 verifier의 Git 제외 경로
- `artifacts/incidents/`: 모니터링 에이전트 보고서가 생성될 수 있는 경로이며 승인된 티켓 저장소로 명시적으로 옮기기 전에는 Git에 포함하지 않음
- `.pdf-tools/`, `.terraform-plugin-cache/`, `.terraform/`, `__pycache__/`: 도구와 공급자 캐시로서 설계 증적이 아니며 Git에서 제외

## 질문별 코드 탐색 순서

| 확인하려는 질문 | 시작 경로 | 다음 증적 |
| --- | --- | --- |
| 전체 아키텍처를 어떻게 나눴는가 | `docs/architecture.md` | `terraform/organization`, `terraform/modules/workload-environment` |
| 운영 환경은 무엇이 다른가 | `terraform/environments/prod/main.tf` | dev·stg 입력 비교와 모듈 변수 검증 |
| EKS를 어떻게 운영하는가 | `docs/eks-operations.md` | `terraform/modules/eks`, `kubernetes-platform`, EKS 점검 스크립트 |
| 장애를 어떻게 분석하는가 | `docs/agent-incident-triage.md` | `agent-runtime`, `schemas`, 모의 장애 시험 |
| 서버 운영 증적을 어떻게 수집하는가 | `scripts/README.md` | Linux·EKS·AWS 읽기 전용 스크립트와 CI |
| 변경을 어떻게 통제하는가 | `docs/terraform-change-management.md` | `.github/workflows`, `validate-terraform.sh` |
| 성과를 어떻게 증명하는가 | `docs/agent-value/README.md` | 측정 보고서와 성과표 양식 |
