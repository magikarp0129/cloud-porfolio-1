# Operations Strategy

## Objective

클라우드 인프라를 배포한 이후에도 안정적으로 운영할 수 있도록 백업, 스케줄링, 패치, 취약점, OS lifecycle, 패키지 관리 전략을 정의합니다.

## Read-Only Operations Evidence

운영자는 변경 전에 현재 상태와 위험을 증적으로 남겨야 합니다. [운영 및 검증 스크립트](../scripts/README.md)는 다음 읽기 전용 점검을 구현합니다.

- Linux 호스트의 CPU, 메모리, 파일시스템, inode, 프로세스, 실패한 systemd unit과 오류 journal 수집
- 트래픽 급증 시 `ss`/`netstat` 기반 socket state·queue, retransmit, interface drop, softnet와 conntrack 증적 수집
- CPU·메모리 급증 시 `top`, `vmstat`, PSI, swap·OOM, 파일 디스크립터, disk·inode와 I/O latency 증적 수집
- 특정 systemd 서비스의 상태, MainPID, 프로세스 자원, 소켓과 journal 증적 수집
- 로컬 패키지 metadata 기준 업데이트 후보, 보안 권고와 재부팅 필요 여부 확인
- 명시한 kubeconfig context의 노드, 비정상 Pod, workload, PDB, HPA, PVC와 이벤트 확인
- CloudWatch Logs의 보존 기간과 KMS 구성 감사

증상별 실행 순서, queue와 자원 지표 해석, Warning/Critical 출발점은 [Linux 장애 분석 스크립트와 판단 가이드](../scripts/operations/linux/README.md)를 기준으로 합니다. 스크립트는 패치 설치, 서비스 재시작, Kubernetes 변경, AWS 변경 API를 실행하지 않습니다. 발견 사항은 티켓과 증적 파일에 연결하고 Terraform 또는 보호된 변경 절차로 전달합니다.

## Backup Strategy

| Target | Frequency | Retention | Notes |
| --- | --- | --- | --- |
| Production database | Daily | 30 days | PITR 또는 automated backup 사용 |
| Production volume | Daily | 14 to 30 days | AWS Backup 또는 EBS snapshot 사용 |
| Staging database | Daily | 7 to 14 days | 운영 배포 검증용 |
| Development database | Optional daily | 3 to 7 days | 비용 최적화 우선 |
| Terraform state | Versioned | Long-term | S3 versioning, DynamoDB lock |

## Instance Scheduling

| Environment | Policy | Example |
| --- | --- | --- |
| `dev` | 업무 시간 외 중지 | 평일 20:00 stop, 08:00 start |
| `stg` | 업무 시간 외 중지 또는 예약 기동 | 평일 21:00 stop, 08:00 start |
| `prod` | 기본적으로 중지하지 않음 | HA와 SLA 우선 |
| `sandbox` | 강제 중지 | 야간 및 주말 stop |

## Patch and Vulnerability Management

| Severity | Response Target |
| --- | --- |
| Critical CVE | 7 days or emergency patch |
| High CVE | 14 days |
| Medium CVE | 30 days |
| Low CVE | Regular maintenance window |

관리 대상:

- Ubuntu
- Red Hat Enterprise Linux
- Amazon Linux
- Container base images
- Docker runtime
- Language runtime packages
- Middleware packages

## EOS and EOL Management

- OS와 middleware의 EOS/EOL 날짜를 inventory로 관리합니다.
- EOS 6개월 전 migration plan을 작성합니다.
- EOS 3개월 전 stg 검증을 완료합니다.
- EOS 1개월 전 prod 교체 일정을 확정합니다.

## Package Repository Strategy

엔터프라이즈 환경에서는 모든 서버가 인터넷에서 직접 패키지를 받는 구조를 피합니다.

후보 구조:

- Private package mirror
- Artifact repository
- Container registry
- Golden AMI pipeline
- Approved package allowlist

## EventBridge and Lambda Automation

- EventBridge Scheduler로 환경별 start/stop 이벤트를 생성합니다.
- Lambda는 태그 기반으로 EC2, RDS instance, Aurora cluster를 조회합니다.
- `Schedule=office-hours` 리소스만 자동 중지 대상으로 분류합니다.
- `Schedule=always-on`과 `Environment=prod`는 자동 중지 대상에서 제외합니다.
- 실행 결과는 CloudWatch Logs와 SNS로 남깁니다.
- 자동화 Lambda는 최소 권한 IAM role과 dry-run 모드를 제공합니다.
- EKS node group은 Cluster Autoscaler 또는 Karpenter가 관리하며 EC2/RDS scheduler 대상에서 제외합니다.

## EKS Platform Lifecycle

EKS를 사용하는 경우 Kubernetes control plane, node group, addon, Helm chart, service mesh를 별도 lifecycle로 관리합니다.

로그 수집·보존, Kubernetes QoS, namespace quota, autoscaling, PDB/topology, backup/restore, upgrade와 incident runbook의 상세 기준은 [EKS Day-2 Operations](eks-operations.md)를 source of truth로 사용합니다. 이 문서는 VM/데이터베이스를 포함한 공통 운영 정책만 유지합니다.

버전 관리 원칙:

- Kubernetes minor version upgrade는 `dev`, `stg`, `prod` 순서로 진행합니다.
- control plane upgrade 후 node group 또는 Karpenter node를 순차 교체합니다.
- 업그레이드 전 deprecated API 사용 여부를 점검합니다.
- cluster upgrade 전 backup, rollback, maintenance window를 확정합니다.

Addon 관리 대상:

- VPC CNI
- CoreDNS
- kube-proxy
- EBS CSI Driver
- EFS CSI Driver
- AWS Load Balancer Controller
- Metrics Server
- Cluster Autoscaler 또는 Karpenter
- ExternalDNS
- cert-manager

Helm 및 Istio 관리:

- Helm chart version과 values 파일은 git에서 관리합니다.
- 환경별 values는 `dev`, `stg`, `prod`로 분리합니다.
- 배포 전 `helm diff`를 수행합니다.
- Istio control plane과 data plane upgrade를 분리합니다.
- sidecar injection은 namespace label로 통제합니다.
- mTLS는 permissive에서 strict로 단계적으로 전환합니다.

## Landing Zone Operations

- Monitoring server 또는 managed observability 계층
- Prometheus and Grafana
- Central log archive
- WAF
- UTM 또는 firewall appliance
- Bastion 또는 Session Manager
- Shared DNS and network inspection layer
