# Role-Specific Operator Request Templates

이 디렉터리의 YAML은 운영자가 Agent에게 질문할 때 필요한 범위와 통제 항목을 빠뜨리지 않도록 돕는 **intake template**입니다. 실행 파일, cloud 권한, 승인 증명 또는 runtime API payload가 아닙니다.

## Usage

1. 요청 목적에 맞는 primary Agent 하나를 선택합니다.
2. 해당 YAML을 ticket 또는 승인된 portal의 요청 양식에 복사합니다.
3. `<...>` 값을 실제 값으로 바꾸고 불필요한 선택 항목은 제거합니다.
4. secret, credential, access key, raw customer data는 입력하지 않습니다.
5. Agent의 응답에서 facts/source, unknowns, risks, operator validation과 handoff를 확인합니다.
6. 다른 전문 영역이 필요하면 같은 요청의 권한을 넓히지 말고 별도 review/handoff를 만듭니다.

`requester identity`, account entitlement와 실제 approval은 템플릿 값을 신뢰하지 않습니다. AI Gateway 또는 protected CI/CD가 인증 token과 server-side policy에서 결정해야 합니다.

## Template Catalog

| Template | Default use | Default maturity | Cloud mutation |
| --- | --- | --- | --- |
| [architecture.yaml](architecture.yaml) | architecture option과 ADR 초안 | Level 1-2 | 금지 |
| [terraform.yaml](terraform.yaml) | Terraform patch와 plan 검토 | Level 2 | 금지 |
| [governance.yaml](governance.yaml) | OU/SCP/tag policy 설계와 simulation | Level 1-2 | 금지 |
| [security.yaml](security.yaml) | IAM/network/KMS/data risk 검토 | Level 1 | 금지 |
| [monitoring.yaml](monitoring.yaml) | metric/log 기반 상태·장애 분석 | Level 1 | 금지 |
| [operations.yaml](operations.yaml) | backup/restore/patch/EOS runbook | Level 1-2 | 금지 |
| [finops.yaml](finops.yaml) | 비용 anomaly와 최적화 후보 검토 | Level 1 | 금지 |
| [cicd.yaml](cicd.yaml) | pipeline/gate/promotion 설계와 검토 | Level 2 | 금지 |
| [reviewer.yaml](reviewer.yaml) | 독립 risk/quality/release review | Level 1-2 | 금지 |
| [documentation.yaml](documentation.yaml) | README/runbook/portfolio 초안 | Level 2 | 금지 |

## Common Field Meaning

| Field | Meaning |
| --- | --- |
| `request` | 운영자가 달성하려는 결과와 이유 |
| `control` | environment, mode, ticket, 비용/시간과 mutation 금지 경계 |
| `scope` | Agent가 읽거나 검토할 명시적 대상과 제외 범위 |
| `inputs` | source revision, evidence, metric/log query 등 허용된 입력 |
| `questions` | Agent가 답해야 할 구체적인 질문 |
| `success_criteria` | 응답을 운영자가 받아들일 조건 |
| `expected_output` | 결과 artifact와 반드시 포함할 구역 |
| `operator_validation` | 운영자가 원본 source에서 다시 확인할 항목 |
| `handoff` | 다음 담당자와 전달해야 할 artifact |

## Runtime Contract Boundary

현재 Monitoring Agent CLI는 [incident request JSON schema](../../schemas/incident-request.schema.json)와 같은 계약을 `contracts.py`에서 방어적으로 다시 검증합니다. CI smoke test는 Schema의 required field·enum과 runtime contract가 어긋나지 않는지 확인합니다. `monitoring.yaml`은 운영자가 문제를 구조화하는 상위 intake이며 CLI에 그대로 전달하지 않습니다. production runtime 요청은 Gateway가 Draft 2020-12 Schema validation을 거쳐 생성하고, 운영자는 생성된 environment, scope, query IDs를 실행 전에 확인해야 합니다.

전체 도입 단계와 사람/Agent 책임은 [Human-Led Agent Adoption Scenarios](../adoption-scenarios.md)를 따릅니다.
