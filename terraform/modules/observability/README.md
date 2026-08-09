# Observability Module

AWS 계층의 모니터링과 로깅 리소스를 정의합니다.

구현 범위:

- CloudWatch dashboards
- VPC Flow Logs with one-minute aggregation
- Rejected-flow metric filter and alarm
- KMS-capable CloudWatch log group with retention
- SNS alarm topic and email subscriptions
- Network troubleshooting dashboard

Kubernetes 계층의 Prometheus와 Grafana는 EKS 생성 이후 `kubernetes-platform` 모듈에서 Helm으로 배포합니다. EKS control-plane/Container Insights log group과 CloudWatch Observability add-on은 `eks` 모듈이 소유합니다. 중앙 archive와 상세 lifecycle은 [EKS Day-2 Operations](../../../docs/eks-operations.md)를 기준으로 후속 구현합니다.
