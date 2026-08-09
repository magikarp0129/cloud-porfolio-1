# Human-Led Agent Adoption Scenarios

## 1. Decision

이 포트폴리오의 초기 Agent 운영 모델은 **Human-led, Agent-assisted**입니다. 운영자가 역할별 요청 템플릿으로 질문하고, Agent가 근거와 선택지를 정리하며, 운영자가 결과를 검증하고 최종 결정을 내립니다.

초기 단계에서 Agent에게 AWS 운영을 직접 맡기지 않습니다. Agent가 만든 분석, 코드, plan, runbook은 제안 artifact이며 ticket, 독립 검토, 사람 승인과 protected CI/CD를 통과해야 실제 변경으로 이어집니다.

장기 목표도 모든 운영을 일괄 자율화하는 것이 아닙니다. 충분한 증적이 축적된 **저위험·반복 가능·복구 가능한 업무**만 업무별로 제한적 위임합니다. 보안 경계 변경, 데이터 삭제, 장애 전환, 비용 약정, production 승인과 같은 고위험 결정은 사람의 책임으로 유지합니다.

## 2. Adoption Principles

1. Agent가 아니라 **업무 유형별로** 성숙도를 평가합니다. 같은 Monitoring Agent라도 로그 요약은 Level 1, 보고서 자동 생성은 Level 2, 서비스 재시작은 허용되지 않을 수 있습니다.
2. 운영자 질문은 역할별 템플릿에서 시작합니다. 범위, 환경, ticket, 데이터 등급, 성공 기준과 금지 사항이 없는 요청은 실행하지 않습니다.
3. 조회와 변경을 분리합니다. 장애 분석 ticket에서 영구 수정이나 배포까지 암묵적으로 확장하지 않습니다.
4. Agent의 결론보다 근거를 우선합니다. 조회 시각, query ID, source revision, plan hash와 불확실성을 artifact에 남깁니다.
5. Agent가 자신의 권한을 확대하거나 자신이 만든 변경을 승인하지 못하게 합니다.
6. live system 접근은 최소 권한, short-lived credential, server-side allowlist와 감사 로그를 전제로 합니다.
7. 모호한 범위, 오래된 증적, 정책 위반, 예상 밖 변경이나 비용이 발견되면 fail closed하고 운영자에게 handoff합니다.

## 3. Maturity Model

| Level | Operating model | Agent capability | Human responsibility | Promotion evidence |
| --- | --- | --- | --- | --- |
| Level 0: Offline evaluation | fixture, 문서, 비운영 repository로 평가 | 템플릿 해석, 분류, 초안, 모의 분석 | 정답 세트와 평가 기준 작성 | 반복 평가 결과, 데이터 유출·도구 오용 없음 |
| Level 1: Read-only advisory | 운영자가 질문하고 Agent가 승인된 정보만 조회 | 사실, 가설, 위험, 선택지, 추가 확인 항목 제시 | 근거 검증, 판단, 모든 실행 | query audit, source coverage, 사람 수정 이력 |
| Level 2: Artifact drafting | branch/patch/plan/runbook을 생성 | 변경 초안과 검증 결과 작성, handoff package 생성 | review, 승인, merge, deploy | 검토 통과율, 재작업률, plan 정확도, rollback 품질 |
| Level 3: Supervised workflow | 사전 정의된 pipeline 단계를 호출 | 비운영 또는 저위험 작업을 policy gate 뒤에서 수행 | 실행 전 승인 또는 명시적 start, 결과 확인 | tool allowlist, canary, 자동 중지, 사후 검증, 완전한 감사 추적 |
| Level 4: Bounded delegation | 승인된 use case에 한해 제한적 자동 처리 | 임계값과 runbook 안에서 실행·검증·rollback 또는 중지 | 정책 소유, 예외 승인, 정기 권한 재인증 | 충분한 성공/실패 rehearsal, rollback 증적, SLO, kill switch, 독립 audit |

Level은 달력이나 Agent 이름으로 승격하지 않습니다. `prod EKS 로그 조회`, `dev idle resource scheduling`처럼 use case와 environment 조합별로 별도 승인합니다. 한 단계의 종료 조건이 충족되지 않으면 다음 단계의 tool permission을 부여하지 않습니다.

### Current Repository Position

