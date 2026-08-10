# Agent Business Value and Engineering Outcomes

## Purpose

이 디렉터리는 AI Agent를 도입했다는 활동 자체가 아니라, Cloud/Infra Engineering과 비즈니스에 어떤 결과를 만들었는지 정의하고 검증하는 canonical source입니다.

Agent 호출 수, 생성한 코드 줄 수, 보고서 수는 단독으로 성과가 아닙니다. 모든 가치 주장은 다음 연결을 보여야 합니다.

```text
Agent capability
  -> engineering behavior or control change
  -> service/operational outcome
  -> business outcome
  -> evidence and accountable validation
```

## Current Evidence Boundary

| Area | Current status | Portfolio claim boundary |
| --- | --- | --- |
| Human-led adoption model | Defined | 운영자가 질문·검증·승인하는 모델을 설명할 수 있음 |
| Role-specific request templates | Implemented as documentation | Manager 1개와 전문 Agent 10개, 총 11개 역할의 intake 표준을 보여줄 수 있음 |
| Monitoring incident report | Read-only MVP implemented | fixture 기반 report 생성과 schema 검증을 보여줄 수 있음 |
| Common business/engineering KPI | Defined in this directory | 측정 방법은 설명할 수 있으나 아직 실적 수치로 주장할 수 없음 |
| Unified production scorecard | Target | live Gateway, Tool Broker, ticket/CI/billing 연계 후 구현 필요 |
| Realized financial or reliability impact | Not measured | baseline과 검증된 actual이 없으므로 절감액·MTTR 개선을 사실로 표현하지 않음 |

`Target`, `Example`, `<baseline>` 값을 실제 성과처럼 사용하지 않습니다. portfolio에는 현재 구현 증적과 향후 측정 설계를 구분해 표시합니다.

## Documents

| Document | Purpose |
| --- | --- |
| [Business Outcomes](business-outcomes.md) | 서비스 연속성, delivery, 비용, risk, 조직 확장성의 가치 정의 |
| [Engineering Outcomes](engineering-outcomes.md) | Incident, change, reliability, EKS, security, FinOps, knowledge KPI catalog |
| [Measurement and Reporting](measurement-reporting.md) | event 연결, report 종류, 검증, 보존과 책임 경계 |
| [Scorecard Template](scorecard-template.md) | 월간 또는 분기 성과 보고서 작성 양식 |

## Operating Principles

1. **Engineering evidence first:** Agent 기능에서 바로 매출·절감액으로 점프하지 않습니다.
2. **Baseline before target:** 도입 전 동일 조건의 기준값을 확보한 뒤 목표와 actual을 비교합니다.
3. **Realized over recommended:** 추천 절감액이나 예상 회피 비용이 아니라 승인·적용·검증된 결과를 사용합니다.
4. **Normalized comparison:** traffic, 계절성, 신규 workload, 가격과 조직 범위 변화를 보정합니다.
5. **Human accountability:** service owner, operations owner, FinOps 또는 risk owner가 결과를 검증합니다.
6. **Safety is an outcome:** 권한 초과, 승인 우회, data leak 0건과 human override 품질을 함께 측정합니다.
7. **Use-case maturity:** Agent 전체가 아니라 업무와 environment별로 가치와 위험을 평가합니다.

## Value Claim Status

| Status | Meaning | Allowed wording |
| --- | --- | --- |
| `defined` | KPI, 계산식, owner가 정의됨 | “측정 기준을 정의했다” |
| `instrumented` | 필요한 event/source가 연결됨 | “측정 가능한 구조를 구현했다” |
| `measured` | baseline과 actual sample이 있음 | “관측 기간에 X를 측정했다” |
| `validated` | domain/business owner가 보정과 attribution을 승인함 | “검증 결과 X% 개선했다” |
| `realized` | 운영 또는 재무 결과가 반복 확인됨 | “실현 절감액/지속 개선으로 확인됐다” |

현재 이 디렉터리의 공통 KPI는 대부분 `defined` 상태입니다. Monitoring fixture report는 기술 경로를 검증하지만 live operational outcome은 아닙니다.

## Ownership

| Responsibility | Accountable role |
| --- | --- |
| Business objective and acceptable trade-off | Service owner / Business owner |
| Engineering KPI definition and source quality | Platform/Operations/Monitoring owner |
| Security, privacy and compliance outcome | Security/Governance owner |
| Cost normalization and realized saving | FinOps/Finance owner |
| Agent quality, human correction and policy violation | AI Platform owner / Reviewer |
| Portfolio wording and source linkage | Documentation Agent + human reviewer |

Agent는 자신의 성과를 스스로 승인하지 않습니다.

## Related Sources

- [Human-Led Agent Adoption Scenarios](../../agents/adoption-scenarios.md)
- [Multi-Agent Operator Guide](../../agents/operator-guide.md)
- [Role-Specific Request Templates](../../agents/request-templates/README.md)
- [Read-Only Agent Incident Triage](../agent-incident-triage.md)
- [Enterprise AI Platform and Agent Operations](../ai-platform.md)
