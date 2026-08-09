# Reports Library

목적: 포트폴리오에서 재사용할 운영 보고서 양식과 공개 가능한 비운영 예시를 관리합니다.

상태: 템플릿 및 sanitized simulation example

Canonical scope: 보고서의 파일 구조, 작성 순서와 공개 가능한 예시만 소유합니다. KPI 정의·보고 주기·보존·승인 기준은 [`docs/agent-value/measurement-reporting.md`](../docs/agent-value/measurement-reporting.md)가 소유합니다.

## Directory Layout

```text
reports/
├── README.md
├── templates/
│   ├── monthly-platform-report.md
│   └── incident-report.md
└── examples/
    ├── monthly/2026-07-platform-monthly.example.md
    └── incidents/INC-2026-0142.example.md
```

## Report Catalog

| Report | Purpose | Owner and review | Source of truth |
| --- | --- | --- | --- |
| Monthly platform report | 신뢰성, 변경, 보안, 운영, 비용과 개선 조치를 한 기간 단위로 검토 | Platform/Operations 작성, Security·FinOps·service owner 검토 | monitoring, ticket, CI/CD, backup, security, CUR evidence |
| Incident report | 영향, timeline, 사실·가설·원인, 복구와 재발 방지 조치를 한 사건 단위로 기록 | Incident Commander accountable, Monitoring/Operations 작성 지원 | ticket, monitoring query, change event, audit artifact |
| Agent value scorecard | Agent의 engineering/business outcome과 안전성을 월간·분기 검토 | AI Platform + human owner | [`scorecard-template.md`](../docs/agent-value/scorecard-template.md) |

## Evidence Boundary

- `reports/templates/`는 빈 양식이며 성과나 운영 증적이 아닙니다.
- `reports/examples/`는 가상 account·service와 fixture를 사용한 `simulation`입니다.
- 실제 장애의 raw log, customer data, credential, prompt/tool trace와 승인 원본은 Git에 저장하지 않습니다.
- 실제 보고서는 `request_id`, `trace_id`, ticket, UTC window, source version, evidence reference와 human sign-off를 연결합니다.
- 값이 없으면 추정하지 않고 `not_available`과 사유를 기록합니다.
- `status=simulation`, `partial`, `blocked`인 보고서는 production KPI 성공 건수에 포함하지 않습니다.

## Relationship to Examples and Schemas

```text
examples/incidents/*.json
  └─ sanitized request/evidence fixture
       └─ Monitoring Agent simulation
            ├─ machine report.json → schemas/incident-report.schema.json
            └─ human report.md → reports/examples/incidents/
```

`examples/`는 실행 가능한 테스트 입력이고 `reports/examples/`는 사람이 읽는 포트폴리오 예시입니다. 같은 raw evidence를 두 위치에 복제하지 않습니다.

## Publishing Rules

1. 해당 템플릿을 승인된 ticket/artifact workspace로 복사합니다.
2. 모든 `<...>`를 실제 값 또는 `not_available`과 사유로 교체합니다.
3. 사실, 가설, 미확인 사항과 제안을 분리합니다.
4. evidence ID는 원본이 아니라 승인된 immutable reference나 hash를 가리킵니다.
5. 실행 조치는 제안과 실제 실행을 분리하고 실행자·승인·시각을 기록합니다.
6. Security/PII 검토와 accountable human sign-off 후 배포합니다.

