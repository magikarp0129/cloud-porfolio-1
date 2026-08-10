# Multi-Agent Operator Guide

## 1. Purpose

이 문서는 플랫폼 운영자, SRE, 보안 담당자, FinOps 담당자가 전문 Agent를 안전하고 일관되게 사용하는 방법을 정의합니다.

Agent는 운영자를 대신하는 AWS 관리자가 아닙니다. Agent는 정보를 분석하고, 변경안을 작성하고, Terraform plan 또는 review artifact를 만드는 역할을 담당합니다. 실제 cloud 변경은 ticket, 사람 승인, protected CI/CD를 통해서만 수행합니다.

현재 저장소에는 Monitoring Agent용 read-only incident evidence collector와 로컬 `agentctl` MVP가 구현되어 있습니다. 실제 AI Gateway, internal portal, Tool Broker와 model runtime은 아직 구현되지 않았습니다. 로컬 MVP의 사용 방법과 보안 경계는 [Read-Only Agent Incident Triage](../docs/agent-incident-triage.md)를 따르며, 이 문서의 operating model과 command contract는 모든 command channel에 공통 적용합니다.

Cloud Platform Manager Agent는 여러 전문 영역이 필요한 요청을 분류하고 handoff를 조정하는 문서화된 역할입니다. 현재 실행 가능한 orchestration runtime은 아니며, 최종 책임과 승인은 Cloud Platform Owner 또는 designated approver에게 있습니다.

초기 도입은 **Human-led, Agent-assisted**가 기본입니다. 운영자는 [역할별 요청 템플릿](request-templates/README.md)으로 질문하고 Agent는 근거, 선택지, 초안과 검증 항목을 제공합니다. 운영 권한은 업무별 증적과 통제 수준이 검증된 이후에만 단계적으로 확대하며, Agent 전체에 일괄 부여하지 않습니다. 단계별 기준과 실제 시나리오는 [Human-Led Agent Adoption Scenarios](adoption-scenarios.md)를 따릅니다.

## 2. Core Rules

1. Agent에게 secret, credential, access key, customer raw data를 입력하지 않습니다.
2. Agent는 `prod`에서 직접 `apply`, restart, stop, delete, failover를 수행하지 않습니다.
3. 중요한 결정과 작업 상태는 대화 기억이 아니라 ticket, pull request, repository 문서, plan artifact에 저장합니다.
4. 변경 요청과 장애 요청을 혼합하지 않습니다. 긴급 복구와 영구 수정은 별도 ticket과 artifact로 관리합니다.
5. Agent 결과는 제안이며, 실행 전 담당자와 Reviewer의 검증이 필요합니다.
6. 권한 성숙도는 Agent 이름이 아니라 use case와 environment 조합별로 관리합니다.
7. 요청 템플릿은 범위를 구조화하는 intake이며 접근 권한, 승인 또는 실행 명령이 아닙니다.
8. Manager Agent는 다른 Agent의 전문 판단, Security/Reviewer finding 또는 사람 승인을 덮어쓰지 않습니다.

## 3. Operator Prerequisites

운영자는 Agent 요청 전에 다음 조건을 확인합니다.

- Corporate IdP와 MFA 인증 완료
- 대상 AWS account와 environment 확인
- repository와 작업 branch 확인
- 변경 또는 incident ticket 발급
- 데이터 등급 확인
- 요청할 Agent와 mode 결정
- 예상 작업 시간과 최대 비용 결정
- `prod` 작업이면 designated approver와 rollback owner 지정

장기 IAM access key는 사용하지 않습니다. AWS 접근이 필요한 검증은 IAM Identity Center 또는 CI/CD OIDC의 short-lived credential을 사용합니다.

<a id="selecting-and-requesting-agent"></a>

## 4. Selecting and Requesting an Agent

### Quick Decision Tree

