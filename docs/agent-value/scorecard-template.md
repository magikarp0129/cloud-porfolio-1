# Agent Value Scorecard Template

> 이 문서는 월간 또는 분기 보고서 양식입니다. `<...>` placeholder는 발행 전에 실제 값 또는 `not_available`과 사유로 교체합니다. 예시 값은 성과 증적이 아닙니다.

## 1. Report Metadata

| Field | Value |
| --- | --- |
| Reporting period | `<start UTC> - <end UTC>` |
| Scope | `<accounts/environments/services/use cases>` |
| Report ID | `<server-generated ID>` |
| Evidence cutoff | `<UTC>` |
| KPI definition version | `<version>` |
| Prepared by | `<Agent/runtime + human owner>` |
| Reviewed by | `<engineering/security/FinOps reviewers>` |
| Approved for publication by | `<accountable human>` |
| Overall claim status | `<defined|instrumented|measured|validated|realized>` |

## 2. Executive Summary

- Business outcome: `<measured result or not yet measured>`
- Engineering outcome: `<measured result or not yet measured>`
- Safety/control result: `<policy violation, data event, approval bypass>`
- Material limitation: `<scope, sample, missing source, attribution>`
- Decision required: `<investment, risk acceptance, maturity promotion or none>`

## 3. Business Outcome Scorecard

| Outcome | Baseline | Target | Actual | Status | Evidence | Accountable owner |
| --- | ---: | ---: | ---: | --- | --- | --- |
| Customer-impact minutes | `<value/n>` | `<value>` | `<value/n>` | `<status>` | `<incident refs>` | `<owner>` |
| Infrastructure delivery lead time | `<value/n>` | `<value>` | `<value/n>` | `<status>` | `<ticket/CI refs>` | `<owner>` |
| Realized cloud saving | `<currency/scope>` | `<value>` | `<value>` | `<status>` | `<CUR/invoice refs>` | `<FinOps/Finance>` |
| Audit evidence preparation time | `<value/n>` | `<value>` | `<value/n>` | `<status>` | `<review refs>` | `<risk owner>` |
| Operational capacity returned | `<hours>` | `<hours>` | `<hours>` | `<status>` | `<time sample>` | `<engineering owner>` |
| Onboarding/supervised task time | `<value/n>` | `<value>` | `<value/n>` | `<status>` | `<training refs>` | `<team owner>` |

## 4. Engineering Outcome Scorecard

| Domain/KPI | Baseline | Actual | Guardrail | Result | Evidence |
| --- | ---: | ---: | ---: | --- | --- |
| Incident evidence collection median/p90 | `<value/n>` | `<value/n>` | Evidence coverage `<value>` | `<result>` | `<report refs>` |
| Change lead time median/p90 | `<value/n>` | `<value/n>` | Failure rate `<value>` | `<result>` | `<PR/CI refs>` |
| Unexpected destructive plan | `<count>` | `<count>` | Blocked before apply `<count>` | `<result>` | `<plan refs>` |
| EKS OOM/eviction/Pending | `<count>` | `<count>` | SLO/error budget `<value>` | `<result>` | `<metric refs>` |
| Restore drill success/RPO/RTO | `<value>` | `<value>` | Data checksum/synthetic `<result>` | `<result>` | `<drill refs>` |
| Critical/high risk age | `<value>` | `<value>` | Exception expiry `<value>` | `<result>` | `<finding refs>` |
| Allocation coverage/unit cost | `<value>` | `<value>` | SLO regression `<value>` | `<result>` | `<CUR/SLO refs>` |
| Runbook/template coverage | `<value>` | `<value>` | Stale document `<count>` | `<result>` | `<inventory refs>` |

## 5. Agent Quality and Safety

| KPI | Value/sample | Threshold | Disposition |
| --- | ---: | ---: | --- |
| Evidence-backed fact rate | `<value/n>` | `<policy>` | `<status/action>` |
| Material human correction rate | `<value/n>` | `<policy>` | `<reason categories>` |
| Recommendation accepted/rejected/deferred | `<counts>` | `N/A` | `<analysis>` |
| Expected/false policy deny | `<counts>` | `<policy>` | `<policy/template action>` |
| Scope expansion or unsafe tool attempt | `<count>` | `0` | `<incident/action>` |
| Secret/PII canary failure | `<count>` | `0` | `<incident/action>` |
| Cost per accepted outcome | `<currency/n>` | `<budget>` | `<trend>` |

## 6. Material Cases

### Case `<ID>`

- Context: `<service/environment/ticket>`
- Agent contribution: `<evidence collection/draft/review>`
- Human decision: `<accepted/changed/rejected and why>`
- Operational outcome: `<verified result>`
- Business relevance: `<validated impact or hypothesis only>`
- Guardrail result: `<failure/change/security/cost>`
- Evidence: `<immutable references>`
- Lesson/action owner: `<action, owner, due date>`

## 7. Controls and Exceptions

| Control/exception | Current state | Risk | Owner | Due/expiry | Evidence |
| --- | --- | --- | --- | --- | --- |
| `<control>` | `<implemented/partial/target>` | `<risk>` | `<owner>` | `<date>` | `<reference>` |

## 8. Maturity Decision

- Use case/environment: `<scope>`
- Current level: `<0-4>`
- Promotion/demotion proposal: `<decision>`
- Completed gates: `<evaluation, permission, canary, rollback, audit>`
- Missing gates: `<items>`
- Independent review: `<reference>`
- Accountable human decision: `<approved/rejected/deferred>`

## 9. Next-Period Commitments

| Action | Outcome/KPI | Owner | Due | Completion evidence |
| --- | --- | --- | --- | --- |
| `<action>` | `<linked outcome>` | `<owner>` | `<date>` | `<expected artifact>` |

## 10. Evidence Register

| Evidence ID | Type | Source/version | Classification | Integrity reference | Retention/access |
| --- | --- | --- | --- | --- | --- |
| `<ID>` | `<report/query/PR/plan/CUR/drill>` | `<source>` | `<class>` | `<hash/version>` | `<policy>` |

## 11. Sign-off

| Role | Name/identity reference | Decision | Timestamp |
| --- | --- | --- | --- |
| Engineering owner | `<identity>` | `<approve/reject>` | `<UTC>` |
| Security/Reviewer | `<identity>` | `<approve/reject>` | `<UTC>` |
| FinOps/Finance when applicable | `<identity>` | `<approve/reject>` | `<UTC>` |
| Business/Service owner | `<identity>` | `<approve/reject>` | `<UTC>` |

Sign-off는 Agent output이나 사용자가 입력한 boolean을 신뢰하지 않고 ticket/approval system의 인증된 event를 참조합니다.