| Area | Current level | Evidence and boundary |
| --- | --- | --- |
| Monitoring incident triage | Level 1 MVP | server-owned query catalog를 사용하는 read-only evidence collector가 구현되어 있습니다. cloud mutation은 없습니다. |
| Architecture, Governance, Security, Operations, FinOps analysis | Level 0-1 operating model | 역할과 템플릿은 정의하지만 공통 AI Gateway 및 live connector는 구현되지 않았습니다. |
| Terraform, CI/CD, Documentation artifact drafting | Level 2 target workflow | patch, plan, 문서 초안을 만들 수 있는 절차를 정의합니다. merge, deploy, `apply`는 사람과 protected CI/CD 책임입니다. |
| Supervised or delegated cloud operation | Not implemented | Level 3-4 Tool Broker, runtime policy enforcement, canary/rollback automation 증적이 없습니다. |

현재 수준을 future target처럼 표현하지 않습니다. 구현 상태는 [AI Platform](../docs/ai-platform.md)과 [Read-Only Agent Incident Triage](../docs/agent-incident-triage.md)의 evidence를 기준으로 판단합니다.

## 4. Day-One Operator Interaction

```text
운영자 ticket + 역할별 템플릿
            |
            v
Agent의 read / draft / plan / review 결과
            |
            v
운영자의 근거·범위·위험 검증
            |
            +---- 추가 질문 또는 반려
            |
            v
PR / change artifact + 독립 Reviewer
            |
            v
사람 승인 + protected CI/CD
```

운영자는 [request-templates](request-templates/README.md)에서 primary Agent의 템플릿을 복사해 ticket 또는 승인된 portal에 입력합니다. 템플릿은 질문을 구조화하는 intake 문서이며 배포 명령, 접근 권한 또는 승인 증명이 아닙니다.

Agent 응답에는 최소한 다음 구역이 있어야 합니다.

- `Facts`: source와 시각으로 확인된 사실
- `Unknowns`: 확인할 수 없거나 최신성이 보장되지 않는 정보
- `Hypotheses`: 사실과 구분된 추론 및 반증 방법
- `Risks`: 보안, 가용성, 비용, 규정, 복구 위험
- `Options`: 아무것도 하지 않는 선택지를 포함한 대안과 trade-off
- `Recommendation`: 권고안과 적용 조건
- `Operator validation`: 사람이 확인해야 할 명령, dashboard 또는 artifact
- `Handoff`: 다음 담당자, 입력 artifact, stop condition

운영자는 응답을 그대로 실행하지 않고 다음을 확인합니다.

1. 환경, account, region, resource와 시간 범위가 ticket과 일치하는가?
2. 사실과 가설이 분리되었고 각 사실에 추적 가능한 근거가 있는가?
3. 데이터 분류, secret/PII, 고객 데이터 처리 기준을 지켰는가?
4. 변경안의 create/update/replace/destroy, 비용, blast radius가 명확한가?
5. rollback 또는 forward fix 책임자와 사후 확인 지표가 있는가?
6. Agent가 요청 범위를 넘어 권한, 승인 또는 실행을 주장하지 않는가?

## 5. Scenario A: Daily Service Health Review

**Purpose:** 운영자가 반복적인 상태 확인 시간을 줄이되 장애 판단과 조치는 계속 소유합니다.

**Primary Agent:** Monitoring  
**Mode:** `read`  
**Current maturity:** Level 1

1. 운영자는 `monitoring.yaml`을 사용해 service, environment, time window, symptom과 허용된 query를 지정합니다.
2. Monitoring Agent는 승인된 metric/log source에서 timeline, 이상 신호, missing evidence를 수집합니다.
3. Agent는 정상/비정상을 단정하는 대신 사실, baseline 대비 차이, 가능한 원인과 다음 query를 반환합니다.
4. 운영자는 dashboard와 원본 query를 표본 검증하고 service owner에게 상태를 공유합니다.
5. 변경이 필요하면 incident ticket과 별도로 change ticket을 생성해 Operations 또는 Terraform Agent에 handoff합니다.

**Done:** 근거 시각, query ID, 관측 공백과 운영자 판단이 ticket에 남아 있습니다.  
**Forbidden:** Agent의 alarm disable, workload restart, scaling, log retention 변경.

현재 실행 가능한 예시는 [prod API 5xx incident request](../examples/incidents/prod-api-5xx-request.json)입니다. 이 JSON은 runtime contract용이며 운영자 intake YAML을 그대로 `agentctl`에 전달하지 않습니다.

## 6. Scenario B: Incident Triage

**Purpose:** Agent가 증적 수집과 가설 정리를 지원하지만 Incident Commander가 판단과 복구를 통제합니다.

**Primary Agent:** Monitoring  
**Supporting Agent:** Operations, Security  
**Modes:** `read` 후 필요하면 별도 `draft`