```text
요청이 두 개 이상의 전문 영역에 걸치는가?
├── 예 또는 담당자가 불명확함
│   └── Cloud Platform Manager Agent에 요청
│       └── work breakdown과 routing plan을 사람이 확인
│           └── 각 Domain Agent에 별도 요청 생성
└── 아니요
    └── 아래 선택표에서 전문 Agent 하나를 primary로 지정
        └── 결과를 Reviewer와 담당 human이 검증
```

현재 Manager orchestration runtime은 구현되지 않았습니다. 따라서 Manager 문서가 하위 Agent를 자동 호출한다고 가정하지 않습니다. 운영자 또는 향후 Portal이 승인된 routing plan을 확인한 뒤 각 Agent 요청과 `request_id` 연결을 생성합니다.

### Request in Six Steps

1. 요청을 한 문장으로 정의하고 ticket, environment와 완료 조건을 준비합니다.
2. cross-domain이면 [`platform-manager.yaml`](request-templates/platform-manager.yaml), 단일 domain이면 [역할별 template](request-templates/README.md)을 선택합니다.
3. `mode`, in/out scope, 금지 작업, source revision, 최대 비용과 timeout을 채웁니다.
4. Agent에게 facts, unknowns, risks, option, recommendation, validation과 handoff를 포함해 달라고 요청합니다.
5. 결과의 원본 source, 변경 파일, validation, 비용·보안 영향과 blocker를 운영자가 확인합니다.
6. 후속 Agent가 필요하면 새 요청을 만들고 handoff artifact를 첨부합니다. production 실행은 별도 사람 승인과 protected CI/CD로만 진행합니다.

### Cross-Domain Manager Request Example

```text
[Agent]
Cloud Platform Manager Agent

[Objective]
prod 서비스 VPC에 신규 EKS workload를 수용하기 위한 변경 업무를 조직별로 나눠 주세요.

[Scope]
- Repository: cloud-portfolio
- Environment: prod
- Ticket: CHG-2026-0102
- Mode: draft
- Source revision: main@<commit>

[Constraints]
- cloud 변경과 terraform apply 금지
- 기존 CIDR 변경 금지
- Security와 Reviewer의 독립 검토 경로 유지
- 예상 비용과 rollback owner가 없으면 blocker 처리

[Expected Output]
- workstream과 Domain Lead
- Agent 실행 순서와 dependency
- Agent별 input, success criteria와 handoff artifact
- human decision, approval gate와 stop condition
```

Manager 결과를 확인한 운영자는 Architecture, Terraform, Security, Operations 등 필요한 Agent에 별도 요청을 만듭니다. Manager의 `ready_for_approval`은 요청 준비 상태이며 승인 자체가 아닙니다.

### Direct Domain Request Example

```text
[Agent]
Monitoring Agent

[Objective]
INC-2026-0142의 prod API 5xx 증가 원인을 read-only로 분석해 주세요.

[Scope]
- Environment: prod
- Service: commerce-api
- Time window: 2026-08-10T01:00:00Z/2026-08-10T03:00:00Z
- Mode: read

[Constraints]
- restart, scale, alarm suppression과 설정 변경 금지
- 허용된 query catalog만 사용
- 사실, 가설과 누락 증거를 분리

[Expected Output]
- timestamp와 source가 있는 facts
- 가능한 원인과 반증 query
- Operations Agent에 전달할 handoff artifact
```

### Organization and Reporting Model

```text
Cloud Platform Owner / Designated Approver (Human)
└── Cloud Platform Manager Agent
    ├── Strategy, Architecture and Governance
    │   └── Architecture Agent (Domain Lead)
    │       ├── Governance Agent
    │       ├── Security Agent (independent escalation)
    │       └── FinOps Agent
    ├── Platform Engineering and Delivery
    │   └── Terraform Agent (Domain Lead)
    │       └── CI/CD Agent
    ├── Reliability and Operations
    │   └── Operations Agent (Domain Lead)
    │       └── Monitoring Agent
    └── Assurance and Knowledge
        └── Reviewer Agent (Independent Assurance Lead)
            └── Documentation Agent
```

