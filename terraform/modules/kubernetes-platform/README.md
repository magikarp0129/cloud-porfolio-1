# Kubernetes Platform Module

EKS가 준비된 뒤 Helm/Kubernetes provider로 배포하는 별도 lifecycle 모듈입니다.

- Revision-based Istio control plane
- Optional Istio ingress gateway
- AZ별 VPC CNI ENIConfig와 전용 Pod subnet 연결
- Namespace revision labels and strict mTLS
- Namespace ResourceQuota and container LimitRange defaults
- Cluster-scoped platform/application/batch PriorityClasses
- Optional PDB interface with exact-selector validation
- kube-prometheus-stack with Prometheus, Alertmanager, and Grafana
- Persistent Prometheus and Grafana data volumes
- Pinned chart versions and atomic Helm upgrades

Istio ingress는 내부 LoadBalancer로 선언됩니다. Public ingress는 이 VPC에서 직접 만들지 않으며 Landing Zone의 중앙 ingress 경로가 내부 LB로 전달해야 합니다. 운영 환경에서는 Grafana bootstrap 비밀번호를 일반 tfvars에 기록하지 않고 CI secret 또는 외부 secrets manager에서 주입해야 합니다.

환경 root에는 `application-dev`, `application-stg`, `application-prod`별 quota/default가 구현되어 있습니다. PDB resource interface는 제공하지만 workload selector를 이 platform module이 추정하지 않도록 실제 PDB instance는 비워 두었습니다. HPA/VPA, Cluster Autoscaler/Karpenter와 Alertmanager receiver/route는 아직 구현하지 않았습니다.

QoS는 LimitRange만으로 보장되지 않으며 init/sidecar를 포함한 workload manifest의 실제 requests/limits 조합으로 결정됩니다. 상세 기준은 [EKS Day-2 Operations](../../../docs/eks-operations.md)를 따릅니다.

`vpc_cni_eni_configs`는 AZ 이름을 key로 하고 foundation의 `subnet_ids.pod`와 `eks_cluster_security_group_id`를 받습니다. VPC CNI managed add-on이 custom networking을 활성화한 뒤 이 manifest가 Pod secondary ENI의 subnet을 결정합니다.
