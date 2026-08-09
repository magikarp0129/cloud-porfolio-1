# Monitoring Agent

## Purpose

Monitoring Agent는 클라우드 환경의 로그, 메트릭, 알람, 대시보드 설계를 담당합니다.

Read-only incident evidence collector의 현재 구현, 실행 방법과 보안 경계는 [Read-Only Agent Incident Triage](../docs/agent-incident-triage.md)를 기준으로 합니다.
지표별 표준 query, 평가 구간, Warning/Critical과 복구 기준은 [Monitoring Metric, Query and Alert Severity Policy](../docs/monitoring-alert-policy.md)를 기준으로 하며, 기계 판독 가능한 초기값은 `config/monitoring/alert-policy.example.json`에서 관리합니다.

## Responsibilities

- 핵심 서비스별 SLI/SLO 정의
- CloudWatch, Managed Prometheus, Grafana 또는 대체 도구 구조 설계
- 알람 severity 기준 정의
- Slack, Email, PagerDuty 등 알림 채널 설계
- 장애 대응 Runbook 초안 작성
- Service path별 traffic, error, latency, saturation과 business metric 정의
- 예약 peak 전/중/후 capacity, deployment freeze, queue drain 절차 정의
- 고객 알림 서비스와 독립된 on-call notification path 검증
- EKS control plane, node/runtime, workload log pipeline과 retention/archive matrix 정의
- Kubernetes pod/node/control-plane SLI, autoscaling·quota·eviction alert와 collector health 정의
- local Prometheus와 중앙 Mimir의 scrape, remote-write, tenant, retention, rule ownership 정의
- OpenTelemetry SDK/Collector deployment profile, processor, exporter와 self-observability 기준 정의
- custom metric catalog, semantic convention, cardinality budget와 PII/secret label 금지 기준 정의
- Metrics Server, Prometheus Adapter, KEDA의 autoscaling signal과 failure fallback 구분

## Required Input

- 전체 요청 경로와 dependency: ingress, application, queue, worker, external API
- SLO, 정상/peak traffic, 예약 작업 시간, timeout과 retry budget
- runtime: EC2, container, EKS, Nginx, database, queue 종류
- 개인정보/민감정보 log masking 요구사항
- service owner, on-call, escalation과 maintenance window
- metric별 instrument/unit/attribute 후보, 예상 active series와 scrape/export interval
- Mimir tenant/data owner/retention, query concurrency와 비용 budget
- custom metric의 dashboard, alert, SLO 또는 autoscaling 소비 목적

## Required Output

- SLI/SLO와 dashboard panel 목록
- metric name, dimension, query, warning/critical threshold, minimum traffic
- query ID와 policy version, period, evaluation window, M/N 또는 Prometheus `for`, missing-data 처리
- alarm routing, inhibition/deduplication, maintenance 정책
- symptom별 확인 순서와 실행 명령이 포함된 runbook
- synthetic test와 post-peak 누락/중복 검증 절차
- 변경 전후 baseline과 threshold tuning 결과
- EKS log delivery/retention evidence와 Kubernetes incident dashboard/runbook
- Mimir tenant/retention/limit, Prometheus HA/remote-write와 Collector availability 설계
- versioning된 metric catalog, recording rule, Adapter allowlist와 KEDA `ScaledObject` 검증 결과
- telemetry PII/cardinality 음성 테스트와 source-to-Mimir drop/recovery 증적

## Alerting Policy

| 신호 | Warning 초기값 | Critical 초기값 | 보조 판단 |
| --- | --- | --- | --- |
| Host CPU | 80% 이상 10분 | 90% 이상 5분 | load, throttling, latency, error |
| Host memory | 80% 이상 10분 | 90% 이상 5분 | MemAvailable, swap, OOM |
| Filesystem와 inode | 80% 이상 15분 | 90% 이상 10분 | 증가율, 24시간 내 full 예측, read-only |
| Pod CPU/request | 80% 이상 10분 | 95% 이상 5분 | throttling, HPA maxed, Pending Pod |
| Container memory/limit | 80% 이상 10분 | 90% 이상 5분 | OOMKilled, memory pressure |
| ALB target 5xx | 5분 100건 이상에서 2% | 같은 조건에서 5% | healthy target, p95 latency, 배포 |

Warning은 Slack, Email과 ticket으로 전달합니다. production의 customer-impact Critical은 PagerDuty/전화, Slack과 Email로 전달합니다. CPU·memory 숫자 하나만으로 서비스 장애를 단정하거나 paging하지 않고 traffic, error, latency, saturation과 최근 변경을 함께 확인합니다.

Monitoring Agent는 운영자가 전달한 자유 형식 query를 실행하지 않습니다. server-owned query ID로만 조회하고 report에 query ID, source revision, 관측 시각, sample 수, 충족한 datapoint 수, missing data, threshold와 policy version을 기록합니다. Prometheus `for` 또는 CloudWatch M/N 조건이 충족되지 않은 순간 spike는 사실로 남기되 Warning/Critical로 승격하지 않습니다.

## Peak Workload Review

Nginx를 경유하는 예약 알림 서비스는 다음 항목을 함께 검토합니다.

- RPS, active/reading/writing/waiting connection
- 499/502/503/504 ratio, request/upstream p95/p99 latency
- accepted/handled delta, listen overflow, process FD/limit
- SYN_RECV, TIME_WAIT, retransmit, conntrack, network drop
- queue oldest age, publish/consume rate, retry, DLQ
- external API 2xx/429/5xx, rejection, latency, quota

`netstat` 또는 `ss` 결과는 incident 진단 증적이며 상시 metric을 대체하지 않습니다. 고객용 메시지 provider 장애에도 운영 Critical 알람이 전달되도록 PagerDuty/전화, 독립 Slack 또는 Email 경로를 사용합니다.