Manager Agent는 cross-domain 요청의 work breakdown과 routing을 담당합니다. 요청이 한 영역에 명확히 속하면 해당 전문 Agent를 바로 primary로 선택합니다. Security와 Reviewer는 독립 finding을 Manager가 아닌 accountable human에게 직접 escalation할 수 있습니다.

| Operator need | Primary Agent | Supporting Agent | Expected output |
| --- | --- | --- | --- |
| 여러 조직이 필요한 요청 또는 owner가 불명확한 요청 | Cloud Platform Manager | Domain Leads, Reviewer | work breakdown, RACI, routing and escalation plan |
| 신규 Landing Zone 또는 module boundary | Architecture | Governance, Security | ADR, architecture proposal |
| Terraform 코드 작성 또는 수정 | Terraform | Security, Reviewer | patch, validation, plan summary |
| OU, SCP, tag policy 변경 | Governance | Security, Reviewer | policy proposal, rollout plan |
| IAM, KMS, network security 검토 | Security | Governance, Terraform | findings, least-privilege patch |
| 장애 원인 분석과 알람 검토 | Monitoring | Operations, Security | timeline, query result, hypothesis |
| 백업, 복구, patch, instance schedule | Operations | Monitoring, Security | runbook, change proposal |
| 비용 급증, budget, rightsizing | FinOps | Operations, Terraform | cost analysis, optimization backlog |
| pipeline, plan, environment promotion | CI/CD | Terraform, Reviewer | workflow patch, gate result |
| 독립적인 위험 및 품질 검토 | Reviewer | Relevant domain Agent | review findings, release decision |
| README, runbook, PDF 업데이트 | Documentation | All producing Agents | documentation patch |

한 요청에서 primary Agent는 하나만 지정합니다. Manager가 primary인 경우에도 각 workstream에는 하나의 domain primary를 별도로 지정합니다. 다른 전문 영역이 필요하면 primary Agent가 handoff artifact를 만들고 supporting Agent가 독립적으로 검토합니다.

## 5. Request Modes

| Mode | Agent may do | Agent must not do |
| --- | --- | --- |
| `read` | repository, approved inventory, metrics, logs 조회와 요약 | 파일 및 cloud 변경 |
| `draft` | 문서, 코드 patch, runbook 초안 작성 | cloud API 변경, merge, deploy |
| `plan` | fmt, validate, plan, 영향 분석, rollback 제안 | apply, restart, delete, purchase |
| `review` | 코드, plan, policy, evidence 독립 검토 | 원안 자동 수정 또는 승인 대행 |

`apply`는 Agent mode가 아닙니다. 적용은 protected CI/CD의 별도 deployment stage이며 사람이 승인합니다.

## 6. Environment Policy

| Environment | Read | Draft | Plan | Deployment rule |
| --- | --- | --- | --- | --- |
| `dev` | 허용 | 허용 | 허용 | CI/CD 실행, service owner 승인 |
| `stg` | 허용 | 허용 | 허용 | CI/CD 실행, 검증 결과와 rollback 확인 |
| `prod` | 허용 | 허용 | 허용 | ticket, plan hash, 2인 review, environment approval |
| Organization management | 제한적 허용 | 허용 | 별도 sandbox/Policy-Staging 검증 | management account 직접 변경 금지 |

`prod`와 organization 변경은 Agent가 생성한 command를 운영자가 터미널에서 바로 실행하는 방식으로 처리하지 않습니다.

## 7. Standard Request Contract

모든 요청은 다음 값을 포함합니다.

역할별 질문 예시는 [request-templates](request-templates/README.md)에 있습니다. 해당 YAML은 운영자 intake이므로 runtime schema가 있는 channel에는 gateway/adapter가 검증된 payload로 변환해야 합니다.

```yaml
agent_id: terraform
task: "prod VPC에 SSM interface endpoint 추가"
repository: "cloud-portfolio"
environment: prod
mode: plan
change_ticket: "CHG-2026-0081"
data_classification: internal
max_cost_usd: 2.00
timeout_minutes: 30
requester_team: platform
success_criteria:
  - "private subnet에서 SSM 연결 가능"
  - "public EKS endpoint를 활성화하지 않음"
constraints:
  - "기존 CIDR 변경 금지"
  - "prod 직접 apply 금지"
evidence:
  - "CloudWatch incident INC-2026-0142"
rollback_owner: "platform-oncall"
```

