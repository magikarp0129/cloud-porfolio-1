# Security Module

계정 및 리전 단위 보안 기준 리소스를 정의합니다.

구현 범위:

- KMS key rotation and EBS default encryption
- Account-level S3 public access block
- IAM password policy for exceptional IAM-user use
- GuardDuty
- Security Hub
- Inspector v2 for EC2, ECR, and Lambda

AWS Config, organization-wide CloudTrail, delegated administrator 설정은 관리 계정과 로그 아카이브 계정 정보가 필요하므로 organization 계층의 후속 단계로 분리합니다.
