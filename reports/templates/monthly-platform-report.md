# Monthly Platform Operations Report

> 상태: 템플릿. `<...>`는 발행 전에 실제 값 또는 `not_available`과 사유로 교체합니다. 이 파일 자체는 운영 성과 증적이 아닙니다.

## 1. Report Metadata

| Field | Value |
| --- | --- |
| Report ID | `<RPT-MONTHLY-YYYY-MM-NNNN>` |
| Reporting period | `<start UTC> - <end UTC>` |
| Evidence cutoff | `<UTC>` |
| Scope | `<accounts/environments/services/platforms>` |
| Status | `<complete|partial|blocked|simulation>` |
| Data classification | `<internal|confidential|restricted>` |
| Repository revision | `<commit/tag>` |
| Policy/KPI version | `<version/hash>` |
| Prepared by | `<team/Agent + human owner>` |
| Reviewed by | `<Platform/Security/FinOps/service owners>` |
| Approved by | `<authenticated approval reference>` |

## 2. Executive Summary

- 서비스 상태: `<availability, customer impact, material incidents>`
- 변경 상태: `<delivery volume, failed/rolled-back change, key risk>`
- 운영 상태: `<capacity, backup/restore, patch/lifecycle>`
- 보안·비용 상태: `<finding/exception, budget/variance>`
- 이번 달 의사결정: `<approval, investment, risk acceptance or none>`
- 가장 중요한 한계: `<missing source, incomplete scope, attribution limit>`

## 3. Evidence Coverage

| Source | Expected scope | Collected scope | Freshness | Status | Gap/owner |
| --- | --- | --- | --- | --- | --- |
| Monitoring/SLO | `<scope>` | `<scope>` | `<UTC>` | `<complete|partial|missing>` | `<gap/owner>` |
| Incident/ticket | `<scope>` | `<scope>` | `<UTC>` | `<status>` | `<gap/owner>` |
| CI/CD/change | `<scope>` | `<scope>` | `<UTC>` | `<status>` | `<gap/owner>` |
| Backup/restore | `<scope>` | `<scope>` | `<UTC>` | `<status>` | `<gap/owner>` |
| Security/governance | `<scope>` | `<scope>` | `<UTC>` | `<status>` | `<gap/owner>` |
| CUR/budget | `<scope>` | `<scope>` | `<UTC>` | `<status>` | `<gap/owner>` |

## 4. Reliability and Incidents

| Service/SLO | Target | Actual/sample | Error budget | Incidents | Result | Evidence |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `<service/SLO>` | `<value>` | `<value/n>` | `<value>` | `<count>` | `<met|missed|not_available>` | `<refs>` |

### Material incident `<INC-ID>`

- 영향과 기간: `<customer/service impact and UTC window>`
- 확인된 원인 또는 현재 상태: `<confirmed cause or under investigation>`
- 복구와 검증: `<action, validation, rollback status>`
- 재발 방지 조치: `<action/owner/due/evidence>`

## 5. Platform, EKS and Network Health

| Domain | Current observation | Risk/threshold | Decision/action | Evidence |
| --- | --- | --- | --- | --- |
| EKS capacity/QoS | `<observation>` | `<risk>` | `<action>` | `<refs>` |
| IP/VPC/TGW | `<address capacity, route/attachment state>` | `<risk>` | `<action>` | `<refs>` |
| Logging/metrics | `<coverage, drop, cardinality>` | `<risk>` | `<action>` | `<refs>` |
| Data/backup | `<backup and restore result>` | `<RPO/RTO gap>` | `<action>` | `<refs>` |
| Patch/CVE/EOS | `<coverage and aging>` | `<exception>` | `<action>` | `<refs>` |

## 6. Changes and Delivery

| KPI | Baseline | Actual/sample | Guardrail | Result | Evidence |
| --- | ---: | ---: | ---: | --- | --- |
| Change lead time median/p90 | `<value/n>` | `<value/n>` | Failure rate `<value>` | `<result>` | `<refs>` |
| Terraform plan/review | `<value>` | `<value>` | Destructive plan blocked `<count>` | `<result>` | `<refs>` |
| Failed/rolled-back change | `<value>` | `<value>` | Rollback verified `<value>` | `<result>` | `<refs>` |

## 7. Security, Governance and Exceptions

| Finding/control | Severity | State | Exception expiry | Owner | Evidence |
| --- | --- | --- | --- | --- | --- |
| `<finding/control>` | `<severity>` | `<open/mitigated/accepted>` | `<UTC/not_applicable>` | `<owner>` | `<refs>` |

## 8. FinOps

| Cost view | Budget/baseline | Actual | Variance | Recommendation | Realized saving | Evidence |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| `<account/service/tag>` | `<currency>` | `<currency>` | `<value>` | `<proposal>` | `<validated value/not_available>` | `<CUR/invoice refs>` |

예상 절감, 승인된 절감안, 구현 결과와 invoice에서 확인된 실현 절감을 분리합니다.

## 9. Agent and Automation Quality

| KPI | Value/sample | Guardrail | Disposition | Evidence |
| --- | ---: | --- | --- | --- |
| Evidence-backed fact rate | `<value/n>` | `<policy>` | `<result/action>` | `<refs>` |
| Material human correction | `<value/n>` | `<threshold>` | `<reason>` | `<refs>` |
| Unsafe tool/scope attempt | `<count>` | `0` | `<incident/action>` | `<refs>` |
| Secret/PII canary failure | `<count>` | `0` | `<incident/action>` | `<refs>` |

## 10. Decisions and Next-Period Actions

| Action/decision | Why | Owner | Due | Stop/escalation condition | Completion evidence |
| --- | --- | --- | --- | --- | --- |
| `<action>` | `<reason>` | `<owner>` | `<date>` | `<condition>` | `<expected artifact>` |

## 11. Evidence Register

| Evidence ID | Source/version | Window | Classification | Integrity reference | Retention/access |
| --- | --- | --- | --- | --- | --- |
| `<ID>` | `<source>` | `<UTC>` | `<class>` | `<hash/immutable ref>` | `<policy>` |

## 12. Sign-off

| Role | Identity reference | Decision | Timestamp |
| --- | --- | --- | --- |
| Platform/Operations owner | `<identity>` | `<approve/reject>` | `<UTC>` |
| Security/Reviewer | `<identity>` | `<approve/reject>` | `<UTC>` |
| FinOps/Finance | `<identity>` | `<approve/reject/not_required>` | `<UTC>` |
| Service owner | `<identity>` | `<approve/reject>` | `<UTC>` |

