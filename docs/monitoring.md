# Monitoring and Alerting

## Objective

운영자가 장애, 성능 저하, 비용 이상 징후를 빠르게 인지하고 대응할 수 있도록 로그, 메트릭, 알람, 대시보드를 설계합니다.

EKS control plane, node/runtime, workload log retention과 Kubernetes SLO/alert/runbook은 [EKS Day-2 Operations](eks-operations.md)에 상세히 정의합니다. Mimir, OpenTelemetry, custom metric, Prometheus Adapter/KEDA의 목표 구조는 [Advanced Metrics and Telemetry Platform](observability-platform.md)을 기준으로 합니다. 이 문서는 공통 알람과 workload-specific 사례를 다룹니다.

지표별 query, 지속 시간, M/N 평가, missing data와 Warning/Critical 초기값의 canonical source는 [Monitoring Metric, Query and Alert Severity Policy](monitoring-alert-policy.md)입니다. 이 문서의 예시와 Agent 결과는 해당 versioned policy를 참조해야 합니다.

## Observability Layers

| Layer | Purpose | Example |
| --- | --- | --- |
| Metrics | 상태와 성능 수치화 | CPU, memory, latency, error rate |
| Logs | 이벤트와 원인 분석 | application log, VPC Flow Logs, audit log |
| Traces | 요청 흐름 추적 | API request path |
| Alerts | 즉시 대응 필요 상태 감지 | service down, error spike |
| Dashboard | 운영 상태 가시화 | service health, cost trend |

## Alert Channels

- Critical: PagerDuty, Slack, Email
- Warning: Slack, Email
- Info: Slack

## Initial Alert Rules

- ALB 5xx error rate exceeds threshold
- Target response time exceeds threshold
- EC2 CPU utilization exceeds threshold
- RDS CPU or storage threshold exceeded
- Transit Gateway와 중앙 egress data processing cost anomaly
- Monthly budget usage exceeds 80 percent
- VPC Flow Logs rejected traffic spike
- EKS node not ready or pod crash loop
- Kubernetes control plane error rate

공통 초기 기준은 Host CPU·memory `80%/10분 Warning`, `90%/5분 Critical`, filesystem·inode `80%/15분 Warning`, `90%/10분 Critical`입니다. 이 값은 시작점이며 CPU·memory 단독 Critical을 고객 장애로 단정하지 않습니다. service latency, error, queue, ready capacity, OOM·throttling과 결합하고 2~4주 baseline과 SLO로 조정합니다.

## Advanced Metric Strategy

현재 구현은 클러스터별 Prometheus와 CloudWatch Observability add-on까지이며, Mimir와 OpenTelemetry Collector는 아직 배포되지 않았습니다. Target은 역할을 다음처럼 분리합니다.

| 역할 | 선택 |
| --- | --- |
| Kubernetes local scrape, fast alert, HPA recording rule | Prometheus |
| 장기 metric, cross-cluster SLO/capacity query | Grafana Mimir |
| 신규 application custom metric 계측 | OpenTelemetry Metrics API/SDK |
| Always-on service metric export | OTel Prometheus exporter → local Prometheus → Mimir |
| Short-lived/push-only metric export | OTLP → OTel Collector → Mimir |
| CPU/memory HPA | Metrics Server |
| Service custom metric HPA | Prometheus Adapter의 승인된 local recording rule |
| SQS/Kafka backlog scaling | KEDA source-native scaler |
| AWS managed service metric | CloudWatch native metric 유지 |

중앙 Mimir 장애가 local alert나 autoscaling을 중단시키지 않아야 합니다. 같은 metric을 Prometheus와 OTLP 경로로 이중 전송하지 않고, metric catalog에 owner, instrument, unit, allowed attribute, cardinality budget, retention과 alert/HPA 소비자를 등록합니다. Linux 계정에 수집 권한을 부여하지 않으며 Collector, Adapter, KEDA는 각각 전용 Kubernetes ServiceAccount와 최소 권한 workload identity를 사용합니다.

