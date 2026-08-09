# Examples

`examples/`는 외부 credential과 운영 데이터 없이 코드·정책·보고 흐름을 반복 검증하기 위한 sanitized fixture입니다.

## 현재 예시

| Path | Role | Actual use |
| --- | --- | --- |
| `incidents/prod-api-5xx-request.json` | Monitoring Agent 입력 계약 예시 | CI validate, contract/security/triage unit test |
| `incidents/prod-api-5xx-evidence.json` | CloudWatch·Kubernetes·Logs 모의 관측값 | offline simulation, redaction과 report 생성 시험 |

두 JSON은 실제 prod 장애 증적이 아닙니다. `prod`, account ID, cluster, ALB와 log group은 placeholder inventory이고 token/email 문자열은 redaction 시험용 canary입니다.

사람이 읽는 발행 예시는 [`reports/examples/`](../reports/examples/)에서 관리합니다. fixture는 테스트 입력, reports example은 설명용 산출물이므로 역할을 섞지 않습니다.

