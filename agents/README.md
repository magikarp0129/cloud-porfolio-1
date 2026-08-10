# Agent Directory

이 디렉터리는 Multi-Agent 운영 모델의 역할 정의와 운영자 사용 지침을 관리합니다.

현재 모델은 운영자가 역할별 template로 질문하고 결과의 근거를 검증하는 Human-led 방식입니다. Monitoring Agent의 read-only MVP만 실행 코드가 있으며, 나머지 Agent 문서는 역할·요청·산출물 계약입니다. Agent가 production에서 직접 `apply`, restart, scale, delete 또는 alarm suppression을 수행하지 않습니다.

## Start Here

- `operator-guide.md`: 운영자가 Agent를 선택하고 요청, 검토, 승인, handoff하는 전체 절차
- `adoption-scenarios.md`: 사람 주도 질의에서 제한적 업무 위임으로 발전하는 단계별 도입 모델과 시나리오
- `request-templates/`: Platform Manager부터 Documentation까지 역할별 운영자 질문 템플릿
- `../docs/agent-value/`: Agent 활용의 비즈니스 outcome, engineering KPI, 측정·보고와 scorecard
- `../docs/monitoring-alert-policy.md`: Monitoring Agent의 metric query, 지속 시간과 Warning/Critical 기준
- `../AGENTS.md`: Agent runtime model과 공통 협업 원칙

## Current Status

| 구분 | 상태 |
| --- | --- |
| 역할 정의 | Manager 1개와 전문 Agent 10개, 총 11개 역할 문서화 완료 |
| 요청 template | 11개 역할별 intake template 제공 |
| 운영 흐름 | 요청, 승인, handoff, session 재개 절차 정의 |
| 실행 가능한 MVP | Monitoring Agent read-only evidence collector |
| 로컬 검증 | 계약·보안·Terraform boundary 시험 25개 통과 |
| Target | Corporate IdP, 중앙 AI Gateway, Tool Broker, live connector와 supervised workflow |

## Role Definitions

| File | Role |
| --- | --- |
| `platform-manager-agent.md` | 요청 triage, 조직 배정, dependency, handoff와 통합 상태 관리 |
| `architecture-agent.md` | Architecture decision과 module boundary |
| `terraform-agent.md` | Terraform code와 environment root |
| `governance-agent.md` | Organizations, OU, SCP, Tag Policy |
| `security-agent.md` | IAM, KMS, network, data protection |
| `monitoring-agent.md` | Metrics, logs, alarms, incident analysis |
| `operations-agent.md` | Backup, restore, scheduling, patch, EOS/EOL |
| `finops-agent.md` | Budget, anomaly, rightsizing, commitment |
| `cicd-agent.md` | Validation, plan, approval, promotion |
| `reviewer-agent.md` | Independent risk and quality review |
| `documentation-agent.md` | README, runbook, portfolio artifacts |

## Organization

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

Manager Agent는 cross-domain 요청을 분해하고 조직 간 handoff를 조정합니다. 단일 domain 요청은 해당 전문 Agent를 primary로 바로 선택할 수 있습니다. Security와 Reviewer는 Manager의 조정 아래에서도 independent finding을 accountable human에게 직접 escalation할 수 있습니다.

역할 문서는 Agent가 무엇을 담당하는지 정의하고, `operator-guide.md`는 운영자가 해당 Agent를 어떻게 사용해야 하는지 정의합니다. 초기 운영은 `adoption-scenarios.md`의 Human-led, Agent-assisted 모델을 따릅니다. 운영자는 cross-domain 요청이면 Manager 템플릿, 단일 domain 요청이면 전문 Agent 템플릿을 선택하고, 결과를 검증한 뒤 사람 승인과 protected CI/CD로만 변경을 진행합니다.

Terraform 관련 요청에서는 [Terraform Structure](../terraform/README.md)의 root/state ownership과 apply order를 먼저 확인합니다. 문서 추가와 canonical source는 [문서 디렉터리 안내](../docs/README.md)를 따릅니다.