## Peak Notification Workload: Nginx to Kakao

예약 발송 시간에 요청이 Nginx를 거쳐 application, queue, worker, Kakao API로 전달되는 서비스를 기준으로 다음 경로를 하나의 service로 관측합니다.

```text
Scheduler/Client -> ALB/WAF -> Nginx -> Application -> Queue -> Sender Worker -> Kakao API
                                      |                         |
                                      +-> access/error log      +-> result/callback/DLQ
```

높은 요청량 자체는 장애가 아닙니다. 예약 시간의 예상 traffic보다 error, latency, saturation, queue lag가 악화되는지를 함께 판단합니다.

### Signal and Example Thresholds

아래 값은 초기 기준입니다. 2~4주의 정상 peak baseline과 service SLO를 측정한 뒤 조정합니다. 단일 지표보다 traffic, error, latency, saturation 중 둘 이상을 결합해 paging noise를 줄입니다.

| Layer | Metric or log | Warning example | Critical example |
| --- | --- | --- | --- |
| End-to-end | synthetic notification success, total completion rate | expected completion rate below 99.5% for 10m | no successful test delivery or below 99% for 5m |
| ALB/Nginx traffic | requests/sec, concurrent/active connections | forecast range exceeded or capacity above 70% for 10m | capacity above 85% for 5m |
| Nginx errors | 499, 502, 503, 504 ratio; upstream timeout | 5xx above 2% for 5m with minimum request count | 5xx above 5% for 5m |
| Nginx latency | request time and upstream response time p95/p99 | p95 above service SLO for 10m | p99 above hard timeout budget for 5m |
| Connection handling | accepted minus handled, dropped connection, listen overflow | any sustained delta or overflow | increasing delta with 5xx/timeout |
| File descriptor | Nginx open FD / process limit; host allocated / max | above 70% for 10m | above 85% for 5m |
| TCP/host | SYN_RECV, TIME_WAIT, retransmit, conntrack usage, ephemeral port errors | 3x normal peak or above 70% capacity | drops/errors or above 85% capacity |
| Queue | depth, publish/consume rate, oldest message age, retry, DLQ | oldest age approaches delivery SLO | oldest age exceeds SLO or DLQ above 0 |
| Kakao API | request latency, 2xx/429/5xx, provider rejection, quota | 429/5xx above 2% or quota above 70% | sustained provider failure or quota above 90% |
| Worker/runtime | CPU throttling, memory, restart, thread/connection pool | saturation above 70% | restart loop, OOM, pool exhaustion |

Threshold에는 minimum traffic 조건을 둡니다. 예를 들어 5xx 1건을 100% 오류로 계산해 호출하지 않도록 `request_count >= 100`과 error ratio를 함께 평가합니다. Peak 직전 15분에는 capacity와 dependency health를 확인하고, peak 중에는 배포를 동결하며, 종료 후에는 queue drain과 누락 건수를 확인합니다.

### Collection Design

- Nginx `stub_status`와 `nginx-prometheus-exporter`는 active/reading/writing/waiting connection과 accepted/handled/request count를 수집합니다.
- OSS `stub_status`만으로 status code, request latency, upstream latency는 얻을 수 없습니다. JSON access log를 CloudWatch Logs/OpenSearch로 보내거나 log exporter/OpenTelemetry를 추가합니다.
- Nginx access log에는 request ID, route, status, request time, upstream response time, upstream status를 남기되 token, phone number, message content는 마스킹합니다.
- Host는 node exporter 또는 CloudWatch Agent로 file descriptor, socket, conntrack, network error/drop, CPU, memory를 수집합니다.
- Nginx process별 FD는 process-exporter 또는 CloudWatch Agent `procstat`으로 수집합니다. Host 전체 FD 지표만으로 Nginx 고갈을 단정하지 않습니다.
- Application은 queue publish 결과, sender result, retry reason, DLQ, oldest message age와 Kakao response class를 business metric으로 노출합니다.
- 신규 application metric은 OpenTelemetry Metrics API/SDK로 계측합니다. 완료율과 오류율은 Gauge로 직접 내보내지 않고 bounded attribute의 Counter/Histogram을 recording rule로 계산합니다.
- 실제 고객에게 메시지를 보내지 않는 test tenant/recipient로 full-path synthetic canary를 운용합니다.

