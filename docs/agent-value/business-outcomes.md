# Business Outcomes

## 1. Executive View

비즈니스는 Agent 자체를 구매하지 않습니다. 서비스 중단 감소, 더 빠른 delivery, 통제된 비용, 낮은 risk와 확장 가능한 운영 역량을 기대합니다.

이 portfolio의 초기 가치 제안은 인력 대체나 production 자율 운영이 아닙니다. 운영자의 반복 조사·검토·보고 부담을 줄이고, 판단 근거와 승인 통제를 표준화하는 것입니다.

## 2. Business Outcome Catalog

| Business outcome | Engineering driver | Business KPI | Required validation |
| --- | --- | --- | --- |
| Service continuity | 빠른 증적 수집, recovery gate, restore rehearsal | 고객 영향 시간, SLO 위반, 중요 업무 중단 | Incident Commander와 service owner 확인 |
| Delivery speed | 표준 요청, patch/plan/review automation | 변경 lead time, environment 준비 시간, release 대기 시간 | CI/CD와 change ticket timestamp |
| Cost efficiency | toil 감소, waste 제거, normalized rightsizing | 운영시간 회수, 단위 서비스 비용, 실현 절감액 | FinOps/Finance의 비용 보정과 승인 |
| Risk reduction | evidence-linked review, least privilege, policy simulation | critical finding, overdue exception, 감사 준비 시간 | Security/Governance risk owner disposition |
| Organizational scale | reusable template, runbook, common evidence | 엔지니어당 관리 범위, 표준 적용률, 온보딩 시간 | Platform owner와 팀 운영 지표 |
| Decision quality | facts/unknowns/options 분리, independent review | recommendation 반려율, 재작업, 근거 없는 결정 | Human reviewer disposition과 사유 |

## 3. Service Continuity

### Value hypothesis

Monitoring Agent가 승인된 source에서 증적을 수집하고 Operations Agent가 recovery 조건을 구조화하면, 운영자는 원인 탐색보다 영향 판단과 복구 선택에 집중할 수 있습니다.

### Engineering evidence

- incident request/report의 `request_id`, `trace_id`, source timestamp
- incident evidence collection duration
- `partial`/`blocked` source와 missing evidence
- runbook precondition, stop condition, rollback과 post-check
- backup recovery point, restore drill, measured RPO/RTO

### Business validation

- 고객 영향 시작/종료 시각은 incident record에서 검증합니다.
- 장애 시간 감소를 Agent에 attribution하려면 동일 severity와 service class를 비교합니다.
- 회피 매출 또는 손실은 Finance가 승인한 영향 모델이 있을 때만 계산합니다.
- 장애가 없었다는 사실만으로 Agent가 위험을 감소시켰다고 주장하지 않습니다.

## 4. Delivery Speed

### Value hypothesis

Architecture, Terraform, Security, Reviewer와 CI/CD Agent의 정형화된 handoff는 요구사항 누락, 반복 review와 environment별 절차 차이를 줄일 수 있습니다.

### Engineering evidence

- request accepted, first patch, plan ready, approval, deployment timestamp
- PR revision, fmt/validate/test와 immutable plan hash
- review finding과 disposition, 재작업 횟수
- dev -> stg -> prod promotion evidence
- change failure, rollback, emergency fix

### Business validation

- lead time 감소와 함께 change failure rate가 악화되지 않아야 합니다.
- Agent가 생성한 초안 시간만 측정하지 않고 human review와 승인 완료까지 포함합니다.
- business release 전체가 아니라 infra/platform이 통제할 수 있는 구간을 명시합니다.

## 5. Cost Efficiency

### Value hypothesis

Agent는 반복적인 데이터 수집, 분류, 보고서 초안과 최적화 후보 탐색을 지원합니다. 서비스 owner는 SLO, capacity와 delivery 계획을 확인하고 적용 여부를 결정합니다.

### Measurement layers

| Layer | Definition | Business use |
| --- | --- | --- |
| Recommendation | Agent가 발견한 후보와 예상 절감 | backlog 우선순위, 실적 아님 |
| Approved | Service/FinOps owner가 적용하기로 한 항목 | forecast, 아직 실현 아님 |
| Implemented | change가 적용되고 post-check를 통과 | 효과 관측 시작 |
| Realized | 정상화된 baseline 대비 실제 invoice/CUR 감소 | 검증된 비용 성과 |

### Calculation guardrails

