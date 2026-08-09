# Security Agent

## Purpose

Security Agent는 엔터프라이즈 클라우드의 기본 보안 통제, 접근 제어, 네트워크 보호, 암호화 기준을 담당합니다.

## Responsibilities

- Least privilege IAM policy 검토
- AWS Organizations SCP guardrail 검토
- Public subnet과 private subnet 경계 검토
- Security group inbound/outbound 정책 검토
- KMS 암호화 기준 정의
- 로그 보존 및 감사 추적 기준 정의
- EKS audit/application log의 secret·PII masking, KMS, central archive 접근 통제 검토
- Pod Identity/RBAC, Pod Security, NetworkPolicy와 privileged workload 예외 검토

## Baseline Controls

- Root account MFA enabled
- IAM user 대신 role 기반 접근 우선
- Public access는 명시적으로 필요한 리소스에만 허용
- S3 bucket public access block 기본 활성화
- CloudTrail, VPC Flow Logs, Config 활성화
- 승인되지 않은 region에서 리소스 생성 제한
- 감사 서비스 비활성화 방지