### Nginx Capacity Notes

`worker_connections`는 client connection뿐 아니라 upstream connection도 소비합니다. 따라서 이론상 `worker_processes * worker_connections`를 그대로 고객 동시 연결 수로 보지 않습니다. `worker_rlimit_nofile`, OS `LimitNOFILE`, process open FD, keepalive, upstream pool을 함께 확인합니다.

### Incident Commands

명령은 상시 metric의 대체재가 아니라 장애 시 원인 확인에 사용합니다.

```bash
curl -s http://127.0.0.1/nginx_status
sudo nginx -T
ss -s
ss -tan state syn-recv
ss -tan state time-wait
cat /proc/$(cat /run/nginx.pid)/limits | grep -i 'open files'
ls /proc/$(cat /run/nginx.pid)/fd | wc -l
cat /proc/sys/fs/file-nr
sudo journalctl -u nginx --since '15 min ago'
```

`netstat`보다 `ss`를 우선 사용합니다. Container/Kubernetes 환경에서는 pod의 process namespace와 host namespace가 다르므로 node, pod, sidecar 중 어느 계층을 조회하는지 명확히 기록합니다.

### Triage Order

1. End-to-end success와 queue oldest age로 고객 영향과 backlog를 확인합니다.
2. ALB/Nginx 5xx, 499, latency와 active connection으로 ingress 병목을 확인합니다.
3. Nginx FD ratio, accepted/handled delta, listen overflow, host socket/conntrack을 확인합니다.
4. Application pool, queue publish/consume, worker retry와 DLQ를 확인합니다.
5. Kakao API 429/5xx, timeout, quota, DNS/TLS/TGW 중앙 egress 경로를 확인합니다.
6. 완화 후 queue drain, 중복 발송, 누락 건수를 검증하고 incident timeline을 남깁니다.

고객용 Kakao 발송 서비스가 실패하면 같은 경로의 운영 알림도 전달되지 않을 수 있습니다. Critical alert는 PagerDuty/전화, 독립 Slack 또는 Email처럼 별도 provider와 network path를 가진 채널로 동시에 전달합니다.

## AI Gateway and Agent Observability

AI 사용량은 provider별 형식을 AI Gateway에서 공통 schema로 정규화합니다.

핵심 dimension:

- `Account`, `Environment`, `Team`, `CostCenter`, `Application`
- `AgentId`, `Provider`, `Model`, `Status`, `PolicyResult`

핵심 metric:

- request count, success/error/throttle rate
- p50/p95 latency와 time to first token
- input/output/cached token
- estimated cost와 budget burn rate
- tool-call success, approval wait time, Agent task success
- PII/secret detection, denied model, privileged tool attempt

Near-real-time metric은 CloudWatch 또는 Prometheus/Grafana에 표시하고, 상세 usage event는 Firehose와 S3에 저장해 Athena로 분석합니다. Raw prompt와 response는 기본 monitoring log에 저장하지 않습니다.

상세 dashboard와 event schema는 [Enterprise AI Platform and Agent Operations](ai-platform.md)를 기준으로 합니다.

## VPC Flow Logs Troubleshooting

- rejected traffic을 기준으로 security group, NACL, route table 문제를 분석합니다.
- source/destination IP, port, protocol 기준으로 연결 실패 원인을 추적합니다.
- Transit Gateway, 중앙 egress, VPC peering 구간의 traffic volume을 확인합니다.
- Athena 또는 CloudWatch Logs Insights로 표준 query를 관리합니다.
- 장애 runbook에 `REJECT`, `ACCEPT`, `NODATA`, asymmetric routing 점검 절차를 포함합니다.
