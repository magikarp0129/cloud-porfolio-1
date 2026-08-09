# Organization Root

## 목적과 State Owner

AWS Organizations management account에서 Organization, OU, SCP와 Tag Policy를 조립하는 독립 root/state입니다. workload, Network, Security account의 resource와 같은 state에 합치지 않습니다.

## 현재 구성

- Root OU: `Security`, `Infrastructure`, `Workloads`, `Sandbox`, `Policy-Staging`
- Child OU: `Workloads/Dev`, `Workloads/Stg`, `Workloads/Prod`
- SCP: organization 이탈 방지, 핵심 audit/security 비활성화 방지, 승인 Region 제한, public-access control 삭제 방지
- Tag Policy: `Environment`, `ManagedBy`

이 root는 AWS account를 만들거나 기존 account를 OU로 이동하지 않습니다. Account vending, delegated administrator, organization CloudTrail/Config와 실제 Log Archive account 연결은 별도 단계입니다.

## 입력과 안전 조건

| Input | 의미 |
| --- | --- |
| `approved_regions` | workload API가 허용되는 Region. Global service 예외 목록과 함께 검토 |
| `security_admin_role_arn_patterns` | 보호된 security control의 조건부 예외 role pattern |

새 deny policy는 `Policy-Staging` OU에서 positive/negative API 시험, break-glass와 rollback attachment를 확인한 뒤 workload OU로 승격합니다. Management account 접근과 Organization 변경은 별도 고위험 승인 대상으로 취급합니다.

## 실행

```bash
terraform init -backend-config=backend.hcl
terraform fmt -check
terraform validate
terraform plan -out=organization.tfplan
```

Agent는 plan과 영향 분석까지만 수행하며 apply는 protected CI/CD와 designated approver가 담당합니다.
