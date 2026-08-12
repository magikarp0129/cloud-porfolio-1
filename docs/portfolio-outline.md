# Portfolio PDF Outline

## 작성 목표

- AWS Landing Zone, Terraform과 EKS가 본문 중심이어야 합니다.
- 독자가 `요구사항 → 설계 판단 → 코드 범위 → 미구현 → 필요한 증거` 순서로 이해할 수 있어야 합니다.
- 목차에는 장과 세부 절을 모두 표시합니다.
- 설명 문단으로 맥락을 먼저 제공하고 표와 텍스트 계층도로 수치·ownership을 확인합니다.
- 코드 존재, 로컬 검토, 실제 배포와 운영 증적을 구분합니다.
- 실제 AWS 배포, 비용 절감이나 가용성 성과로 오해할 표현을 사용하지 않습니다.
- README와 domain 문서를 복제하지 않고 포트폴리오 독자에게 필요한 요약만 사용합니다.

## 목차

### 1. 프로젝트 개요

- 포트폴리오가 답하는 질문
- 환경 3, 서비스 5, VPC 15, subnet tier 7, module 17의 의미
- 중심 범위와 단순화한 범위

### 2. 증거와 완료 상태를 읽는 방법

- Code, Reviewed, Deployed, Operational Evidence
- 현재 주장하는 것과 주장하지 않는 것

### 3. Target Cloud Architecture

- Organizations와 account 역할
- 중앙 ingress/egress, TGW와 private spoke
- 공통 platform VPC와 service VPC

### 4. Landing Zone

- IPAM `10.64.0.0/10`
- TGW, RAM과 route-table domain
- 다른 account와의 통신 경계

### 5. 서비스 네트워크와 IP 설계

- 5개 서비스의 dev/stg/prod CIDR
- 7개 private subnet tier
- commerce-prod AZ별 상세 예시

### 6. Terraform 구조와 변경 관리

- organization, landing-zone, service, environment와 platform state
- 17개 reusable module group
- 적용 순서, plan 승인과 rollback

### 7. Private EKS와 Kubernetes Platform

- EKS 1.35, private API, node/add-on과 Pod Identity
- Cluster, Node, Pod subnet 분리
- Istio, Prometheus/Grafana, quota와 PriorityClass
- autoscaling, PDB와 NetworkPolicy gap

### 8. Monitoring, Security and Governance

- log/metric 수집과 retention
- IAM, KMS, detection과 WAF
- OU, SCP와 정책 승격

### 9. Operations and FinOps

- backup, scheduler, patch와 EOS
- Budget, Cost Anomaly와 비용 검증
- 월간·장애 보고서 양식

### 10. 협업과 승인 경계

- 역할별 전문 검토
- 사람 승인과 protected deployment
- 코드와 production 실행의 분리

### 11. 저장소 탐색

- 최소화된 디렉터리 구조
- 질문별 코드 시작 위치
- PDF source, builder와 verifier

### 12. 다음 단계

- 현재 코드 산출물
- 삭제·단순화한 자산
- sandbox plan/apply/restore 우선순위
- production promotion gate

## 시각 품질 기준

- A4, 한글 본문 10pt, 충분한 행간과 일관된 여백
- 장 제목은 새 페이지에서 시작
- 표는 한 페이지 폭을 넘지 않고 반복 header를 사용
- 빈 페이지, 잘림, 겹침과 깨진 한글이 없어야 함
- 모든 페이지를 PNG로 렌더링해 확인
