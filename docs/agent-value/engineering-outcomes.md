# Engineering Outcomes

## 1. Measurement Objective

Engineering KPI는 Agent 활동량이 아니라 운영 시스템의 속도, 품질, 안정성, 통제 가능성을 측정합니다. 각 KPI는 definition, event source, scope, owner와 guardrail을 가져야 합니다.

## 2. Outcome Domains

| Domain | Primary outcomes | Primary evidence |
| --- | --- | --- |
| Incident management | 증적 수집과 복구 판단 단축, 가설 품질 향상 | incident request/report, query audit, ticket timeline |
| Change management | lead time 단축과 failure 감소 | PR, plan, CI run, approval, deployment marker |
| Reliability/EKS | SLO, capacity, recovery, lifecycle 안정성 | metric/log, Kubernetes state, restore/upgrade drill |
| Security/Governance | least privilege, policy 준수, risk closure | finding, policy simulation, exception register |
| FinOps | allocation 품질, waste 제거, realized saving | CUR/invoice, tag coverage, approved changes |
| Knowledge/Operations | runbook, handoff, 반복 작업 표준화 | report catalog, runbook inventory, ticket sample |
| Agent quality/safety | evidence 품질, human oversight, 권한 경계 | model/tool audit, correction, deny and violation event |

## 3. Incident Management KPI

| KPI | Definition | Evidence | Guardrail |
| --- | --- | --- | --- |
| Evidence collection duration | request accepted부터 review 가능한 report 생성까지 | Gateway/CLI timestamp, report status | `simulation` 제외, `partial` 별도 표시 |
| Time to human acknowledgement | incident open부터 accountable operator 확인까지 | Incident platform event | Agent report 생성과 혼동하지 않음 |
| Time to recovery | 고객 영향 시작부터 검증된 복구까지 | incident timeline, SLI | severity/service class로 정규화 |
| Evidence coverage | 요청된 source 중 성공하고 timestamp가 있는 source 비율 | report `evidence`와 `gaps` | source failure를 정상으로 계산 금지 |
| Hypothesis validation rate | 검증 또는 반증된 가설 비율 | follow-up query와 disposition | 높은 수치가 root cause 정확도와 같지 않음 |
| Repeat incident rate | 동일 failure mode 재발 | postmortem taxonomy | 영구 수정 완료 여부와 함께 측정 |

Monitoring Agent의 현재 fixture report는 schema/redaction 경로를 검증할 뿐 live MTTR 성과에는 포함하지 않습니다.

## 4. Change Management KPI

| KPI | Definition | Evidence | Guardrail |
| --- | --- | --- | --- |
| Change lead time | approved request부터 production verified까지 | ticket, PR, CI/CD, deployment marker | 승인 대기와 구현 시간을 분리 표시 |
| Review cycle time | review 요청부터 blocking finding disposition까지 | PR review, Reviewer report | 단순 승인 속도만 최적화하지 않음 |
| Change failure rate | 장애, rollback, hotfix가 필요한 production change 비율 | change와 incident 연결 | change 유형과 risk tier로 구분 |
| Unexpected destructive plan | 승인 scope 밖 replace/destroy가 발견된 plan 수 | immutable plan summary | 발견 후 차단은 positive control event |
| Rollback readiness | 실행 전 owner, trigger, steps, evidence가 있는 change 비율 | ticket/PR checklist | 문서 존재와 rehearsal을 구분 |
| Post-check completion | 배포 후 동일 SLI window를 검증한 change 비율 | metric snapshot, deployment record | green alarm 하나만으로 완료 금지 |

Agent가 patch를 빨리 만들었더라도 review 재작업, failure 또는 emergency change가 늘면 engineering 성과로 인정하지 않습니다.

## 5. Reliability and EKS KPI

### Service reliability

- SLI/SLO 달성률과 error budget consumption
- workload availability와 dependency failure contribution
- saturation 상태에서의 latency/error 변화
- alert precision, actionable alarm, runbook linkage
- capacity forecast error와 quota/subnet/node ceiling 도달 시간

### EKS workload quality

| KPI | Definition/evidence |
| --- | --- |
| Resource declaration coverage | application/init/sidecar container의 CPU, memory, ephemeral-storage requests/limits coverage |
| QoS distribution | namespace/tier별 Guaranteed, Burstable, BestEffort Pod 비율 |
| OOM/eviction pressure | OOMKilled, memory/disk/inode pressure eviction과 recurrence |
| Scheduling health | Pending duration, unschedulable reason, subnet IP/node max/quota ceiling |
| Availability policy coverage | critical workload의 replicas, probes, PDB, topology spread 적용과 실제 status |
| Scaling effectiveness | HPA max 체류, scale-out latency, node provision failure, scale-down disruption |
| Log pipeline health | source coverage, dropped/failed record, archive reconciliation, masking test |
| Lifecycle compliance | 지원 종료 전 cluster/add-on/node/controller upgrade 비율 |
| Recovery evidence | backup child status, namespace/cluster restore 성공, checksum/synthetic, measured RPO/RTO |

QoS, PDB 또는 backup object 존재를 실제 안정성 성과로 간주하지 않습니다. admission test, disruption rehearsal, restore drill과 post-check가 필요합니다.

## 6. Security and Governance KPI

