# Documentation Guide

`docs/`는 Terraform 코드만으로 설명하기 어려운 설계 판단, 운영 기준, residual risk와 PDF 원고를 관리합니다. 같은 주제의 상세 기준은 한 문서만 소유하고 README와 PDF에는 요약과 링크만 둡니다.

## 문서 목록

| 문서 | 상태 | Canonical scope |
| --- | --- | --- |
| [architecture.md](architecture.md) | 혼합 | AWS Organizations, account, network와 platform 전체 구조 |
| [service-network-architecture.md](service-network-architecture.md) | 혼합 | IPAM, TGW, 5개 서비스 CIDR와 subnet 계산 |
| [terraform-change-management.md](terraform-change-management.md) | 설계 기준 | state ownership, plan, 승인, apply와 rollback |
| [eks-operations.md](eks-operations.md) | 혼합 | EKS logging, QoS, scaling, upgrade, backup와 Day-2 runbook |
| [monitoring.md](monitoring.md) | 혼합 | CloudWatch, Prometheus/Grafana와 alert 흐름 |
| [monitoring-alert-policy.md](monitoring-alert-policy.md) | 설계 기준 | query, 지속 시간, Warning/Critical과 missing data |
| [operations.md](operations.md) | 혼합 | backup, scheduler, patch, CVE/EOS와 공통 운영 |
| [finops.md](finops.md) | 설계 기준 | tag, budget, anomaly와 비용 최적화 |
| [identity-access.md](identity-access.md) | 설계 기준 | Corporate IdP, IAM Identity Center와 account 접근 |
| [security-review.md](security-review.md) | 검토 결과 | 구현 통제, residual risk와 production gate |
| [repository-structure.md](repository-structure.md) | 현재 구조 | 디렉터리 책임과 질문별 코드 탐색 순서 |
| [portfolio-outline.md](portfolio-outline.md) | 작성 기준 | PDF의 독자 흐름과 내용 경계 |
| [portfolio-presentation.md](portfolio-presentation.md) | 빌드 source | 최종 PDF 본문 |
| [portfolio-presentation-header.tex](portfolio-presentation-header.tex) | 빌드 source | PDF 글꼴, 여백, 표와 머리말 스타일 |

## 상태 표기

| 상태 | 의미 |
| --- | --- |
| 현재 구현 | 저장소 코드에서 확인 가능 |
| 혼합 | 현재 코드와 아직 필요한 Target을 명시적으로 구분 |
| 설계 기준 | 향후 적용할 정책이나 운영 기준이며 배포 완료가 아님 |
| 검토 결과 | 현재 통제, 위험과 완료 조건을 기록 |
| 빌드 source | PDF 생성을 위한 원고 또는 스타일 |

코드가 존재하는 것과 실제 AWS에 배포되어 동작하는 것은 다릅니다. `Target`, example과 placeholder는 운영 실적처럼 인용하지 않습니다.

## 문서 변경 규칙

1. 새 문서보다 기존 canonical 문서에 한 절을 추가할 수 있는지 먼저 확인합니다.
2. 임계값, CIDR, retention과 module 목록을 여러 문서에 복제하지 않습니다.
3. Terraform 값 변경 시 관련 구성도와 PDF 원고의 인용값도 함께 확인합니다.
4. 문서 첫 부분에서 Current와 Target을 구분합니다.
5. 실제 값이 없으면 추정하지 않고 필요한 evidence를 기록합니다.
6. 파일 이동·삭제 시 루트 README와 상대 링크를 같은 변경에서 갱신합니다.
