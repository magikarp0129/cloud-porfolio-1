# SCP Policy Module

## 목적과 상태

AWS Organizations의 SCP 또는 Tag Policy를 logical key로 생성하고 OU·account target에 attachment하는 구현 module입니다. 현재 `terraform/organization` root에서 사용합니다.

## 소유 범위

- `policies` map의 policy document, 이름, 설명과 type
- `attachments` map의 policy-to-target 연결
- logical policy key 기준 policy ID output

이 module은 정책의 업무 승인, 예외 만료, break-glass 검증과 target OU 승격 판단을 대신하지 않습니다. deny 정책은 allow 권한을 부여하지 않으며 management account에는 SCP가 적용되지 않는 AWS Organizations 동작도 별도로 고려해야 합니다.

정책 변경은 JSON 문법뿐 아니라 영향받는 service/API, 예외 role, Policy-Staging 결과와 rollback attachment를 검토한 뒤 적용합니다.