AI Gateway는 `user_id`, role, account entitlement, approval 여부를 사용자 입력에서 신뢰하지 않고 인증 token과 server-side policy에서 주입해야 합니다.

## 8. Standard Operator Prompt

자연어 채널을 사용하는 경우 다음 형식을 사용합니다.

```text
[Agent]
Terraform Agent

[Objective]
stg EKS add-on upgrade 변경안을 작성하고 영향도를 분석해 주세요.

[Scope]
- Repository: cloud-portfolio
- Environment: stg
- Ticket: CHG-2026-0082
- Mode: plan

[Constraints]
- apply 금지
- Kubernetes minor version 변경 금지
- 현재 VPC CNI, CoreDNS, kube-proxy 호환성 확인
- 문제가 있으면 변경하지 말고 blocker로 보고

[Expected Output]
- 변경 파일
- terraform fmt/validate 결과
- plan 영향 요약
- 위험과 rollback 절차
- prod promotion 전 검증 항목
```

"알아서 처리", "운영에 적용", "문제 없게 변경"처럼 범위와 성공 기준이 없는 요청은 사용하지 않습니다.

## 9. Controlled Execution Flow

1. 운영자가 ticket, environment, data classification, success criteria를 준비합니다.
2. 단일 domain이면 전문 Agent를, cross-domain이면 Cloud Platform Manager Agent를 primary로 선택합니다.
3. Manager Agent가 필요한 경우 workstream, Domain Lead, dependency, review gate와 human owner를 지정합니다.
4. AI Gateway가 identity, entitlement, model/tool allowlist, quota를 검증합니다.
5. 각 Agent가 가정, 조회 근거, 변경 범위와 blocker를 먼저 기록합니다.
6. 변경이 필요하면 branch 또는 patch를 만들고 검증 결과를 첨부합니다.
7. Security/Governance 등 supporting Agent가 전문 영역을 검토합니다.
8. Reviewer Agent가 독립적으로 위험, 누락 테스트, rollback 가능성을 검토합니다.
9. CI/CD Agent가 fmt, validate, policy scan, plan artifact를 생성합니다.
10. Manager Agent가 cross-domain 결과의 완료 여부, handoff와 unresolved blocker를 통합합니다.
11. 운영자와 designated approver가 ticket, plan hash, 비용 변화, rollback을 확인합니다.
12. Protected CI/CD가 승인된 environment에 적용합니다.
13. Monitoring Agent가 post-deployment metric과 alarm을 확인합니다.
14. Documentation Agent가 README, runbook, decision log를 갱신합니다.

## 10. Workflow: Infrastructure Change

적용 대상: Terraform module, VPC, IAM, EKS, observability, backup, budget 변경

### Before the request

- 변경 목적과 business impact를 ticket에 작성합니다.
- 대상 state가 organization, foundation, platform 중 어디인지 확인합니다.
- 예상 resource create/update/destroy를 기록합니다.
- rollback이 state rollback인지 forward fix인지 결정합니다.

### Agent sequence

```text
Manager routing -> Architecture/Governance -> Terraform -> Security -> Reviewer
-> Manager status -> Human approval -> CI/CD execution -> Monitoring
```

### Required evidence

- 변경된 파일 목록
- `terraform fmt -check -recursive`
- 대상 root의 `terraform validate`
- plan summary와 create/change/destroy 수
- IAM, network, KMS, public exposure 변화
- 월간 비용 추정 변화
- rollback 또는 forward-fix 절차
- post-deployment 확인 metric

### Stop conditions

- 예상하지 않은 destroy 또는 replace
- state backend 또는 provider 변경
- public endpoint, `0.0.0.0/0`, wildcard IAM 추가
- KMS, audit log, GuardDuty, Security Hub 약화
- plan과 ticket scope 불일치

## 11. Workflow: Incident Response