| KPI | Definition | Evidence |
| --- | --- | --- |
| Critical/high exposure | 검증된 critical/high finding의 수와 age | Security review, finding source |
| Remediation SLA | severity별 finding closure 또는 risk acceptance 시간 | ticket disposition |
| Least-privilege exception | wildcard/privilege exception 수, owner, expiry | exception register |
| Policy test coverage | allow/deny, negative, lockout scenario를 검증한 policy 비율 | simulator/test artifact |
| Evidence freshness | control claim을 지원하는 source의 age | report metadata |
| Approval integrity | artifact hash와 승인 대상이 일치한 production change 비율 | CI/CD attestation |
| Agent policy violation | scope expansion, unsafe tool, data leakage, approval bypass event | Gateway/Tool Broker audit |

Policy deny는 모두 실패가 아닙니다. 위험한 요청을 사전에 차단한 deny는 control effectiveness로 별도 분류합니다. 반복적인 legitimate deny는 template/policy 품질 문제로 분석합니다.

## 7. FinOps Engineering KPI

| KPI | Definition | Evidence |
| --- | --- | --- |
| Allocation coverage | owner/service/environment/cost center에 할당된 비용 비율 | CUR allocation fields |
| Recommendation acceptance | 분석 후보 중 owner가 수락/반려/보류한 비율 | FinOps backlog disposition |
| Implementation rate | 수락된 항목 중 change와 post-check를 완료한 비율 | PR/change record |
| Realized saving | 정상화된 baseline 대비 실제 run-rate 감소 | CUR/invoice reconciliation |
| Unit cost | business transaction, customer, request 또는 workload 단위 비용 | service KPI + billing data |
| Optimization regression | 비용 절감 후 SLO, capacity, incident 악화 | metric and incident correlation |
| Agent operating cost | model, tool, human review와 rework 비용 | AI Gateway usage + labor sample |

예상 절감액과 realized saving을 한 열에 합산하지 않습니다.

## 8. Knowledge and Operational Scale KPI

- 중요 service/alarm/change type의 runbook coverage
- report와 handoff template adoption
- ticket당 누락된 필수 field 및 clarification 횟수
- 신규 운영자의 supervised task 완료 시간
- 반복 수동 query/command 감소
- 담당자 부재로 인한 escalation과 지연
- 엔지니어당 account/cluster/service 범위
- 관리 범위 증가에 따른 incident/change failure 추이

문서 수와 runbook 줄 수는 품질 지표가 아닙니다. 실제 ticket에서 사용되고 최신 source와 owner가 확인된 문서만 coverage에 포함합니다.

## 9. Agent Quality and Safety KPI

| KPI | Purpose | Calculation note |
| --- | --- | --- |
| Evidence-backed fact rate | 근거 없는 단정 탐지 | source ID와 timestamp가 있는 fact / 전체 fact |
| Human correction rate | output 품질과 review 부담 파악 | material correction / reviewed output; 사유별 분류 |
| Recommendation disposition | 수락 편향과 usefulness 확인 | accepted/rejected/deferred/expired |
| Reproducibility | 동일 source에서 reviewer가 결론을 재현 | sampled independent review |
| Tool success/failure | integration 품질과 evidence gap 식별 | source/tool/query별 분리 |
| Policy deny rate | 안전 통제와 UX 문제 분리 | expected deny / false deny / policy defect |
| Scope expansion attempt | 요청 범위를 넘는 행동 감지 | Gateway/Tool Broker deny event |
| Secret/PII redaction | data protection 확인 | canary test + detected output event |
| Cost per accepted outcome | 활동량이 아닌 유효 결과 비용 | model/tool/review cost / accepted outcome |

Human correction rate가 0이라고 항상 좋은 것은 아닙니다. 표본 검토가 없거나 운영자가 결과를 비판 없이 승인하는 경우를 별도 점검합니다.

## 10. Baseline and Comparison Rules

1. KPI마다 environment, service tier, severity, change type와 기간을 고정합니다.
2. 최소한 baseline과 pilot에서 같은 event definition을 사용합니다.
3. 평균만 사용하지 않고 median, p90/p95와 outlier 사유를 함께 봅니다.
4. 표본 수가 작으면 수치를 일반화하지 않고 case study로 표시합니다.
5. traffic, 조직 범위, 신규 service, 가격과 계절성을 보정합니다.
6. Agent가 참여하지 않은 control group 또는 historical comparison을 가능한 범위에서 유지합니다.
7. 품질·안전 guardrail이 악화되면 속도 개선을 성공으로 판정하지 않습니다.

## 11. Minimum Evidence Record

각 KPI sample은 다음을 연결해야 합니다.

```yaml
metric_id: change.lead_time
period: "<start/end UTC>"
scope:
  environment: "<dev|stg|prod>"
  service: "<service>"
definition_version: "1.0"
baseline:
  value: "<number>"
  sample_size: "<n>"
actual:
  value: "<number>"
  sample_size: "<n>"
evidence:
  - "<ticket/PR/report/query reference>"
guardrails:
  change_failure_rate: "<value>"
validation:
  status: "<defined|instrumented|measured|validated|realized>"
  owner: "<human accountable role>"
  reviewed_at: "<UTC>"
```

Template의 placeholder는 report 발행 전에 제거하거나 `not_available`과 사유로 바꿉니다.
