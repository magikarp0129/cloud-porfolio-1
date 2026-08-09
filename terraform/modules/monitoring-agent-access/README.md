# Monitoring Agent Access Module

Monitoring Agent Tool Broker가 사용할 전용 short-lived diagnostic IAM role을 생성합니다. 광범위한 security audit role을 재사용하지 않습니다. 정확한 trusted principal ARN이 비어 있으면 role을 생성하지 않습니다.

허용 범위:

- CloudWatch metric, alarm과 dashboard read
- 승인 log group의 제한된 Logs Insights query
- 선택적 EKS `DescribeCluster`
- 선택적 AMP workspace query

명시적 deny는 log unmask, Secret/Parameter/KMS data read, interactive SSM, role chaining, alarm suppression과 주요 production mutation을 차단합니다. Trust policy는 server-generated `req-*` 값을 STS SourceIdentity와 RoleSessionName에 연결합니다.

이 module은 Kubernetes RBAC와 Agent Runtime을 생성하지 않습니다. Environment root의 EKS Access Entry가 assumed role을 `monitoring-agent-readers` group에 연결하고, 실제 `get/list` 범위는 `kubernetes-platform`이 소유합니다. live Tool Broker와 Prometheus 연결은 아직 목표 단계입니다.

상세 실행·검증 경계는 [Read-Only Agent Incident Triage](../../../docs/agent-incident-triage.md)를 따릅니다.
