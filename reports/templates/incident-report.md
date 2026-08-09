# Incident Report

> 상태: 템플릿. Monitoring Agent의 구조화 결과는 `schemas/incident-report.schema.json`을 따르고, 이 문서는 Incident Commander와 운영자가 검토하는 사람용 보고서입니다.

## 1. Incident Metadata

| Field | Value |
| --- | --- |
| Incident ticket | `<INC-YYYY-NNNN>` |
| Report status | `<complete|partial|blocked|simulation>` |
| Severity | `<critical|high|warning|info>` |
| Environment/service | `<environment/service>` |
| Started / detected / recovered | `<UTC timestamps>` |
| Customer-impact window | `<UTC or not_available>` |
| Request ID / Trace ID | `<server-generated IDs>` |
| Data classification | `<class>` |
| Incident Commander | `<authenticated identity reference>` |
| Prepared / reviewed by | `<roles and references>` |

## 2. Executive Summary

- 발생한 현상: `<symptom>`
- 영향: `<customer/service/data impact or not_available>`
- 현재 상태: `<recovered|monitoring|investigating>`
- 원인 상태: `<confirmed|probable|unknown>`
- 핵심 복구 조치: `<actual action or none>`
- 가장 중요한 미확인 사항: `<gap>`

## 3. Impact

| Dimension | Observation | Measurement/evidence | Confidence |
| --- | --- | --- | --- |
| Customer | `<impact>` | `<SLI/ticket ref>` | `<high|medium|low|unknown>` |
| Service | `<error/latency/capacity>` | `<metric ref>` | `<confidence>` |
| Data/security | `<impact or none observed>` | `<audit ref>` | `<confidence>` |
| Cost/operations | `<impact>` | `<source>` | `<confidence>` |

영향이 측정되지 않았으면 `영향 없음`이 아니라 `not_available`로 기록합니다.

## 4. Timeline

| UTC | Actor/source | Event | Evidence | Decision/approval |
| --- | --- | --- | --- | --- |
| `<timestamp>` | `<actor/source>` | `<observation/action>` | `<ID>` | `<decision/ref>` |

## 5. Confirmed Facts

| Fact | Evidence ID | Source/window | Freshness |
| --- | --- | --- | --- |
| `<fact>` | `<ID>` | `<source/window>` | `<UTC>` |

## 6. Hypotheses and Evidence Gaps

| Hypothesis | Confidence | Supporting evidence | Counter evidence | Verify next |
| --- | --- | --- | --- | --- |
| `<hypothesis>` | `<high|medium|low>` | `<IDs>` | `<IDs/none>` | `<bounded check>` |

| Evidence gap | Why it matters | Owner | Due/stop condition |
| --- | --- | --- | --- |
| `<gap>` | `<risk>` | `<owner>` | `<condition>` |

## 7. Root Cause and Contributing Factors

- Root cause: `<confirmed cause or not_confirmed>`
- Trigger: `<event or unknown>`
- Contributing factors: `<design/process/monitoring factors>`
- Detection gap: `<why prevention/detection did not work>`
- Evidence supporting conclusion: `<IDs>`

원인이 확인되지 않았으면 가설을 root cause로 승격하지 않습니다.

## 8. Response, Recovery and Validation

### Proposed actions

| Proposal | Risk | Approval required | Owner |
| --- | --- | --- | --- |
| `<proposal>` | `<risk>` | `<approval>` | `<owner>` |

### Executed actions

| UTC | Action | Executor | Approval/ticket | Result | Rollback state |
| --- | --- | --- | --- | --- | --- |
| `<timestamp or none>` | `<action>` | `<identity>` | `<reference>` | `<result>` | `<state>` |

Monitoring Agent의 read-only 보고서는 `executed_mutations=[]`이며 실행 조치를 주장하지 않습니다.

### Recovery validation

| Check | Before | After | Window/sample | Result | Evidence |
| --- | --- | --- | --- | --- | --- |
| `<SLI/health/data check>` | `<value>` | `<value>` | `<window>` | `<pass/fail/not_available>` | `<ID>` |

## 9. Corrective and Preventive Actions

| Action | Type | Priority | Owner | Due | Success/closure evidence |
| --- | --- | --- | --- | --- | --- |
| `<action>` | `<corrective|preventive|detection>` | `<P0-P3>` | `<owner>` | `<date>` | `<evidence>` |

## 10. Evidence Register and Security Handling

| Evidence ID | Source/query | Window | Classification | Redaction | Integrity reference |
| --- | --- | --- | --- | --- | --- |
| `<ID>` | `<source/query>` | `<UTC>` | `<class>` | `<result>` | `<hash/ref>` |

- Secret/PII exposure: `<none observed|finding reference|not_available>`
- Raw evidence location: `<approved store reference; do not paste raw customer data>`
- Retention/access: `<approved policy>`

## 11. Lessons, Handoff and Sign-off

- 잘 작동한 통제: `<items>`
- 작동하지 않은 통제: `<items>`
- 다음 담당자와 handoff: `<owner/artifact/condition>`

| Role | Identity reference | Decision | Timestamp |
| --- | --- | --- | --- |
| Incident Commander | `<identity>` | `<approve/reopen>` | `<UTC>` |
| Service owner | `<identity>` | `<approve/reopen>` | `<UTC>` |
| Security/Reviewer | `<identity>` | `<approve/follow-up>` | `<UTC>` |

