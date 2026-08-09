# Organization Module

## 목적과 상태

AWS Organizations의 organization과 root·child OU를 생성하는 구현 module입니다. `terraform/organization` root가 소유하며 workload 환경 state에서 호출하지 않습니다.

## 소유 범위

- `feature_set = ALL` organization
- CloudTrail, Config, GuardDuty, Security Hub, Inspector 등 service access principal
- Organization root에서 활성화할 SCP와 Tag Policy type
- root-level OU와 1단계 child OU

## 주요 Interface

| 구분 | 항목 |
| --- | --- |
| Input | `organizational_units`, `aws_service_access_principals`, `enabled_policy_types` |
| Output | `root_id`, logical key 기준 `organizational_unit_ids` |

`parent_key`는 존재하는 root-level OU만 참조하도록 검증합니다. 이 module은 AWS account 생성·이동, Control Tower Account Factory, delegated administrator와 SCP 내용을 소유하지 않습니다. 정책 문서와 attachment는 `scp-policy` module이 담당합니다.

적용 전 management account 권한과 조직 영향 범위를 검토하고, 신규 deny 정책은 `Policy-Staging` OU에서 먼저 시험합니다.
