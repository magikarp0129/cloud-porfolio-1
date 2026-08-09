# Common Workload Environments

## 목적과 State 분리

`dev`, `stg`, `prod`는 공통 AWS foundation을 동일한 `workload-environment` module로 조립하고 입력값만 다르게 적용합니다. 각 환경의 `platform/`은 private EKS API에 연결해 Helm/Kubernetes resource를 관리하는 별도 state입니다.

```text
environments/<env>/             AWS provider: VPC, security, IAM, logs, backup, cost, EKS
environments/<env>/platform/    AWS + Kubernetes + Helm providers: Istio, namespace policy, Prometheus/Grafana
```

## 환경 차이

| 환경 | VPC | AZ/연결 | EKS node | Logs | Prometheus | Operations |
| --- | --- | --- | --- | --- | --- | --- |
| dev | `10.10.0.0/16` | 2 AZ, Landing Zone TGW | Spot 1/1/3 | control 90일, container 30일 | 7일 | Scheduler 사용, backup plan 14일, selection tag는 `none` |
| stg | `10.15.0.0/16` | 2 AZ, Landing Zone TGW | On-Demand 2/2/5 | 90일/90일 | 15일 | Scheduler 사용, backup plan 35일, selection tag는 `none` |
| prod | `10.20.0.0/16` | 3 AZ, Landing Zone TGW | system 3/3/6 + app 3/3/12 | 365일/365일 | 30일 | Scheduler 금지, backup 35일, Vault Lock, `daily` selection tag |

Node 크기는 `min/desired/max`입니다. Terraform은 managed node group `desired_size` drift를 무시하지만 HPA, Cluster Autoscaler와 Karpenter controller는 아직 설치하지 않았습니다.

## 적용 전 조건

1. `backend.hcl`과 환경별 state key를 승인된 backend 값으로 생성합니다.
2. account/role, Region, `transit_gateway_id`, KMS와 alarm email 등 환경 input을 승인된 경로에서 주입합니다.
3. Foundation을 먼저 plan/apply하고 EKS endpoint, CA와 cluster name output을 확인합니다.
4. `platform/` runner가 private EKS endpoint에 도달하고 승인 role로 token을 발급받을 수 있어야 합니다. Foundation의 `subnet_ids.pod`와 `eks_cluster_security_group_id`를 platform input으로 전달합니다.
5. Grafana bootstrap password는 tfvars에 저장하지 않고 CI secret 또는 외부 secret manager로 주입합니다.
6. 동일 namespace, PDB, NetworkPolicy 또는 workload를 application release state와 중복 관리하지 않습니다.

상세 EKS Current/Target/Evidence는 [EKS 운영 표준](../../docs/eks-operations.md)을 따릅니다.
