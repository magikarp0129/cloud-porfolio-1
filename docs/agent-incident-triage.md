# Read-Only Agent Incident Triage

## Purpose and current boundary

이 구현은 운영 장애에서 Monitoring Agent가 사용할 **read-only evidence collector MVP**입니다. 운영자가 제출한 incident request를 검증하고, repository에 versioning된 query catalog만 실행한 뒤 사실, 가설, evidence gap을 JSON과 Markdown으로 남깁니다.

현재 구현되는 범위:

- `agent_id=monitoring`, `mode=read`, incident ticket, environment, region, service와 시간 범위 검증
- caller가 넣은 `user_id`, role, account, approval 값 거부
- AWS caller account와 server-side environment registry 일치 확인
- CloudWatch metric과 제한된 CloudWatch Logs Insights query
- Kubernetes node, Pod, workload controller와 event의 선택 필드 조회
- Prometheus `query_range`의 range, step, series, response 크기 제한
- Grafana Viewer API의 dashboard metadata 조회
- secret, token, AWS key pattern, email, 전화번호 마스킹
- fact, deterministic hypothesis, evidence gap, handoff를 포함한 report와 audit event 생성

현재 구현하지 않는 범위:

- 실제 AI Gateway, Corporate IdP 인증, central Tool Broker와 model invocation
- Agent에 의한 restart, scale, rollback, drain, failover, alarm suppression
- Kubernetes Secret, ConfigMap, Pod log, environment, `describe`, `exec`, `attach`, port-forward
- 자유 형식 shell, AWS API, PromQL, Logs Insights query
- CloudTrail account-wide search, SSM session/command, raw customer payload 수집

따라서 이 collector의 report는 향후 AI Gateway가 Monitoring Agent에 제공할 sanitized context이거나, 현재 운영자가 직접 검토할 incident artifact입니다. Agent가 incident commander나 production executor가 되는 것은 아닙니다.

## Components

```text
Incident request JSON
        │ contract and scope validation
        ▼
scripts/agent/agentctl.py
        │ fixed query IDs only
        ├── CloudWatch metric/Logs Insights adapter
        ├── Kubernetes selected-field adapter
        ├── Prometheus bounded query_range adapter
        └── Grafana dashboard-metadata adapter
        │
        ▼
redaction → facts/hypotheses/gaps → report.json + report.md + audit.jsonl
```

| Path | Purpose |
| --- | --- |
| `agent-runtime/src/cloud_portfolio_agents/contracts.py` | 요청, 환경 registry, 비용·시간·query 범위 검증 |
| `agent-runtime/src/cloud_portfolio_agents/adapters/` | typed read-only data source adapters |
| `agent-runtime/src/cloud_portfolio_agents/redaction.py` | output 마스킹 |
| `agent-runtime/src/cloud_portfolio_agents/triage.py` | evidence 정규화와 deterministic triage |
| `schemas/incident-request.schema.json` | portal/gateway 입력 schema |
| `schemas/incident-report.schema.json` | downstream handoff 출력 schema |
| `config/monitoring/runtime.example.json` | 환경 registry와 versioned query catalog 예제 |
| `config/monitoring/alert-policy.example.json` | metric query, Warning/Critical, 지속 시간과 missing-data 기준 |
| `docs/monitoring-alert-policy.md` | 운영자가 검토하는 공통 지표·severity 정책과 조정 절차 |
| `terraform/modules/monitoring-agent-access` | 전용 AWS diagnostic role과 deny guardrail |

## Safe evaluation with fixtures

외부 credential이나 network 없이 전체 요청·마스킹·보고서 경로를 검증합니다.

```bash
python3 scripts/agent/agentctl.py validate \
  --request examples/incidents/prod-api-5xx-request.json \
  --config config/monitoring/runtime.example.json

python3 scripts/agent/agentctl.py run monitoring \
  --request examples/incidents/prod-api-5xx-request.json \
  --config config/monitoring/runtime.example.json \
  --fixture examples/incidents/prod-api-5xx-evidence.json \
  --simulation \
  --output-dir /tmp/INC-2026-0142
```