1. Incident Commander가 심각도, 영향, 시작 시각, 대상 서비스와 안전상 금지할 조치를 선언합니다.
2. Monitoring Agent가 변경 이력, metric, log, alarm state를 수집해 공통 timeline을 만듭니다.
3. Security signal이 있으면 동일 증적을 Security Agent에 별도 `review` 요청으로 전달합니다.
4. Operations Agent는 승인된 runbook의 적용 조건, 위험, 되돌리기와 확인 항목을 제시합니다.
5. Incident Commander가 복구 선택지를 결정하고 권한 있는 운영자가 기존 절차 또는 protected automation으로 실행합니다.
6. Monitoring Agent가 사후 지표를 확인하고 Documentation Agent가 incident record를 정리합니다.
7. 영구 수정은 새로운 change ticket과 PR로 분리합니다.

**Stop conditions:** 서로 충돌하는 resource identity, 잘못된 시간 범위, PII 노출, 증적 부재, runbook precondition 불일치.  
**Forbidden:** Agent가 severity를 낮추거나 incident를 종료하고, 승인 없이 failover/restart/delete를 수행하는 행위.

## 7. Scenario C: EKS Add-on or Platform Change

**Purpose:** 운영자가 변경 설계와 검증 부담을 줄이면서 production 적용 책임을 유지합니다.

**Primary Agent:** Terraform  
**Supporting Agent:** Architecture, Security, Reviewer, CI/CD, Monitoring  
**Modes:** `draft` -> `review` -> `plan`

1. 운영자가 `terraform.yaml`에 현재/목표 version, environment, 호환성 제약, maintenance window, success metric과 rollback owner를 입력합니다.
2. Terraform Agent가 source revision을 고정하고 code patch를 작성합니다. AWS API나 cluster에 적용하지 않습니다.
3. Architecture Agent가 state/module ownership을, Security Agent가 IAM·network·KMS 변경을 검토합니다.
4. CI/CD가 fmt, validate, policy scan과 speculative plan을 만들고 plan hash를 ticket에 연결합니다.
5. Reviewer Agent가 replace/destroy, add-on compatibility, PDB/drain, rollback과 missing test를 독립 검토합니다.
6. 운영자가 dev와 stg의 실제 검증 결과를 확인한 뒤 production change approval을 요청합니다.
7. protected CI/CD가 승인된 artifact만 적용하고 Monitoring Agent가 사후 SLI와 alarm을 확인합니다.

**Done:** code review, immutable plan, 사람 승인, 환경별 promotion evidence와 post-change result가 연결됩니다.  
**Forbidden:** Agent가 latest version을 자동 선택하거나 `prod`에서 직접 `terraform apply`, `kubectl drain`, add-on update를 수행하는 행위.

## 8. Scenario D: Monthly FinOps Review

**Purpose:** 비용 분석과 후보 발굴을 자동화하되 서비스 수준, 구매와 삭제 결정을 사람에게 둡니다.

**Primary Agent:** FinOps  
**Supporting Agent:** Operations, Terraform, Reviewer  
**Mode:** `read`, 이후 승인된 항목만 별도 `draft`

1. 운영자는 `finops.yaml`에 billing period, account/OU, cost allocation tag, 비교 baseline과 제외 항목을 입력합니다.
2. FinOps Agent는 증가 요인, anomaly, idle 후보, rightsizing 및 commitment 후보를 근거와 함께 분리합니다.
3. Service owner가 성능, resilience, RTO/RPO와 예정된 사업 변화를 확인해 후보를 수락 또는 반려합니다.
4. 수락된 schedule 또는 rightsizing 항목만 새로운 change ticket으로 Terraform/Operations Agent에 전달합니다.
5. Savings Plan/Reserved Instance 구매는 재무 및 designated approver가 별도 승인합니다.
6. 적용 후 실제 절감액, 성능 영향과 recommendation accuracy를 다음 review에 반영합니다.

**Forbidden:** Agent의 리소스 stop/delete, commitment 구매, budget threshold 변경, tag 없는 비용의 임의 귀속.

## 9. Future Scenario: Supervised Low-Risk Automation

Level 3의 첫 후보는 `dev`의 검증 가능한 반복 작업처럼 blast radius가 작은 use case로 제한합니다. 예를 들어 승인된 schedule에 따라 비업무 시간의 개발 리소스를 조정하는 workflow는 다음 조건이 모두 있을 때만 검토할 수 있습니다.

