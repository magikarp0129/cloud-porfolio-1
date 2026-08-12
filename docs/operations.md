# Operations Strategy

## Objective

클라우드 인프라를 배포한 이후에도 안정적으로 운영할 수 있도록 백업, 스케줄링, 패치, 취약점, OS lifecycle, 패키지 관리 전략을 정의합니다.

## Operations Evidence

운영자는 변경 전에 현재 상태와 위험을 ticket에 남기고, 변경 후 같은 관측 범위로 결과를 비교합니다. 최소 증적은 UTC window, account/environment, 실행자, 사용한 query나 명령, 원본 저장 위치와 무결성 참조를 포함합니다.

이 저장소에는 호스트·EKS·AWS 진단 스크립트를 포함하지 않습니다. 실제 운영 도구는 대상 환경, 권한, 민감정보 처리와 보존 정책이 확정된 뒤 별도 runbook 또는 운영 저장소에서 관리합니다.

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