```text
Realized cloud saving
= normalized baseline run rate
- normalized actual run rate after implementation
- migration or one-time cost

Engineering capacity returned
= verified repetitive hours removed
- Agent review/rework/runtime hours
```

- traffic, seasonality, 신규/종료 workload와 가격 변화를 보정합니다.
- 절감 시간을 즉시 인건비 절감이나 인력 감축으로 환산하지 않습니다.
- 회수된 시간은 reliability backlog, platform engineering 또는 delivery capacity로 사용했는지 함께 기록합니다.
- RI/Savings Plans는 추천과 구매를 분리하고 Finance/FinOps owner가 승인합니다.

## 6. Risk and Compliance

### Value hypothesis

Governance, Security와 Reviewer Agent가 정책과 evidence를 일관된 형식으로 검토하면, production 전에 위반과 missing control을 발견하고 audit 준비 비용을 줄일 수 있습니다.

### Engineering evidence

- policy finding, severity, affected scope와 source revision
- IAM/network/KMS/public exposure 변화
- exception owner, reason, expiry와 compensating control
- policy simulation, negative test와 staged rollout
- approval chain과 immutable artifact hash

### Business validation

- finding 발견은 risk 제거와 동일하지 않습니다. remediation 또는 risk acceptance까지 추적합니다.
- critical risk 감소는 자산 범위와 threat model이 동일할 때 비교합니다.
- 감사 준비 시간은 증적 수집 시작부터 reviewer가 사용 가능한 package를 승인할 때까지 측정합니다.

## 7. Organizational Scale and Knowledge Continuity

### Value hypothesis

역할별 요청 템플릿, report schema, runbook과 handoff contract는 숙련자의 암묵지를 반복 가능한 운영 product로 전환합니다.

### Candidate KPI

- 중요 alarm 중 owner와 runbook이 연결된 비율
- standard request/report template 사용률
- 신규 운영자의 supervised task 완료까지 걸린 시간
- 특정 담당자 부재로 지연된 ticket 수
- 동일 질문 또는 수동 evidence 재수집 횟수
- 엔지니어당 지원 account, cluster, service 수와 quality guardrail

관리 대상 수가 늘었더라도 incident와 change failure가 함께 증가하면 확장성 성과로 인정하지 않습니다.

## 8. Decision Quality

Agent 결과는 정답률 하나로 평가하지 않습니다. 다음을 함께 봅니다.

- evidence coverage와 source freshness
- fact와 hypothesis 분리
- human correction/override와 사유
- recommendation acceptance, rejection, deferred 비율
- 실행하지 않는 선택지와 trade-off의 품질
- scope expansion, policy deny, unsafe tool attempt
- 동일 evidence에서 Reviewer가 결론을 재현할 수 있는지

높은 수락률만을 목표로 하면 운영자가 비판 없이 결과를 승인하는 automation bias가 생길 수 있습니다. 표본 독립 검토와 반대 증적을 포함합니다.

## 9. Maturity and Value Realization

| Adoption level | Near-term business value | Value not yet claimed |
| --- | --- | --- |
| Level 0: Offline | 적용 대상과 위험 파악, template/evaluation 자산화 | live 운영 개선 |
| Level 1: Read-only | 분석·보고 시간 감소, 근거 일관성 | cloud action 절감, 자율 복구 |
| Level 2: Drafting | 변경 준비와 review 처리량 개선 | Agent가 실행한 production 성과 |
| Level 3: Supervised | 저위험 반복 업무 처리량과 응답성 개선 | broad production autonomy |
| Level 4: Bounded | 검증된 use case의 24x7 제한 위임 | 전략·불가역·고위험 결정 위임 |

Level 승격은 business case만으로 승인하지 않습니다. 권한, failure mode, canary, rollback, kill switch와 audit gate를 모두 충족해야 합니다.

## 10. Portfolio Claim Pattern

### Evidence가 없을 때

> Agent-assisted operating model과 KPI를 정의했으며, live baseline과 actual은 향후 production pilot에서 측정한다.

### 측정만 완료했을 때

> 4주 pilot에서 incident evidence collection duration을 측정했으며, 서비스 범위와 표본 수를 함께 공개한다.

### 검증된 후

> 동일 service/severity 조건의 baseline과 pilot을 비교하고 Incident Commander가 검증한 결과, evidence collection median이 X에서 Y로 변화했다. change failure와 policy violation은 증가하지 않았다.

숫자, 기간, scope, sample size와 검증 owner가 없는 개선 주장은 사용하지 않습니다.
