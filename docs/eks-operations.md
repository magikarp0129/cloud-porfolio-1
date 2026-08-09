# EKS 운영 표준

## 1. 목적과 적용 범위

이 문서는 Amazon EKS를 배포한 뒤 안정적으로 운영하기 위한 Day-2 기준을 정의합니다. 대상은 EKS control plane, managed node group, Kubernetes platform add-on, namespace, workload, persistent volume, 로그·메트릭·trace, 백업과 복구입니다.

이 문서에서 제시하는 보존 기간과 SLO 숫자는 포트폴리오의 **초기 운영 기준**입니다. 실제 운영 적용 전 service owner, Data owner, Security, Compliance가 업무 중요도와 법적 의무를 근거로 승인해야 합니다. 규제 또는 계약 기준이 더 엄격하면 그 기준을 우선합니다.

Agent는 분석, 문서, patch, plan, review artifact까지만 만듭니다. `prod`의 `apply`, 재시작, drain, failover, restore, alarm suppression은 ticket, 사람 승인, protected CI/CD 또는 승인된 runbook으로만 실행합니다. 공통 실행 경계는 [Multi-Agent Operator Guide](../agents/operator-guide.md)를 따릅니다.

## 2. 현재 구현과 목표 상태

이 문서의 `Current`는 repository에서 확인한 코드 상태, `Target`은 향후 구현할 운영 기준, `Evidence`는 완료를 입증할 실행 결과입니다. Target 문구는 현재 cloud에 배포되었음을 의미하지 않습니다.

| 영역 | Current: 저장소 evidence | Target | Gap / 완료 evidence |
| --- | --- | --- | --- |
| Control plane log | 5종 `api`, `audit`, `authenticator`, `controllerManager`, `scheduler`, 전용 KMS, `dev/stg/prod=90/90/365일` (`terraform/modules/eks`, `terraform/environments/*`) | 중앙 Log Archive 계정으로 실시간 복제, source별 장기 보존·검색·무결성 통제 | 부분 구현 / source-to-S3 전달·검색·retention test 필요 |
| Workload/system log | `amazon-cloudwatch-observability` add-on, Pod Identity, KMS 암호화된 `application/dataplane/host/performance` log group, `dev/stg/prod=30/90/365일` | collector coverage와 손실 감시, JSON schema/PII 통제, 중앙 S3 archive | 부분 구현 / node별 coverage, drop=0, archive query 증적 필요 |
| Metrics/alert | `kube-prometheus-stack`, Prometheus `dev=7d`, `stg=15d`, `prod=30d`, Prometheus/Grafana PVC, Alertmanager 활성화 (`terraform/environments/*/platform`, `terraform/modules/kubernetes-platform`) | SLI/SLO, recording rule, 외부 on-call receiver route, 장기 metric 전략 | 부분 구현 / Alertmanager receiver·route와 실제 test notification 없음 |
| Network/IP | EKS control-plane `cluster_subnet_ids`, managed node `node_subnet_ids`, VPC CNI custom networking·prefix delegation, AZ별 Pod subnet `ENIConfig` 구현 | CNI IP 사용률·prefix warm pool·ENIConfig drift 알람, 중앙 ingress/egress 장애 우회 | 부분 구현 / 실제 CNI bootstrap, Pod IP 할당, TGW 경로와 failover 증적 필요 |
| QoS | 환경별 application namespace에 LimitRange·ResourceQuota, `platform-critical/application-high/batch-low` 3개 PriorityClass 구현. PDB resource interface는 있으나 환경 instance 없음 (`terraform/modules/kubernetes-platform`, `terraform/environments/*/platform`) | workload별 PDB, topology spread, resource 누락·BestEffort admission gate | 부분 구현 / PDB instance와 admission·scheduling·drain test 필요 |
| Autoscaling | node group의 Terraform `desired_size` drift만 무시하며 HPA, Metrics Server, Karpenter, Cluster Autoscaler 없음 | HPA + VPA recommendation + Karpenter 또는 Cluster Autoscaler | 미구현 / load 기반 Pod·node scale-out/in 측정 필요 |
| Backup | 태그 기반 AWS Backup plan, `prod` Vault Lock 구성 (`terraform/modules/operations`) | EKS composite recovery point 검증, cross-account/Region copy, restore drill | 부분 구현 / EKS cluster selection, child recovery point, restore 증적 없음 |
| Upgrade | minor version 명시, managed add-on 호환 버전 조회, AL2023 managed node group (`terraform/modules/eks`) | 지원 종료 추적, upgrade insight, add-on matrix, rollback rehearsal | 부분 구현 / `dev→stg→prod` 실행 기록과 rollback evidence 필요 |
| Security | private API, Access Entry, KMS secret encryption, IMDSv2, VPC CNI/EBS CSI Pod Identity, restricted PSS `audit`/`warn`, strict mTLS | PSS `enforce`, default-deny NetworkPolicy, workload별 Pod Identity, image admission, runtime detection | 부분 구현 / deny·identity·detection test 필요 |

`terraform/modules/eks`가 AWS EKS와 node lifecycle을, `terraform/modules/kubernetes-platform`이 Kubernetes/Helm lifecycle을 관리하는 현재 state 경계는 유지합니다. workload manifest와 애플리케이션 release는 별도 application repository 또는 GitOps state가 소유해야 합니다.

## 3. 책임과 RACI

### 3.1 운영 역할

| 역할 | 책임 |
| --- | --- |
| Platform owner | EKS control plane, node group, CNI/CSI/CoreDNS, namespace baseline, capacity와 upgrade 총괄 |
| Service owner | workload requests/limits, probes, HPA, PDB, topology, 애플리케이션 SLO와 runbook |
| Operations Agent/운영팀 | 백업, restore drill, node lifecycle, patch/CVE/EOS, 장애 복구안과 증적 |
| Monitoring Agent/SRE | 로그·메트릭·trace pipeline, dashboard, SLI/SLO, 알람과 on-call routing |
| Security Agent/보안팀 | Access Entry/RBAC, Pod Identity, PSS, NetworkPolicy, KMS, image/runtime control, 침해 대응 |
| FinOps Agent/FinOps | 비용 label, CUR split cost, rightsizing, telemetry·data transfer 비용 검토 |
| CI/CD Agent/배포팀 | 검증, plan artifact, policy gate, 환경 승격, 승인된 변경의 실행 |
| Data owner | 데이터 등급, RPO/RTO, 보존·삭제, 복구 데이터 접근 승인 |
| Incident commander | 장애 등급, 완화·복구 승인, 이해관계자 소통, 종료 판단 |
| Reviewer Agent | 변경 위험, rollback 가능성, 누락된 검증과 운영 증적의 독립 검토 |

### 3.2 RACI matrix

`R`은 수행, `A`는 최종 책임/승인, `C`는 사전 협의, `I`는 결과 공유입니다. Agent의 `A` 표기는 설계 품질 책임이며 production 실행 승인을 의미하지 않습니다.

| 활동 | Platform | Service | Operations | Monitoring | Security | FinOps | CI/CD | Data/IC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Control plane/add-on/node upgrade 설계 | A/R | C | R | C | C | I | R | I |
| Workload requests/limits, HPA, PDB | C | A/R | C | R | C | C | R | I |
| 로그 schema, 수집, 보존 | C | R | C | A/R | C | C | R | Data owner C |
| Audit/PII/불변 보관 정책 | C | C | C | R | A/R | I | R | Data owner C |
| 백업 plan과 restore drill | C | C | A/R | C | C | I | R | Data owner A |
| SLI/SLO와 알람 | C | A/R | C | R | C | I | R | I |
| 보안 incident | C | C | R | R | A/R | I | I | IC A |
| 비용 allocation과 최적화 | C | C | R | C | I | A/R | C | I |
| `prod` 배포 | C | C | C | I | C | C | R | 지정 승인자 A |
| 장애 중 drain/restart/scale/failover | R | C | R | C | C | I | I | IC A |

## 4. 로그 수집·보관 표준

Kubernetes는 cluster-level log 저장소를 제공하지 않으며 Pod가 퇴거되거나 node가 사라지면 node 로컬 로그도 함께 사라질 수 있습니다. 애플리케이션은 `stdout`/`stderr`에 기록하고, node별 수집 agent가 별도 backend로 전달해야 합니다. Kubernetes 공식 [Logging Architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/)와 AWS의 [EKS control plane logging](https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html)을 기준으로 합니다.

### 4.1 수집 대상

