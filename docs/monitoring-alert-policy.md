# Monitoring Metric, Query and Alert Severity Policy

## 목적과 적용 경계

이 문서는 CloudWatch Alarm, Prometheus rule과 운영자가 동일한 지표·질의·지속 시간·등급 기준을 사용하기 위한 공통 기준입니다.

일부 CloudWatch alarm resource는 Terraform에 있지만 아래 전체 정책을 실제 Alarm 또는 PrometheusRule로 배포한 것은 아닙니다. production 적용 전 서비스 owner가 SLO, 정상·peak 시간대의 2~4주 baseline, 자원 요청값과 실제 장애 이력을 검토해야 합니다.

| 상태 | 의미 |
| --- | --- |
| `documented_target` | metric math 또는 rule의 설계만 존재함 |
| `terraform_defined` | 일부 CloudWatch alarm이 Terraform에 정의되었지만 실제 통지 시험은 없음 |
| `implemented` | 실제 datasource, rule, route와 test alarm 증적까지 확인된 상태. 현재 이 정책에는 해당 항목 없음 |

## 평가 원칙

1. 하나의 순간값이 아니라 `period`, 평가 구간과 필요한 위반 datapoint 수를 함께 정의합니다.
2. Prometheus에서는 `for`로 지속 시간을 확인하고, CloudWatch에서는 `Period`, `EvaluationPeriods`, `DatapointsToAlarm`의 M/N 조건으로 표현합니다.
3. CPU와 memory 사용률만으로 고객 장애를 단정하지 않습니다. latency, error, queue, ready capacity, OOM·throttling 같은 영향 지표와 결합합니다.
4. 비율 알람은 최소 traffic을 둡니다. 요청 1건 중 실패 1건을 100% 장애로 paging하지 않습니다.
5. missing data는 정상으로 간주하지 않습니다. 지표 미수집은 telemetry pipeline 상태로 별도 경보하고 report에는 evidence gap으로 표시합니다.
6. Warning은 대응 여유가 있는 성능 저하·용량 위험, Critical은 현재 고객 영향 또는 임박한 서비스 중단을 기준으로 합니다.
7. 정상 복귀는 임계값 바로 아래가 아니라 별도 recovery 기준을 10~15분 유지해 flapping을 막습니다.

## Severity와 통보

| 등급 | 판단 기준 | 기본 통보 | 운영자 행동 |
| --- | --- | --- | --- |
| Critical | 서비스 중단, SLO의 빠른 소진, OOM·디스크 고갈·ready capacity 손실처럼 즉시 조치하지 않으면 고객 영향이 커지는 상태 | PagerDuty/전화, Slack, Email | 즉시 인지, incident 선언 여부 판단, 증거 확인 후 완화 승인 |
| Warning | 현재 서비스는 동작하지만 지속 시 SLO 또는 용량에 영향을 줄 상태 | Slack, Email, ticket | 30분 이내 추세·변경 이력·관련 지표 확인, 필요 시 owner 할당 |
| Info | 배포, scale, backup 같은 상태 변화 또는 추세 정보 | Dashboard, Slack 선택 | 기록과 추세 확인, paging하지 않음 |

개발 환경의 Critical은 기본적으로 Slack/ticket에만 전달하고, production의 customer-impact Critical만 on-call을 호출합니다. 고객 알림 서비스와 같은 provider를 Critical의 유일한 통보 경로로 사용하지 않습니다.

## 공통 인프라 초기 기준

다음 값은 첫 배포를 위한 시작점이며 서비스별 baseline으로 조정합니다.

| 신호 | Warning | Critical | 복구 기준 | 함께 확인할 지표 |
| --- | --- | --- | --- | --- |
| Host CPU 사용률 | 80% 이상 10분, 10개 중 8개 위반 | 90% 이상 5분, 5개 모두 위반 | 70% 미만 15분 | load/run queue, throttling, latency, 상위 process |
| Host memory 사용률 | 80% 이상 10분 | 90% 이상 5분 | 75% 미만 15분 | MemAvailable, swap, major fault, OOM, cgroup working set |
| Filesystem 사용률 | 80% 이상 15분 | 90% 이상 10분 | 75% 미만 15분 | 증가율, 24시간 내 full 예측, read-only, deleted-open file |
| Inode 사용률 | 80% 이상 15분 | 90% 이상 10분 | 75% 미만 15분 | 작은 파일 급증, spool·log·임시 디렉터리 |
| Pod CPU/request | 80% 이상 10분 | 95% 이상 5분 | 70% 미만 15분 | throttling, HPA maxed, Pending Pod, latency |
| Container memory/limit | 80% 이상 10분 | 90% 이상 5분 | 75% 미만 15분 | OOMKilled, memory pressure, heap/cache, sidecar |
| CPU throttling period | 20% 이상 10분 | 40% 이상 5분 | 10% 미만 15분 | CPU limit/request, latency와 replica 수 |
| ALB target 5xx | 5분 요청 100건 이상에서 2% 이상 5분 | 같은 조건에서 5% 이상 5분 | 1% 미만 10분 | HealthyHostCount, p95 latency, deployment, app error |
| Node NotReady | 1대 이상 2분 | 1대 이상 5분 또는 critical capacity 감소 | 모두 Ready 10분 | EC2, kubelet, CNI, disk pressure, Pod placement |
| Monitoring target `up` | 0이 5분 | production critical target이 15분 미수집 | 1이 10분 | service discovery, exporter, network, collector drop |