Agent는 incident commander가 아니며 사람의 의사 결정을 대체하지 않습니다.

### Agent sequence

```text
Human Incident Commander -> Manager coordination -> Monitoring -> Operations
-> Security if suspected -> Terraform permanent fix -> Reviewer
```

### Operating procedure

1. Incident commander가 incident ID, severity, affected service, start time을 선언합니다.
2. Monitoring Agent에는 read mode로 metric, log, recent deployment, Flow Logs 분석을 요청합니다.
3. Operations Agent는 가설별 확인 절차와 안전한 복구 후보를 작성합니다.
4. 보안 침해 가능성이 있으면 Security Agent가 evidence preservation과 containment를 검토합니다.
5. restart, failover, scale, rollback은 승인된 runbook을 사람이 실행합니다.
6. 서비스 복구 후 Terraform Agent가 drift 또는 permanent fix를 별도 change ticket으로 작성합니다.
7. Documentation Agent가 timeline, root cause, action item을 postmortem에 기록합니다.

### Incident request example

```text
Monitoring Agent를 read mode로 사용합니다.
INC-2026-0142, prod, API 5xx 급증을 분석해 주세요.
10:20 KST 이후 ALB, EKS ingress, pod restart, RDS connection metric을 비교하고
사실, 가설, 추가 확인이 필요한 항목을 구분해 주세요.
변경이나 alarm suppression은 수행하지 마세요.
```

### Incident prohibitions

- Agent의 첫 가설만으로 production 변경
- 장애 중 원본 log 삭제 또는 retention 축소
- 원인 확인 없이 alarm disable
- incident ticket 없이 break-glass 사용
- 복구 작업과 영구 infrastructure 변경을 같은 승인으로 처리

## 12. Workflow: Vulnerability and EOS Response

### Agent sequence

```text
Manager routing -> Security -> Operations -> Terraform/CI-CD -> Reviewer
-> Human approval
```

### Required input

- CVE ID 또는 EOS 대상 제품
- severity와 exploit 여부
- 영향 account, image, package, node group
- 현재 version과 target version
- maintenance window

### Response target

| Severity | Target | Expected action |
| --- | --- | --- |
| Critical | 7일 이내 또는 emergency change | image rebuild, emergency patch, compensating control |
| High | 14일 이내 | scheduled patch and verification |
| Medium | 30일 이내 | normal maintenance |
| Low | 정기 cycle | backlog and monthly review |

Agent는 scanner finding을 그대로 취약하다고 확정하지 않고 runtime exposure, package usage, exploitability와 compensating control을 구분해 기록합니다.

## 13. Workflow: Backup and Restore

### Agent sequence

```text
Manager routing -> Operations -> Security -> Monitoring -> Reviewer -> Human execution
```

### Restore request requirements

- restore source와 recovery point
- target account, Region, VPC, isolated subnet
- expected RPO와 RTO
- 데이터 등급과 접근 승인
- 원본 workload에 영향을 주지 않는 검증 방법
- 복구 데이터 폐기 절차

### Restore procedure

1. Operations Agent가 recovery point와 restore dependency를 확인합니다.
2. Security Agent가 KMS, IAM, network isolation, data access를 검토합니다.
3. 운영자가 승인된 isolated environment에 restore를 실행합니다.
4. Monitoring Agent가 application health와 data integrity 검증 항목을 확인합니다.
5. 실제 소요 시간, RPO, RTO, 실패 원인을 restore evidence에 기록합니다.
6. 검증 데이터는 retention 정책에 따라 안전하게 폐기합니다.

백업 job 성공은 복구 성공의 증거가 아닙니다. 월간 restore drill과 분기별 RPO/RTO 검증 결과가 필요합니다.

## 14. Workflow: FinOps Review

### Agent sequence

```text
Manager routing -> FinOps -> Operations -> Terraform -> Reviewer -> FinOps owner approval
```

### Review cadence

