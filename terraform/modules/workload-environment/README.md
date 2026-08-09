# Workload Environment Composition

환경 루트에서 network, security, IAM, observability, operations, FinOps, EKS 모듈을 일관되게 조립하는 composition module입니다. 실제 리소스 로직은 하위 모듈에 유지하고 이 모듈은 환경 공통 정책과 의존 관계만 표현합니다.

## 조립 범위

```text
network/TGW -> security/IAM -> observability
        -> operations/cost -> EKS -> monitoring-agent-access
```

주요 output은 VPC ID, 7개 private subnet tier, TGW attachment, EKS cluster security group, alarm topic, EKS cluster name, Backup vault와 Monitoring Agent role ARN입니다. Environment root가 CIDR, AZ, Landing Zone TGW, endpoint, budget, scheduler, backup, EKS version·log retention·node group과 trust principal을 전달합니다.

EKS control-plane/Container Insights log retention과 managed node group lifecycle 입력을 environment root에서 전달합니다. Kubernetes namespace quota, LimitRange, PriorityClass와 선택적 PDB는 private cluster 접근이 필요한 별도 `platform/` root가 소유합니다. 상세 경계는 [EKS Day-2 Operations](../../../docs/eks-operations.md)를 따릅니다.

EKS control plane은 `eks_cluster` subnet, managed node group은 `node` subnet을 사용합니다. `pod` subnet과 EKS cluster security group output은 별도 platform state가 AZ별 VPC CNI `ENIConfig`를 만들 때 사용합니다.

이 module은 AWS resource composition만 소유하며 Kubernetes application manifest, 중앙 Log Archive, HPA/node autoscaler와 실제 deployment workflow를 생성하지 않습니다.
