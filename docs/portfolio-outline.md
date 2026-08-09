# 포트폴리오 PDF 구성

## 작성 기준

- 문서의 중심은 설계 이유가 아니라 현재 AWS와 Kubernetes 구성입니다.
- 각 장은 `전체 흐름 → 주요 컴포넌트 → 환경별 값 → 현재 구현 상태` 순서로 작성합니다.
- 설계 원칙, 장문의 변경 절차, 성과 체계, 교훈과 로드맵은 본문에서 제외합니다.
- Terraform 코드에 존재하는 항목과 존재하지 않는 항목을 `구현`과 `미구현`으로 구분합니다.
- 실제 AWS 배포 완료로 오해할 수 있는 표현은 사용하지 않습니다.
- AWS, Terraform, EKS와 리소스 이름 외의 설명은 한국어로 작성합니다.
- 표지는 제목, 기술 범위, 작성 정보와 목차만 표시합니다.
- 본문은 A4 보고서 형식을 유지하고 표와 간단한 계층도로 빠르게 확인할 수 있게 구성합니다.

## 작성 정보

- 작성자가 엔터프라이즈 AWS 아키텍처와 구성을 정의합니다.
- `OpenAI Codex`, `GPT-5.6-Sol`, 추론 수준 `xhigh`는 코드 분석, 원고 작성, 일관성 확인과 PDF 제작을 보조합니다.
- AI 생성 내용은 Terraform 코드와 저장소 문서를 기준으로 재검증합니다.

## 목차

### 1. 프로젝트 개요

- 전체 AWS 구성 흐름
- 환경, 서비스, VPC, EKS, Terraform 규모
- 코드 구현과 실제 배포의 표시 기준

### 2. 프로젝트 배경

- 구축 대상과 요구 영역
- Organization, 네트워크, EKS, 관측성, 운영 범위
- 현재 코드에 포함된 항목과 포함되지 않은 항목

### 3. 랜딩 존 아키텍처

- IPAM, Transit Gateway, RAM과 routing domain
- 공통 dev/stg/prod VPC 차이
- 서비스 VPC의 LB/AP/DB/Node/Pod/TGW/EKS Cluster 7개 subnet tier

### 4. Terraform 아키텍처

- Organization, Landing Zone, 서비스, 환경, 플랫폼 state 구조
- Terraform 디렉터리와 module 그룹
- 배포 순서와 검증 진입점

### 5. 모니터링 및 관측성 아키텍처

- VPC, EKS, Container Insights, Prometheus 신호 흐름
- 환경별 로그와 metric 보존
- CPU, memory, disk, Pod, 5xx와 Node 알람 기준
- 현재 Alertmanager와 중앙 장기 저장 상태

### 6. EKS 아키텍처

- Private EKS 1.35, Access Entry, KMS와 managed add-on
- EKS Cluster, Node, VPC CNI Pod subnet 분리와 AZ별 ENIConfig
- 환경별 Managed Node Group instance와 min/desired/max
- Karpenter, Cluster Autoscaler, HPA/KEDA 설치 여부
- Istio, namespace ResourceQuota, LimitRange, PriorityClass
- PDB, NetworkPolicy, Load Balancer Controller 상태

### 7. 보안 아키텍처

- IAM role, EKS 접근과 Pod Identity
- KMS와 EBS 암호화
- GuardDuty, Security Hub, Inspector
- WAF module과 실제 연결 상태

### 8. 서비스 아키텍처

- commerce, payments, analytics, customer-profile, internal-admin
- 서비스별 dev/stg/prod CIDR
- 서비스 VPC의 현재 생성 항목
- 서비스 애플리케이션, EKS와 RDS의 구현 여부

### 9. 거버넌스

- Security, Infrastructure, Workloads, Sandbox, Policy-Staging OU
- 조직 탈퇴, 감사 서비스, 리전, S3와 tag 정책
- 공통 tag와 AWS account 생성 범위

### 10. 비용 관리

- 환경별 월 예산과 Cost Anomaly 기준
- Budget 50/80/100% SNS 알림
- dev/stg scheduler와 prod 차단
- TGW 중앙 경로와 Interface Endpoint 환경 차이
