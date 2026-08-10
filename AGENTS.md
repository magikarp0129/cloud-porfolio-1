# Multi-Agent Operating Model

이 문서는 Terraform 기반 엔터프라이즈 클라우드 구축 포트폴리오에서 사용할 에이전트 역할, 책임, 산출물, 협업 규칙을 정의합니다.

## Goal

엔터프라이즈 클라우드 환경을 구축하기 위해 여러 전문 에이전트가 역할을 나누어 설계, 구현, 검토, 비용 최적화, 모니터링 운영을 수행합니다.

초기 운영 모델은 Agent에게 production을 위임하는 구조가 아니라 **Human-led, Agent-assisted** 방식입니다. Agent는 승인된 정보 조회, 문서·patch·plan·review artifact 작성과 검증을 지원하고, 운영자가 근거를 확인해 최종 판단합니다.

## Current Implementation Boundary

| 영역 | 현재 저장소에서 확인 가능한 내용 | 아직 목표 단계인 내용 |
| --- | --- | --- |
| 역할과 요청 | Manager 1개와 전문 역할 10개, 역할별 request template, operator guide와 adoption scenario | 사내 portal과 ChatOps 통합 |
| 실행 Runtime | Monitoring Agent read-only evidence collector, 고정 query catalog, redaction, report/audit 생성 | 중앙 AI Gateway, Tool Broker, model router와 live connector 배포 |
| Monitoring 정책 | CPU·memory·disk·EKS·서비스 품질 11개 alert policy, Prometheus query catalog 10개 준비 | Prometheus source 활성화, rule 배포, 자동 severity evaluator와 on-call route |
| 검증 | Agent 계약·보안·Terraform boundary 로컬 시험 25개 | live incident, IAM policy simulation, 운영 KPI baseline/actual |
| 변경 실행 | branch/patch/plan/review 계약과 protected CI/CD 경계 | Agent의 production 직접 변경은 의도적으로 지원하지 않음 |

`Current`, `Defined`, `Target`, `Evidence`를 구분합니다. 코드나 문서가 존재하는 것, 로컬 시험이 통과한 것, 실제 AWS에 배포되어 운영 증적이 있는 것은 서로 다른 완료 단계입니다.

## Organization and Reporting Lines

Agent 조직은 사람의 책임을 대체하지 않습니다. **Cloud Platform Owner가 최종 accountable human**이고, Cloud Platform Manager Agent는 요청 접수, 업무 분해, 담당 조직 배정, handoff와 상태 통합을 담당하는 workflow manager입니다.

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

보고선과 승인선은 다릅니다.

- Manager Agent는 우선순위, dependency, 담당 Agent와 완료 조건을 정리하지만 domain 결론을 임의로 덮어쓰지 않습니다.
- Security Agent는 보안 위험에 대한 stop/escalation 권한을 가지며 Security Owner에게 직접 보고할 수 있습니다.
- Reviewer Agent는 Manager와 산출 Agent로부터 독립적으로 finding을 작성하고 unresolved finding을 사람 승인자에게 직접 전달합니다.
- Manager Agent, Domain Lead와 Reviewer를 포함한 어떤 Agent도 자신의 결과를 최종 승인하거나 production 변경을 실행할 수 없습니다.

## Agents