| Cadence | Review |
| --- | --- |
| Daily | budget, anomaly, unexpected service/Region spend |
| Weekly | idle EBS/EIP/LB, NAT and cross-AZ transfer, schedule compliance |
| Monthly | owner/service allocation, rightsizing, commitment coverage |
| Quarterly | Savings Plans/RI portfolio, architecture cost efficiency |

FinOps Agent는 삭제, instance 변경, RI/Savings Plans 구매를 직접 수행하지 않습니다. 절감안에는 예상 절감액, 성능 위험, commitment 기간, break-even, rollback 가능성을 포함합니다.

## 15. Workflow: Alarm Change

### Agent sequence

```text
Manager routing -> Monitoring -> Service owner -> Operations -> Reviewer -> CI/CD
```

Alarm 변경안은 기존 event 수, false positive 비율, missed incident 가능성, 새 threshold와 evaluation period, notification target, runbook URL을 포함해야 합니다.

Incident 중 임시 suppression이 필요하면 종료 시간, 대상 alarm, 승인자, 복구 확인자를 ticket에 기록합니다. 만료 시간이 없는 suppression은 허용하지 않습니다.

## 16. Approval Matrix

| Change type | Required Agent review | Human approval | Executor |
| --- | --- | --- | --- |
| Dev module change | Terraform, Reviewer | Service owner | Dev CI/CD role |
| Stg promotion | Terraform, Security as needed, Reviewer | Platform owner | Stg CI/CD role |
| Prod infrastructure | Terraform, Security, Reviewer | Platform owner + service owner | Protected prod CI/CD |
| SCP/Tag Policy | Governance, Security, Reviewer | Cloud governance owner | Organization pipeline |
| IAM privilege increase | Security, Governance, Reviewer | Security owner + resource owner | Protected pipeline |
| Backup restore | Operations, Security | Data owner + operations owner | Authorized operator/runbook |
| Alarm suppression | Monitoring, Operations | Incident commander | Monitoring pipeline/operator |
| RI/Savings Plans purchase | FinOps, Reviewer | FinOps owner | Authorized billing operator |
| Break-glass | Security review after event | Incident commander + security owner | Named emergency operator |

Agent는 자신의 결과를 최종 승인할 수 없습니다.

Cloud Platform Manager Agent는 approval matrix의 검토자를 대신하지 않습니다. Manager의 `ready_for_approval` 상태는 필수 전문 검토와 evidence가 모였다는 workflow 상태일 뿐 승인 자체가 아닙니다.

## 17. Agent Handoff Contract

다른 Agent에게 넘길 때 다음 내용을 artifact로 남깁니다.

```yaml
request_id: req-01JXYZ
from_agent: monitoring
to_agent: operations
ticket: INC-2026-0142
environment: prod
status: needs_action_plan
facts:
  - "10:20 KST부터 ALB 5xx 증가"
  - "동시간 EKS pod restart 증가"
hypotheses:
  - "readiness probe 또는 dependency timeout"
artifacts:
  - "logs-insights-query.txt"
  - "dashboard-snapshot-url"
constraints:
  - "production 변경 금지"
requested_output:
  - "복구 후보와 risk 비교"
  - "사람이 실행할 검증 명령"
```

구두 또는 대화 내용만으로 handoff하지 않습니다.

Cross-domain 요청에서는 Manager Agent가 handoff artifact index와 전체 상태를 관리하되, 각 artifact의 사실·판단 책임은 작성한 domain Agent에게 남습니다.

## 18. Required Agent Output

모든 Agent 결과는 가능한 범위에서 다음 구조를 따릅니다.

1. 요청 요약과 scope
2. 확인된 사실과 evidence
3. 가정과 불확실성
4. 변경 또는 대응 제안
5. 수정 파일과 artifact
6. 검증 결과
7. 보안, 가용성, 비용 영향
8. rollback 또는 recovery 절차
9. blocker와 필요한 사람 승인
10. 다음 Agent 또는 operator action

`성공했습니다`라는 문장만으로 작업을 종료하지 않습니다. 실행한 검증과 실행하지 못한 검증을 구분해야 합니다.

## 19. Session and Context Management

