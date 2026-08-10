# Enterprise Cloud Portfolio

Terraform 기반으로 엔터프라이즈 클라우드 구축 환경을 설계하고 구현하는 포트폴리오 프로젝트입니다.

이 저장소의 목적은 단순히 Terraform 리소스를 만드는 것이 아니라, 실제 기업 클라우드 플랫폼 팀이 고려해야 하는 아키텍처, 보안, 모니터링, 알람, FinOps, 운영 프로세스, 멀티 에이전트 협업 방식을 하나의 구축 사례로 정리하는 것입니다.

## 목차

- [1. Project Goal](#project-goal)
- [2. Target Scope](#target-scope)
  - [2.1 AWS 클라우드 및 네트워크 설계](#scope-aws-network)
  - [2.2 Terraform과 IaC 설계](#scope-terraform-iac)
  - [2.3 EKS 및 Kubernetes Platform 설계](#scope-eks-platform)
  - [2.4 Monitoring 및 Observability 설계](#scope-observability)
  - [2.5 Operations 설계](#scope-operations)
  - [2.6 Security, Governance 및 Workforce Identity 설계](#scope-security-governance-identity)
  - [2.7 FinOps 및 Cost Governance 설계](#scope-finops)
  - [2.8 AI Platform 및 Multi-Agent 설계](#scope-ai-agent)
  - [2.9 Documentation 및 Validation 설계](#scope-documentation-validation)
- [3. Repository Layout](#repository-layout)
- [4. Recommended Build Order](#recommended-build-order)
- [5. Multi-Agent Operating Model](#multi-agent-operating-model)
- [6. Agent Responsibilities](#agent-responsibilities)
- [7. Target Cloud Architecture](#target-cloud-architecture)
- [8. Terraform Implementation Strategy](#terraform-implementation-strategy)
- [9. Monitoring and Alerting](#monitoring-and-alerting)
- [10. Operations Strategy](#operations-strategy)
- [11. FinOps Strategy](#finops-strategy)
- [12. Security and Governance](#security-and-governance)
- [13. PDF 포트폴리오 구성](#pdf-portfolio)
- [14. 현재 상태](#current-status)
- [15. 다음 구현 단계](#next-steps)
- [16. Definition of Done](#definition-of-done)

<a id="project-goal"></a>

## 1. Project Goal

이 포트폴리오는 다음 질문에 답할 수 있어야 합니다.

- 엔터프라이즈 클라우드 환경을 어떤 구조로 설계할 것인가?
- Terraform 코드는 어떻게 모듈화하고 환경별로 분리할 것인가?
- 보안 기준과 접근 제어는 어떻게 잡을 것인가?
- 장애와 이상 징후는 어떻게 모니터링하고 알림을 받을 것인가?
- 비용은 어떻게 추적하고 최적화할 것인가?
- 여러 전문 에이전트가 역할을 나누어 인프라 구축을 수행한다면 어떤 방식으로 협업할 것인가?
- 각 에이전트를 운영환경에서 어떤 identity, tool, 승인 경계로 명령할 것인가?
- 사내 생성형 AI를 AI Gateway로 어떻게 통제하고 token 사용량과 비용을 어떻게 보여줄 것인가?
- 폐쇄망 엔지니어와 개발자가 Corporate SSO와 IAM Identity Center를 통해 AWS account에 어떻게 접근할 것인가?
- 최종 결과를 PDF 포트폴리오로 어떻게 정리할 것인가?

<a id="target-scope"></a>

## 2. Target Scope

초기 버전은 AWS 기준으로 작성합니다. 이후 Azure 또는 GCP 버전으로 확장할 수 있습니다.

구축 범위는 설계 영역별로 다음과 같이 나눕니다.

<a id="scope-aws-network"></a>

### 2.1 AWS 클라우드 및 네트워크 설계

- AWS Organizations 기반 multi-account와 Landing Zone 구조
- VPC, LB/AP/DB/EKS Node/Pod/TGW/EKS Cluster subnet 분리
- Public/private network segmentation과 중앙 ingress/egress
- IPAM, Transit Gateway, RAM과 서비스 간 routing domain
- Compute workload 배포 구조와 dev/stg/prod 환경 분리

<a id="scope-terraform-iac"></a>

### 2.2 Terraform과 IaC 설계

- Organization, Landing Zone, service, environment와 platform root 분리
- reusable Terraform module, input/output과 dependency 구조
- remote state, state ownership과 적용 순서
- 환경별 variable과 promotion 전략
- format, validate, plan review와 protected CI/CD 승인 경계

<a id="scope-eks-platform"></a>

### 2.3 EKS 및 Kubernetes Platform 설계

- Private EKS, managed node group, managed add-on과 Pod Identity
- EKS control plane, node와 VPC CNI Pod network 분리
- Istio, namespace policy, ResourceQuota, LimitRange와 PriorityClass
- EKS Day-2 운영: 로그, QoS, 용량, 가용성, backup, upgrade와 장애 대응
- HPA, KEDA, Cluster Autoscaler/Karpenter와 PDB ownership 경계

<a id="scope-observability"></a>

### 2.4 Monitoring 및 Observability 설계

- CloudWatch, Prometheus와 Grafana 기반 observability stack
- metric, log, trace, dashboard와 alerting flow
- Warning/Critical threshold, 지속 시간과 missing-data policy
- EKS control plane, node/runtime와 application signal 수집
- Mimir, OpenTelemetry와 custom metric 확장 구조

<a id="scope-operations"></a>

### 2.5 Operations 설계

- AWS Backup, restore drill과 retention policy
- Instance scheduling과 workload runtime policy
- Systems Manager patch, CVE/EOS와 OS lifecycle 관리
- Package repository, container image와 artifact 관리
- Linux, EKS와 AWS 읽기 전용 점검, runbook과 정기 운영 보고

<a id="scope-security-governance-identity"></a>

### 2.6 Security, Governance 및 Workforce Identity 설계

- IAM least privilege, security baseline과 encryption
- AWS Organizations OU, SCP와 Tag Policy governance
- network segmentation, WAF, threat detection과 audit logging
- Corporate IdP, IAM Identity Center와 permission set 기반 workforce access
- 폐쇄망 Console/CLI, JIT access와 production 변경 승인

<a id="scope-finops"></a>

### 2.7 FinOps 및 Cost Governance 설계

- 공통 tag와 account/environment/service별 비용 귀속
- AWS Budgets, Cost Anomaly Detection과 알림
- scheduler, rightsizing과 idle resource 최적화
- TGW, endpoint, data transfer와 observability 비용 관리
- baseline, actual billing과 accountable sign-off 기반 절감 효과 검증

<a id="scope-ai-agent"></a>

### 2.8 AI Platform 및 Multi-Agent 설계

- Architecture, Terraform, Security, Monitoring 등 역할별 Agent 운영 모델
- Enterprise AI Gateway, Agent Runtime과 Tool Broker 경계
- identity, model/tool allowlist, data classification과 production 승인
- AI token usage, latency, error와 estimated cost dashboard
- request, evidence, report와 audit artifact의 `request_id`/`trace_id` 연결

<a id="scope-documentation-validation"></a>

### 2.9 Documentation 및 Validation 설계

- README, domain 문서와 PDF 포트폴리오의 canonical ownership
- schema, synthetic fixture, report template/example의 역할 분리
- Terraform, Agent contract, monitoring policy와 운영 스크립트 자동 검증
- 현재 구현, 목표 구조와 production evidence를 구분하는 문서 체계
- PDF 포트폴리오 생성과 전체 페이지 시각 검수

<a id="repository-layout"></a>

## 3. Repository Layout

```text
.
├── AGENTS.md
├── README.md
├── .github/workflows/
│   ├── terraform-validate.yml
│   ├── agent-runtime-test.yml
│   └── operations-scripts-test.yml
├── agents/
│   ├── README.md
│   ├── operator-guide.md
│   ├── adoption-scenarios.md
│   ├── request-templates/
│   ├── platform-manager-agent.md
│   ├── architecture-agent.md
│   ├── terraform-agent.md
│   ├── governance-agent.md
│   ├── security-agent.md
│   ├── monitoring-agent.md
│   ├── operations-agent.md
│   ├── finops-agent.md
│   ├── cicd-agent.md
│   ├── reviewer-agent.md
│   └── documentation-agent.md
├── docs/
│   ├── README.md
│   ├── repository-structure.md
│   ├── portfolio-outline.md
│   ├── agent-value/
│   │   ├── README.md
│   │   ├── business-outcomes.md
│   │   ├── engineering-outcomes.md
│   │   ├── measurement-reporting.md
│   │   └── scorecard-template.md
│   ├── architecture.md
│   ├── service-network-architecture.md
│   ├── identity-access.md
│   ├── ai-platform.md
│   ├── monitoring.md
│   ├── observability-platform.md
│   ├── operations.md
│   ├── eks-operations.md
│   ├── finops.md
│   ├── monitoring-alert-policy.md
│   ├── portfolio-presentation.md
│   ├── terraform-change-management.md
│   ├── security-review.md
│   └── agent-incident-triage.md
├── agent-runtime/
│   ├── src/cloud_portfolio_agents/
│   └── tests/
├── config/monitoring/
├── examples/incidents/
├── schemas/
├── reports/
│   ├── templates/
│   └── examples/
├── scripts/
│   ├── README.md
│   ├── agent/
│   ├── validation/
│   ├── operations/
│   ├── pdf/
│   ├── lib/
│   └── tests/
├── terraform/
    ├── README.md
    ├── diagrams/
    │   ├── README.md
    │   ├── aws-infrastructure-diagram.md
    │   ├── aws-infrastructure-tree.md
    │   └── aws-infrastructure.drawio
    ├── organization/
    │   └── README.md
    ├── landing-zone/
    │   ├── README.md
    │   ├── ipam/
    │   ├── network-hub/
    │   └── connectivity/
    ├── services/
    │   ├── README.md
    │   └── {commerce,payments,analytics,customer-profile,internal-admin}/{dev,stg,prod}/
    ├── environments/
    │   ├── README.md
    │   ├── dev/
    │   │   └── platform/
    │   ├── stg/
    │   │   └── platform/
    │   └── prod/
    │       └── platform/
    └── modules/
        ├── README.md
        ├── organization/
        ├── scp-policy/
        ├── network/
        ├── service-vpc/
        ├── transit-gateway-hub/
        ├── transit-gateway-routing/
        ├── security-group/
        ├── route-policy/
        ├── workload-environment/
        ├── eks/
        ├── kubernetes-platform/
        ├── compute/
        ├── security/
        ├── waf/
        ├── observability/
        ├── operations/
        ├── iam/
        ├── cost/
        └── monitoring-agent-access/
└── enterprise-cloud-portfolio.pdf
```

`README.md`는 전체 내용을 설명하는 메인 문서이며, `docs/`의 전체 파일 목적·상태·canonical 경계는 [문서 디렉터리 안내](docs/README.md)를 먼저 확인합니다. 각 디렉터리의 책임, 생성 파일과 질문별 코드 탐색 순서는 [저장소 구조와 코드 탐색 가이드](docs/repository-structure.md)를 기준으로 합니다. 현재 Terraform 구현은 [AWS 인프라 Mermaid 구성도](terraform/diagrams/aws-infrastructure-diagram.md)에서 그림으로 확인하고, 세부 검색에는 [Markdown 트리](terraform/diagrams/aws-infrastructure-tree.md), 도형 편집에는 [draw.io 원본](terraform/diagrams/aws-infrastructure.drawio)을 사용합니다. Linux, EKS, AWS 운영 점검 도구의 사용법과 안전 경계는 [운영 및 검증 스크립트](scripts/README.md)에 정리합니다. `agents/`는 역할별 에이전트 정의를 분리하고, Agent 도입 성과와 측정 보고 기준은 [Agent Business Value and Engineering Outcomes](docs/agent-value/README.md)를 canonical source로 사용합니다.

| 찾으려는 내용 | 기준 문서 |
| --- | --- |
| Agent 역할, 권한과 production 금지 경계 | [AGENTS.md](AGENTS.md), [Agent Directory](agents/README.md) |
| Terraform root, module, state와 적용 순서 | [Terraform Structure](terraform/README.md) |
| Architecture·운영 문서 전체 목록 | [문서 디렉터리 안내](docs/README.md) |
| 운영 스크립트와 검증 명령 | [운영 및 검증 스크립트](scripts/README.md) |
| 현재 포트폴리오 PDF 원고 | [portfolio-presentation.md](docs/portfolio-presentation.md) |

<a id="recommended-build-order"></a>

## 4. Recommended Build Order

1. `AGENTS.md`에서 에이전트 역할과 협업 규칙을 정의합니다.
2. `docs/README.md`에서 문서별 canonical scope를 확인하고 `docs/portfolio-presentation.md`를 기준으로 현재 PDF 목차와 본문을 관리합니다.
3. `docs/architecture.md`에 전체 클라우드 아키텍처를 설계합니다.
4. `docs/identity-access.md`에 Corporate SSO, IAM Identity Center, 폐쇄망 접근을 설계합니다.
5. `docs/ai-platform.md`에 AI Gateway, Agent Runtime, token dashboard를 설계합니다.
6. `docs/agent-value/`에 비즈니스 outcome, engineering KPI, evidence와 scorecard 기준을 정의합니다.
7. `terraform/modules/README.md`의 ownership에 따라 reusable module을 작성합니다.
8. `terraform/organization`에서 AWS Organizations, OU, SCP와 Tag Policy를 정의합니다.
9. `terraform/landing-zone`에서 IPAM, TGW hub와 중앙 connectivity state를 준비합니다.
10. `terraform/services`에서 5개 서비스의 dev/stg/prod VPC와 TGW attachment를 구성합니다.
11. `terraform/environments/dev`, `stg`, `prod` 순으로 공통 AWS foundation을 승격합니다.
12. 각 `environments/<env>/platform`에서 EKS 이후 Kubernetes/Helm 계층을 별도 state로 적용합니다.
13. `docs/monitoring.md`와 `docs/monitoring-alert-policy.md`에 signal, query, 지속 시간과 severity를 정리합니다.
14. `docs/observability-platform.md`에 Mimir, OpenTelemetry, custom metric과 autoscaling 경계를 정리합니다.
15. `docs/eks-operations.md`에 EKS 로그, QoS, 가용성, 백업, 업그레이드와 runbook을 정리합니다.
16. `docs/operations.md`, `docs/finops.md`, `docs/security-review.md`에 운영·비용·잔여 위험을 정리합니다.
17. `scripts/`의 Linux, EKS, AWS 읽기 전용 운영 점검과 CI 검증을 구성합니다.
18. Reviewer가 코드, diagram, README, 현재/목표와 검증 증거의 일관성을 확인합니다.
19. 최종적으로 `docs/portfolio-presentation.md`를 PDF로 빌드하고 전체 페이지를 검수합니다.

<a id="multi-agent-operating-model"></a>

## 5. Multi-Agent Operating Model

이 프로젝트는 하나의 에이전트가 모든 작업을 처리하는 방식이 아니라, Manager가 요청과 handoff를 조정하고 기능별 전문 조직이 설계·구현·운영·검토를 담당하는 구조입니다. Cloud Platform Owner가 최종 책임을 지고 Agent는 승인된 범위에서 분석과 artifact 작성을 지원합니다.

### Agent 조직도

```text
Cloud Platform Owner / Designated Approver (Human)
└── Cloud Platform Manager Agent
    ├── Strategy, Architecture and Governance Team
    │   ├── Architecture Agent (Domain Lead)
    │   ├── Governance Agent
    │   ├── Security Agent
    │   └── FinOps Agent
    ├── Platform Engineering and Delivery Team
    │   ├── Terraform Agent (Domain Lead)
    │   └── CI/CD Agent
    ├── Reliability and Operations Team
    │   ├── Operations Agent (Domain Lead)
    │   └── Monitoring Agent
    └── Assurance and Knowledge Team
        ├── Reviewer Agent (Independent Assurance Lead)
        └── Documentation Agent
```

| 조직 | 책임 | Domain Lead | 구성 Agent |
| --- | --- | --- | --- |
| Strategy, Architecture and Governance | 목표 구조, 조직 정책, 보안과 비용 전략 | Architecture | Governance, Security, FinOps |
| Platform Engineering and Delivery | Terraform 구현, state와 delivery gate | Terraform | CI/CD |
| Reliability and Operations | 장애, 관측성, backup, patch와 lifecycle | Operations | Monitoring |
| Assurance and Knowledge | 독립 검토, 기록, runbook과 portfolio | Reviewer | Documentation |

Cloud Platform Manager Agent는 cross-domain 요청의 scope, workstream, dependency, 담당 Agent와 완료 조건을 정리합니다. 전문 판단을 덮어쓰거나 최종 승인하지 않으며 production 변경 권한도 없습니다. Security Agent와 Reviewer Agent는 unresolved finding을 Manager를 거치지 않고 Security Owner 또는 designated approver에게 직접 escalation할 수 있습니다.

| Agent | Primary Responsibility | Main Outputs |
| --- | --- | --- |
| Cloud Platform Manager Agent | 요청 triage, 업무 분해, 조직 배정, dependency·handoff·상태 통합 | work breakdown, RACI, routing plan, consolidated status, escalation packet |
| Architecture Agent | 요구사항, 전체 아키텍처, module boundary 설계 | architecture decision, target architecture |
| Terraform Agent | Terraform 코드 작성, 모듈화, 환경 분리 | `terraform/modules`, `terraform/environments`, `terraform/organization` |
| Governance Agent | AWS Organizations, OU, SCP, 정책 준수, 변경 승인 | governance model, SCP catalog, compliance checklist |
| Security Agent | IAM, 네트워크 보안, 정책, 암호화 기준 | security baseline, IAM policy, guardrail |
| Monitoring Agent | 로그, 메트릭, 알람, 대시보드와 장애 증적 설계 | monitoring architecture, alert policy, incident report |
| Operations Agent | 백업, 스케줄, 패치, CVE/EOS, OS lifecycle와 정기 운영 보고 | backup policy, patch policy, operations runbook, monthly platform report |
| FinOps Agent | 비용 태깅, 예산, 사용량 분석, 절감안 | cost policy, budget, optimization report |
| CI/CD Agent | Terraform 검증, plan 리뷰, 배포 자동화 | pipeline, validation workflow, deployment approval |
| Reviewer Agent | 코드 리뷰, 보안 리뷰, 운영 리스크 점검 | review report, improvement backlog |
| Documentation Agent | README, docs, 운영 보고서 양식과 PDF 포트폴리오 문서화 | README, report template/example, PDF outline, portfolio narrative |

협업 흐름은 다음과 같습니다.

1. Cloud Platform Manager Agent가 요청을 접수하고 단일 domain인지 cross-domain인지 분류합니다.
2. cross-domain 요청이면 workstream, Domain Lead, supporting Agent, dependency와 human owner를 지정합니다.
3. Architecture Agent가 target architecture와 module boundary를 정의하고 Governance, Security, FinOps Agent가 전략 제약을 병렬 검토합니다.
4. Terraform Agent와 CI/CD Agent가 코드, state, 검증과 promotion gate를 준비합니다.
5. Operations Agent와 Monitoring Agent가 운영 기준, alert와 post-change evidence를 연결합니다.
6. Security와 Governance Agent가 구현 결과의 guardrail과 정책 준수를 확인합니다.
7. Reviewer Agent가 독립 검토하고 Documentation Agent가 decision과 운영 문서를 정리합니다.
8. Manager Agent가 완료 조건, handoff, blocker와 evidence를 통합합니다.
9. Cloud Platform Owner 또는 designated approver가 최종 판단합니다.
10. protected CI/CD 또는 승인된 human operator만 실제 변경을 실행합니다.

실제 운영에서는 각 Agent를 별도 AWS 관리자로 실행하지 않습니다. 중앙 AI Gateway와 Agent Runtime에 역할별 profile로 등록하고 internal portal, `agentctl` CLI, pull request command 또는 승인된 CI/CD API로 명령합니다.

표준 실행 흐름:

1. 사용자가 Corporate IdP로 인증하고 Agent, task, repository, environment, change ticket을 제출합니다.
2. AI Gateway가 identity, model/tool allowlist, data classification, token/cost quota를 검증합니다.
3. cross-domain 요청은 Manager Agent가 workstream, Domain Lead, dependency와 review gate를 정의합니다.
4. 전문 Agent는 각 profile의 제한된 short-lived credential로 read, draft, validation, plan 작업만 수행합니다.
5. Reviewer가 독립 finding을 작성하고 Manager가 완료 상태와 handoff를 통합합니다.
6. 코드와 정책 변경은 pull request 또는 review report로 제출합니다.
7. `prod` 배포는 plan artifact와 사람 승인을 검증한 protected CI/CD만 수행합니다.
8. model 호출, tool call, handoff, 승인과 결과는 `request_id`와 `trace_id`로 중앙 감사합니다.

Agent 명령 계약과 역할별 runtime 권한은 [Enterprise AI Platform and Agent Operations](docs/ai-platform.md), 사용자 SSO와 account 접근은 [Enterprise Workforce Identity and AWS Account Access](docs/identity-access.md)를 기준으로 합니다.

### Operator Usage Guide

운영자가 Agent를 선택하고 요청, 검토, 승인, handoff하는 전체 절차는 [Multi-Agent Operator Guide](agents/operator-guide.md)를 기준으로 합니다.

현재 저장소에는 Monitoring Agent의 read-only incident evidence collector와 로컬 `agentctl` MVP가 구현되어 있습니다. 실제 Corporate IdP, 중앙 AI Gateway, internal portal, Tool Broker, model runtime은 아직 target architecture이며, 구현된 CLI는 고정 query catalog와 fixture를 이용한 안전한 검증 경로를 제공합니다. 사용 방법과 경계는 [Read-Only Agent Incident Triage](docs/agent-incident-triage.md)를 기준으로 합니다.

Agent 활용 성과는 호출 수나 생성 코드량이 아니라 `Agent capability -> engineering outcome -> service outcome -> business outcome -> evidence`로 평가합니다. 비즈니스 outcome, engineering KPI, report 검증과 월간/분기 scorecard 양식은 [Agent Business Value and Engineering Outcomes](docs/agent-value/README.md)에 정리되어 있습니다. 현재 공통 KPI는 대부분 `defined` 상태이며 live baseline과 검증된 actual이 없으므로 절감액이나 MTTR 개선을 실적처럼 주장하지 않습니다.

운영 원칙:

- Agent에게 secret, access key, customer raw data를 입력하지 않습니다.
- Manager Agent는 다른 Agent의 권한을 상속하거나 사람 승인과 전문 검토를 대행하지 않습니다.
- Agent는 `prod`에서 직접 `apply`, restart, stop, delete, failover를 수행하지 않습니다.
- 중요한 상태는 대화 기억이 아니라 ticket, pull request, repository, plan artifact에 저장합니다.
- 장애 복구와 영구 infrastructure 수정은 별도 ticket으로 관리합니다.
- Agent 결과는 제안이며 사람과 Reviewer의 검증을 거쳐야 합니다.

Agent mode:

| Mode | Allowed | Prohibited |
| --- | --- | --- |
| `read` | repository, metric, log, approved inventory 분석 | 파일 및 cloud 변경 |
| `draft` | 문서, code patch, runbook 초안 | merge, deploy, cloud API 변경 |
| `plan` | fmt, validate, plan, 영향 및 rollback 분석 | apply, restart, delete, purchase |
| `review` | code, plan, policy, evidence 독립 검토 | 원안 자동 승인 또는 deploy |

`apply`는 Agent mode가 아닙니다. 실제 적용은 protected CI/CD deployment stage가 수행합니다.

표준 요청 계약:

```yaml
agent_id: terraform
task: "prod VPC에 SSM interface endpoint 추가"
repository: cloud-portfolio
environment: prod
mode: plan
change_ticket: CHG-2026-0081
data_classification: internal
max_cost_usd: 2.00
timeout_minutes: 30
success_criteria:
  - "private subnet에서 SSM 연결 가능"
constraints:
  - "기존 CIDR 변경 금지"
  - "prod 직접 apply 금지"
rollback_owner: platform-oncall
```

업무별 Agent 순서:

| Workflow | Agent sequence |
| --- | --- |
| Infrastructure change | Manager routing -> Architecture/Governance -> Terraform -> Security -> Reviewer -> Manager status -> Human approval -> CI/CD -> Monitoring |
| Incident response | Human Incident Commander -> Manager coordination -> Monitoring -> Operations -> Security if needed -> Terraform permanent fix -> Reviewer |
| CVE/EOS response | Manager routing -> Security -> Operations -> Terraform/CI-CD -> Reviewer -> Human approval |
| Backup restore | Manager routing -> Operations -> Security -> Monitoring -> Reviewer -> Human execution |
| FinOps review | Manager routing -> FinOps -> Operations -> Terraform -> Reviewer -> FinOps owner |
| Alarm change | Manager routing -> Monitoring -> Service owner -> Operations -> Reviewer -> CI/CD |

Production 승인 기준:

- ticket과 plan scope가 일치해야 합니다.
- 예상하지 않은 destroy/replace가 없어야 합니다.
- IAM, network, KMS, public exposure와 비용 변화가 검토되어야 합니다.
- rollback 또는 forward-fix 절차와 post-deployment metric을 지정해야 합니다.
- Terraform, Security, Reviewer 검토와 platform/service owner 승인이 필요합니다.
- Agent는 자신의 결과를 최종 승인할 수 없습니다.

Agent handoff에는 `request_id`, ticket, environment, 확인된 사실, 가설, artifact, 제약, 요청할 output을 포함합니다. 구두 또는 대화 내용만으로 다른 Agent에게 넘기지 않습니다.

세션과 context 관리:

- Agent 세션은 운영 기록의 source of truth가 아닙니다.
- 새 세션이 이전 대화를 자동으로 완전히 기억한다고 가정하지 않습니다.
- 세션 종료 전에 목표, 완료 조건, 변경 파일, branch/PR, 검증 결과, blocker, 다음 단계, plan hash를 저장합니다.
- 새 세션에서는 ticket과 PR을 source of truth로 지정하고 이미 완료된 작업을 명시합니다.

운영자는 Agent에게 credential 출력, production 직접 변경, Terraform state 강제 수정, audit/security service 비활성화, 검증 없는 SCP/WAF/IAM 완화, alarm suppression, RI/Savings Plans 구매, protected branch 우회를 요청하지 않습니다.

<a id="agent-responsibilities"></a>

## 6. Agent Responsibilities

### Cloud Platform Manager Agent

Cloud Platform Manager Agent는 여러 전문 영역이 포함된 요청의 intake, 업무 분해, 조직 배정과 handoff를 관리합니다.

주요 책임:

- 요청의 목적, scope, environment, ticket과 완료 조건 확인
- workstream, Domain Lead, supporting Agent와 dependency 정의
- Security와 Reviewer의 독립 review path 보존
- handoff artifact, blocker와 전체 진행 상태 통합
- 필요한 human decision과 approval gate escalation
- 완료, 부분 완료와 미확인 항목을 분리한 status report 작성

Manager Agent는 domain 결론을 임의로 변경하거나 production 변경을 승인·실행하지 않습니다. 상세 역할 계약은 [Cloud Platform Manager Agent](agents/platform-manager-agent.md)를 기준으로 합니다.

### Architecture Agent

Architecture Agent는 엔터프라이즈 클라우드의 전체 구조, 요구사항, 설계 원칙, 계층별 책임을 정의합니다.

주요 책임:

- 비즈니스 및 기술 요구사항 정리
- AWS Organizations, landing zone, network, security, workload 구조 설계
- `dev`, `stg`, `prod` 환경 분리 기준 정의
- 고가용성, 확장성, 복구 전략 설계
- Terraform module boundary 설계
- 포트폴리오 PDF에 들어갈 아키텍처 설명 구조 작성

### Terraform Agent

Terraform Agent는 엔터프라이즈 클라우드 인프라를 코드로 정의하고, 재사용 가능한 모듈과 환경별 배포 구조를 관리합니다.

주요 책임:

- Terraform provider, backend, version constraint 정의
- VPC, subnet, routing, security group, IAM, compute, observability 모듈 작성
- AWS Organizations, OU, SCP 구조 작성
- `dev`, `stg`, `prod` 환경 분리
- 변수, 출력값, 태그 표준화
- `terraform fmt`, `terraform validate`, `terraform plan` 기준 관리

### Governance Agent

Governance Agent는 AWS Organizations, OU, SCP, 태그 정책, 변경 승인, 정책 준수 기준을 관리합니다.

Security Agent가 기술적 보안 통제를 담당한다면, Governance Agent는 조직 차원의 운영 규칙과 guardrail을 담당합니다.

주요 책임:

- AWS Organizations 및 OU 구조 설계 검토
- SCP guardrail 설계 및 적용 범위 검토
- 승인 region, 필수 태그, 계정 분리 정책 정의
- Terraform 변경 승인 프로세스 정의
- 정책 예외 처리 기준 정의
- 감사 및 컴플라이언스 리포트 기준 작성

기본 guardrail:

- member account의 organization 이탈 방지
- CloudTrail, AWS Config, GuardDuty 비활성화 방지
- 승인되지 않은 region에서 리소스 생성 제한
- public access 정책 위반 탐지
- 필수 태그 누락 탐지
- production 변경에 대한 plan review 필수화

### Security Agent

Security Agent는 엔터프라이즈 클라우드의 기본 보안 통제, 접근 제어, 네트워크 보호, 암호화 기준을 담당합니다.

주요 책임:

- Least privilege IAM policy 검토
- Landing Zone 중앙 경계와 workload private subnet route 검토
- Security group inbound/outbound 정책 검토
- KMS 암호화 기준 정의
- 로그 보존 및 감사 추적 기준 정의

기본 보안 기준:

- Root account MFA enabled
- IAM user 대신 role 기반 접근 우선
- Public access는 명시적으로 필요한 리소스에만 허용
- S3 bucket public access block 기본 활성화
- CloudTrail, VPC Flow Logs, AWS Config 활성화

### Monitoring Agent

Monitoring Agent는 클라우드 환경의 로그, 메트릭, 알람, 대시보드 설계를 담당합니다.

주요 책임:

- 핵심 서비스별 SLI/SLO 정의
- CloudWatch, Managed Prometheus, Grafana 또는 대체 도구 구조 설계
- 알람 severity 기준 정의
- Slack, Email, PagerDuty 등 알림 채널 설계
- 장애 대응 Runbook 초안 작성
- Mimir tenant/retention/HA와 Prometheus remote-write 장애 격리 설계
- OpenTelemetry 계측·Collector pipeline과 custom metric/cardinality 표준 정의
- Metrics Server, Prometheus Adapter, KEDA의 autoscaling signal과 fallback 검토
- Host CPU·memory 80% 10분 Warning/90% 5분 Critical, disk·inode 80% 15분/90% 10분을 시작점으로 query·M/N·missing-data 정책 관리

### Operations Agent

Operations Agent는 운영 시간 정책, 백업, 패치, OS lifecycle, 패키지 저장소, 인스턴스 스케줄링, 장애 대응 runbook을 담당합니다.

주요 책임:

- 백업 정책과 복구 기준 정의
- `dev`, `stg`, `prod` 운영 시간 및 인스턴스 스케줄 정책 정의
- OS, container image, package lifecycle 관리
- CVE, 취약점, EOL/EOS 대응 프로세스 정의
- 내부 패키지 mirror 또는 artifact repository 구조 설계
- 운영 runbook과 정기 점검 항목 작성

### FinOps Agent

FinOps Agent는 클라우드 비용 가시성, 예산 통제, 리소스 최적화 전략을 담당합니다.

주요 책임:

- 태그 정책 정의
- AWS Budgets, Cost Explorer, CUR 구조 설계
- 비용 알람 기준 정의
- 미사용 리소스 탐지 기준 작성
- Reserved Instances, Savings Plans, right sizing 전략 문서화

### CI/CD Agent

CI/CD Agent는 Terraform 코드의 품질 검증, plan 리뷰, 배포 승인, 환경별 배포 흐름을 자동화합니다.

주요 책임:

- Terraform `fmt`, `validate`, `plan` 자동화
- Pull request 기반 인프라 변경 리뷰 설계
- `dev`, `stg`, `prod` 배포 promotion flow 정의
- OIDC 기반 CI/CD 배포 role 설계
- Terraform state backend와 lock 전략 검토
- 정책 검사 및 보안 스캔 도구 연결

### Reviewer Agent

Reviewer Agent는 Terraform 코드, 아키텍처, 보안, 모니터링, FinOps 문서를 포트폴리오와 실무 품질 관점에서 검토합니다.

주요 책임:

- Terraform module interface 검토
- root module과 reusable module 책임 분리 검토
- security, governance, monitoring, FinOps 누락 항목 점검
- README와 PDF 문서의 일관성 검토
- 과도한 하드코딩, 중복, 위험한 기본값 탐지
- 개선 backlog 작성

### Documentation Agent

Documentation Agent는 README, 세부 문서, PDF 포트폴리오 산출물을 관리합니다.

주요 책임:

- README를 단일 진입 문서로 유지
- `docs/` 문서와 README의 내용 일관성 검토
- PDF 포트폴리오 목차와 본문 작성
- 아키텍처, Terraform 구조, 에이전트 역할, 운영 전략을 설명 가능한 형태로 정리
- 변경 이력과 향후 개선 로드맵 문서화

<a id="target-cloud-architecture"></a>

## 7. Target Cloud Architecture

AWS workload VPC는 인터넷 경계를 직접 갖지 않는 private spoke 구조로 설계합니다.

핵심 구성요소:

- VPC
- Internal LB subnets
- Application subnets
- Database subnets
- EKS node subnets
- VPC CNI Pod subnets
- TGW attachment subnets
- EKS control-plane subnets
- Inspection subnet
- Transit Gateway 또는 VPC peering
- Landing Zone Transit Gateway
- Route tables
- VPC endpoints
- Route 53 private hosted zone
- Security groups
- IAM roles
- Observability stack
- Cost governance resources
- AWS Organizations
- Organizational Units
- Service Control Policies

네트워크 전략:

- 외부·사내 ingress와 egress는 Landing Zone의 중앙 연결 계층을 통과합니다.
- 내부 Load Balancer, application, database, EKS node와 Pod 주소 영역을 분리합니다.
- EKS control-plane x-ENI, node primary ENI, Pod secondary ENI가 서로 다른 subnet을 사용합니다.
- 보안 장비 또는 네트워크 검사 계층은 inspection subnet에 배치합니다.
- S3, ECR, CloudWatch, SSM 등 AWS 서비스 접근은 VPC endpoint를 우선 검토합니다.
- 운영 환경에서는 Multi-AZ 구성을 기본값으로 둡니다.
- Workload VPC에는 public subnet, Internet Gateway와 NAT Gateway를 만들지 않습니다. 외부 outbound가 필요하면 TGW 너머의 중앙 egress를 사용합니다.

Landing zone network 전략:

- `Security` 계정: 중앙 로그, 보안 탐지, WAF/Firewall 정책 관리
- `Network` 또는 `Infrastructure` 계정: shared VPC, Transit Gateway, inspection VPC, DNS 관리
- `Workload` 계정: 서비스별 VPC 또는 shared services와 연결된 workload VPC
- `Sandbox` 계정: 실험 환경이며 강한 비용 제한과 자동 중지 정책 적용

보안 및 트래픽 검사 전략:

- 외부 HTTP/HTTPS 진입점에는 WAF를 적용합니다.
- north-south traffic은 ALB, WAF, firewall 정책으로 보호합니다.
- east-west traffic은 security group, NACL, inspection VPC, service mesh 또는 workload 정책으로 통제합니다.
- UTM 또는 firewall appliance가 필요한 경우 centralized inspection VPC에 배치합니다.
- 관리 접속은 bastion보다 AWS Systems Manager Session Manager를 우선 검토합니다.

모니터링 landing zone 전략:

- CloudWatch는 AWS native metric, log, alarm의 기본 계층으로 사용합니다.
- Prometheus는 Kubernetes local scrape, fast alert, HPA recording rule 계층으로 사용합니다.
- Grafana Mimir는 Prometheus remote-write와 OTel push metric의 중앙 장기 저장·cross-cluster query 계층으로 사용합니다.
- 신규 application custom metric은 OpenTelemetry Metrics API/SDK로 계측하고, always-on service는 Prometheus exporter, short-lived workload는 OTLP를 사용합니다.
- Grafana는 CloudWatch, Mimir, Loki 또는 OpenSearch dashboard 통합 계층으로 사용합니다.
- CPU/memory HPA는 Metrics Server, service custom metric HPA는 Prometheus Adapter, SQS/Kafka event scaling은 KEDA로 분리합니다.
- 중앙 로그 계정에는 CloudTrail, VPC Flow Logs, WAF logs, application logs를 보관합니다.
- 운영 대시보드는 service health, infrastructure health, security events, cost trend를 분리합니다.

상세 tenant, 보존, HA, cardinality, PII와 rollout 기준은 [Advanced Metrics and Telemetry Platform](docs/observability-platform.md)에 정의합니다. Mimir, OTel Collector, Prometheus Adapter와 KEDA는 현재 Terraform 배포가 아니라 Target architecture입니다.

환경 분리 전략:

- `dev`: 비용을 낮춘 검증 환경
- `stg`: 운영 배포 전 검증 환경
- `prod`: 고가용성, 보안, 모니터링 기준을 강화한 운영 환경

조직 구조 전략:

- `Security` OU: 보안 감사, 로그 아카이브, 탐지 서비스 계정
- `Infrastructure` OU: 네트워크, shared service, CI/CD 계정
- `Workloads` OU: 서비스별 workload 계정
- `Sandbox` OU: 실험 및 학습용 계정

Workforce identity 전략:

- Corporate IdP를 SAML 2.0과 SCIM으로 IAM Identity Center organization instance에 연결합니다.
- `Security` OU의 전용 `Identity` account에서 delegated administration을 수행합니다.
- IdP group을 permission set과 AWS account에 연결하고 IAM user와 장기 access key 사용을 피합니다.
- 폐쇄망은 PAW/VDI, Direct Connect 또는 VPN, Console Private Access를 조합합니다.
- `prod` 변경 권한은 ticket, JIT group, MFA, 짧은 session duration을 적용합니다.

AI Platform 전략:

- `Infrastructure` OU에 `AI-Platform-Dev`와 `AI-Platform-Prod` account를 분리합니다.
- 사람과 workload는 private AI Gateway를 통해서만 승인된 model과 Agent를 호출합니다.
- Gateway는 identity, model/tool allowlist, data classification, token/cost quota를 검증합니다.
- Amazon Bedrock은 interface VPC endpoint로 호출하고 외부 provider는 중앙 inspection egress를 사용합니다.
- token, latency, error, policy result, estimated cost를 중앙 usage lake와 dashboard에 기록합니다.

상세 내용은 [Workforce Identity](docs/identity-access.md)와 [AI Platform](docs/ai-platform.md) 문서를 기준으로 합니다.

SCP 전략:

- member account의 organization 이탈 방지
- CloudTrail, Config, GuardDuty 같은 감사 서비스 비활성화 방지
- 승인되지 않은 region에서 리소스 생성 제한
- root 또는 break-glass role 예외는 별도 정책으로 관리

State 전략:

- 포트폴리오 초안에서는 remote backend 설계를 문서화합니다.
- 실제 적용 시 S3 backend와 DynamoDB lock table을 사용합니다.
- State 파일은 git에 커밋하지 않습니다.

구현된 state 경계:

| State | 포함 범위 | 분리 이유 |
| --- | --- | --- |
| `organization/organization.tfstate` | AWS Organizations, OU, SCP, Tag Policy | 조직 전체 영향 정책을 workload 배포와 격리 |
| `workloads/<env>/foundation.tfstate` | VPC, IAM, security, logs, backup, budget, EKS | AWS resource lifecycle과 계정 권한 경계 관리 |
| `workloads/<env>/platform.tfstate` | Helm, Istio, Prometheus, Grafana, namespace policy | Kubernetes API와 chart upgrade lifecycle 분리 |

<a id="terraform-implementation-strategy"></a>

## 8. Terraform Implementation Strategy

Terraform 코드는 environment와 module을 분리합니다.

`terraform/organization`:

- AWS Organizations 관리 root module
- OU 생성
- SCP 생성 및 attachment
- 계정 거버넌스 baseline

이 root module은 실제 workload 배포 환경과 분리합니다. 조직 정책은 변경 영향 범위가 크기 때문에 `dev/stg/prod` workload root module과 같은 lifecycle로 운영하지 않습니다.

`terraform/environments/dev`:

- 개발 및 검증용 root module
- 비용을 줄이기 위해 최소 리소스 구성
- 빠른 테스트와 모듈 검증 목적

`terraform/environments/stg`:

- 운영 배포 전 검증용 root module
- 운영과 유사한 네트워크 및 모니터링 기준 적용
- 배포, 알람, 정책 변경 검증 목적

`terraform/environments/prod`:

- 운영용 root module
- 보안, 가용성, 모니터링 기준 강화
- 변경 전 `plan` 리뷰 필수

`terraform/modules/organization`:

- AWS Organization
- Organizational Unit
- AWS service access principal
- Organization policy type

`terraform/modules/scp-policy`:

- Service Control Policy
- SCP attachment
- OU/account 단위 guardrail

`terraform/modules/network`:

- VPC
- AZ별 LB/AP/DB/Node/Pod/TGW/EKS Cluster subnet
- tier별 Route table과 TGW attachment
- LB/AP/Node/Pod/EKS Cluster의 Landing Zone TGW 기본 route
- internet default route가 없는 database route table
- S3 gateway endpoint와 선택형 interface endpoint

`terraform/modules/security-group`:

- service security group 생성 또는 기존 security group의 rule 전용 관리
- `aws_vpc_security_group_ingress_rule`과 `aws_vpc_security_group_egress_rule` 사용
- `alb_https`, `app_to_db` 같은 stable semantic key 기반 `for_each`
- source/destination 하나만 허용하고 암묵적인 allow-all egress를 만들지 않음

`terraform/modules/route-policy`:

- foundation route table에 추가하는 TGW, VPC peering, inspection, endpoint route
- route table ID와 route policy를 분리하고 stable map key 사용
- destination 하나와 target 하나만 허용
- workload VPC의 TGW default route는 foundation network module이 계속 소유

`terraform/modules/security`:

- KMS key rotation과 EBS default encryption
- account-level S3 public access block
- GuardDuty, Security Hub, Inspector v2
- IAM user 예외 사용을 위한 password policy

`terraform/modules/iam`:

- CI/CD deployment role과 GitHub OIDC claim 제한
- Read-only/SecurityAudit role
- 선택형 MFA break-glass role
- 환경별 managed policy와 permissions boundary 입력

`terraform/modules/observability`:

- CloudWatch Log Group
- CloudWatch Alarm
- CloudWatch Dashboard
- SNS Topic
- Metric Filter
- VPC Flow Logs와 rejected-flow query/dashboard

`terraform/modules/operations`:

- AWS Backup plan
- Backup vault
- EventBridge Scheduler
- Lambda start/stop automation
- Systems Manager Patch Manager
- OS별 Systems Manager patch baseline
- Inspector 기반 EC2/ECR/Lambda 취약점 탐지
- 태그 기반 AWS Backup selection과 선택형 Vault Lock

`terraform/modules/compute`:

- EC2 Auto Scaling Group
- ECS Fargate

`terraform/modules/eks`:

- private EKS API endpoint와 Access Entry
- KMS secret encryption과 전체 control plane logs, 환경별 `90/90/365일` 보존
- CloudWatch Observability add-on과 KMS 암호화된 Container Insights 4종 log group, 환경별 `30/90/365일` 보존
- AL2023 managed node group, encrypted gp3, IMDSv2
- VPC CNI, CoreDNS, kube-proxy, Pod Identity Agent, EBS CSI
- EKS Cluster subnet과 Node subnet 분리, VPC CNI custom networking과 prefix delegation
- CNI/EBS CSI/CloudWatch Pod Identity role 분리
- node Kubernetes/release version과 rolling unavailable 제어

`terraform/modules/kubernetes-platform`:

- AZ별 VPC CNI ENIConfig와 Pod subnet 연결
- revision 기반 Istio control plane과 ingress gateway
- namespace injection label과 strict mTLS
- 환경별 ResourceQuota, LimitRange와 PriorityClass 3종
- workload selector가 확정된 경우에만 사용하는 선택형 PDB interface
- kube-prometheus-stack, Alertmanager, Grafana
- chart version pinning, atomic upgrade

현재 HPA/VPA와 Cluster Autoscaler/Karpenter, Alertmanager receiver/route, 중앙 S3 log archive, 실제 PDB instance는 production backlog입니다. 상세 Current/Target/Evidence는 [EKS Day-2 Operations](docs/eks-operations.md)에 구분했습니다.

`terraform/modules/waf`:

- source IP rate limiting
- AWS managed common, known-bad-input, IP reputation, SQLi rules
- CloudWatch logging과 Authorization header redaction

`terraform/modules/cost`:

- AWS Budgets
- Cost anomaly detection
- 예산 50/80/100 percent SNS 알림

`terraform/modules/workload-environment`:

- network, security, IAM, observability, operations, cost, EKS 조합
- 동일 module interface로 `dev`, `stg`, `prod` 차이를 입력값으로 제한

기본 Terraform 명령:

```bash
terraform fmt -recursive
terraform init -backend-config=backend.hcl
terraform validate
terraform plan
terraform apply
```

전체 정적 검증:

```bash
./scripts/validation/validate-terraform.sh
```

적용 순서:

1. `terraform/organization`을 `Policy-Staging` OU부터 적용합니다.
2. 대상 환경의 foundation root를 적용해 VPC, 보안, 운영 자동화, EKS를 만듭니다.
3. private EKS endpoint에 접근 가능한 VPN 또는 runner에서 해당 환경의 `platform/` root를 적용합니다.
4. `dev`, `stg`, `prod` 순서로 동일 변경을 promotion합니다.
5. 운영 변경은 plan, 비용 영향, 보안 검사 결과와 두 명 이상의 승인을 남깁니다.

Root module 작성 원칙:

- root module은 provider, backend, locals, module 호출만 담당합니다.
- 실제 리소스 구현은 `terraform/modules/*`에 둡니다.
- 환경별 차이는 variable 값으로 표현합니다.
- `dev`, `stg`, `prod`가 같은 모듈을 호출하도록 유지합니다.
- module output을 통해 계층 간 의존성을 명확히 연결합니다.

Module 작성 원칙:

- 모듈은 단일 책임을 가져야 합니다.
- 변수 타입과 description을 반드시 작성합니다.
- 중요한 값은 output으로 노출합니다.
- 환경 이름을 모듈 내부에 하드코딩하지 않습니다.
- 보안 기본값은 닫힌 방향으로 둡니다.
- 비용이 큰 리소스는 enable flag를 제공합니다.

### 변경 빈도가 높은 Network Policy 관리

Security group과 route table은 업무 추가, 연계 시스템 변경, 점검 경로 신설로 자주 바뀝니다. 그러나 변경 빈도만으로 모든 정책을 별도 state로 분리하면 의존성과 적용 순서가 불필요하게 복잡해집니다.

| 구분 | Foundation이 소유 | 변경 정책이 소유 | State 분리 조건 |
| --- | --- | --- | --- |
| Route | route table, TGW default route, association | peering, firewall inspection과 서비스 허용 route | Network 팀의 권한과 배포 주기가 foundation과 다를 때 |
| Security group | VPC endpoint 등 foundation 전용 group | application/service group과 개별 rule | Service 팀이 독립 배포하고 별도 승인 책임을 가질 때 |
| Kubernetes | EKS와 platform bootstrap | NetworkPolicy, Istio AuthorizationPolicy | Application release lifecycle에 속할 때 |

구현 규칙:

- 동일 security group rule 또는 동일 route destination을 둘 이상의 module/state/Console에서 동시에 관리하지 않습니다.
- 변경 정책은 inline block 대신 독립 resource를 사용해 한 규칙 변경이 다른 규칙의 주소를 흔들지 않게 합니다.
- `for_each` key는 CIDR이나 배열 번호가 아닌 `office_https`, `orders_to_db`, `prod_a_to_inspection` 같은 업무 의미를 사용합니다.
- state 분리는 소유 팀, 승인 권한, lifecycle 중 하나 이상이 다를 때만 수행합니다.
- 정책 PR은 `fmt`, `validate`, 정적 보안 검사, plan, CODEOWNER 승인을 거쳐 `dev -> stg -> prod`로 승격합니다.
- 운영 Console 긴급 변경은 ticket, 작업자, 만료 시간, 원복 조건을 기록하고 다음 영업일에 Terraform 코드와 state를 일치시킵니다.

예시:

```hcl
module "orders_sg" {
  source = "../../modules/security-group"

  name   = "orders-api"
  vpc_id = module.foundation.vpc_id

  ingress_rules = {
    alb_https = {
      description                  = "HTTPS from the application load balancer"
      ip_protocol                  = "tcp"
      from_port                    = 8443
      to_port                      = 8443
      referenced_security_group_id = module.alb_sg.security_group_id
    }
  }
}

module "inspection_routes" {
  source = "../../modules/route-policy"

  route_table_ids = module.foundation.route_table_ids.ap
  routes = {
    private_a_to_inspection = {
      route_table_key       = "ap-northeast-2a"
      destination_cidr_block = "10.0.0.0/8"
      transit_gateway_id    = var.transit_gateway_id
    }
  }
}
```

전체 설계와 migration 절차는 [Terraform Change Management](docs/terraform-change-management.md)에 정리되어 있습니다.

<a id="monitoring-and-alerting"></a>

## 9. Monitoring and Alerting

운영자가 장애, 성능 저하, 비용 이상 징후를 빠르게 인지하고 대응할 수 있도록 로그, 메트릭, 알람, 대시보드를 설계합니다.

관측성 레이어:

| Layer | Purpose | Example |
| --- | --- | --- |
| Metrics | 상태와 성능 수치화 | CPU, memory, latency, error rate |
| Logs | 이벤트와 원인 분석 | application log, VPC Flow Logs, audit log |
| Traces | 요청 흐름 추적 | API request path |
| Alerts | 즉시 대응 필요 상태 감지 | service down, error spike |
| Dashboard | 운영 상태 가시화 | service health, cost trend |

알람 등급:

| Severity | Example | Notification |
| --- | --- | --- |
| Critical | 서비스 중단, DB 연결 불가 | PagerDuty, Slack, Email |
| Warning | CPU, Memory, Latency 임계치 초과 | Slack, Email |
| Info | 배포 완료, 비용 예산 접근 | Slack |

초기 알람 후보:

- ALB 5xx error rate exceeds threshold
- Target response time exceeds threshold
- EC2 CPU utilization exceeds threshold
- RDS CPU or storage threshold exceeded
- Transit Gateway와 중앙 egress data processing cost anomaly
- VPC Flow Logs rejected traffic spike
- Transit Gateway 또는 중앙 egress data transfer anomaly
- EKS node not ready or pod crash loop
- Kubernetes control plane error rate
- Monthly budget usage exceeds 80 percent
- Monthly budget usage exceeds 100 percent

공통 지표의 실제 PromQL과 CloudWatch metric math, 최소 traffic, 지속 시간, 복구 조건은 [Monitoring Metric, Query and Alert Severity Policy](docs/monitoring-alert-policy.md)에서 관리합니다. 기계 판독 가능한 `config/monitoring/alert-policy.example.json`은 현재 배포 완료 알람이 아니라 검토·조정을 위한 초기 기준이며 `python3 scripts/validation/validate-monitoring-alert-policy.py`로 query ID 중복, 임계값 역전과 M/N 형식을 검사합니다.

### EKS 운영 관측성

EKS는 control plane, node/runtime, workload/application 계층을 분리해 수집합니다. control plane logging을 켜는 것만으로 container의 `stdout`/`stderr`, kubelet, container runtime 로그가 자동 수집되는 것은 아닙니다.

| Signal plane | Current implementation | Target retention/pipeline | 운영 목적 |
| --- | --- | --- | --- |
| EKS control plane | 5종 -> 전용 KMS encrypted CloudWatch Logs, dev/stg/prod 90/90/365일 | 중앙 S3에서 source/data class별 장기 archive | 인증/RBAC 변경, API 오류, scheduler/controller 진단 |
| Node and runtime | CloudWatch Observability add-on/Fluent Bit, KMS log groups, 30/90/365일 | collector coverage/drop 검증과 중앙 archive | kubelet, containerd, kernel OOM, disk/network pressure 진단 |
| Workload and application | add-on application log group과 Istio stdout, 30/90/365일 | JSON schema/PII filter와 source-to-archive reconciliation | request/error/latency와 배포 버전 상관 분석 |
| Metrics and state | Prometheus 7/15/30일, Alertmanager route 미구현 | Prometheus HA/local control loop + Mimir 30/90/400일 + OTel custom metric | saturation, restart, pending, eviction, quota, autoscaling, 장기 SLO 탐지 |

운영 규칙:

- production에서는 control plane 5종 로그를 모두 켜고 KMS 암호화와 명시적 retention을 적용합니다.
- application은 구조화 JSON으로 `timestamp`, `level`, `service`, `environment`, `cluster`, `namespace`, `pod`, `container`, `trace_id`, `request_id`, `release`를 남깁니다.
- token, credential, cookie, 주민번호, 전화번호, 메시지 본문은 collector로 보내기 전에 제거하거나 마스킹합니다. Kubernetes `Secret` 값과 API request body가 audit/application log에 섞이지 않는지 샘플링 검사합니다.
- CloudWatch는 즉시 검색과 알람용 hot tier로 사용하고, 장기 감사 자료는 subscription/Firehose를 통해 Log Archive account의 S3로 전달해 Object Lock, lifecycle, Athena query를 적용하는 것이 목표입니다. 중앙 archive는 현재 미구현 production gate입니다.
- log ingestion byte, Logs Insights scanned byte, cardinality, dropped/retried record를 비용·파이프라인 건전성 지표로 함께 감시합니다.
- `CrashLoopBackOff`, `OOMKilled`, pod pending, node `NotReady`, memory/disk/PID pressure, API server 5xx/429, audit deny, HPA max replica 지속, PDB 위반 위험을 환경별로 알람화합니다.
- 중앙 Mimir 장애가 local alert와 autoscaling을 막지 않도록 HPA는 local Metrics Server/Prometheus Adapter, queue workload는 KEDA source-native scaler를 사용합니다.

상세 log matrix, SLO/alert 기준과 장애 runbook은 [EKS Day-2 Operations](docs/eks-operations.md)를 기준으로 하고, Mimir·OpenTelemetry·custom metric은 [Advanced Metrics and Telemetry Platform](docs/observability-platform.md)을 기준으로 합니다.

### 예약 발송 시간대 Nginx/Kakao 알림 서비스 모니터링

예시 서비스 경로는 `Scheduler/Client -> ALB/WAF -> Nginx -> Application -> Queue -> Sender Worker -> Kakao API`입니다. 요청량 증가 자체보다 오류율, 지연, 포화도, queue 적체를 함께 확인합니다.

| Layer | 반드시 볼 항목 | 초기 알람 기준 예시 |
| --- | --- | --- |
| End-to-end | synthetic success, 전체 발송 성공률 | 5분간 성공 없음 또는 발송 성공률 99% 미만 |
| Nginx traffic | RPS, active/reading/writing/waiting connection | 정상 peak의 3배 또는 산정 capacity 70/85% |
| Nginx quality | 499/502/503/504, request/upstream p95/p99 | 최소 100건에서 5xx 2% warning, 5% critical |
| Nginx capacity | accepted-handled delta, listen overflow, process FD ratio | drop 발생 또는 FD 70/85% |
| Host/TCP | SYN_RECV, TIME_WAIT, retransmit, conntrack, ephemeral port | 정상 peak 3배, drop 발생, capacity 70/85% |
| Queue/worker | depth, oldest age, publish/consume, retry, DLQ | oldest age가 발송 SLO 초과 또는 DLQ 1건 이상 |
| Kakao API | latency, 2xx/429/5xx, rejection, quota | 429/5xx 2% 이상 또는 quota 70/90% |

운영 세부 기준:

- `nginx-prometheus-exporter`와 `stub_status`는 connection/request count를 수집합니다.
- status code와 request/upstream latency는 구조화 access log 또는 별도 exporter/OpenTelemetry가 필요합니다.
- node exporter/CloudWatch Agent는 host FD, socket, conntrack, network drop을 수집하고 process-exporter 또는 `procstat`은 Nginx process FD를 수집합니다.
- `worker_connections`에는 client와 upstream connection이 모두 포함되므로 `worker_processes * worker_connections`를 그대로 실사용 capacity로 보지 않습니다.
- 예약 peak 15분 전 dependency health와 capacity를 확인하고 peak 중 배포를 동결하며, 종료 후 queue drain, 누락, 중복 발송을 확인합니다.
- 고객용 Kakao 발송 경로를 운영 Critical 알람의 유일한 채널로 사용하지 않습니다. PagerDuty/전화와 독립 Slack 또는 Email 경로를 병행합니다.

장애 시 빠른 확인 명령:

```bash
curl -s http://127.0.0.1/nginx_status
sudo nginx -T
ss -s
ss -tan state syn-recv
ss -tan state time-wait
cat /proc/$(cat /run/nginx.pid)/limits | grep -i 'open files'
ls /proc/$(cat /run/nginx.pid)/fd | wc -l
sudo journalctl -u nginx --since '15 min ago'
```

`netstat`/`ss`는 상시 모니터링이 아니라 incident 진단 도구입니다. 상세 수집 설계, 개인정보 마스킹, triage 순서는 [Monitoring and Alerting](docs/monitoring.md)에 정리되어 있습니다.

알림 흐름:

1. CloudWatch Alarm 또는 Cost Alert가 이벤트를 발생시킵니다.
2. SNS Topic으로 이벤트를 전달합니다.
3. Critical 이벤트는 PagerDuty, Slack, Email로 전달합니다.
4. Warning 이벤트는 Slack과 Email로 전달합니다.
5. Info 이벤트는 Slack 운영 채널로만 전달합니다.
6. 장애 대응 내용은 Runbook에 기록합니다.

AI Gateway 및 Agent 관측성:

- `Team`, `CostCenter`, `Application`, `AgentId`, `Provider`, `Model`, `Environment`를 공통 dimension으로 사용합니다.
- request, error, throttle, p95 latency, input/output/cached token, estimated cost를 수집합니다.
- tool-call 성공률, 승인 대기 시간, Agent task 성공률, policy deny를 별도 지표로 관리합니다.
- 실시간 metric은 CloudWatch 또는 Grafana, 상세 usage event는 Firehose/S3/Athena로 조회합니다.
- raw prompt와 response는 기본 monitoring log에 저장하지 않습니다.

VPC Flow Logs 기반 네트워크 트러블슈팅:

- rejected traffic을 기준으로 security group, NACL, route table 문제를 분석합니다.
- 특정 source/destination IP, port, protocol 기준으로 연결 실패 원인을 추적합니다.
- Transit Gateway, 중앙 egress, VPC peering 구간의 traffic volume을 확인합니다.
- Athena 또는 CloudWatch Logs Insights로 flow log query를 표준화합니다.
- 장애 대응 runbook에 `REJECT`, `ACCEPT`, `NODATA`, asymmetric routing 점검 절차를 포함합니다.

예시 분석 관점:

| Symptom | Flow Log Check |
| --- | --- |
| 애플리케이션에서 DB 연결 실패 | app subnet to db subnet `REJECT` 여부 확인 |
| 외부 API 호출 실패 | subnet → TGW → 중앙 egress route와 `REJECT` 확인 |
| 특정 포트만 실패 | destination port 기준 NACL/security group 확인 |
| 비용 급증 | TGW, 중앙 egress, cross-AZ와 internet egress traffic volume 확인 |

<a id="operations-strategy"></a>

## 10. Operations Strategy

운영 전략은 비용 절감만이 아니라 장애 복구, 보안 패치, 취약점 대응, OS lifecycle, 패키지 공급망 관리를 포함합니다.

### Tagging Strategy

필수 태그는 비용, 운영, 보안, 자동화 기준으로 나눕니다.

| Tag | Purpose | Example |
| --- | --- | --- |
| `Environment` | 환경 구분 | `dev`, `stg`, `prod` |
| `Owner` | 책임 조직 | `platform-team` |
| `Service` | 서비스 식별 | `cloud-portfolio` |
| `CostCenter` | 비용 배부 | `cloud-platform` |
| `ManagedBy` | 관리 방식 | `terraform` |
| `BackupPolicy` | 백업 정책 연결 | `daily-30d`, `none` |
| `Schedule` | 자동 시작/중지 정책 | `office-hours`, `always-on` |
| `DataClass` | 데이터 등급 | `public`, `internal`, `confidential` |
| `PatchGroup` | 패치 그룹 | `linux-prod`, `linux-stg` |
| `Compliance` | 규정 준수 범위 | `baseline`, `pci`, `internal-audit` |

태그 적용 원칙:

- Terraform provider `default_tags`로 공통 태그를 적용합니다.
- 백업, 스케줄, 비용 알람은 태그 기반으로 자동 적용되도록 설계합니다.
- `prod` 리소스는 `Owner`, `Service`, `CostCenter`, `BackupPolicy` 누락 시 배포를 막는 정책을 검토합니다.

### Backup Strategy

| Target | Frequency | Retention | Recovery Goal |
| --- | --- | --- | --- |
| Production database | Daily plus PITR | 30 days | RPO 15 minutes to 24 hours |
| Production EBS volume | Daily | 14 to 30 days | Service-specific RTO |
| Staging database | Daily | 7 to 14 days | Deployment rollback validation |
| Development database | Optional daily | 3 to 7 days | Low-cost recovery |
| Terraform state | Versioned | Long-term | State recovery and audit |
| Container image | Immutable tag | Release lifecycle | Rollback by image digest |

백업 구현 후보:

- AWS Backup plan
- RDS automated backup and PITR
- EBS snapshot lifecycle policy
- S3 versioning and lifecycle
- Cross-region backup for critical production data
- Backup vault lock for ransomware protection 검토

백업 검증:

- 월 1회 restore drill을 수행합니다.
- `stg`에서 운영 백업 복구 절차를 검증합니다.
- 백업 성공/실패 이벤트는 Slack 또는 Email로 알림을 보냅니다.

### Instance Scheduling Strategy

비운영 환경은 비용 최적화를 위해 업무 시간 기반 스케줄을 적용합니다.

| Environment | Policy | Example Schedule |
| --- | --- | --- |
| `dev` | 업무 시간 외 중지 | 평일 20:00 stop, 08:00 start |
| `stg` | 업무 시간 외 중지 또는 배포 일정 기반 기동 | 평일 21:00 stop, 08:00 start |
| `prod` | 기본 always-on | SLA와 HA 우선 |
| `sandbox` | 야간 및 주말 강제 중지 | 평일 야간, 주말 stop |

스케줄 구현 후보:

- EventBridge Scheduler
- Lambda start/stop automation
- AWS Instance Scheduler
- Auto Scaling scheduled action
- Kubernetes cluster autoscaler and node group scaling

EventBridge 및 Lambda 자동화 전략:

- EventBridge Scheduler로 환경별 start/stop 이벤트를 생성합니다.
- Lambda는 태그 기반으로 대상 EC2, RDS instance, Aurora cluster를 조회합니다.
- `Schedule=office-hours` 리소스만 자동 중지 대상으로 분류합니다.
- `Schedule=always-on`과 `Environment=prod`는 자동 중지 대상에서 제외합니다.
- 실행 결과는 CloudWatch Logs와 SNS로 남기고 실패 시 Slack 또는 Email로 알림을 보냅니다.
- 자동화 Lambda는 최소 권한 IAM role을 사용하고 dry-run 모드를 제공합니다.
- EKS node group은 Terraform desired size와 autoscaler 충돌을 피하기 위해 이 Lambda에서 제외하고 Cluster Autoscaler 또는 Karpenter로 scale-down합니다.

예외 기준:

- 배포 테스트 기간에는 `stg` 스케줄을 임시 해제할 수 있습니다.
- `prod`는 비용 절감 목적의 자동 중지를 기본 정책으로 두지 않습니다.
- batch, analytics, CI runner는 workload별 schedule tag로 별도 관리합니다.

### Patch, CVE, and EOS Management

운영 대상:

- Ubuntu
- Red Hat Enterprise Linux
- Amazon Linux
- Docker runtime
- Container base images
- Language runtimes
- Middleware packages
- OpenSSL, glibc, Java, Python, Node.js 같은 핵심 runtime dependency

CVE 대응 기준:

| Severity | Response Target | Action |
| --- | --- | --- |
| Critical | 7 days or emergency change | emergency patch, image rebuild, service restart |
| High | 14 days | scheduled patch |
| Medium | 30 days | regular maintenance |
| Low | regular cycle | monthly review |

EOS/EOL 관리 기준:

- OS, middleware, database, runtime의 EOL 날짜를 inventory로 관리합니다.
- EOL 6개월 전 migration plan을 작성합니다.
- EOL 3개월 전 `stg` 검증을 완료합니다.
- EOL 1개월 전 `prod` 변경 일정을 확정합니다.
- EOL 이후 리소스는 신규 배포를 차단하는 정책을 검토합니다.

취약점 관리 도구 후보:

- Amazon Inspector
- AWS Systems Manager Patch Manager
- AWS Systems Manager Inventory
- ECR image scanning
- Security Hub
- GuardDuty
- Trivy 또는 Grype 기반 container scan

### OS and Package Management

엔터프라이즈 환경에서는 모든 서버가 인터넷에서 직접 패키지를 받는 구조를 피합니다.

운영 전략:

- 승인된 OS 이미지를 golden AMI로 관리합니다.
- Ubuntu, Red Hat, Amazon Linux는 OS family별 patch group을 분리합니다.
- container workload는 base image를 승인 목록으로 관리합니다.
- Docker image는 digest 기반으로 배포해 재현성을 확보합니다.
- 외부 package repository 접근은 private mirror 또는 artifact repository를 통해 통제합니다.

패키지 관리 서버 후보:

- Private package mirror
- Nexus Repository
- JFrog Artifactory
- AWS CodeArtifact
- Amazon ECR
- Golden AMI pipeline

관리 기준:

- 승인되지 않은 package source 사용을 제한합니다.
- 패키지 업데이트는 `dev`, `stg`, `prod` 순서로 promotion합니다.
- critical package 업데이트는 CVE 대응 SLA와 연결합니다.

### EKS Platform Lifecycle

EKS를 사용하는 경우 Kubernetes control plane, node group, addon, Helm chart, service mesh를 별도 lifecycle로 관리합니다.

상세 운영 기준은 [EKS Day-2 Operations](docs/eks-operations.md)를 source of truth로 사용합니다. Terraform foundation state는 EKS/AWS 리소스를, platform state는 namespace policy와 Helm/Kubernetes 리소스를 관리하며, application repository는 Deployment, Service, HPA, PDB 같은 workload manifest를 소유합니다.

#### Kubernetes QoS와 namespace resource policy

Kubernetes QoS는 임의의 등급 값을 설정하는 기능이 아니라 Pod 내 모든 container의 CPU/memory `requests`와 `limits` 조합으로 `Guaranteed`, `Burstable`, `BestEffort`가 자동 결정되는 메커니즘입니다. QoS는 node pressure eviction에 영향을 주지만 PriorityClass, PDB, replica 수, topology 분산을 대체하지 않습니다.

| Workload class | QoS/priority baseline | Required controls |
| --- | --- | --- |
| Cluster critical | `Guaranteed`, 전용 `platform-critical` PriorityClass | 모든 container와 sidecar의 CPU/memory request=limit, 2개 이상 replica, PDB, AZ/node 분산 |
| Business critical | load test 결과에 따라 `Guaranteed` 또는 `Burstable`, 높은 application priority | request 필수, memory limit 필수, HPA, PDB, topology spread, readiness/startup probe |
| Standard service | `Burstable`, 기본 application priority | request 필수, 합리적 limit, HPA 또는 고정 capacity 근거, disruption 정책 |
| Batch/CI | `Burstable`, 낮은 non-preempting priority | quota, concurrency/queue 한도, interruption 재시도, Spot 허용 여부 명시 |
| Best-effort diagnostic | `BestEffort` 가능 | prod 상시 실행 금지, 시간 제한과 owner 승인, 서비스 SLO 대상에서 제외 |

namespace에는 다음 policy를 함께 적용합니다.

- `LimitRange`: request/limit 누락 시 안전한 기본값을 주고 container별 최소/최대와 request-to-limit ratio를 제한합니다. 기본값은 실제 sizing의 대체물이 아니며 CI에서 명시값을 요구합니다.
- `ResourceQuota`: namespace의 CPU, memory, ephemeral storage, PVC, LoadBalancer, Secret/ConfigMap/Job object 수를 제한합니다. quota 합계가 실제 allocatable capacity를 초과하지 않는지 월별로 검토합니다.
- `PriorityClass`: platform-critical, application-critical, default, batch로 분리하고 high priority 사용 namespace를 제한합니다. Priority와 QoS는 서로 독립적이므로 두 정책을 모두 검증합니다.
- `PodDisruptionBudget`: replica가 있는 workload에 `minAvailable` 또는 `maxUnavailable`을 지정하되 drain을 영구 차단하지 않도록 replica 수와 여유분을 함께 검증합니다. PDB는 node 장애 같은 비자발적 disruption을 막지 못합니다.
- `topologySpreadConstraints`: `topology.kubernetes.io/zone`과 `kubernetes.io/hostname` 기준으로 critical replica를 분산합니다. `DoNotSchedule` 사용 시 AZ/node capacity 부족으로 Pending이 발생하는지도 사전 검증합니다.
- ephemeral storage request/limit와 emptyDir `sizeLimit`을 명시하고, container log 증가가 node disk pressure/eviction으로 이어지지 않도록 log rotation과 collector backpressure를 감시합니다.

#### Autoscaling과 capacity ownership

| Layer | Controller | 운영 원칙 |
| --- | --- | --- |
| Pod replica | HPA/KEDA | CPU·memory 또는 queue/traffic 지표로 scale; request 정확성이 전제 |
| Pod sizing | VPA recommendation | 초기에는 recommendation/audit mode로 사용하고 prod 자동 재시작은 승인 전 금지 |
| Node capacity | Cluster Autoscaler 또는 Karpenter 중 하나 | Terraform은 min/max와 안전 경계를, autoscaler는 runtime desired capacity를 소유 |
| Scheduled/batch | CronJob/KEDA/event source | 동시성, deadline, retry, history limit과 downstream quota를 함께 제한 |

HPA가 max replica에 고정되거나 Pending pod가 지속될 때는 무조건 max를 높이지 않고 request 과다, IP 부족, taint/toleration, AZ/PV affinity, quota, node limit을 순서대로 확인합니다. production node group은 system workload용 on-demand baseline과 application capacity를 분리하고, Spot은 interruption-tolerant workload에만 사용합니다.

현재 Terraform은 managed node group의 `desired_size` drift를 무시해 향후 autoscaler가 runtime capacity를 소유할 경계만 마련했습니다. Cluster Autoscaler/Karpenter, HPA/KEDA, VPA controller 자체는 아직 설치하지 않았으며 production backlog입니다. 반면 환경별 namespace ResourceQuota/LimitRange와 3개 PriorityClass는 platform root에 구현되어 있습니다.

#### EKS backup, restore와 재해 복구

- Terraform/Git/Helm values와 image digest를 desired-state source of truth로 유지합니다.
- AWS Backup의 EKS composite recovery point 또는 승인된 Kubernetes backup 도구로 cluster state와 지원되는 persistent volume을 보호합니다. database consistency가 필요한 workload는 application-native backup/PITR을 별도로 사용합니다.
- ECR image, external database, external secret source, DNS/WAF/IAM 같은 cluster 외부 dependency는 EKS cluster backup에 포함된다고 가정하지 않습니다.
- restore는 새 cluster 또는 격리된 `stg` namespace에서 검증하고, 기존 object를 덮어쓰지 않는 restore 동작, skipped/partial object, CRD 순서, StorageClass/AZ, Pod Identity/IRSA, external secret 재연결을 확인합니다.
- 월간 namespace restore, 분기별 cluster rebuild/restore drill에서 실제 RPO/RTO, data checksum, synthetic transaction, alert 복구를 증적화합니다.

현재 AWS Backup module은 태그 기반 selection과 vault를 제공하지만 EKS service opt-in, composite recovery point 생성, namespace/cluster restore 성공 증적은 아직 없습니다. node root EBS snapshot 성공을 EKS cluster state/PV 복구 성공으로 간주하지 않습니다.

#### EKS release와 변경 gate

버전 관리 원칙:

- EKS control plane version은 AWS 지원 버전 내에서 유지합니다.
- Kubernetes minor version upgrade는 `dev`, `stg`, `prod` 순서로 진행합니다.
- control plane upgrade 후 managed node group 또는 Karpenter node를 순차 교체합니다.
- 운영 업그레이드 전 deprecated API 사용 여부를 점검합니다.
- cluster upgrade 전 backup, rollback, maintenance window를 확정합니다.
- EKS upgrade insight와 audit log로 deprecated API 사용을 확인하고 owner가 없는 deprecated object는 upgrade blocker로 처리합니다.
- control plane은 한 번에 한 minor version만 올리고, add-on/controller 호환성 확인 후 managed node group을 교체합니다.
- 변경 전 PDB, replica, topology, quota 여유, IP와 node headroom을 검사하고 변경 중 API 5xx/429, Pending, restart, DNS/CNI/storage error와 service SLI를 감시합니다.
- rollback 가능 범위를 release note에서 확인하되, Kubernetes object schema나 application data migration은 별도 forward-fix/restore 절차를 준비합니다.

EKS addon 관리 대상:

- VPC CNI
- CoreDNS
- kube-proxy
- EBS CSI Driver
- EFS CSI Driver
- AWS Load Balancer Controller
- Metrics Server
- Cluster Autoscaler 또는 Karpenter
- ExternalDNS
- cert-manager

Addon 운영 원칙:

- AWS managed addon은 Terraform 또는 Helm release로 버전을 명시합니다.
- addon version은 cluster version compatibility를 확인한 뒤 승격합니다.
- addon 변경은 `stg`에서 pod networking, DNS, ingress, storage 동작을 검증한 뒤 `prod`에 적용합니다.
- CNI, CoreDNS, kube-proxy 변경은 장애 영향이 크므로 별도 change window를 둡니다.

Helm 관리 전략:

- Helm chart는 chart version과 values 파일을 git에서 관리합니다.
- 환경별 values는 `dev`, `stg`, `prod`로 분리합니다.
- 배포 전 `helm diff` 또는 plan equivalent 검토를 수행합니다.
- chart repository는 내부 artifact repository 또는 승인된 registry를 사용합니다.
- rollback 가능한 release history를 유지합니다.

Istio 및 service mesh 전략:

- Istio는 ingress, mTLS, traffic shifting, canary release, service-to-service policy가 필요한 경우 적용합니다.
- control plane과 data plane upgrade를 분리해서 관리합니다.
- sidecar injection 범위는 namespace label로 통제합니다.
- mTLS mode는 workload 영향도를 고려해 permissive에서 strict로 단계적 전환합니다.
- ingress gateway, virtual service, destination rule, authorization policy는 git 기반으로 관리합니다.
- mesh metric은 Prometheus와 Grafana dashboard에 연결합니다.

<a id="finops-strategy"></a>

## 11. FinOps Strategy

클라우드 비용을 사후 정산 대상이 아니라 설계, 배포, 운영 단계에서 지속적으로 관리되는 품질 지표로 취급합니다.

필수 태그:

| Tag | Example |
| --- | --- |
| `Environment` | `dev`, `stg`, `prod` |
| `Owner` | `platform-team` |
| `Service` | `cloud-portfolio` |
| `CostCenter` | `cloud-platform` |
| `ManagedBy` | `terraform` |

비용 관리 기준:

| Area | Control |
| --- | --- |
| Tagging | Required tags enforced by Terraform variables |
| Budget | Environment-level AWS Budgets |
| Anomaly | Cost anomaly detection |
| Optimization | Right sizing and unused resource review |
| Reporting | Monthly service and owner cost report |

AI 비용 관리 기준:

- AI Gateway가 provider별 input/output/cached token을 공통 schema로 정규화합니다.
- 비용은 `CostCenter`, `Team`, `Application`, `Environment`, `AgentId`, `Model` 단위로 배부합니다.
- model price는 effective date가 있는 versioned catalog로 관리합니다.
- gateway 추정 비용은 AWS CUR 또는 provider invoice와 일별 대사합니다.
- user sandbox에는 일별 token/concurrency 한도, team에는 월별 USD budget과 RPM/TPM quota를 적용합니다.

리뷰 주기:

- Daily: budget and anomaly alerts
- Weekly: unused resource review
- Monthly: cost report and optimization backlog

초기 최적화 항목:

- 미사용 EBS volume 제거
- 장기간 미사용 Elastic IP 제거
- 낮은 사용률의 EC2 instance right sizing
- TGW와 중앙 egress data processing cost 점검
- RDS storage와 backup retention 점검
- 운영 워크로드에 Savings Plans 적용 검토

RI 및 Savings Plans 전략:

- `prod`에서 24x7로 동작하는 안정적인 baseline workload는 Savings Plans 또는 RI 후보로 분류합니다.
- `dev`와 `stg`는 자동 중지 및 right sizing을 우선 적용하고 RI 구매 대상에서 제외합니다.
- 30일 이상 사용률이 안정적인 EC2, RDS, OpenSearch, ElastiCache를 약정 구매 후보로 검토합니다.
- 약정 구매 전 1개월 usage baseline을 확인합니다.
- Compute Savings Plans는 유연성이 필요한 compute workload에 우선 검토합니다.
- Standard RI는 장기 고정 DB workload처럼 변동성이 낮은 리소스에만 검토합니다.

비용 알람 기준:

- 예산 50 percent: Info
- 예산 80 percent: Warning
- 예산 100 percent: Critical
- 전일 대비 비용 급증: Warning
- TGW, 중앙 egress, data transfer, snapshot 비용 급증: Warning

스케줄 기반 비용 절감:

- `dev`와 `stg` EC2, RDS, EKS node group은 업무 시간 외 중지 또는 scale-down합니다.
- sandbox 리소스는 야간 및 주말 자동 중지를 기본값으로 둡니다.
- idle load balancer, unattached EBS, unused EIP는 주간 리포트로 정리합니다.

<a id="security-and-governance"></a>

## 12. Security and Governance

보안은 나중에 붙이는 기능이 아니라 Terraform 설계 단계에서 기본값으로 적용합니다.

핵심 기준:

- Least privilege IAM
- Role-based access
- Network segmentation
- Encryption at rest
- Encryption in transit
- Centralized audit logging
- Public access restriction
- Policy-as-code 검토
- Corporate IdP MFA와 IAM Identity Center permission set
- AI model/tool allowlist와 prompt data protection
- Agent production direct mutation 금지와 human approval

검토 항목:

- Workload VPC에 public subnet·IGW·NAT가 생성되지 않았는가?
- Security group inbound가 `0.0.0.0/0`로 과도하게 열려 있지 않은가?
- IAM policy에 wildcard action/resource가 불필요하게 포함되어 있지 않은가?
- 로그 보존 기간이 운영 기준에 맞는가?
- 비용 추적 태그가 모든 리소스에 적용되는가?
- 승인되지 않은 OS, container image, package source가 사용되지 않는가?
- EOL/EOS 대상 리소스가 production에 남아 있지 않은가?

구현된 보안 통제:

| Boundary | Implemented Control |
| --- | --- |
| Organization | nested workload OU, deny-leave, audit protection, region deny, tag policy |
| Identity | explicit trust, GitHub OIDC subject allowlist, audit role, MFA break-glass option |
| Data | rotating KMS keys, EBS default encryption, EKS secrets/volume encryption |
| Network | private EKS endpoint, LB/AP/DB/Node/Pod subnet 분리, TGW 중앙 경로, DB route isolation, VPC endpoints |
| Runtime | Access Entry, AL2023, IMDSv2, Pod Identity, strict mTLS |
| Detection | GuardDuty, Security Hub, Inspector, VPC Flow Logs, CloudWatch/SNS alarms |
| Edge | WAF managed rules, rate limit, request logging and sensitive-header redaction |

Production 적용 전 남은 gate:

- Organization CloudTrail, Config aggregator, immutable central log archive는 Security/Log Archive account ID 확정 후 별도 root로 구현합니다.
- SCP는 `Policy-Staging` OU에서 account 단위로 검증하고 break-glass rehearsal 후 확대합니다.
- private EKS endpoint에 접근할 VPN, Direct Connect, SSM 연결 runner 또는 self-hosted runner가 필요합니다.
- Grafana bootstrap password는 Terraform state에서 제거할 수 있도록 Secrets Manager와 External Secrets로 전환합니다.
- WAF는 ingress ARN 생성 후 count 관찰, false positive exclusion 검토, block 승격 순서로 연결합니다.
- central inspection VPC, Transit Gateway, AWS Network Firewall/UTM route는 Network account 정보가 확정된 뒤 구현합니다.
- sandbox AWS account에서 `plan`, `apply`, restore drill, destroy까지 실행해 runtime 증적을 남깁니다.

상세 검토표는 [Terraform Security Review](docs/security-review.md)에 정리되어 있습니다.

<a id="pdf-portfolio"></a>

## 13. PDF 포트폴리오 구성

최종 PDF는 루트 README의 서술 흐름을 기준으로 작성합니다. 구현값만 빠르게 나열하지 않고 `왜 필요한가 → 어떤 경계로 설계했는가 → 무엇을 구현했는가 → 무엇이 남았는가 → 어떤 증거가 있어야 완료인가`를 순서대로 읽을 수 있게 구성합니다.

현재 PDF 목차:

1. 프로젝트 목표
2. 범위와 증거를 읽는 방법
3. 저장소 구조와 권장 탐색 순서
4. Multi-Agent Operating Model
5. Target Cloud Architecture
6. Landing Zone과 서비스 네트워크
7. Terraform Implementation Strategy
8. EKS와 Kubernetes Platform
9. Monitoring and Alerting
10. Operations Strategy
11. FinOps Strategy
12. Security and Governance
13. 현재 구현과 검증 상태
14. 다음 구현 단계
15. Definition of Done과 Production Promotion Gate

PDF에 포함할 핵심 산출물:

- 프로젝트가 답하는 질문과 Current/Defined/Target/Evidence 구분
- 저장소 탐색 순서, Manager와 4개 기능 조직, Agent 역할과 Human-led 승인 경계
- IPAM, TGW, RAM과 서비스 VPC subnet 구성
- Terraform state, 디렉터리와 module 구성
- CloudWatch, Prometheus, Grafana와 주요 알람 기준
- EKS cluster, managed add-on과 환경별 managed node group 수치
- Karpenter, Cluster Autoscaler, HPA/KEDA의 현재 설치 여부
- Istio, ResourceQuota, LimitRange, PriorityClass와 PDB 상태
- IAM, KMS, GuardDuty, Security Hub, Inspector와 WAF 연결 상태
- 5개 서비스의 dev/stg/prod CIDR과 실제 생성 리소스
- OU, SCP, Tag Policy와 account 생성 범위
- backup, patch, scheduler, Budget와 Cost Anomaly 구성
- 현재 로컬 검증의 의미, production 전 잔여 위험과 promotion gate

PDF 원고는 README를 그대로 복제하지 않고 설명 문단으로 맥락을 먼저 제공한 뒤 표와 계층도로 수치, ownership과 구현 여부를 확인하는 독자판으로 관리합니다. 상세 작성 원칙과 목차는 [포트폴리오 PDF 구성](docs/portfolio-outline.md), 실제 본문은 [PDF 원고](docs/portfolio-presentation.md)가 소유합니다. 작성자는 전체 아키텍처와 구성을 정의하며 OpenAI Codex는 코드 분석, 원고 작성, 일관성 확인과 PDF 제작을 보조합니다.

PDF 생성과 검수:

```bash
python3 scripts/pdf/build/build_portfolio_presentation_pdf.py
python3 scripts/pdf/verify/verify_portfolio_pdf.py enterprise-cloud-portfolio.pdf
```

최종 산출물은 최상위 `enterprise-cloud-portfolio.pdf`입니다. 검수 스크립트는 PDF 텍스트 계층, 15개 장의 목차·책갈피, 빈 페이지, 페이지 수와 핵심 경계를 검사하고 시스템 임시 경로에 Poppler 페이지 PNG와 한눈에 보는 이미지를 생성합니다. 현재 PDF는 A4 21페이지 README 기반 독자판입니다.

<a id="current-status"></a>

## 14. 현재 상태

현재 반영된 내용:

- Cloud Platform Manager와 4개 기능 조직을 포함한 11개 Agent 역할·보고선 정의
- Architecture, Governance, CI/CD, Reviewer, Documentation Agent 추가
- Operations Agent 추가
- Agent Runtime 명령 및 production 승인 경계 정의
- Agent business outcome, engineering KPI, measurement/reporting과 scorecard template 정의
- Enterprise AI Gateway와 token/cost dashboard 설계
- Corporate IdP, IAM Identity Center, 폐쇄망 account 접근 설계
- 포트폴리오 문서 목차
- AWS 기반 엔터프라이즈 아키텍처 초안
- 모니터링 및 알람 정책과 Nginx/Kakao peak workload 상세 runbook
- Monitoring metric query 11개, 지속 시간, Warning/Critical, missing-data 정책과 자동 형식 검증 구현
- EKS 로그 lifecycle, QoS, autoscaling, backup/restore, upgrade와 incident runbook 문서화
- 백업, 스케줄링, CVE/EOS, OS/패키지 관리 전략 초안
- FinOps 전략 초안
- Terraform `dev`/`stg`/`prod` 환경 구조
- Terraform `organization` root module 구조
- Terraform `organization`, `scp-policy`, `network`, `iam`, `security`, `observability`, `operations`, `cost` 모듈 구현
- 변경 빈도가 높은 rule/route를 위한 `security-group`, `route-policy` 모듈 구현
- 중첩 OU, SCP/Tag Policy, `Policy-Staging` OU 구현
- Public/IGW/NAT를 제외하고 LB/AP/DB/Node/Pod/TGW/EKS Cluster subnet, DB route 격리, VPC Endpoint를 포함한 network 모듈 구현
- private EKS, AL2023 node group, managed add-on, Pod Identity를 포함한 `eks` 모듈 구현
- EKS control-plane, managed node, VPC CNI Pod 주소를 전용 subnet으로 분리하고 custom networking·prefix delegation·AZ별 ENIConfig 구현
- EKS control-plane 및 Container Insights log group, 환경별 retention, CloudWatch Observability add-on과 전용 KMS 구현
- revision Istio, strict mTLS, Prometheus/Alertmanager/Grafana, namespace quota/LimitRange/PriorityClass를 포함한 `kubernetes-platform` 모듈 구현
- 태그 기반 EC2/RDS EventBridge-Lambda scheduler와 prod 이중 차단 구현
- AWS Backup, Vault Lock, SSM patch baseline, Inspector 구현
- AWS Budgets, Cost Anomaly Detection, SNS 50/80/100 percent 알림 구현
- WAF managed rules, rate limit, logging 모듈 구현
- foundation/platform remote state 분리와 backend 예시 구현
- GitHub Actions와 로컬 검증 script 구현
- Linux 호스트·traffic·socket queue·CPU·memory·FD·disk·systemd·패치, EKS 상태와 CloudWatch Logs 보존 감사를 위한 읽기 전용 운영 스크립트 7개와 전용 CI 구현
- Terraform module 디렉터리 19개 중 18개 구현, `compute`는 향후 runtime을 위한 예약 디렉터리
- `organization` 1개, 공통 환경·platform 6개, Landing Zone 3개, standalone module 3개, 서비스 VPC 15개로 총 28개 validation target 정의
- 최신 로컬 검증에서 `fmt`, 구성도와 서비스 CIDR 중복 검사는 통과했으나 전체 `terraform validate`는 local AWS provider schema handshake에서 중단되어 28/28 통과로 주장하지 않음
- Monitoring Agent request/security/read-only boundary unit test 25개 통과
- `examples/` fixture, `schemas/` machine contract와 `reports/` 월간·장애 보고서 양식·simulation 예시의 역할 분리 및 CI smoke 검증
- 보안 검토와 production 적용 전 residual risk 문서화
- A4 21페이지 README 기반 한국어 포트폴리오 생성과 전체 페이지 시각 검수 완료
- Agent 선택, 요청, workflow, 승인, handoff, session 재개를 포함한 운영자 사용설명서 작성

<a id="next-steps"></a>

## 15. 다음 구현 단계

다음 구현 순서는 아래가 적절합니다.

1. Sandbox AWS organization/account에서 plan, apply, restore, destroy 증적 생성
2. Log Archive/Security account ID를 입력으로 organization CloudTrail과 Config aggregator 구현
3. EKS ingress를 만든 뒤 WAF association과 AWS Load Balancer Controller 권한 구현
4. current Prometheus series/cardinality/cost baseline을 수집하고 dev Mimir/S3/KMS/auth gateway PoC 구현
5. 한 application에 OTel SDK/Collector를 적용하고 metric translation, drop/retry, PII 음성 테스트 수행
6. Prometheus Adapter allowlist와 필요한 queue workload의 KEDA를 dev/stg에서 검증
7. Cluster Autoscaler 또는 Karpenter, workload HPA/PDB/topology와 NetworkPolicy/AuthorizationPolicy 구현
8. `identity-center` root와 module에 permission set, account assignment 추가
9. `ai-gateway` module에 private ingress, runtime, Bedrock VPC endpoint 추가
10. `ai-observability` module에 token metric, usage lake, dashboard 추가
11. Trivy/Checkov 및 OPA 정책 검사를 CI release gate에 추가
12. README와 실제 AWS 실행 결과를 기반으로 PDF를 지속 업데이트

<a id="definition-of-done"></a>

## 16. Definition of Done

이 포트폴리오의 1차 완성 기준은 다음과 같습니다.

- Terraform 구조가 환경별로 분리되어 있다.
- 모듈은 재사용 가능하도록 입력값과 출력값이 명확하다.
- 보안 기준은 명시적으로 문서화되어 있다.
- 비용 추적을 위한 태그 정책이 정의되어 있다.
- 모니터링 및 알람 흐름이 설명되어 있다.
- Prometheus local control loop와 Mimir 장기 metric 저장의 tenant, retention, HA와 장애 격리 기준이 설명되어 있다.
- OpenTelemetry와 custom metric catalog, cardinality/PII guardrail, Prometheus Adapter/KEDA 경계가 설명되어 있다.
- 백업, 스케줄링, 패치, CVE/EOS, OS/패키지 관리 전략이 설명되어 있다.
- 에이전트별 책임과 협업 흐름이 설명되어 있다.
- Agent별 command, tool permission, token/cost quota, production approval 경계가 설명되어 있다.
- Agent 성과가 business outcome, engineering KPI와 evidence로 연결되어 있다.
- AI Gateway와 token 사용량/비용 dashboard 구현 구조가 설명되어 있다.
- Corporate IdP, IAM Identity Center, permission set, 폐쇄망 Console/CLI 접근이 설명되어 있다.
- PDF 포트폴리오로 변환 가능한 문서 구조가 있다.
