# Operations Module

백업, 스케줄링, 패치, 취약점 관리 자동화 리소스를 정의할 Terraform 모듈입니다.

구현 범위:

- AWS Backup plan
- AWS Backup vault
- EventBridge Scheduler
- Lambda start/stop automation
- Systems Manager Patch Manager
- Systems Manager Inventory
- Backup and patch notification SNS topic
- Tag-based automation
- Lambda error alarm
- OS-specific SSM patch baselines for Ubuntu, RHEL, and Amazon Linux 2023
- Optional Inspector v2 enablement

태그 기반 스케줄러는 `Environment=<dev|stg>`와 `Schedule=office-hours`가 모두 일치하는 EC2, RDS instance, Aurora cluster만 처리합니다. Terraform lifecycle과 Kubernetes autoscaler 상태가 충돌할 수 있으므로 EKS node group은 이 Lambda의 대상에서 제외하고 별도의 scaling policy로 관리합니다.

EKS AL2023 node의 `PatchGroup`은 환경별 SSM patch baseline key와 일치시키지만, node 운영의 기본 방식은 수동 in-place patch가 아니라 검증된 EKS optimized AMI와 managed node group의 순차 교체입니다. 이 모듈의 태그 기반 AWS Backup selection만으로 EKS composite recovery point와 restore 성공을 보장하지 않으므로 service opt-in, child recovery point와 격리 restore를 별도 검증합니다. 상세 기준은 [EKS Day-2 Operations](../../../docs/eks-operations.md)를 따릅니다.
