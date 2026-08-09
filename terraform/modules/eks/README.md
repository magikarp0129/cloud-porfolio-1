# EKS Module

보안 기본값과 업그레이드 가능성을 우선한 EKS 인프라 모듈입니다.

- Private API endpoint by default
- Kubernetes secrets KMS encryption
- API, audit, authenticator, controller, scheduler logs with explicit retention
- Dedicated CloudWatch Logs KMS key and scoped encryption context
- CloudWatch Observability add-on, Fluent Bit/agent Pod Identity, and pre-created Container Insights log groups
- Access Entry based cluster administrators
- AL2023 managed node groups
- IMDSv2-required launch templates and encrypted gp3 volumes
- EKS managed add-ons with compatible-version and conflict-resolution controls
- VPC CNI custom networking, prefix delegation, and AZ-based ENIConfig label selection
- Pod Identity roles for VPC CNI, EBS CSI, and CloudWatch Observability
- Node Kubernetes/release version and rolling-unavailable controls
- Desired-size drift ignored so a future autoscaler can own runtime capacity

클러스터 버전은 환경별로 명시하고 한 번에 한 minor version만 올립니다. add-on 버전은 계획 시 호환 가능한 최신 버전으로 계산되며, 실제 운영 저장소에서는 검증된 plan의 결과 버전을 릴리스 기록에 남깁니다.

현재 environment root는 control-plane 로그를 `dev/stg/prod=90/90/365일`, Container Insights 로그를 `30/90/365일`로 설정합니다. 중앙 Log Archive account로의 subscription/Firehose/S3 전달은 아직 production backlog입니다. Cluster Autoscaler/Karpenter controller는 이 모듈에 포함하지 않습니다.

EKS control-plane x-ENI는 `cluster_subnet_ids`, managed node group은 `node_subnet_ids`를 사용합니다. Pod 전용 subnet의 AZ별 `ENIConfig` object는 private API에 연결하는 별도 `kubernetes-platform` state가 소유합니다.

상세 운영·보존·복구 기준은 [EKS Day-2 Operations](../../../docs/eks-operations.md)를 따릅니다.
