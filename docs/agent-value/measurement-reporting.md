# Measurement and Reporting

## 1. Purpose

Agent 운영 보고서는 대화 요약이 아니라 의사결정, 승인, 실행과 결과를 재현할 수 있는 evidence package입니다. 기계가 검증하는 JSON, 사람이 검토하는 Markdown/PDF, 원본 evidence reference와 append-only audit를 분리합니다.

## 2. Evidence Chain

```text
request/ticket
  -> authenticated identity and policy decision
  -> model/tool/query events
  -> Agent report and human review
  -> immutable change/approval artifact
  -> deployment or operator action
  -> post-check and service outcome
  -> business/FinOps validation
```

모든 단계는 `request_id`, `trace_id`, ticket, environment, source/artifact version과 UTC timestamp로 연결합니다.

## 3. Report Catalog

| Report | Trigger/cadence | Owner | Minimum content | Current status |
| --- | --- | --- | --- | --- |
| Agent request result | every request | Primary Agent + operator | facts, unknowns, proposal, validation, handoff | Common format defined |
| Incident triage | incident/on demand | Monitoring + IC | timeline, facts, hypotheses, gaps, evidence | Read-only MVP implemented |
| Change readiness | before deployment | Terraform/CI-CD + reviewer | patch, plan hash, risk, approval, rollback | Contract defined, unified schema target |
| Change outcome | after deployment | Service/Platform owner | actual change, SLI before/after, issue, rollback | Target |
| Backup/restore drill | monthly/quarterly by tier | Operations + data owner | recovery point, steps, checksum, RPO/RTO, gap | Target |
| EKS operations | daily/weekly/monthly | Platform/Operations | logging, QoS, capacity, lifecycle, backup, security | Checklist defined, report target |
| Security/governance | per change and periodic | Security/Governance | findings, exceptions, evidence freshness, disposition | Review artifacts, scorecard target |
| FinOps | monthly | FinOps/Finance | allocation, variance, recommendation, realized saving | Cadence defined, unified schema target |
| Agent value scorecard | monthly/quarterly | AI Platform + business owners | business/engineering KPI, controls, evidence, roadmap | Template defined |

## 4. Artifact Layout

로컬 개발과 fixture 검증의 권장 구조입니다.

```text
artifacts/
|-- incidents/<INC-ID>/
|   |-- request.json
|   |-- report.json
|   |-- report.md
|   `-- audit.jsonl
`-- operations/<environment>/<period-or-ticket>/
    |-- request.yaml
    |-- report.json
    |-- report.md
    |-- evidence-index.json
    |-- approvals.json
    `-- audit.jsonl
```

Production artifact는 raw log나 customer data를 Git에 commit하지 않습니다. 암호화, retention, legal hold, immutable version과 role-based access를 제공하는 ticket/artifact store에 저장하고 repository에는 schema, sanitized example과 link만 둡니다.

## 5. Common Report Contract

모든 report type은 domain field 외에 다음 envelope를 가져야 합니다.

```yaml
schema_version: "<version>"
report_type: "<incident|change-readiness|change-outcome|restore|eks-operations|finops|agent-value>"
status: "<complete|partial|blocked|simulation>"
request_id: "<server generated>"
trace_id: "<server generated>"
ticket: "<change/incident/review ID>"
environment: "<dev|stg|prod|organization>"
scope: "<explicit services/resources>"
window:
  started_at: "<UTC>"
  ended_at: "<UTC>"
source_versions:
  repository_revision: "<commit>"
  policy_version: "<version/hash>"
facts: []
unknowns: []
evidence: []
recommendations: []
risks: []
validation:
  automated_checks: []
  human_reviewers: []
approvals: []
actions:
  proposed: []
  executed: []