| Agent | Primary Responsibility | Main Outputs |
| --- | --- | --- |
| Cloud Platform Manager Agent | 요청 triage, 업무 분해, 조직 배정, dependency·handoff·상태 통합 | work breakdown, RACI, routing plan, consolidated status, escalation packet |
| Architecture Agent | 요구사항, 전체 아키텍처, module boundary 설계 | architecture decision, target architecture |
| Terraform Agent | Terraform 코드 작성, 모듈화, root/state와 환경 분리 | `terraform/modules`, `terraform/organization`, `terraform/landing-zone`, `terraform/services`, `terraform/environments` |
| Governance Agent | AWS Organizations, OU, SCP, 정책 준수, 변경 승인 | governance model, SCP catalog, compliance checklist |
| Security Agent | IAM, 네트워크 보안, SCP, 정책, 암호화 기준 | security baseline, IAM policy, guardrail |
| Monitoring Agent | 로그, 메트릭, 알람, 대시보드와 장애 증적 설계 | monitoring architecture, alert policy, incident report |
| Operations Agent | 백업, 스케줄, 패치, CVE/EOS, OS lifecycle와 정기 운영 보고 | backup policy, patch policy, operations runbook, monthly platform report |
| FinOps Agent | 비용 태깅, 예산, 사용량 분석, 절감안 | cost policy, budget, optimization report |
| CI/CD Agent | Terraform 검증, plan 리뷰, 배포 자동화 | pipeline, validation workflow, deployment approval |
| Reviewer Agent | 코드 리뷰, 보안 리뷰, 운영 리스크 점검 | review report, improvement backlog |
| Documentation Agent | README, docs, 운영 보고서 양식과 PDF 포트폴리오 문서화 | README, report template/example, PDF outline, portfolio narrative |

## Collaboration Flow

1. Cloud Platform Manager Agent가 요청을 접수하고 scope, risk, dependency와 필요한 전문 조직을 식별합니다.
2. Architecture Agent가 target architecture와 module boundary를 정의하고 Governance, Security, FinOps Agent가 전략 제약을 병렬 검토합니다.
3. Terraform Agent가 organization, Landing Zone, service VPC, environment/platform root와 reusable module 구조를 작성합니다.
4. CI/CD Agent가 검증, plan artifact와 environment promotion gate를 구성합니다.
5. Operations Agent가 backup, schedule, patch, CVE/EOS와 lifecycle 기준을 정의하고 Monitoring Agent가 signal, alert와 post-change evidence를 연결합니다.
6. Security Agent와 Governance Agent가 구현 결과의 guardrail, identity와 정책 준수를 다시 확인합니다.
7. Reviewer Agent가 전체 산출물을 독립적으로 검토하고 unresolved finding을 사람 승인자에게 보고합니다.
8. Documentation Agent가 decision, runbook, README와 PDF를 갱신합니다.
9. Cloud Platform Manager Agent가 완료 조건, handoff, blocker와 evidence를 하나의 상태 보고로 통합합니다.
10. Cloud Platform Owner 또는 designated approver가 최종 판단하고 protected CI/CD만 승인된 변경을 실행합니다.

## Runtime Execution Model

운영자 요청 방법, 업무별 실행 순서, 승인 matrix, handoff, session 재개 절차는 `agents/operator-guide.md`를 기준으로 합니다.

초기 도입은 운영자가 `agents/request-templates/`의 역할별 양식으로 질문하고 Agent의 근거와 제안을 검증하는 Human-led, Agent-assisted 방식입니다. read-only advisory, artifact drafting, supervised workflow, bounded delegation으로 이어지는 업무별 성숙도와 승격 조건은 `agents/adoption-scenarios.md`를 기준으로 합니다. 성숙도는 Agent 전체가 아니라 use case와 environment 조합별로 관리합니다.

각 Agent는 별도 AWS 관리자가 아니라 중앙 AI Gateway와 Agent Runtime에 등록된 역할별 실행 profile입니다. 사용자는 internal portal, `agentctl` CLI, pull request command 또는 승인된 CI/CD API를 통해 Agent를 명령합니다.

표준 요청에는 최소한 다음 정보가 포함되어야 합니다.

- `agent_id`
- `task`
- `repository`
- `environment`
- `mode` (`read`, `draft`, `plan`, `review`)
- `change_ticket`
- `data_classification`
- `max_cost_usd`

운영 원칙:

