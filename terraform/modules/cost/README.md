# Cost Module

FinOps 리소스를 정의할 Terraform 모듈입니다.

구현 범위:

- AWS Budgets
- Cost anomaly detection
- Environment tag-filtered monthly budget
- Forecasted 50 percent and actual 80/100 percent alerts
- Service-level Cost Anomaly Detection
- SNS integration with the shared alarm topic

CUR 저장소와 Athena 테이블은 조직의 payer account에서 한 번만 만들어야 하므로 workload 환경 모듈과 분리합니다.