| 계층 | 필수 source | 주 용도 | 소유자 |
| --- | --- | --- | --- |
| EKS control plane | `api`, `audit`, `authenticator`, `controllerManager`, `scheduler` | API 장애, 인증·인가, RBAC 변경, scheduling/control loop 분석 | Platform/Security |
| AWS control plane | CloudTrail의 EKS, IAM, EC2, ELB, ECR, KMS API event | AWS 주체와 변경 attribution | Security |
| Node | kubelet, containerd, kernel/journald, bootstrap, SSM, disk·network 오류 | NodeNotReady, image pull, OOM, filesystem·kernel 문제 | Operations |
| Kubernetes system | CoreDNS, VPC CNI, kube-proxy, EBS/EFS CSI, metrics-server | DNS, IP, service routing, volume, autoscaling 장애 | Platform |
| Platform controller | AWS Load Balancer Controller, ExternalDNS, cert-manager, autoscaler, Istio | reconcile 실패, quota, cloud API throttle | Platform |
| Workload | application, ingress/sidecar, job/worker의 구조화 로그 | 고객 영향, error, latency, business transaction | Service owner |
| Security | audit, admission denial, NetworkPolicy, GuardDuty finding | 비인가 접근과 runtime 위협 | Security |

제어 플레인 로그 전달은 수분 지연될 수 있는 best-effort 방식이므로 audit log 하나만을 즉시 차단 제어로 사용하지 않습니다. AWS API 변경은 CloudTrail, runtime 행위는 GuardDuty/보안 agent, 애플리케이션 행위는 workload log와 함께 상관 분석합니다.

### 4.2 Current collector와 목표 archive pipeline

Current는 `amazon-cloudwatch-observability` EKS add-on과 네 종류의 KMS 암호화 log group까지입니다. 아래에서 CloudWatch Logs 이후의 subscription, Firehose, 중앙 S3, Object Lock과 Lifecycle은 Target이며 아직 구현 증적이 없습니다.

```text
Pod stdout/stderr ─┐
system containers ─┼─> Fluent Bit DaemonSet ─> CloudWatch Logs(Standard, hot/search)
node/journald ──────┘                              │
                                                   ├─> metric filter / Logs Insights / alarm
EKS control plane ────────────────────────────────>│
                                                   └─> subscription → Firehose → central S3
                                                                                │
                                                                                ├─ KMS encryption
                                                                                ├─ Object Lock if approved
                                                                                └─ Lifecycle → archive → expire
```

- AWS는 Container Insights의 log forwarder로 Fluent Bit 사용을 권고하며 FluentD 지원은 폐기했습니다. [CloudWatch EKS log setup](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Container-Insights-EKS-logs.html)을 기준으로 Fluent Bit을 DaemonSet으로 배포합니다.
- 지속 archive에는 반복적인 CloudWatch export job 대신 subscription을 사용합니다. AWS도 연속 archive에는 subscription을 권고합니다. [CloudWatch subscriptions](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Subscriptions.html), [S3 export considerations](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/S3Export.html)을 참고합니다.
- Subscription filter는 `Standard` log class에서만 지원되므로 중앙 전달 대상 log group은 `Standard`를 사용합니다.
- 중앙 S3 bucket은 Log Archive 계정에 두고 workload account에는 write-only 전달 권한만 부여합니다. bucket versioning, Block Public Access, KMS, 최소 권한 query role을 적용합니다.
- 감사 증적에 삭제 방지가 필요하면 S3 Object Lock을 사용합니다. Compliance mode는 root를 포함해 보호 기간 중 삭제할 수 없으므로, 보존 기간과 legal hold 절차를 Security/Data owner가 승인한 뒤 설정합니다. [S3 Object Lock](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html)을 참고합니다.
- archive는 S3 Lifecycle로 Standard/Intelligent-Tiering에서 Glacier 계열로 전환합니다. 검색 RTO와 최소 보관 기간 비용을 먼저 검증합니다. [S3 Lifecycle transitions](https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-transition-general-considerations.html)을 참고합니다.

### 4.3 Log group과 schema

권장 log group 이름은 환경과 source가 한눈에 구분되어야 합니다.

```text
/aws/eks/<cluster>/cluster                  # EKS managed control plane
/aws/containerinsights/<cluster>/application
/aws/containerinsights/<cluster>/host
/aws/containerinsights/<cluster>/dataplane
/platform/eks/<cluster>/<component>
/workload/<env>/<namespace>/<service>
```

Workload는 한 줄 JSON을 사용하고 다음 필드를 표준화합니다.

| 필드 | 요구사항 |
| --- | --- |
| `timestamp` | UTC RFC3339, 수집 시간과 event 시간을 구분 |
| `level` | `debug`, `info`, `warn`, `error` 중 하나 |
| `service`, `environment` | 안정적인 서비스와 환경 식별자 |
| `cluster`, `namespace`, `pod`, `container` | 수집기가 Kubernetes metadata로 보강 |
| `trace_id`, `span_id`, `request_id` | log·metric·trace 상관관계. 고객 식별자를 대신 사용하지 않음 |
| `event`, `outcome`, `error_code` | 자유문장 대신 집계 가능한 값 |
| `duration_ms` | latency event에 사용 |
| `deployment_version` | image digest 또는 release ID |
| `data_classification` | `public`, `internal`, `confidential`, `restricted` |

Pod name, container ID, request ID처럼 cardinality가 큰 값은 log 검색 field로 유지하고 Prometheus label로 무분별하게 승격하지 않습니다.

### 4.4 PII, secret, 접근 통제