디스크 95% 이상, filesystem read-only, OOMKilled, synthetic 전면 실패처럼 빠르게 복구 불가능해질 수 있는 사건은 일반 지속 시간보다 긴급 조건이 우선합니다.

## 표준 PromQL

Linux node는 node exporter, Kubernetes workload는 cAdvisor와 kube-state-metrics를 전제로 합니다. 아래 질의가 반환하는 label과 series 수는 환경별 recording rule에서 제한합니다.

```promql
# Host CPU 사용률(%): 5분 idle rate를 CPU별 평균
100 * (1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])))

# Host memory 사용률(%): free가 아니라 실제 재사용 가능한 MemAvailable 기준
100 * (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)

# Filesystem 사용률(%): 운영 대상 mount만 allowlist하고 pseudo filesystem 제외
100 * (1 - node_filesystem_avail_bytes{fstype!~"tmpfs|overlay|squashfs"}
  / node_filesystem_size_bytes{fstype!~"tmpfs|overlay|squashfs"})

# Inode 사용률(%)
100 * (1 - node_filesystem_files_free{fstype!~"tmpfs|overlay|squashfs"}
  / node_filesystem_files{fstype!~"tmpfs|overlay|squashfs"})

# Pod CPU 사용량 / request(%). request 누락은 별도 policy violation으로 처리
100 * sum by (namespace, pod) (
  rate(container_cpu_usage_seconds_total{namespace="{namespace}",container!="",image!=""}[5m])
) / clamp_min(sum by (namespace, pod) (
  kube_pod_container_resource_requests{namespace="{namespace}",resource="cpu",unit="core"}
), 0.001)

# Container memory working set / limit(%)
100 * container_memory_working_set_bytes{namespace="{namespace}",container!="",image!=""}
  / clamp_min(kube_pod_container_resource_limits{
      namespace="{namespace}",resource="memory",unit="byte"
    }, 1)
```

CPU 사용률 80%는 CPU limit 80%와 같지 않습니다. Host는 전체 CPU 시간, Kubernetes workload는 request 대비 사용량과 throttling을 각각 확인해야 합니다. Memory도 host의 `MemAvailable`, container working set, request/limit과 OOM을 구분합니다.

## CloudWatch와 Logs Insights 기준

| 목적 | Metric 또는 query | 평가 기준 |
| --- | --- | --- |
| EC2 CPU | `AWS/EC2 CPUUtilization` Average 1분 | 공통 Host CPU 초기 기준을 적용하되 Auto Scaling 여부와 credit metric을 함께 확인 |
| ALB 5xx 비율 | `IF(RequestCount>0, 100*HTTPCode_Target_5XX_Count/RequestCount, 0)` | 5분 합계 100건 이상에서 2% Warning, 5% Critical |
| ALB 지연 | `TargetResponseTime` p95 | service route SLO로 Warning, timeout budget으로 Critical 설정 |
| RDS 저장 공간 | `FreeStorageSpace` | percent 환산에 필요한 allocated storage를 inventory에서 결합하고 절대 GiB와 소진 예상 시간을 함께 평가 |
| Application 오류 요약 | `filter level='error' | stats count(*) by error_code, deployment_version` | raw message 대신 집계, 배포 전후 변화와 error rate 확인 |

CloudWatch에서 1분 period로 10분 지속을 표현할 때는 예를 들어 10개 평가 구간 중 8개 위반을 Warning으로 사용합니다. Critical은 5개 중 5개처럼 짧고 확실한 지속 조건을 적용할 수 있습니다. 각 metric의 발행 특성에 맞게 `treat_missing_data`를 명시하고, sparse event metric과 continuous utilization metric을 같은 방식으로 처리하지 않습니다.

## 운영 검토 기록

알람을 검토할 때는 다음 정보를 ticket 또는 장애 보고서에 남깁니다.

| 항목 | 예시 |
| --- | --- |
| Query identity | metric/query 이름, policy version, source revision |
| 관측 범위 | prod, service, node/pod, UTC 시작·종료, sample 수 |
| 평가 | 최대 92%, 10개 중 9개가 80% 이상, Warning 충족 |
| 관련 신호 | latency 정상, error 정상, throttling 3%, deployment 없음 |
| 결론 | CPU Warning은 사실이나 customer-impact Critical 근거는 없음 |
| 다음 확인 | process CPU, load/run queue, request trend와 HPA headroom |

## 검증과 조정 절차

1. Prometheus `promtool check rules` 또는 CloudWatch sandbox alarm으로 문법과 evaluation을 검증합니다.
2. 정상·peak·배포·장애 시나리오로 Warning/Critical/복구 상태와 missing data 처리를 확인합니다.
3. dev에서 CPU stress, memory pressure, 임시 disk fill과 exporter 중단을 안전한 한도에서 수행합니다.
4. 원본 dashboard와 운영 보고서를 표본 대조하고 false positive와 false negative를 기록합니다.
5. 2~4주 후 서비스별 p95/p99 baseline, SLO와 incident 결과로 threshold를 조정하고 policy version을 증가시킵니다.
6. production 반영은 Monitoring, service owner와 Security/Operations review를 통과합니다.

## 참고 기준

- Amazon CloudWatch Alarm evaluation: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/alarm-evaluation.html
- Amazon CloudWatch missing data: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/alarms-and-missing-data.html
- Prometheus alerting rules: https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/
- Prometheus node exporter: https://prometheus.io/docs/guides/node-exporter/
- Kubernetes resource metrics pipeline: https://kubernetes.io/docs/tasks/debug/debug-cluster/resource-metrics-pipeline/
