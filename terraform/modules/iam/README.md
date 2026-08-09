# IAM Module

역할 기반 접근 제어를 정의할 Terraform 모듈입니다.

구현 범위:

- Workload roles
- CI/CD deployment role
- Read-only audit role
- Environment-specific managed policy attachments
- Optional permissions boundary
- MFA-enforced break-glass role

배포 역할에는 기본 권한을 넣지 않습니다. 각 환경 루트가 필요한 정책 ARN만 전달해야 하며, 운영 환경은 GitHub OIDC의 repository와 environment claim을 구체적으로 제한해야 합니다.