1. 애플리케이션에서 password, API key, access/refresh token, session cookie, `Authorization` header, Kubernetes Secret 값, 개인 식별번호, 카드정보, 전화번호, 이메일, 원문 message body를 기록하지 않습니다.
2. 업무상 필요한 고객 correlation은 비가역 token 또는 내부 subject ID를 사용하고 mapping store 접근을 분리합니다.
3. 수집 전 application/filter 단계에서 제거합니다. CloudWatch Logs data protection policy의 탐지·마스킹은 방어 계층이지 source redaction의 대체재가 아닙니다. [CloudWatch sensitive data masking](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/mask-sensitive-data.html)을 참고합니다.
4. 민감 log group의 `logs:Unmask`, Logs Insights query, S3/Athena read는 JIT role, MFA, ticket, 짧은 session으로 제한하고 CloudTrail로 감사합니다.
5. incident에서 추가 payload 수집이 꼭 필요하면 IC와 Security/Data owner의 시간 제한 승인을 받고 격리된 log group에 기록합니다. 종료 시 retention과 삭제 증적을 남깁니다.
6. Kubernetes Secret은 환경변수보다 volume 또는 external secret provider를 우선합니다. 환경변수는 diagnostic output에 노출될 수 있습니다. [EKS secrets guidance](https://docs.aws.amazon.com/eks/latest/best-practices/data-encryption-and-secrets-management.html)를 참고합니다.

### 4.5 Current retention과 Target tiering matrix

Control plane 5종은 EKS가 하나의 log group에 전달하므로 CloudWatch retention을 stream별로 다르게 설정할 수 없습니다. Current hot retention은 그대로 유지하고, Target 중앙 archive에서 source/stream prefix와 data class별 Lifecycle을 분리합니다.

| 환경·데이터 | Current CloudWatch hot | Target 중앙 S3 | 무결성/완료 evidence |
| --- | --- | --- | --- |
| `dev` control plane | 90일 | 기본 90일, 필요 시 archive 제외 | IaC retention과 실제 log group 일치 |
| `dev` Container Insights 4종 | 30일 | 기본 90일 | application/dataplane/host/performance query |
| `stg` control plane | 90일 | 1년 | release 재현 기간과 Lifecycle 검증 |
| `stg` Container Insights 4종 | 90일 | 180일 | source/archive count reconciliation |
| `prod` control plane 5종 | 365일 | 일반 source 1년, audit/authenticator 7년 초기 기준 | audit prefix, versioning, KMS, 승인된 Object Lock |
| `prod` Container Insights 4종 | 365일 | 1년 초기 기준 | 중앙 archive query와 복원 시간 측정 |
| 보안 incident legal hold | 기존 retention 연장 | 사건 종료 정책 | Object Lock/legal hold, 일반 lifecycle 제외 |

7년 audit 보존은 법적 기본값이 아니라 이 포트폴리오의 초기 보안 기준입니다. Security, Data owner, Legal이 더 짧거나 긴 법적 기간을 승인하면 그 결정을 기록합니다. 중앙 archive의 완전성과 검색 RTO가 입증된 뒤에만 CloudWatch hot retention 단축을 별도 FinOps 변경으로 검토합니다. CloudWatch와 S3에 같은 데이터를 불필요하게 장기 중복 보존하지 않으며, retention 축소 전에는 incident 보존 여부를 확인합니다.

### 4.6 Pipeline 자체의 운영 지표

- Fluent Bit `DaemonSet` desired/ready 불일치, restart/OOM, retry, dropped record, buffer 사용량
- CloudWatch subscription `DeliveryErrors`, `DeliveryThrottling`, 전달 지연, Firehose failure와 S3 backup prefix 적재
- 각 source별 last event age와 5분 이상 무수집 gap
- KMS `AccessDenied`, bucket policy denial, lifecycle/Object Lock 변경 event
- 일일 source-to-destination count/byte reconciliation. Subscription은 at-least-once로 중복이 가능하므로 downstream은 event ID로 중복을 허용하거나 제거합니다.

초기 목표는 `prod` 필수 source의 99.9%가 5분 안에 hot backend에 검색 가능하고, archive 전달 실패가 15분 이상 지속되지 않는 것입니다. 실제 처리량 baseline을 2~4주 수집한 뒤 SLO와 threshold를 조정합니다.

## 5. Kubernetes QoS와 workload reliability

Kubernetes의 QoS class는 수동 label이 아니라 Pod 내 모든 container의 CPU/memory `requests`와 `limits` 관계로 결정되며, node pressure에서 eviction 순서에 영향을 줍니다. 자세한 기준은 [Pod QoS classes](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/)를 따릅니다.

### 5.1 Requests와 limits 원칙

- Scheduler와 node autoscaler는 실제 사용량이 아니라 주로 `requests`를 기준으로 배치·용량을 판단합니다. 너무 낮은 request는 과밀 배치와 OOM/latency를, 너무 높은 request는 Pending과 낭비를 만듭니다.
- Memory limit 초과는 container OOM kill로 이어질 수 있습니다. CPU limit 초과는 일반적으로 throttling을 유발하므로 latency-sensitive workload는 부하 시험과 throttling metric으로 limit 사용 여부를 결정합니다.
- 모든 app, init container, sidecar에 requests/limits를 검토합니다. Sidecar 누락도 Pod QoS와 node 용량 계산을 왜곡합니다.
- `prod` workload의 BestEffort는 금지합니다. 단기 debug Pod도 명시적 최소 request/limit, TTL, owner, ticket을 가져야 합니다.
- 수치는 추측으로 고정하지 않습니다. `stg` 부하 시험과 2~4주 p95/p99/peak, OOM, CPU throttle, working set을 근거로 변경합니다.

### 5.2 QoS 사용 기준

| 등급 | 생성 조건 요약 | 사용 기준 | 운영 주의 |
| --- | --- | --- | --- |
| Guaranteed | 모든 container에 CPU·memory request와 limit가 있고 각 resource가 동일 | 반드시 살아야 하는 작은 platform component, 예측 가능한 memory workload | CPU limit throttling과 과도한 reservation을 검증 |
| Burstable | Guaranteed가 아니며 하나 이상의 request/limit 존재 | 일반 서비스, worker, 탄력적 workload의 기본 | request 초과 사용 중 node pressure이면 eviction 후보가 될 수 있음 |
| BestEffort | CPU·memory request/limit 모두 없음 | `prod` 금지, 격리된 실험 환경만 예외 | node pressure에서 우선 eviction 대상 |

QoS와 PriorityClass는 서로 다른 제어입니다. 높은 PriorityClass라고 Guaranteed가 되는 것이 아니며 scheduler preemption은 QoS보다 priority를 사용합니다. Priority는 node-pressure eviction에도 영향을 주므로 둘을 함께 설계합니다.

### 5.3 Namespace baseline: LimitRange와 ResourceQuota

`LimitRange`는 container/PVC별 기본값과 최소·최대를, `ResourceQuota`는 namespace 전체 합계와 object 수를 제한합니다. API admission 시 적용되며 이미 생성된 Pod를 소급 변경하지 않습니다. [LimitRange](https://kubernetes.io/docs/concepts/policy/limit-range/)와 [ResourceQuota](https://kubernetes.io/docs/concepts/policy/resource-quotas/)를 참고합니다.

Current 구현은 다음과 같습니다. 이는 Terraform object가 정의되었다는 evidence이며, 실제 cluster admission test를 통과했다는 evidence는 아닙니다.

| 환경 namespace | 기본 request | 기본 limit | Namespace request quota | Pod/PVC/LB 상한 |
| --- | --- | --- | --- | --- |
| `application-dev` | 100m / 128Mi | 500m / 512Mi | CPU 4 / memory 8Gi | 50 / 10 / 2 |
| `application-stg` | 250m / 256Mi | 1 CPU / 1Gi | CPU 12 / memory 24Gi | 150 / 20 / 4 |
| `application-prod` | 250m / 512Mi | 1 CPU / 2Gi | CPU 40 / memory 80Gi | 400 / 50 / 8 |

다음 manifest는 object 관계를 설명하는 Target reference입니다. repository의 환경별 값과 별도로 적용하지 않으며 workload profile에 맞춰 조정해야 합니다.

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: workload-defaults
  namespace: example
spec:
  limits:
    - type: Container
      defaultRequest:
        cpu: 100m
        memory: 128Mi
      default:
        cpu: 500m
        memory: 512Mi
      min:
        cpu: 25m
        memory: 32Mi
      max:
        cpu: "4"
        memory: 8Gi
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: workload-budget
  namespace: example
spec:
  hard:
    requests.cpu: "16"
    requests.memory: 32Gi
    limits.cpu: "32"
    limits.memory: 64Gi
    requests.storage: 2Ti
    persistentvolumeclaims: "20"
    pods: "200"
    services.loadbalancers: "2"
```

- 기본값은 누락을 안전하게 막는 최후의 방어선입니다. 실제 workload manifest에는 측정된 값을 명시합니다.
- Quota는 namespace의 정상 peak, HPA `maxReplicas`, rolling update surge, Job 병렬도, 복구 시 임시 replica를 합쳐 정합니다.
- Quota 사용률 80%는 Warning, 90%와 quota denial 증가는 Critical 후보로 두되 Pending 원인과 함께 판단합니다.
- `prod` namespace 생성 pipeline은 owner, cost center, data class, LimitRange, ResourceQuota, PSS, NetworkPolicy, log retention, alert route가 없으면 실패해야 합니다.

### 5.4 PriorityClass와 preemption

Current catalog는 `platform-critical`, `application-high`, `batch-low` 세 개이며 모두 Terraform으로 생성됩니다. 추가 class는 Target change로 취급합니다.

| class | 구현 상태/대상 | 원칙 |
| --- | --- | --- |
| Kubernetes 예약 class | EKS 핵심 system component만 | `system-cluster-critical`, `system-node-critical`을 application이 사용하지 못하게 함 |
| `platform-critical` | Current / CNI·CSI·DNS, admission, autoscaler, logging/monitoring 핵심 경로 | Platform 승인, ResourceQuota로 사용 범위 제한 |
| `application-high` | Current / 승인된 고객 경로 | Service+Platform 승인, 낮은 priority workload에 미칠 영향 검증 |
| 기본 priority | Kubernetes 기본 / 일반 web·worker | 별도 class가 없으면 0이며 global default class는 현재 없음 |
| `batch-low` | Current / 재시도 가능한 batch·개발 작업 | `preemptionPolicy: Never`로 다른 Pod를 축출하지 않음 |

PriorityClass는 cluster-scoped이므로 application team이 임의 생성하지 않습니다. 높은 priority의 남용은 다른 workload를 preempt할 수 있고 PDB 준수도 best-effort입니다. [Pod Priority and Preemption](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/)을 기준으로 승인된 catalog와 namespace별 quota를 운영합니다.

### 5.5 PDB, replica, topology

Current module에는 PDB를 생성할 수 있는 typed interface와 validation이 있지만 `dev`, `stg`, `prod` platform root가 값을 전달하지 않아 실제 PDB instance는 0개입니다. 아래 PDB/topology 기준과 workload instance 생성은 Target입니다.

- 고객 경로 workload는 정상 시 최소 2개 이상의 replica를 사용하고, 단일 node/AZ 장애가 전체 replica를 잃지 않도록 `topology.kubernetes.io/zone`과 `kubernetes.io/hostname` 기준 spread를 둡니다.
- `topologySpreadConstraints`의 `maxSkew: 1`을 시작점으로 하며, 중요 workload는 `DoNotSchedule`, 일반 workload는 capacity 부족 시 `ScheduleAnyway`를 선택할 수 있습니다. 선택은 가용성과 schedulability trade-off를 ticket에 기록합니다. [Topology spread constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/)를 참고합니다.
- PDB는 node drain, managed node update 같은 voluntary disruption만 제한하며 node 장애, OOM, application rolling update의 모든 불가용성을 막지 않습니다.
- 동일 controller의 replica가 변하는 workload는 보통 `maxUnavailable: 1` 또는 percentage가 관리하기 쉽습니다. `maxUnavailable: 0`은 drain을 영구 차단할 수 있으므로 명시적 예외와 해제 runbook이 필요합니다.
- PDB selector가 실제 Pod label과 일치하고 `status.disruptionsAllowed > 0`인지 maintenance 전 확인합니다. [PodDisruptionBudget guidance](https://kubernetes.io/docs/tasks/run-application/configure-pdb)를 따릅니다.
- readiness probe는 traffic 수신 가능 상태, liveness probe는 복구 불가능한 deadlock, startup probe는 느린 기동을 구분합니다. 모든 replica를 동시에 재시작하게 만드는 공격적인 liveness 설정을 금지합니다.
- `terminationGracePeriodSeconds`, `preStop`, connection draining, queue checkpoint를 application timeout과 load balancer deregistration 시간에 맞춥니다.

예시:

```yaml
spec:
  replicas: 3
  template:
    metadata:
      labels:
        app.kubernetes.io/name: api
    spec:
      priorityClassName: service-critical
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app.kubernetes.io/name: api
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              app.kubernetes.io/name: api
```

## 6. Autoscaling 운영

### 6.1 Scaling chain

```text
business load → application metric → HPA replica → unschedulable Pod
              → node autoscaler(Karpenter 또는 Cluster Autoscaler) → EC2 node
```

1. HPA는 workload replica를, Karpenter/Cluster Autoscaler는 node capacity를 관리합니다.
2. 같은 node pool/ASG를 두 node autoscaler가 동시에 제어하지 않습니다.
3. Metrics Server는 HPA용 point-in-time resource metric source이며 장기 모니터링 저장소가 아닙니다. [EKS Metrics Server](https://docs.aws.amazon.com/eks/latest/userguide/metrics-server.html)를 참고합니다.
4. CPU percentage HPA는 CPU request를 분모로 사용하므로 request 정확도가 필수입니다. Queue consumer는 queue oldest age/depth, API는 RPS/concurrency/latency처럼 saturation을 선행하는 custom/external metric을 우선 검토합니다.
5. HPA `minReplicas`는 AZ 장애와 maintenance 중에도 SLO를 지킬 수 있게 정하고, `maxReplicas`는 ResourceQuota, downstream connection/quota, node maximum과 일관되어야 합니다.
6. 급격한 scale-in을 막는 stabilization window와 step policy를 두고 배포 직후 warm-up 동안 잘못된 축소를 방지합니다.

### 6.2 VPA와 right-sizing

- VPA는 먼저 recommendation/audit mode로만 운영하고 월간 rightsizing review에서 제안을 검토합니다.
- production 자동 변경은 Pod 재생성과 성능 변화를 일으킬 수 있으므로 dev/stg 부하 시험과 change approval 없이는 사용하지 않습니다.
- HPA와 VPA가 같은 CPU/memory signal을 동시에 자동 제어하지 않도록 설계합니다.
- 변경 전후 p95/p99 usage, throttling, OOM, restart, latency, node bin-packing, 비용을 증적으로 남깁니다. AWS도 [EKS compute cost guidance](https://docs.aws.amazon.com/eks/latest/best-practices/cost-opt-compute.html)에서 HPA, VPA recommendation, node autoscaler 조합을 권고합니다.

### 6.3 Node autoscaler 선택

| 조건 | 권장 |
| --- | --- |
| 현재 managed node group/ASG를 단순 운영 | Cluster Autoscaler |
| workload별 instance, AZ, architecture, Spot 다양성과 빠른 scale-out 필요 | Karpenter |
| EKS Auto Mode 도입 | 별도 architecture decision과 migration 검증 후 사용 |

- Cluster Autoscaler version은 cluster version과 맞추고 auto-discovery와 cluster-scoped least privilege IAM을 사용합니다. [EKS Cluster Autoscaler](https://docs.aws.amazon.com/eks/latest/best-practices/cas.html)를 참고합니다.
- Karpenter는 unschedulable Pod의 request, affinity, taint/toleration, topology를 보고 node를 고릅니다. `NodePool.spec.limits`, 허용 instance/zone/capacity type, disruption budget을 정의하고 production AMI는 검증된 release로 고정합니다. [EKS Karpenter guidance](https://docs.aws.amazon.com/eks/latest/best-practices/karpenter.html)를 참고합니다.
- Autoscaler, CNI, DNS, logging 같은 핵심 controller는 autoscaler가 없애지 않는 3-AZ On-Demand system node group 또는 별도 안정된 capacity에 배치합니다.
- Spot은 interruption 허용 workload에만 사용하고 topology, PDB, checkpoint/retry, On-Demand fallback을 함께 제공합니다.

### 6.4 Autoscaling 검증

- scale-out: metric 발생 → HPA 반응 → Pending → node 생성 → Ready → Pod Ready까지 시간을 측정합니다.
- scale-in: PDB, graceful termination, queue drain, connection draining, stateful volume detach를 확인합니다.
- `maxReplicas`, node/EC2 quota, subnet IP, ENI, EBS, load balancer target quota를 peak 이전에 확인합니다.
- 월 1회 synthetic load 또는 scheduled game day로 0/최소 capacity에서 peak까지 검증합니다.

## 7. Observability, SLI/SLO와 알람

### 7.1 수집 계층

| 계층 | 권장 source | 보존/용도 |
| --- | --- | --- |
| Resource/autoscaling | Metrics Server | HPA와 즉시 `kubectl top`; 장기 분석 금지 |
| Kubernetes object state | kube-state-metrics | Pod/Deployment/StatefulSet/PDB/HPA/PVC 상태 |
| Node/container | kubelet/cAdvisor, node exporter 또는 Container Insights | CPU, memory, disk, network, restart, node condition |
| Control plane | API server `/metrics`, control plane logs | request latency/error, inflight, throttling, scheduler/controller 오류 |
| Application | OpenTelemetry SDK 또는 기존 Prometheus exporter | traffic, error, latency, saturation; trace backend는 별도 |
| Synthetic/business | 독립 canary와 business counter | 실제 고객 경로 성공과 누락/중복 |

Current Prometheus retention은 `dev=7일`, `stg=15일`, `prod=30일`이고 `amazon-cloudwatch-observability` add-on도 기본 활성화되어 있습니다. 이 구성은 metric/log source가 존재한다는 evidence이지만 SLO, 외부 Alertmanager receiver route, 장기 capacity trend가 완성되었다는 evidence는 아닙니다. Target은 local Prometheus를 scrape·fast alert·HPA 계층으로 유지하고 중앙 Mimir에 remote write해 dev/stg/prod metric을 30/90/400일 보존합니다. 신규 custom metric은 OpenTelemetry Metrics API/SDK를 사용하며 Prometheus Adapter와 KEDA의 제어 경계를 분리합니다. 상세 설계와 production gate는 [Advanced Metrics and Telemetry Platform](observability-platform.md)을 기준으로 합니다. Container Insights의 cluster/node/pod/service metric은 [Container Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ContainerInsights.html), [EKS metric catalog](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Container-Insights-metrics-EKS.html)을 기준으로 검증합니다.

### 7.2 SLI/SLO catalog

아래 목표는 production service의 초기 예시이며 service owner가 traffic과 business impact를 근거로 승인합니다.

| 범위 | SLI | 초기 목표 | 측정 원칙 |
| --- | --- | --- | --- |
| 고객 API availability | 성공 요청 / 유효 요청 | 월 99.9% 이상 | 잘못된 client 4xx 처리 기준을 명시 |
| 고객 API latency | 정상 요청 p95/p99 | route별 승인 threshold | timeout보다 낮고 dependency budget과 합치 |
| 비동기 처리 | SLO 내 완료 / 접수 | 99.9% 이상 | queue oldest age, DLQ, 누락·중복 포함 |
| Pod availability | desired 대비 ready replica | 중요 workload 99.9% | deployment 중 영향도 포함 |
| Pod startup | create → Ready | p99 기준 승인값 | image pull/init 포함 별도 분해 |
| Control plane | API error/latency | upstream SLI와 baseline | mutating/read 분리 |
| DNS/network | CoreDNS success, CNI IP allocation | 오류율 baseline 이하 | SERVFAIL, timeout, IP 부족 구분 |
| Storage | PVC attach/mount와 I/O latency | 실패 0, latency baseline | AZ mismatch와 CSI error 구분 |
| Log pipeline | source → searchable latency | 99.9%가 5분 이내 | source별 gap과 drop 포함 |
| Metric pipeline | source → local/Mimir query 가능 | 99.9%가 승인 시간 이내 | remote-write/Collector drop과 ingest lag 포함 |
| Backup | schedule 내 성공 recovery point | 100% | parent/child 성공과 issue message 부재를 함께 확인 |
| Restore | 승인 RPO/RTO 달성 | drill 100% | 기능·데이터 무결성까지 검증 |

CloudWatch Application Signals를 선택하면 latency/availability SLI, error budget, burn-rate alarm을 구성할 수 있습니다. [CloudWatch SLO](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-ServiceLevelObjectives.html)를 참고합니다. Platform SLO와 고객 service SLO는 분리하고, EKS endpoint SLA를 application availability로 대신 사용하지 않습니다.

### 7.3 필수 dashboard

1. **Service overview**: RPS, success/error, p50/p95/p99, saturation, SLO/error budget, deployment marker.
2. **Cluster capacity**: node allocatable/request/usage, Pending, quota, subnet IP, HPA와 node autoscaler decision.
3. **Workload health**: desired/ready, restart, OOMKilled, CrashLoopBackOff, probe failure, CPU throttling, memory working set.
4. **Control plane**: API latency/error/429, inflight, audit 401/403, scheduler pending, webhook latency/failure.
5. **Network/DNS/ingress**: CoreDNS, CNI IP, conntrack, packet drop, ALB target, Istio 4xx/5xx/latency.
6. **Storage**: PVC Pending, attach/mount failure, EBS burst/latency, filesystem usage/inode.
7. **Operations**: add-on/node version, backup/restore, log/OTel/remote-write/Mimir pipeline, certificate expiry, cardinality, cost and quota.

### 7.4 초기 alert policy

Threshold는 2~4주 baseline 뒤 조정하며 minimum traffic와 `for` 시간을 둡니다.

| Severity | 조건 예시 | 라우팅 | 첫 runbook |
| --- | --- | --- | --- |
| Critical | 고객 availability/latency SLO fast burn, 합성 요청 연속 실패 | PagerDuty/전화 + 독립 Slack/Email | service path triage |
| Critical | `cluster_failed_node_count > 0`이고 replica/SLO 영향, 다중 AZ node loss | PagerDuty | node failure |
| Critical | CoreDNS/CNI/CSI 전체 replica 불가, admission webhook이 API write 차단 | PagerDuty | platform dependency |
| Critical | audit log 중단, archive 전달 실패 장기 지속, GuardDuty high/critical | Security on-call + IC | evidence/security |
| Critical | backup failed/partial 후 RPO 초과, restore drill RTO 초과 | Operations + Data owner | backup/restore |
| Warning | Pending Pod 10분, HPA max 지속, node request 80% 이상 | Platform Slack | autoscaling/capacity |
| Warning | OOMKilled/restart 증가, CPU throttling과 latency 동반 | Service Slack | QoS/right-sizing |
| Warning | PDB `disruptionsAllowed=0`, node AMI/add-on/version 지원 종료 임박 | Platform/Operations | maintenance readiness |
| Warning | PVC usage 80%, inode 80%, attach/mount 오류 증가 | Service+Operations | storage |
| Warning | Collector queue 70%, remote-write backlog, tenant cardinality budget 80% | Monitoring+Platform | telemetry pipeline |
| Critical | Collector/remote-write drop 또는 Mimir ingest 실패가 metric SLO 초과 | Monitoring on-call + 독립 CloudWatch 경로 | telemetry pipeline |
| Info | 배포/upgrade/backup 완료, HPA scale event | change channel | post-change verify |

알람에는 cluster, environment, namespace, workload, 현재값/threshold, 시작 시각, dashboard, 최근 배포, runbook URL, owner를 포함합니다. 같은 incident의 Pod별 알람은 service 단위로 deduplicate하고, maintenance suppression은 대상·승인자·만료 시각·복구 확인자를 기록합니다.

## 8. 백업, 복구와 DR

### 8.1 보호 단위

| 대상 | 보호 방식 | 백업이 대체하지 않는 것 |
| --- | --- | --- |
| Terraform/platform config | Git, protected branch, release artifact, remote state versioning | AWS/Kubernetes runtime data |
| EKS cluster state | AWS Backup EKS composite recovery point | 외부 dependency 전체와 image registry |
| EBS/EFS/S3 PVC | EKS composite에 포함되는 지원 CSI storage와 service별 backup | application-consistent quiesce, DB PITR |
| RDS/DynamoDB 등 외부 data | 각 service의 backup/PITR/replication | Kubernetes manifest |
| ECR image/chart | digest 고정, cross-account/Region 복제, release retention | EKS backup은 container image를 포함하지 않음 |
| Secret/KMS/IAM | IaC, external secret backup, key/role DR 설계 | cluster object만 복구해도 KMS/IAM dependency는 자동 해결되지 않음 |

AWS Backup은 EKS cluster state와 지원되는 EBS/EFS/S3 PVC를 composite recovery point로 보호합니다. Parent job이 `COMPLETED`여도 일부 Kubernetes object가 실패하면 issue 메시지가 남을 수 있고, child recovery point가 실패하거나 composite recovery point가 partial일 수 있습니다. 따라서 parent status만으로 성공 처리하지 않습니다. 지원되지 않는 CSI migration/in-tree volume, 일부 EFS subpath, FSx 등의 제한은 [Amazon EKS backups](https://docs.aws.amazon.com/aws-backup/latest/devguide/eks-backups.html)에서 매 release 확인합니다.

### 8.2 복구 등급

| Tier | 예시 | 초기 RPO | 초기 RTO | 요구사항 |
| --- | --- | --- | --- | --- |
| Tier 0 | 결제/핵심 거래 | 15분 이하 | 1시간 이하 | 애플리케이션·data service의 multi-Region replication과 warm/active cluster 필요 |
| Tier 1 | 주요 고객 API | 4시간 | 4시간 | 일 6회 이상 recovery point 또는 data별 PITR, secondary Region 준비 |
| Tier 2 | 일반 내부 서비스 | 24시간 | 8시간 | 일일 backup과 IaC 재구성 |
| Tier 3 | 재생성 가능한 dev/batch | Git 기준 | 24시간 | data backup 예외를 Data owner가 승인 |

Daily backup만으로 Tier 0/1 RPO를 충족한다고 선언하지 않습니다. Database, queue, object storage의 실제 복제·PITR와 workload checkpoint를 함께 계산합니다.

### 8.3 Backup policy

- `prod` EKS cluster ARN이 tag selection에 실제 포함되고 composite recovery point가 만들어지는지 배포 후 확인합니다.
- Backup Vault는 workload account와 분리된 backup account copy를 기본으로 하고, Tier 0/1은 승인된 secondary Region copy를 추가합니다.
- KMS encryption, 최소 권한 backup/restore role, Vault Lock, deletion alarm을 적용합니다. Vault Lock 변경 가능 기간과 retention은 Data/Security 승인 후 고정합니다.
- Backup/restore job 실패, `COMPLETED` 상태의 issue 메시지, composite partial, child recovery point 실패, copy 실패를 SNS/EventBridge notification과 정기 reconciliation으로 탐지합니다. API/notification event 이름은 적용 시점의 AWS Backup 공식 enum을 조회해 사용합니다.
- backup window가 peak, batch, DB snapshot과 충돌하지 않도록 조정하고 application-consistent snapshot이 필요한 workload는 pre/post hook 또는 service-native backup을 사용합니다.
- 새 CRD/CSI/storage type을 배포할 때 backup/restore 지원 여부를 release gate에서 확인합니다.

### 8.4 Restore 절차

AWS Backup의 EKS restore는 기존 object를 덮어쓰지 않는 non-destructive 방식이므로 “완료” 상태만 보고 복구 성공으로 판단하면 안 됩니다. [Restore an EKS cluster](https://docs.aws.amazon.com/aws-backup/latest/devguide/restoring-eks.html)를 기준으로 다음 순서를 사용합니다.

1. Incident/change ticket, recovery point, 대상 account/Region, namespace/full restore, RPO/RTO, Data owner, 폐기 책임자를 확정합니다.
2. 원본과 분리된 account/VPC/namespace 또는 새 cluster를 Terraform으로 준비합니다. private API 접근, KMS, security group, DNS, quota를 확인합니다.
3. 대상 Kubernetes version/API compatibility, CRD, EKS add-on/CSI driver, StorageClass, AZ와 EBS volume mapping을 먼저 준비합니다.
4. Pod Identity/IAM role, IRSA OIDC trust, external secret, image registry와 cross-account/Region permission을 복구합니다. Cross-cluster portability에는 cluster별 OIDC trust가 없는 Pod Identity를 우선 검토합니다.
5. namespace 또는 full composite restore를 실행하고 skipped/failed object 알림을 확인합니다. 기존 object와 이름이 충돌하면 자동 overwrite되지 않으므로 차이를 수동 검토합니다.
6. Deployment/StatefulSet ready, Service/Ingress, PVC mount, DNS, AWS API 권한, synthetic transaction, data count/checksum과 business invariant를 검증합니다.
7. 실제 RPO/RTO, 누락 object, 수동 단계, 비용, 보안 접근과 query 증적을 ticket에 기록합니다.
8. 검증 환경과 복구 data를 승인된 retention에 따라 폐기합니다. production failover는 별도 IC/변경 승인으로 수행합니다.

### 8.5 Drill cadence와 DR

- 매월: 무작위 namespace + PVC restore, application smoke test.
- 분기: 새 cluster full restore, IAM/CSI/image/network dependency 포함 RPO/RTO 측정.
- 반기: secondary Region에서 Tier 0/1 failover game day, DNS/traffic 전환과 failback 포함.
- 모든 drill은 backup job 성공이 아니라 고객 경로와 data integrity 검증을 종료 조건으로 합니다.

EKS control plane은 Region 내 여러 AZ에 걸쳐 관리되지만 Region 장애를 자동 복구하는 multi-Region service는 아닙니다. Regional DR은 별도 EKS cluster, 복제된 artifact/data, 독립 quota·KMS·IAM·network, traffic steering이 필요합니다. [EKS resiliency](https://docs.aws.amazon.com/eks/latest/userguide/disaster-recovery-resiliency.html)와 AWS Well-Architected의 [periodic recovery test](https://docs.aws.amazon.com/wellarchitected/latest/framework/rel_backing_up_data_periodic_recovery_testing_data.html)를 따릅니다.

## 9. Upgrade, add-on과 node lifecycle

### 9.1 Version policy

- cluster, managed node group, `kubelet`, `kube-proxy`, CoreDNS, VPC CNI, CSI, controllers, Helm chart, CRD, client의 version inventory와 지원 종료일을 월 1회 갱신합니다.
- EKS standard support 안에서 운영하고 extended support 진입은 비용·보안 위험을 명시한 예외 승인을 요구합니다.
- Kubernetes minor version은 한 번에 하나만 `dev → stg → prod` 순서로 올립니다. `kubectl`과 component skew는 Kubernetes [Version Skew Policy](https://kubernetes.io/releases/version-skew-policy/)와 더 엄격한 EKS 조건을 따릅니다.
- Terraform이 호환 가능한 최신 add-on을 plan 시 조회하더라도 production은 검증된 plan의 exact version과 configuration을 release manifest에 기록합니다. “latest”를 무검증 자동 승격하지 않습니다.

### 9.2 Upgrade gate와 순서

**30~14일 전**

1. EKS version lifecycle, release note, API deprecation, cluster upgrade insight를 확인합니다.
2. CRD와 admission webhook conversion, Helm/chart/controller/add-on 호환 matrix를 만듭니다.
3. `kubectl`/client, node AMI, CNI/CSI, service mesh, autoscaler의 target version을 고정합니다.
4. backup과 restore 결과, capacity surge, subnet IP/EC2 quota, PDB, topology, rollback owner를 확인합니다.
5. `dev`와 `stg`에서 load, scale, drain, network, volume, DNS, auth, synthetic transaction을 검증합니다.

**변경 창**

1. ticket, plan hash, 두 명 review, change freeze, IC/rollback owner, dashboard를 확인합니다.
2. 최신 recovery point와 control plane/audit log 수집 상태를 확인합니다.
3. control plane을 한 minor version upgrade합니다. 시작 후 중단할 수 없으므로 사전 gate를 통과하지 못하면 시작하지 않습니다.
4. 호환 matrix에 따라 EKS managed add-on과 platform controller를 단계별로 업데이트하고 각 단계의 health를 확인합니다.
5. 새 launch template/AMI의 managed node group을 작은 batch로 교체합니다. Current 기본과 `stg/prod`는 `max_unavailable_percentage = 25`, `dev` general group은 50입니다. 이 값이 실제 replica/PDB와 spare capacity에 안전한지는 upgrade마다 다시 검토합니다.
6. Helm/Istio는 canary/revision 방식으로 data plane을 순차 전환합니다.
7. 최소 30~60분 SLO, 5xx/latency, Pending/restart/OOM, DNS/CNI/CSI, audit, autoscaler, backup을 관찰합니다.

AWS의 전체 흐름은 [Update EKS cluster](https://docs.aws.amazon.com/eks/latest/userguide/update-cluster.html)와 [managed node update phases](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-update-behavior.html)를 따릅니다.

### 9.3 Rollback/forward-fix

현재 EKS는 in-place upgrade 뒤 7일 안에 직전 minor version으로 control plane rollback을 지원합니다. 그러나 managed node group, self-managed node, EKS add-on과 application은 자동 rollback 대상이 아니며 운영자가 호환성을 맞춰야 합니다. [EKS rollback](https://docs.aws.amazon.com/eks/latest/userguide/rollback-cluster.html)을 기준으로 합니다.

- upgrade 전에 이전 node launch template/AMI, add-on/chart, application release artifact를 보존합니다.
- rollback readiness insight의 `ERROR`/`UNKNOWN`을 강제로 우회하지 않습니다. Security/Platform/Reviewer가 위험을 서면 승인한 emergency만 예외입니다.
- 이미 새 API로 object가 저장되었는지 확인합니다. Control plane rollback은 etcd data를 삭제하지 않으므로 incompatible object가 남을 수 있습니다.
- 7일 이후 또는 복합 migration은 blue/green cluster와 traffic migration을 사용합니다.
- database/schema처럼 비가역 변경은 Kubernetes rollback과 분리된 forward-compatible migration 절차를 가집니다.

### 9.4 Node/AMI 운영

- Node를 장기 patch하는 pet으로 취급하지 않고 검증된 AL2023 AMI/launch template로 immutable 교체합니다.
- Critical/High CVE와 AMI release를 주간 검토하고 저장소 공통 CVE SLA를 적용합니다.
- 새 node가 Ready이고 CNI/CSI/log/security DaemonSet이 배치된 후 기존 node를 cordon/drain합니다.
- PDB, local storage, daemonset, long termination, volume detach를 점검하며 `--force`, `--delete-emptydir-data`, PDB 무시 사용은 별도 승인 없이는 금지합니다.
- Managed node auto repair를 도입할 때 repair threshold, PDB 영향, 알람, maintenance와의 충돌을 먼저 game day로 검증합니다.
- SSM은 read-only 진단과 승인된 break-glass에만 사용하고 node에서 수동 package 변경을 영구 해결책으로 남기지 않습니다.
- Node root disk의 container log/image 사용량, inode, image GC, ephemeral storage request/limit을 감시합니다.

## 10. Security 운영 기준

1. **API access**: private endpoint를 유지하고 VPN/DX/SSM-connected runner 또는 self-hosted CI에서만 접근합니다. Access Entry는 federated short-lived IAM role을 사용하고 cluster-admin은 최소 인원·JIT·MFA로 제한합니다. [EKS access entries](https://docs.aws.amazon.com/eks/latest/userguide/access-entries.html)를 참고합니다.
2. **Kubernetes authorization**: namespace Role/RoleBinding을 기본으로 하고 wildcard verb/resource와 Secret `list/watch`를 제한합니다. Break-glass 사용과 RBAC 변경은 audit alarm을 발생시킵니다.
3. **Workload identity**: application별 service account와 EKS Pod Identity role을 사용하며 node role credential을 사용하지 않습니다. IMDS 접근을 제한하고 `hostNetwork` 예외를 review합니다. [EKS Pod Identity](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html)를 참고합니다.
4. **Pod security**: restricted PSS를 `audit`/`warn`으로 검증한 뒤 application namespace에 version-pinned `enforce`로 승격합니다. privileged, hostPID/IPC, hostPath, root, privilege escalation, unrestricted capability는 승인된 system namespace만 예외로 둡니다. [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)를 따릅니다.
5. **Network**: namespace별 ingress/egress default-deny 후 DNS, ingress, approved dependency, observability만 허용합니다. VPC CNI NetworkPolicy는 명시적으로 기능을 켜야 하며 strict startup enforcement를 검토합니다. [EKS NetworkPolicy](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html)를 참고합니다.
6. **Secret/data**: KMS envelope encryption, Secrets Manager/external provider, rotation, volume mount, Secret access audit를 적용합니다. backup/restore role도 KMS decrypt 범위를 최소화합니다.
7. **Supply chain**: private ECR, immutable tag와 digest deploy, ECR/Inspector continuous scan, SBOM, 서명/attestation admission을 적용합니다. Critical 취약 image는 예외 ticket 없이 배포하지 않습니다. [EKS image security](https://docs.aws.amazon.com/eks/latest/best-practices/image-security.html)를 참고합니다.
8. **Detection**: audit 401/403, anonymous request, Secret access, Role/ClusterRoleBinding, exec/attach, privileged Pod, NetworkPolicy/PSS 변경을 탐지합니다. GuardDuty EKS Protection과 Runtime Monitoring 도입 시 agent coverage와 비용, Fargate/Hybrid 제한을 확인합니다. [GuardDuty EKS Runtime Monitoring](https://docs.aws.amazon.com/guardduty/latest/ug/how-runtime-monitoring-works-eks.html)을 참고합니다.
9. **Encryption**: control plane log, Prometheus/Grafana volume, workload PVC, backup vault, archive bucket의 KMS key owner와 rotation/recovery를 문서화합니다.
10. **Evidence**: 침해 의심 시 원본 log retention을 늘리고 snapshot/recovery point를 보존합니다. Pod/node를 삭제하기 전에 Security가 필요한 volatile evidence와 isolation 방식을 결정합니다.

## 11. Incident runbook

### 11.1 공통 절차

1. IC가 incident ID, severity, 고객 영향, 시작 시각, 대상 cluster/namespace/service를 선언합니다.
2. 최근 배포/upgrade/scale/권한 변경과 SLO를 확인합니다.
3. 사실, 가설, 추가 확인을 분리하고 모든 시간은 UTC와 KST를 함께 기록합니다.
4. read-only 진단을 우선하고 restart, drain, scale, rollback, failover, policy 완화는 IC 승인 후 실행합니다.
5. 완화 뒤 synthetic/business invariant, backlog drain, 중복·누락, data integrity를 확인합니다.
6. 장애 복구와 영구 수정은 별도 ticket/PR로 분리하고 postmortem을 남깁니다.

기본 증적 명령:

```bash
kubectl get nodes -o wide
kubectl get pods -A -o wide
kubectl get events -A --sort-by=.lastTimestamp
kubectl get deploy,statefulset,daemonset,hpa,pdb -A
kubectl top nodes
kubectl top pods -A --containers
kubectl get pvc,pv -A
kubectl auth can-i --list
aws eks describe-cluster --name <cluster> --region <region>
aws eks list-addons --cluster-name <cluster> --region <region>
```

Output에는 secret, token, environment dump를 첨부하지 않습니다. `kubectl describe pod`도 environment reference와 annotation을 포함할 수 있으므로 ticket 첨부 전에 마스킹합니다.

### 11.2 Pod restart, OOMKilled, CrashLoopBackOff

1. Ready/desired, restart delta, `lastState`, exit code, OOMKilled, probe failure, CPU throttle, memory working set을 확인합니다.
2. 같은 release/AZ/node/image/config/secret에 묶이는지 비교합니다.
3. application log의 직전 종료와 node kernel OOM/disk pressure를 상관 분석합니다.
4. Memory limit만 올리기 전에 leak, request/limit, HPA, node pressure를 구분합니다.
5. 고객 영향이 있으면 승인된 이전 release rollback 또는 replica 확장을 사용합니다. 반복 restart를 감추기 위한 liveness 완화는 변경 ticket으로 처리합니다.

### 11.3 Pending Pod 또는 scale-out 실패

1. Pod event의 `FailedScheduling` reason, request, taint/toleration, affinity/topology, PVC, quota를 확인합니다.
2. HPA desired/max, node autoscaler log, NodePool/ASG max, EC2 quota, subnet IP/ENI를 확인합니다.
3. `DoNotSchedule` topology와 실제 사용 가능한 AZ, PDB/priority preemption을 확인합니다.
4. 임의 request 축소보다 capacity/quota 원인을 먼저 해소합니다. Emergency capacity 증가는 IC+Platform 승인 후 만료/원복 계획을 둡니다.

### 11.4 NodeNotReady와 drain 실패

1. node condition, lease age, EC2/system status, kubelet/containerd, CNI, disk/inode, network를 확인합니다.
2. 영향 Pod가 다른 AZ/node에서 Ready인지 확인하고 PDB `disruptionsAllowed`를 봅니다.
3. Managed node repair/ASG/Karpenter action과 동시에 수동 작업하지 않습니다.
4. Cordon/drain/terminate는 IC 또는 change approver가 승인합니다. PDB 차단은 service owner가 capacity를 확보하거나 예외 시간을 승인한 뒤 처리합니다.

### 11.5 5xx/latency 또는 queue lag

1. synthetic와 SLO로 고객 영향을 확인합니다.
2. ingress/mesh → application → queue/worker → external dependency 순서로 traffic, error, latency, saturation을 비교합니다.
3. HPA max, CPU throttle/OOM, connection/thread pool, DNS, TGW 중앙 egress, downstream quota를 확인합니다.
4. 확장이 downstream 과부하를 악화시키지 않는지 확인한 뒤 scale, rate limit, queue pause, rollback 중 승인된 완화를 선택합니다.

### 11.6 API 401/403/429 또는 control plane 지연

1. audit `authorization.k8s.io/decision/reason`, user, source IP, verb/resource와 authenticator log를 확인합니다.
2. Access Entry/RBAC 변경, expired token, webhook latency/failure, controller의 list/watch storm과 API 429를 확인합니다.
3. 권한 확대나 webhook bypass를 즉시 적용하지 않습니다. Security/Platform 승인과 최소 범위/만료를 둡니다.
4. API latency가 높으면 bulk list, client retry/backoff, controller replica와 request pattern을 확인합니다.

### 11.7 DNS/CNI/NetworkPolicy

1. CoreDNS ready/restart/latency/SERVFAIL, upstream resolver를 확인합니다.
2. `aws-node`와 network policy agent, IPAMD, subnet free IP, ENI quota를 확인합니다.
3. NetworkPolicy/PSS/admission의 최근 변경과 denied flow를 확인합니다.
4. default-deny 전체 해제 대신 필요한 source/destination/port만 시간 제한으로 허용합니다.

### 11.8 PVC attach/mount/I/O

1. PVC/PV/StorageClass/CSI event, volume AZ와 node AZ, CSI controller/node Pod를 확인합니다.
2. EBS/EFS quota, KMS permission, security group/NFS path, filesystem usage/inode를 확인합니다.
3. 강제 detach 또는 volume 삭제는 data owner 승인과 snapshot/recovery point 확인 없이는 수행하지 않습니다.
4. 복구 후 application checksum/transaction과 backup 상태를 검증합니다.

### 11.9 로그 유실 또는 지연

1. 애플리케이션이 `stdout`/`stderr`에 쓰는지, node local log rotation과 disk pressure를 확인합니다.
2. Fluent Bit desired/ready, buffer/retry/drop, IAM/KMS/network endpoint를 확인합니다.
3. CloudWatch log group/stream last event, subscription error/throttle, Firehose/S3 failure prefix를 확인합니다.
4. 원본 node를 교체하기 전에 가능한 local log와 incident evidence를 보존합니다. 수집 복구 후 gap과 source/archive count를 기록합니다.

### 11.10 침해 의심

1. Security incident로 승격하고 일반 장애 채널에서 secret/원본 증적을 공유하지 않습니다.
2. audit, CloudTrail, GuardDuty, runtime, VPC Flow Logs, image digest, Pod/node identity를 보존합니다.
3. 격리 방법은 NetworkPolicy/security group/traffic removal 중 증거 훼손과 고객 영향을 고려해 Security+IC가 승인합니다.
4. credential·secret 회전, image rebuild, node immutable replacement, RBAC/Pod Identity 수정은 containment와 eradication 단계로 분리합니다.

## 12. FinOps 운영

- AWS CUR split cost allocation data를 활성화해 cluster, namespace, workload, Pod의 CPU/memory shared EC2 비용을 배분합니다. `cost-center`, `application`, `owner`, `environment` label을 표준화하고 management account에서 cost allocation tag를 활성화합니다. [EKS Kubernetes label cost allocation](https://docs.aws.amazon.com/cur/latest/userguide/split-cost-allocation-data-kubernetes-labels.html)을 참고합니다.
- requests 대비 사용률, node allocatable 대비 request/usage, HPA max 체류, idle node, DaemonSet overhead를 주간 검토합니다. 절감은 request를 무조건 줄이는 것이 아니라 SLO와 OOM/throttle를 함께 봅니다.
- 안정적인 system/baseline은 On-Demand/Savings Plans 후보, interruption-safe workload는 diversified Spot 후보로 분리합니다. 구매는 FinOps owner 승인 사항입니다.
- AZ 간 호출, TGW·중앙 egress, external image pull, cross-Region log/backup, EBS/EFS, LoadBalancer 수를 월간 점검합니다.
- log level, retention, duplicate pipeline, high-cardinality metric/label, trace sampling, Logs Insights scan을 서비스별 비용으로 배분합니다. AWS [EKS observability cost guidance](https://docs.aws.amazon.com/eks/latest/best-practices/cost-opt-observability.html)를 따릅니다.
- Karpenter/Cluster Autoscaler의 최대 용량은 비용 ceiling이며 동시에 재해·peak capacity 요구를 충족해야 합니다. 월 예산만으로 scale-out을 차단하지 않고 quota/NodePool limit 변경은 SLO 영향 검토를 거칩니다.

## 13. 변경과 승인

| 변경 | 필수 artifact | Agent review | 사람 승인 | 실행 |
| --- | --- | --- | --- | --- |
| requests/limits, HPA, PDB | 부하 시험, 전후 metric, quota, rollback | Monitoring, Operations, Reviewer | Service + Platform owner | app CI/CD |
| LimitRange/ResourceQuota/PriorityClass | namespace 영향, dry-run/admission test | Platform, Security, Reviewer | Platform owner | protected platform pipeline |
| Control plane/add-on/node upgrade | insight, compatibility matrix, backup, PDB, plan, rollback | Operations, Security, CI/CD, Reviewer | Platform + Service owner | protected CI/CD |
| Log source/retention/masking | data class, 비용, 검색/법적 요구, delivery test | Monitoring, Security, FinOps, Reviewer | Data/Security owner | observability pipeline |
| Backup/restore | recovery point, RPO/RTO, 대상 격리, 폐기 | Operations, Security, Monitoring, Reviewer | Data + Operations owner | authorized operator/runbook |
| Network/PSS/RBAC/Pod Identity | communication/permission matrix, deny test | Security, Platform, Reviewer | Security + resource owner | protected pipeline |
| Emergency scale/restart/drain | incident ID, 영향, 성공/중단 조건, 원복 | Operations/Monitoring read analysis | IC | 승인된 runbook |

모든 production 변경은 다음을 만족해야 합니다.

1. change/incident ticket, environment, data classification, success criteria, max cost, owner가 있습니다.
2. PR에 manifest/Terraform diff, policy scan, plan, 비용, risk, rollback/forward-fix, post-check를 첨부합니다.
3. public endpoint, wildcard IAM/RBAC, audit/retention/KMS 약화, 예상 외 delete/replace가 있으면 중단합니다.
4. 배포 전과 후 동일한 SLI window를 비교하고 deployment marker를 남깁니다.
5. emergency 변경은 만료 시간과 영구 수정 ticket을 만들며 incident 종료 후 자동 또는 확인된 원복을 수행합니다.

## 14. 구현 checklist

체크 항목은 Terraform object의 존재가 아니라 runtime evidence까지 완료해야 닫습니다. `[Current IaC / verify]`는 코드가 있으나 배포·동작 증적이 필요한 항목, `[Target]`은 아직 구현할 항목입니다.

### Phase 0: 소유권과 inventory

- [ ] cluster/namespace/workload별 Platform, Service, on-call, Data owner 등록
- [ ] version/add-on/CRD/CSI/node AMI/support 종료 inventory 자동 생성
- [ ] 업무별 SLO, RPO/RTO, data class, legal retention 승인
- [ ] 현재 resource request/usage, log GB, metric series, cost baseline 수집

### Phase 1: 로그와 관측성

- [ ] `[Current IaC / verify]` CloudWatch Observability collector가 모든 Linux node/taint를 cover하고 resource/PDB/priority가 충분한지 확인
- [ ] `[Current IaC / verify]` application/dataplane/host/performance log group, KMS, 환경별 retention 확인
- [ ] `[Target]` 중앙 subscription/Firehose/S3, failure backup, Object Lock/lifecycle 검증
- [ ] `[Target]` JSON schema와 PII/secret source redaction, CloudWatch data protection policy 적용
- [ ] `[Target]` pipeline gap/drop/error alarm과 source/archive reconciliation 구현
- [ ] `[Current IaC / verify]` Prometheus/Container Insights source와 kube-state/node/control plane/app metric coverage 확인
- [ ] `[Target]` SLO/error budget와 외부 Alertmanager receiver route/runbook URL 등록

### Phase 2: QoS와 availability

- [ ] `[Current IaC / verify]` 환경별 namespace LimitRange/ResourceQuota default·quota admission test
- [ ] `[Target]` namespace template에 owner/data class label, PSS enforce, NetworkPolicy 포함
- [ ] `prod` BestEffort와 resource 누락 admission 차단
- [ ] `[Current IaC / verify]` 3개 PriorityClass catalog와 preemption 동작 확인, namespace별 사용 quota 승인
- [ ] `[Target]` 모든 중요 workload에 probes, graceful termination, HPA, PDB instance, AZ/host topology 적용
- [ ] quota, HPA max, node max, subnet IP, downstream quota 일관성 시험
- [ ] VPA recommendation report와 월간 right-sizing review 운영

### Phase 3: Node와 autoscaling

- [ ] Karpenter 또는 Cluster Autoscaler ADR 작성, 동일 pool 중복 제어 방지
- [ ] system controller용 3-AZ On-Demand capacity와 taint/toleration 검증
- [ ] node autoscaler IAM least privilege, max capacity/cost ceiling, alarm 구현
- [ ] scale-out/scale-in, Spot interruption, PDB, connection/queue drain game day 수행
- [ ] AL2023 AMI pin/release, CVE SLA, immutable replacement와 node repair 절차 구현

### Phase 4: Backup/DR

- [ ] `prod` EKS composite recovery point와 모든 child 상태 확인
- [ ] unsupported CSI/storage와 외부 DB/queue/image dependency gap 등록
- [ ] backup account/secondary Region copy, KMS, Vault Lock, notification 구성
- [ ] 월간 namespace/PVC, 분기 full cluster restore와 checksum/synthetic 검증
- [ ] Tier 0/1 regional failover/failback runbook과 반기 game day 완료
- [ ] drill의 실제 RPO/RTO, skipped object, 수동 단계와 개선 backlog 보관

### Phase 5: Security와 change gate

- [ ] Access Entry/RBAC JIT, break-glass, Secret access audit 구현
- [ ] application별 Pod Identity와 IMDS 차단 검증
- [ ] restricted PSS `enforce`, default-deny NetworkPolicy와 승인 예외 구현
- [ ] ECR digest/immutable/scanning/SBOM/signature admission 구현
- [ ] GuardDuty EKS Protection/Runtime Monitoring coverage와 alarm 검증
- [ ] upgrade insight, deprecated API, add-on matrix, PDB/backup/rollback을 CI gate로 자동화

## 15. 완료 증적

EKS 운영 준비 완료는 문서나 Terraform resource 존재만으로 선언하지 않습니다. 다음 evidence를 release/ticket에 보관합니다.

- log source별 end-to-end 전달, PII masking, archive query와 deletion/lock test
- requests/limits 누락 거부, quota denial, priority/PDB/topology scheduling test
- HPA/node scale-out과 scale-in 측정, peak/Spot/node failure game day
- SLO dashboard, alert fire/route/ack/runbook 실행 결과
- EKS backup composite/child 상태, namespace/full restore, RPO/RTO와 data checksum
- dev/stg upgrade, cluster insight, add-on/node/version inventory, rollback 또는 forward-fix rehearsal
- PSS/NetworkPolicy/RBAC/Pod Identity/image admission과 GuardDuty test finding
- CUR split cost allocation, telemetry 비용, right-sizing 전후 SLO/비용 비교

## 16. 공식 근거

### AWS

- [Amazon EKS control plane logs](https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html)
- [Amazon EKS auditing and logging best practices](https://docs.aws.amazon.com/eks/latest/best-practices/auditing-and-logging.html)
- [CloudWatch Container Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ContainerInsights.html)
- [CloudWatch Logs subscriptions](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Subscriptions.html)
- [CloudWatch sensitive data masking](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/mask-sensitive-data.html)
- [Amazon EKS data plane best practices](https://docs.aws.amazon.com/eks/latest/best-practices/data-plane.html)
- [EKS HPA](https://docs.aws.amazon.com/eks/latest/userguide/horizontal-pod-autoscaler.html)
- [EKS Karpenter best practices](https://docs.aws.amazon.com/eks/latest/best-practices/karpenter.html)
- [EKS Cluster Autoscaler best practices](https://docs.aws.amazon.com/eks/latest/best-practices/cas.html)
- [Amazon EKS and Kubernetes Container Insights metrics](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Container-Insights-metrics-EKS.html)
- [CloudWatch Service Level Objectives](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-ServiceLevelObjectives.html)
- [Amazon EKS backups](https://docs.aws.amazon.com/aws-backup/latest/devguide/eks-backups.html)
- [Restore an Amazon EKS cluster](https://docs.aws.amazon.com/aws-backup/latest/devguide/restoring-eks.html)
- [Update an EKS cluster](https://docs.aws.amazon.com/eks/latest/userguide/update-cluster.html)
- [Rollback an EKS cluster](https://docs.aws.amazon.com/eks/latest/userguide/rollback-cluster.html)
- [EKS security best practices](https://docs.aws.amazon.com/eks/latest/best-practices/security.html)
- [EKS Pod Identity](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html)
- [EKS NetworkPolicy](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy-configure.html)
- [EKS cost optimization](https://docs.aws.amazon.com/eks/latest/best-practices/cost-opt.html)
- [EKS labels for split cost allocation](https://docs.aws.amazon.com/cur/latest/userguide/split-cost-allocation-data-kubernetes-labels.html)

### Kubernetes

- [Logging Architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/)
- [Pod Quality of Service Classes](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/)
- [Limit Ranges](https://kubernetes.io/docs/concepts/policy/limit-range/)
- [Resource Quotas](https://kubernetes.io/docs/concepts/policy/resource-quotas/)
- [Pod Priority and Preemption](https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/)
- [Pod Disruptions](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/)
- [Pod Topology Spread Constraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints/)
- [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Version Skew Policy](https://kubernetes.io/releases/version-skew-policy/)