- AI Gateway가 Corporate IdP 또는 workload identity를 검증하고 Agent별 model, tool, token quota를 적용합니다.
- Manager Agent는 요청을 분류하고 조정하지만 다른 Agent 권한을 상속하거나 사람 승인을 대행하지 않습니다.
- Agent는 실행 시점에만 범위가 제한된 short-lived credential을 받습니다.
- 코드와 정책 변경은 branch, patch 또는 pull request로 제출합니다.
- Terraform Agent를 포함한 모든 Agent는 `prod`에서 직접 `apply`하거나 AWS API를 변경하지 않습니다.
- 실제 배포는 plan artifact, ticket, designated approver를 검증하는 protected CI/CD가 수행합니다.
- model 호출, tool call, 승인, 결과 artifact는 `request_id`와 `trace_id`로 연결해 감사합니다.

상세 구현은 `docs/ai-platform.md`와 `docs/identity-access.md`를 기준으로 합니다. 역할 목록과 템플릿은 `agents/README.md`, 전체 문서의 canonical scope는 `docs/README.md`, Terraform root/state/module 설명은 `terraform/README.md`에서 관리합니다. Monitoring metric query와 Warning/Critical 기준은 `docs/monitoring-alert-policy.md`가 소유합니다.

## Terraform Agent Boundary

| 대상 | Agent가 만들 수 있는 산출물 | 실제 실행 책임 |
| --- | --- | --- |
| Module과 root code | branch patch, 입력·출력 설명, 영향 분석 | 사람 review 후 merge |
| 검증 | `fmt`, 정적 검사, `validate`, diagram/CIDR 검사 결과 | CI와 Reviewer가 결과 확인 |
| Plan | 환경·ticket·provider lock이 고정된 plan artifact와 요약 | designated approver가 plan hash 승인 |
| Apply | Agent mode에 포함하지 않음 | protected CI/CD deployment role |
| 긴급 변경 | 원복안, import/code 반영안, 사후 점검 초안 | Incident Commander와 운영자가 승인·실행 |

Terraform Agent는 하나의 resource, route destination, security-group rule 또는 Kubernetes object가 두 state에서 동시에 관리되지 않는지 확인합니다. root/state ownership과 apply order는 `terraform/README.md`, 변경 승인과 rollback은 `docs/terraform-change-management.md`를 따릅니다.

## Artifact and Documentation Ownership

| 산출물 | Canonical owner |
| --- | --- |
| 역할·공통 실행 경계 | `AGENTS.md` |
| 운영자 요청·승인·handoff | `agents/operator-guide.md` |
| 역할별 질문 template | `agents/request-templates/` |
| Architecture와 운영 기준 | `docs/README.md`에서 지정한 domain 문서 |
| Terraform root/module/state 설명 | `terraform/README.md`와 각 module README |
| 보고 종류·주기·보존·승인 기준 | `docs/agent-value/measurement-reporting.md` |
| 월간·장애 보고서 양식과 공개 가능한 예시 | `reports/` |
| Agent runtime machine contract | `schemas/` |
| 테스트용 sanitized request/evidence fixture | `examples/` |
| 현재 포트폴리오 PDF 본문 | `docs/portfolio-presentation.md` |

Documentation Agent는 같은 표를 여러 문서에 복사하지 않고 canonical 문서를 링크합니다. 코드 값이 바뀌면 root README, 관련 module README, diagram과 PDF 원고에서 해당 값을 함께 검색해 갱신합니다.

## Reporting and Evidence Boundary

- `examples/`는 CI와 로컬 시험이 실행하는 synthetic fixture이며 운영 증적이 아닙니다.
- `schemas/`는 Portal/Gateway와 runtime/downstream 사이의 machine-readable 계약입니다.
- `reports/templates/`는 발행 양식, `reports/examples/`는 사람이 읽는 sanitized simulation 예시입니다.
- 실제 raw log, customer data, credential, prompt/tool trace와 승인 원본은 Git에 저장하지 않고 승인된 artifact/ticket store에서 관리합니다.
- 보고서 값이 없으면 추정하지 않고 `not_available`과 사유를 기록합니다.
- `simulation`, `partial`, `blocked`는 production KPI 성공이나 운영 완료로 합산하지 않습니다.
- 실제 보고서는 `request_id`, `trace_id`, ticket, UTC window, source version, evidence reference와 accountable human sign-off를 연결합니다.