- service owner가 대상 resource allowlist와 제외 기간을 소유합니다.
- Agent는 raw AWS API가 아니라 입력이 고정된 Tool Broker action만 호출합니다.
- AI Gateway가 identity, environment, ticket, maintenance window, cost와 action policy를 server side에서 검증합니다.
- 실행 전 dry run, 대상 목록, 예상 영향과 rollback을 운영자가 확인합니다.
- canary 대상부터 실행하고 health check 실패 시 확장을 중지합니다.
- 모든 tool call에 `request_id`, `trace_id`, actor, input hash와 결과를 남깁니다.
- break-glass disable과 사람의 즉시 중지 경로가 있습니다.
- Agent가 scope를 확대하거나 다른 action을 합성하지 못합니다.

Level 3에서도 `prod` 변경을 자동 승인하지 않습니다. Level 4 검토는 use case별 성공·실패 rehearsal, 독립 audit와 rollback evidence가 축적된 이후 별도 architecture decision으로 진행합니다.

## 10. Promotion Gates

| Gate | Required questions |
| --- | --- |
| Business ownership | service owner와 최종 책임자가 명확한가? 자동화하지 말아야 할 결정은 무엇인가? |
| Input quality | 입력 source, freshness, missing-data 동작과 schema가 정의되어 있는가? |
| Evaluation | 정상, 경계, 실패, 공격적 입력에 대한 정답/허용 범위가 있는가? |
| Permission | resource, action, environment, 시간과 호출 횟수가 server side에서 제한되는가? |
| Change safety | dry run, canary, idempotency, concurrency control과 blast radius limit가 있는가? |
| Recovery | rollback 또는 안전한 중지 절차를 실제로 rehearsal했는가? |
| Approval | requester, reviewer, approver, executor 분리가 강제되는가? |
| Audit | prompt, model/tool version, source, decision, approval, action과 결과가 연결되는가? |
| Operations | SLO, alert, on-call, kill switch, fallback manual procedure가 있는가? |
| Cost and data | token/tool budget, 데이터 등급, retention, masking과 residency가 적용되는가? |

모든 gate를 문서로만 통과했다고 간주하지 않습니다. fixture evaluation, non-production rehearsal, 실패 주입과 실제 audit artifact로 검증합니다.

## 11. Metrics and Review Cadence

초기 단계의 성공 기준은 “자동 실행 수”가 아니라 운영 품질과 통제 가능성입니다.

- 근거가 연결된 사실의 비율과 stale/missing source 검출률
- 운영자가 수정하거나 반려한 recommendation의 비율과 사유
- incident evidence 수집 시간, change review lead time, 반복 문서 작성 시간
- false positive/negative, 누락된 risk와 예상하지 않은 변경 수
- secret/PII 노출, 권한 초과, 승인 우회, scope expansion 건수
- plan과 실제 change의 차이, rollback 준비도와 사후 검증 통과율
- request당 model/tool 비용, timeout과 재시도율
- `request_id`에서 source, decision, approval, action, outcome까지 연결되는 audit coverage

Reviewer, Security, Governance 담당자는 정기적으로 실패 사례와 human override를 검토합니다. 권한 초과, audit 단절, 복구 실패 또는 data handling 위반이 발생하면 해당 use case를 이전 Level로 내리고 원인이 해결될 때까지 tool access를 중지합니다.

## 12. Responsibility Boundary

| Role | Accountable for | Must not delegate to Agent |
| --- | --- | --- |
| Operator / Incident Commander | 요청 범위, 현황 판단, 실행 선택, 결과 확인 | incident 종료, 불가역 복구 결정 |
| Service owner | SLO, architecture constraint, maintenance와 risk acceptance | business impact와 availability trade-off |
| Designated approver | production/organization 변경 승인 | 자신의 identity와 승인 권한 판단 |
| Domain Agent | 근거 기반 분석, 초안, 검증 항목, handoff | 권한 확대, self-approval, 범위 밖 실행 |
| Reviewer Agent + human reviewer | 독립적인 누락·위험·증적 검토 | 원안 작성자와 동일한 승인 주체가 되는 것 |
| Protected CI/CD / Tool Broker | immutable artifact 실행, policy enforcement, audit | 자연어만으로 대상/action을 결정하는 것 |

## 13. Related Documents

- [Agent Operator Guide](operator-guide.md)
- [Role-specific Request Templates](request-templates/README.md)
- [AI Platform](../docs/ai-platform.md)
- [Identity and Access](../docs/identity-access.md)
- [Read-Only Agent Incident Triage](../docs/agent-incident-triage.md)
- [Agent Collaboration and Runtime Model](../AGENTS.md)
