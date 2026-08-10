# 포트폴리오 PDF 구성

## 작성 기준

- 루트 `README.md`의 흐름을 PDF 서사의 기준으로 사용합니다.
- 독자가 `왜 필요한가 → 어떤 경계로 설계했는가 → 무엇을 구현했는가 → 무엇이 남았는가 → 어떤 증거가 있어야 완료인가`를 순서대로 이해할 수 있어야 합니다.
- 각 장은 설명 문단으로 맥락을 먼저 제공하고, 표와 간단한 계층도로 수치와 ownership을 확인하게 합니다.
- Terraform 코드에 있는 항목, 정의된 정책, 목표 아키텍처와 실제 운영 evidence를 명시적으로 구분합니다.
- 실제 AWS 배포, 비용 절감이나 MTTR 개선으로 오해할 수 있는 표현을 사용하지 않습니다.
- 세부 기준을 여러 문서에 복사하지 않고 README와 domain canonical 문서를 요약·참조합니다.
- AWS, Terraform, EKS와 resource 이름은 원문 표기를 유지하고 설명은 한국어로 작성합니다.
- A4 보고서 형식, 충분한 행간, 일관된 장 제목, 머리말, 페이지 번호와 bookmark를 유지합니다.

## 작성 정보

- 작성자가 엔터프라이즈 AWS architecture와 최종 구성을 정의합니다.
- OpenAI Codex는 코드 분석, 원고 작성, 일관성 확인과 PDF 제작을 보조합니다.
- AI가 작성한 내용은 Terraform 코드, README와 canonical 문서를 기준으로 다시 검증합니다.

## 목차와 독자 흐름

### 1. 프로젝트 목표

- 포트폴리오가 답하는 질문
- AWS, Terraform, EKS, Observability, Operations, FinOps, Security/Identity, AI/Agent와 Documentation/Validation으로 나눈 Target Scope
- 전체 구축 흐름과 핵심 범위
- 저장소 구현과 실제 배포의 구분

### 2. 범위와 증거를 읽는 방법

- Current, Defined, Target, Evidence
- fixture, schema, template과 production evidence 경계

### 3. 저장소 구조와 권장 탐색 순서

- README, AGENTS, docs, Terraform과 runtime 역할
- 질문별 시작 문서와 구축·검토 순서

### 4. Multi-Agent Operating Model

- Human → Cloud Platform Manager → Domain Lead → Specialist의 4단계 조직도와 총 11개 Agent 역할
- Human-led, Agent-assisted 실행 흐름
- read/draft/plan/review와 protected CI/CD 경계

### 5. Target Cloud Architecture

- Organizations, Landing Zone, workload와 EKS 전체 계층
- dev/stg/prod 운영 의도
- Workforce Identity와 AI Platform의 목표 경계

### 6. Landing Zone과 서비스 네트워크

- IPAM, TGW, RAM과 routing domain
- 공통 환경 VPC와 7개 subnet tier
- 5개 서비스의 15개 VPC와 현재 생성 범위

### 7. Terraform Implementation Strategy

- root, state와 module ownership
- 적용 순서와 변경 승인
- 하나의 object를 두 state가 관리하지 않는 원칙

### 8. EKS와 Kubernetes Platform

- Private EKS 1.35, Access Entry, KMS와 managed add-on
- 환경별 node group과 VPC CNI custom networking
- Istio, quota, PriorityClass와 autoscaling/PDB의 현재 경계

### 9. Monitoring and Alerting

- CloudWatch와 Prometheus 신호 흐름
- 로그·metric 보존과 주요 severity
- 현재 Alertmanager, central archive와 Mimir 상태

### 10. Operations Strategy

- tag, backup, scheduler, patch와 CVE/EOS
- read-only Linux, EKS와 AWS 점검 도구

### 11. FinOps Strategy

- 환경별 budget와 Cost Anomaly
- 비용 귀속, scheduler와 절감 효과 검증 기준

### 12. Security and Governance

- IAM, network, encryption, detection과 WAF
- OU, SCP, Tag Policy
- production 전 잔여 위험

### 13. 현재 구현과 검증 상태

- 현재 저장소 산출물
- Agent test, Terraform validation, policy와 report 검증의 의미
- 로컬 시험이 증명하지 않는 범위

### 14. 다음 구현 단계

- sandbox evidence, central audit, EKS ingress와 WAF
- Mimir, OpenTelemetry, autoscaling, Identity Center와 AI Gateway

### 15. Definition of Done과 Production Promotion Gate

- 저장소 산출물의 완료 기준
- 실제 production 승격에 필요한 plan, 승인, health와 rehearsal evidence