`report.json`, `report.md`, `audit.jsonl`이 생성됩니다. fixture mode는 `--simulation`을 필수로 요구하며 report와 audit에 `simulation=true`, `status=simulation`을 기록합니다. AWS CLI, `kubectl`, Prometheus, Grafana에는 연결하지 않고 tool call 수를 0으로 기록하므로 운영 evidence로 사용할 수 없습니다.

## Live environment setup

### 1. Configure the server-side registry

`runtime.example.json`을 승인된 deployment repository의 환경별 설정으로 복사하고 다음 placeholder를 실제 값으로 교체합니다.

- 환경별 AWS account ID와 Region
- 허용 service와 cluster, namespace, ALB dimension, log group을 묶은 service inventory
- EKS read-only context
- query template에서 사용하는 ALB dimension과 승인 log group
- Prometheus/Grafana를 사용할 경우 정확한 HTTPS host allowlist

Request는 account ID, endpoint URL, query text를 지정하지 않습니다. request의 resource identifier도 portal 또는 Tool Broker가 service inventory에서 생성하는 것이 목표입니다. 현재 로컬 MVP에서는 request scope 값을 정규식과 environment registry로 제한하지만, production Gateway에서는 service-to-resource registry와 다시 대조해야 합니다.

Live CLI는 config를 호출자가 임의 교체하지 못하도록 server-owned `AGENT_CONFIG_ROOT` 아래의 regular file만 허용하고, CI가 승인한 SHA-256을 `AGENT_POLICY_SHA256`으로 주입해야 실행됩니다. 두 값이 없거나 config가 symlink이거나 hash가 다르면 외부 tool을 호출하기 전에 실패합니다. Simulation은 config hash를 report에 기록하지만 live authorization으로 취급하지 않습니다.

### 2. Create the dedicated diagnostic role

환경 root의 다음 변수에 **central Tool Broker의 정확한 IAM principal ARN**과 승인 workload log group ARN을 설정합니다.

```hcl
monitoring_agent_trusted_principal_arns = [
  "arn:aws:iam::<ai-platform-account>:role/central-agent-tool-broker",
]

monitoring_agent_additional_log_group_arns = [
  "arn:aws:logs:ap-northeast-2:<workload-account>:log-group:/workload/prod/application-prod/example-api",
]
```

`terraform plan`과 보안 review 후 protected CI/CD로 적용합니다. 기존 security audit role, EKS admin Access Entry, Grafana admin password를 재사용하지 않습니다.

`monitoring-agent-access`는 metric/alarm/dashboard read, 지정 log group의 Logs Insights, EKS describe만 허용합니다. `logs:Unmask`, Secret/Parameter/KMS read, SSM interactive access, role chaining, alarm suppression과 주요 production mutation은 명시적으로 거부합니다.

### 3. Establish Kubernetes read access

Foundation state는 diagnostic role을 EKS group `monitoring-agent-readers`에 연결합니다. Platform state는 이 group에 다음 권한만 부여합니다.

- cluster: node `get`, `list`
- application namespace: Pod/event/PVC와 선택된 workload/HPA/PDB의 `get`, `list`

Secret, ConfigMap, Pod log, RBAC object, service account, exec/attach/port-forward와 모든 write verb는 포함하지 않습니다. EKS endpoint가 private이므로 Tool Broker runner는 승인된 VPC/VPN/Direct Connect 경로 안에서 실행해야 합니다.

### 4. Run live triage

Tool Broker가 server-generated request ID를 STS SourceIdentity와 RoleSessionName에 동일하게 설정해 15분 이하의 환경별 diagnostic session을 발급하고 `AWS_REGION`, AWS credential, read-only kube context를 실행 context에 주입한 뒤 실행합니다. Runtime은 `GetCallerIdentity`의 account, role, session name을 registry와 request ID에 대조합니다. 또한 EKS `DescribeCluster`의 ARN·endpoint와 kubeconfig endpoint를 비교하고 kubeconfig가 같은 cluster의 AWS exec authentication을 사용하는지 확인합니다. credential 자체를 request, config, command history에 넣지 않습니다.

