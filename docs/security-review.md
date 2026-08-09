# Terraform Security Review

## Review Scope

검토 범위는 AWS Organizations/SCP, IAM trust policy, KMS, network, EKS, operations automation, observability, FinOps module입니다. 2026-08-08 기준 Terraform 1.15.3, AWS provider 5.100.0, Kubernetes provider 2.38.0 schema로 모든 root module을 검증했습니다.

## Implemented Controls

| Area | Control | Evidence |
| --- | --- | --- |
| Organization | Nested workload OUs, deny-leave, audit-service protection, region restriction, tag policy | `terraform/organization` |
| IAM | Explicit trusted principals, scoped GitHub OIDC subjects, audit role, MFA break-glass option | `terraform/modules/iam` |
| Encryption | Rotating customer-managed KMS keys, EBS default encryption, EKS secrets and node volume encryption | `security`, `eks` modules |
| Network | LB/AP/DB/Node/Pod subnet 분리, TGW 중앙 경로, DB internet-route isolation, private endpoints | `network` module |
| EKS | Private endpoint, Access Entry administrators, AL2023 nodes, IMDSv2, control-plane logs, Pod Identity | `eks` module |
| Runtime | Istio revision upgrade, strict mTLS, Prometheus, Alertmanager, Grafana | `kubernetes-platform` module |
| Operations | Tag-scoped scheduler, prod exclusion, Backup Vault Lock option, patch baselines, Inspector | `operations` module |
| Detection | GuardDuty, Security Hub, Inspector, VPC Flow Logs, rejected-flow alarm | `security`, `observability` modules |
| Edge | WAF managed rules, rate limiting, logging, sensitive-header redaction | `waf` module |

## Review Decisions

- SCP는 권한을 부여하지 않고 최대 권한만 제한하므로 IAM role policy와 함께 검토합니다.
- SCP 변경은 `Policy-Staging` OU에서 먼저 검증하고 작은 account 단위로 승격합니다.
- GitHub OIDC trust는 repository, branch 또는 environment가 포함된 `sub` claim allowlist가 비어 있으면 생성하지 못하게 합니다.
- EKS cluster creator bootstrap admin은 끄고, 명시적 Access Entry가 최소 하나 있어야 cluster를 만들 수 있습니다.
- EKS add-on 권한은 node role에 몰지 않고 VPC CNI와 EBS CSI에 Pod Identity role을 분리합니다.
- dev/stg scheduler의 IAM policy와 Lambda 로직 모두 `Environment`와 `Schedule` 태그를 확인하며 prod 실행은 precondition과 runtime check로 이중 차단합니다.
- Workload VPC는 public subnet, Internet Gateway와 NAT Gateway를 만들지 않으며 DB subnet은 internet default route를 갖지 않습니다.

## Residual Risks and Required Production Work

| Risk | Current State | Production Gate |
| --- | --- | --- |
| Central audit | Organization CloudTrail, Config aggregator, immutable log archive account는 account ID가 없어 미구현 | Log Archive/Security account ID 확정 후 별도 root에서 구현 |
| EKS data-plane logs | CloudWatch Observability add-on, Pod Identity, KMS log group과 환경별 retention은 구현됐지만 central archive와 runtime 증적 없음 | collector coverage, masking, delivery/drop alarm과 archive E2E 검증 |
| EKS resource policy | 환경별 LimitRange/ResourceQuota와 PriorityClass catalog 구현, PDB interface는 instance 없음 | workload requests/HPA/PDB/topology owner 확정 후 admission/drain/eviction test |
| EKS autoscaling | managed node group desired-size drift만 무시하고 controller 미설치 | Cluster Autoscaler 또는 Karpenter 선택, HPA 연동, capacity/Spot/PDB 검증 |
| EKS recovery | Backup vault/tag selection은 있으나 EKS composite backup/restore 증적 없음 | service opt-in, isolated namespace/cluster restore와 RPO/RTO 증적 |
| SCP lockout | Portfolio policy는 실제 organization에 적용하지 않음 | Policy-Staging OU 테스트와 break-glass rehearsal 완료 |
| Private EKS access | Public API endpoint disabled | VPN, Direct Connect, SSM-connected runner 또는 self-hosted CI runner 확보 |
| Grafana bootstrap secret | Sensitive Terraform variable와 state에 존재 | External Secrets/Secrets Manager 연동 후 bootstrap credential 회전 |
| WAF attachment | Reusable ACL은 구현됐지만 ALB/API Gateway가 없음 | ingress ARN 생성 후 count mode 관찰, exclusion 검토, block 승격 |
| UTM/firewall routing | Central inspection VPC와 AWS Network Firewall route는 설계만 존재 | Network account, TGW route table, appliance mode 설계 확정 |
| Central ingress/egress | Workload VPC default route는 TGW를 향하지만 실제 ingress/egress attachment는 입력되지 않음 | 중앙 ingress·inspection·egress attachment, return route와 장애 우회 검증 |
| Restore proof | Backup plan은 구현됐지만 restore 결과가 없음 | 월간 restore drill과 RPO/RTO 증적 저장 |
| Runtime policy | Istio AuthorizationPolicy와 NetworkPolicy는 서비스 요구사항에 따라 달라 미포함 | namespace별 default-deny와 허용 통신표 승인 |
| Provider plan | AWS 자격 증명이 없어 실제 account plan/apply 미수행 | sandbox account에서 plan, cost estimation, apply/destroy 검증 |

## Release Gate

1. `terraform fmt -check -recursive`, 모든 root `init -backend=false`, `validate`를 통과합니다.
2. Pull request에 plan, 비용 변화, 보안 스캔 결과를 첨부합니다.
3. `prod`는 두 명 이상 리뷰와 environment approval을 요구합니다.
4. SCP는 Policy-Staging OU에서 CloudTrail service-last-accessed data와 함께 검증합니다.
5. EKS upgrade는 deprecated API, add-on compatibility, PodDisruptionBudget, rollback 절차를 확인합니다.
6. Backup restore와 break-glass 절차는 분기별로 실제 실행하고 증적을 남깁니다.
