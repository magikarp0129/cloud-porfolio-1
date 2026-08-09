# Compute Module

## 현재 상태

향후 EC2 Auto Scaling Group 또는 ECS runtime을 위한 **예약 디렉터리**입니다. 현재 `.tf` resource가 없으며 구현된 module 수에 포함하지 않습니다.

## 계획 범위

- Launch Template과 EC2 Auto Scaling Group
- ECS cluster/service와 Fargate capacity provider
- runtime별 deployment, scaling, health와 rollback interface

## 명시적 제외

- EKS control plane, managed node group와 AWS add-on은 `modules/eks`가 소유합니다.
- Helm, Istio, namespace policy와 Prometheus/Grafana는 `modules/kubernetes-platform`이 소유합니다.
- Cluster Autoscaler/Karpenter와 HPA/KEDA는 현재 어느 module에도 구현되지 않았습니다.

새 runtime을 추가하기 전 account/VPC placement, workload owner, state, 배포 방식과 EKS 중복 여부를 Architecture Decision으로 먼저 확정합니다.