다음 환경변수는 운영자가 요청마다 만드는 값이 아니라 Tool Broker deployment가 server-side로 주입합니다.

```text
AGENT_CONFIG_ROOT=/approved-config
AGENT_POLICY_SHA256=<CI가 승인한 prod-monitoring.json SHA-256>
```

```bash
python3 scripts/agent/agentctl.py run monitoring \
  --request /secure/requests/INC-2026-0142.json \
  --config /approved-config/prod-monitoring.json \
  --output-dir /secure-artifacts/INC-2026-0142
```

Prometheus 또는 Grafana를 활성화할 경우 endpoint와 Viewer token은 config에 지정한 환경변수 이름으로만 주입합니다. CLI는 HTTPS와 exact host allowlist를 검증하며 Grafana data-source proxy는 호출하지 않습니다.

HTTP adapter는 redirect를 따르지 않고 연결 전 DNS 결과에서 loopback, link-local, unspecified, multicast 주소를 차단합니다. DNS rebinding의 최종 방어는 Tool Broker subnet의 firewall/egress allowlist와 IMDS 차단으로 적용합니다.

## Query catalog rules

1. 운영자는 request에 query text나 command를 넣지 않고 승인된 `requested_queries` ID만 선택합니다.
2. Logs Insights에서 `unmask`와 `SOURCE`는 거부합니다.
3. Logs query는 approved log groups와 `allowed_fields`를 반드시 지정합니다.
4. Application query는 집계를 우선하고 raw `@message`를 기본 출력으로 허용하지 않습니다.
5. Prometheus query는 template에 두되 request의 service, namespace 등 안전한 값만 치환합니다.
6. query 추가는 PR, Monitoring/Security review, policy version 증가와 fixture test를 거칩니다.
7. severity는 query 결과의 순간 최대값이 아니라 승인된 alert policy의 threshold, 지속 시간, M/N과 minimum traffic으로 평가합니다.
8. report에는 policy version, 관측 sample 수, breaching datapoint 수와 missing-data 처리를 남깁니다.

현재 MVP는 evidence를 안전하게 수집하는 단계이며 `alert-policy.example.json`을 자동 평가해 severity를 재분류하는 rule evaluator는 아직 연결되지 않았습니다. 따라서 운영자는 원본 dashboard와 policy 조건을 대조하고, Agent가 요청에 적힌 incident severity를 독립적으로 입증한 것으로 해석하지 않습니다.

## Output and handoff

Report status 의미:

| Status | Meaning |
| --- | --- |
| `complete` | 요청된 source가 성공했고 evidence를 생성함 |
| `partial` | 일부 source가 실패했지만 다른 source evidence가 있음 |
| `blocked` | 사용 가능한 정상 evidence가 없음 |
| `simulation` | fixture 기반 비운영 결과이며 live evidence로 사용할 수 없음 |

Source 실패는 정상 상태의 증거가 아니며 반드시 `gaps`에 남습니다. `hypotheses`는 결정적 root cause가 아니라 다음 검증 순서를 제시합니다. 복구 후보는 Operations Agent가 별도 artifact로 작성하고 restart, scale, rollback 등 production action은 Incident Commander가 승인합니다.

현재 MVP의 `max_cost_usd`는 요청 상한 계약이며 provider invoice를 실시간 계산하지 않습니다. 대신 query window, log group, row, tool-call, response byte와 timeout을 강제하고 Logs Insights의 scanned byte를 evidence에 기록합니다. 실제 달러 비용 hard stop은 Gateway price catalog와 billing telemetry가 연결되는 다음 단계에서 구현해야 합니다.

## Verification

```bash
python3 -m unittest discover -s agent-runtime/tests -v
terraform fmt -check -recursive
./scripts/validation/validate-terraform.sh
```

실제 배포 전에는 별도 sandbox에서 IAM policy simulation, `kubectl auth can-i` positive/negative matrix, dev role의 prod 접근 실패, fake secret/PII canary 마스킹, Logs Insights scan cost와 timeout을 검증해야 합니다.