outcomes: []
handoff: []
```

`status=complete`는 모든 source가 성공했다는 뜻으로 사용하고, source 실패나 evidence gap이 있으면 `partial` 또는 `blocked`로 낮춥니다. `simulation`은 live 운영 증적으로 합산하지 않습니다.

## 6. Report Verification Pipeline

### Stage 1: Contract validation

- JSON/YAML schema와 allowed enum 검증
- required field, size, format, UTC timestamp 확인
- server-generated request/trace ID와 authenticated context 대조
- template placeholder, secret, token, raw PII 거부

### Stage 2: Evidence integrity

- source, query ID, timestamp, account/region/resource identity 확인
- repository revision, policy version, plan/artifact hash 고정
- source freshness와 incomplete/failed collection을 `gaps`에 기록
- sanitized reference가 원본 evidence store와 연결되는지 확인

### Stage 3: Engineering review

- facts, hypotheses, recommendation 분리
- security, availability, cost, rollback/recovery와 stop condition 검토
- automated check와 미수행 검증 구분
- primary Agent와 독립된 Reviewer/human reviewer disposition

### Stage 4: Operational outcome

- 실행 주체, 시각, 대상과 승인 artifact 일치
- 배포/복구 전후 동일 SLI window 비교
- rollback, hotfix, incident와 unexpected outcome 연결
- report의 proposed action과 actual action 차이 기록

### Stage 5: Business validation

- baseline/actual scope와 normalization 확인
- realized saving, customer impact, delivery result를 accountable owner가 승인
- attribution 한계, sample size, side effect와 guardrail 공개
- `validated` 또는 `realized` status 승격 기록

## 7. Reporting Cadence

| Cadence | Review focus | Typical audience |
| --- | --- | --- |
| Per request/change | evidence, risk, approval, immediate outcome | Operator, reviewer, approver |
| Daily | incident, policy deny, failed/blocked report, critical safety signal | On-call, platform/security owner |
| Weekly | change quality, EKS health, backlog, repeated gaps | Engineering leads, service owners |
| Monthly | engineering KPI, FinOps, Agent quality, human correction | Platform/FinOps/Security management |
| Quarterly | business outcome, maturity promotion, investment and risk acceptance | Technology and business leadership |

보고서를 만들기 위한 보고는 피합니다. 이상이 없는 daily raw report는 dashboard로 대체하고, 월간/분기 보고서는 trend, decision, exception과 action owner에 집중합니다.

## 8. Scorecard Aggregation Rules

1. `simulation`, fixture, training data는 production KPI에서 제외합니다.
2. `partial`과 `blocked` report를 성공으로 합산하지 않습니다.
3. median과 p90/p95, sample size와 scope를 함께 표시합니다.
4. recommendation, approved, implemented, realized 값을 분리합니다.
5. 속도 KPI는 change failure, policy violation, human correction guardrail과 함께 봅니다.
6. 단순 report 수와 token 수를 business value로 합산하지 않습니다.
7. 동일 request의 retry/duplicate를 unique outcome으로 중복 계산하지 않습니다.
8. KPI definition version이 바뀌면 이전 기간과 직접 비교하지 않거나 재계산합니다.

## 9. Retention and Access

| Artifact | Suggested class | Retention decision | Access |
| --- | --- | --- | --- |
| Sanitized executive scorecard | Internal | business/audit requirement | leadership, platform owners |
| Engineering report | Internal/Confidential | service lifecycle and audit | engineering/reviewer |
| Incident evidence | Confidential/Restricted | incident/legal policy | incident/security need-to-know |
| Prompt/tool audit | Confidential/Restricted | AI governance requirement | AI platform/security audit |
| Approval/change artifact | Internal/Confidential | change/audit requirement | approver, CI/CD, auditor |

실제 기간은 조직의 data classification, legal, incident와 audit policy에서 승인합니다. report가 원본보다 오래 보존되면서 secret/PII를 복제하지 않도록 redaction과 evidence reference를 사용합니다.

## 10. Responsibility and Separation

| Activity | Responsible | Accountable/validator |
| --- | --- | --- |
| Report generation | Domain Agent/runtime | Operator/domain owner |
| Schema/pipeline | AI Platform/Documentation | Architecture/Reviewer |
| Engineering KPI | Monitoring/Platform | Engineering owner |
| Security outcome | Security/Governance | Risk owner |
| Realized cost | FinOps | Finance/FinOps owner |
| Business impact | Service/Business analyst | Business owner |
| Portfolio publication | Documentation Agent | Human reviewer |

Agent, report generator 또는 지표 owner가 자신의 production 변경과 business impact를 단독 승인하지 못하게 합니다.

## 11. Current Implementation and Next Gate

현재 `schemas/incident-report.schema.json`과 Monitoring CLI가 `report.json`, `report.md`, `audit.jsonl`을 생성합니다. `reports/templates/`에는 월간 플랫폼 운영 보고서와 장애 보고서 양식이 있으며 `reports/examples/`는 fixture를 사용한 sanitized simulation만 제공합니다. 실제 월간 집계 source와 human sign-off는 아직 target입니다.

다음 구현 순서는 다음과 같습니다.

1. 공통 report envelope와 domain별 JSON schema 정의
2. sanitized fixture/golden report와 invalid case test
3. ticket/PR/CI/Monitoring/CUR event adapter와 identity registry 연결
4. secure artifact store의 encryption, access, retention, immutability 적용
5. dev/stg pilot에서 baseline, actual, correction과 failure event 수집
6. human owner validation을 거친 월간 scorecard 발행
7. 독립 audit 후 use case별 maturity 승격 검토