Agent 대화 세션은 운영 기록의 source of truth가 아닙니다. 새 세션이 이전 대화를 자동으로 완전히 기억한다고 가정하지 않습니다.

세션을 종료하기 전에 다음을 repository, ticket 또는 pull request에 저장합니다.

- request ID와 ticket
- 현재 목표와 완료 조건
- 변경 파일과 branch/commit/PR
- 수행한 검증과 결과
- 아직 해결하지 못한 blocker
- 다음 실행 단계
- 승인 상태와 plan artifact hash

새 세션 요청 예시:

```text
CHG-2026-0082 작업을 이어서 진행합니다.
Source of truth는 PR #142와 agents handoff artifact입니다.
현재 stg validate까지 완료했고 plan review가 남았습니다.
기존 파일을 다시 작성하지 말고 변경분과 reviewer finding부터 확인해 주세요.
```

## 20. Prohibited Actions

운영자는 Agent에게 다음 작업을 요청하지 않습니다.

- credential, private key, token, production secret 출력
- `terraform apply`, `destroy`, state 강제 수정 직접 실행
- 승인 없는 production restart, stop, failover, scaling
- CloudTrail, Config, GuardDuty, Security Hub, Flow Logs 비활성화
- SCP, WAF, IAM guardrail을 검증 없이 완화
- 원본 log 또는 incident evidence 삭제
- 승인 없는 alarm suppression
- 승인 없는 budget 변경 또는 RI/Savings Plans 구매
- protected branch 우회, review 생략, plan artifact 교체
- 개인 정보나 고객 raw prompt/response를 일반 log에 저장

## 21. Escalation and Stop Conditions

Agent는 다음 상황에서 작업을 중지하고 운영자에게 escalation해야 합니다.

- 요청 scope와 ticket 내용이 다름
- 필요한 account, environment, data owner가 불명확함
- destructive change 또는 resource replacement가 발견됨
- privilege escalation 또는 public exposure가 추가됨
- secret 또는 restricted data가 입력에서 발견됨
- provider/API version 호환성을 확인할 수 없음
- 실제 cloud 상태와 Terraform state가 충돌함
- rollback이 불가능하거나 RTO 내 복구가 불확실함
- 비용이 `max_cost_usd` 또는 승인 budget을 초과할 가능성이 있음

## 22. Operator Checklists

### Before running an Agent

- [ ] 올바른 Agent와 mode를 선택했다.
- [ ] ticket, repository, environment를 명시했다.
- [ ] 성공 기준과 금지 조건을 작성했다.
- [ ] secret과 restricted data를 제거했다.
- [ ] 최대 비용과 timeout을 정했다.

### Before approving a change

- [ ] plan이 ticket scope와 일치한다.
- [ ] 예상하지 않은 destroy/replace가 없다.
- [ ] 보안 및 public exposure 변화가 검토됐다.
- [ ] 비용 변화와 rollback이 기록됐다.
- [ ] Reviewer finding이 해결되거나 수용됐다.
- [ ] post-deployment metric과 담당자가 지정됐다.

### After deployment

- [ ] 배포 결과와 artifact hash를 ticket에 저장했다.
- [ ] alarm, log, service health를 확인했다.
- [ ] drift와 failed resource가 없다.
- [ ] 문서와 runbook을 갱신했다.
- [ ] 임시 권한, JIT group, suppression을 회수했다.

## 23. Related Documents

- `AGENTS.md`: 역할, runtime 원칙, control ownership
- `docs/ai-platform.md`: AI Gateway, command contract, tool permission, token/cost telemetry
- `docs/identity-access.md`: Corporate IdP, IAM Identity Center, JIT, break-glass
- `docs/security-review.md`: Terraform 보안 통제와 production gate
- `docs/monitoring.md`: 알람과 VPC Flow Logs 분석
- `docs/observability-platform.md`: Mimir, OpenTelemetry, custom metric, Adapter/KEDA 설계와 production gate
- `docs/operations.md`: 백업, patch, scheduling, EOS/EOL
- `docs/finops.md`: tagging, budget, anomaly, commitment
