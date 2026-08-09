# WAF Module

ALB, API Gateway, AppSync 또는 CloudFront 앞단에 적용할 WAFv2 baseline입니다.

- Source-IP rate limit
- AWS Common, Known Bad Inputs, IP Reputation, SQL injection managed rules
- CloudWatch metrics and sampled requests
- Authorization header redaction in WAF logs
- Optional regional resource associations

처음에는 managed rule action을 count mode로 검증한 뒤 block mode로 승격하는 것이 안전합니다. 현재 포트폴리오 baseline은 block 동작을 사용하므로 실제 서비스 트래픽 패턴에 맞춰 exclusion을 검토해야 합니다.