## Runtime Control Ownership

| Control | Responsible Agent |
| --- | --- |
| Request intake, work breakdown, team routing, dependency와 handoff status | Cloud Platform Manager Agent |
| Agent profile, tool boundary, target architecture | Architecture Agent |
| Model allowlist, account/OU policy, approval rule | Governance Agent |
| Identity validation, data classification, secret/PII control | Security Agent |
| Request, token, latency, error, tool-call telemetry | Monitoring Agent |
| Token quota, model cost, budget, invoice reconciliation | FinOps Agent |
| Protected deployment and environment approval gate | CI/CD Agent |
| Runtime risk and output quality review | Reviewer Agent |

## Definition of Done

다음은 **저장소 산출물의 완료 기준**입니다. 실제 production 완료를 주장하려면 이어지는 Production Promotion Gate도 별도로 충족해야 합니다.

- Terraform 구조가 환경별로 분리되어 있다.
- 모듈은 재사용 가능하도록 입력값과 출력값이 명확하다.
- AWS Organizations 및 SCP 기반 guardrail 구조가 있다.
- Governance, Security, FinOps, Monitoring 책임이 분리되어 있다.
- 보안 기준은 명시적으로 문서화되어 있다.
- 비용 추적을 위한 태그 정책이 정의되어 있다.
- 모니터링 및 알람 흐름이 설명되어 있다.
- 백업, 스케줄링, 패치, CVE/EOS 관리 기준이 설명되어 있다.
- Linux, EKS, AWS 운영 상태를 수집하는 읽기 전용 스크립트와 자동 검증이 있다.
- EKS control plane, node/runtime, workload 로그의 수집·보존·중앙 archive 기준이 정의되어 있다.
- Prometheus local 수집과 Mimir 장기 저장의 tenant, retention, HA, 장애 격리 기준이 정의되어 있다.
- OpenTelemetry 수집 표준과 custom metric catalog, cardinality/PII, Adapter/KEDA 경계가 정의되어 있다.
- EKS QoS, namespace quota, PriorityClass, PDB/topology, autoscaling ownership이 정의되어 있다.
- EKS backup/restore drill, upgrade gate, incident runbook과 production readiness 기준이 설명되어 있다.
- Agent command, tool permission, production approval 경계가 정의되어 있다.
- Manager, Domain Lead, independent Reviewer와 accountable human의 보고·승인선이 구분되어 있다.
- Agent capability가 business outcome, engineering KPI, evidence와 accountable validation으로 연결되어 있다.
- examples, schemas, runtime contract와 report template/example의 역할이 분리되고 자동 검증된다.
- 월간 플랫폼 보고서와 장애 보고서 양식이 사실·가설·gap·실행·승인·evidence를 분리한다.
- AI Gateway의 인증, model routing, token quota, audit 기준이 정의되어 있다.
- Corporate IdP, IAM Identity Center, permission set 기반 account 접근 흐름이 정의되어 있다.
- PDF 포트폴리오로 변환 가능한 문서 구조가 있다.

## Production Promotion Gate

- 실제 계정과 리전에 대한 승인된 `terraform plan`과 plan hash가 있다.
- 적용 identity, ticket, 승인자, maintenance window와 rollback owner가 연결되어 있다.
- 배포 후 health, log, metric, backup과 비용 검증 증적이 있다.
- EKS restore, upgrade, drain/PDB와 autoscaling은 격리 환경 rehearsal 결과가 있다.
- Monitoring query와 Warning/Critical rule은 synthetic alarm과 missing-data 시험을 통과했다.
- Agent 결과는 원본 query/plan과 표본 대조되었고 운영자 수정·반려 이력이 남아 있다.
- `Target` 또는 fixture 결과를 실제 배포·절감·MTTR 성과로 표현하지 않는다.
