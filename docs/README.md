# 문서 디렉터리 안내

## 이 디렉터리의 역할

`docs/`는 Terraform 코드만으로 설명하기 어려운 아키텍처 판단, 운영 기준, 검증 경계와 포트폴리오 PDF 원고를 관리합니다. 전체 프로젝트 소개는 루트 `README.md`, Agent 역할과 운영자 사용법은 `agents/`, 실제 Terraform 사용법은 `terraform/README.md`, 운영 스크립트 사용법은 `scripts/README.md`를 기준으로 합니다.

문서 수가 늘어나더라도 같은 내용을 여러 파일에 복사하지 않습니다. 한 주제의 상세 기준은 하나의 canonical 문서가 소유하고, 다른 문서는 요약과 링크만 둡니다.

## 먼저 찾을 문서

| 확인하려는 내용 | 시작 문서 | 다음 상세 문서 |
| --- | --- | --- |
| 프로젝트 전체 범위와 구현 상태 | [루트 README](../README.md) | [저장소 구조](repository-structure.md) |
| AWS 전체 아키텍처 | [전체 아키텍처](architecture.md) | [서비스 네트워크](service-network-architecture.md), [Identity](identity-access.md) |
| Terraform 코드와 변경 절차 | [저장소 구조](repository-structure.md) | [Terraform 변경 관리](terraform-change-management.md), [Terraform README](../terraform/README.md) |
| EKS 운영 | [EKS 운영 표준](eks-operations.md) | [Monitoring](monitoring.md), [공통 Operations](operations.md) |
| CPU·메모리·디스크 알람 기준과 query | [Monitoring Alert Policy](monitoring-alert-policy.md) | [Monitoring 개요](monitoring.md), [확장 관측성 플랫폼](observability-platform.md) |
| AI Agent 플랫폼과 안전 경계 | [AI Platform](ai-platform.md) | [Read-only Incident Triage](agent-incident-triage.md), [Agent 운영 안내](../agents/README.md) |
| Agent의 비즈니스·엔지니어링 성과 | [Agent Value 안내](agent-value/README.md) | business, engineering, measurement, scorecard 문서 |
| 월간·장애 보고서 양식과 비운영 예시 | [Reports Library](../reports/README.md) | [Measurement and Reporting](agent-value/measurement-reporting.md) |
| 포트폴리오 PDF 원고와 생성 기준 | [현재 PDF 원고](portfolio-presentation.md) | [작성 원칙](portfolio-outline.md), [PDF 빌드 도구](../scripts/pdf/build/build_portfolio_presentation_pdf.py) |

## 문서 상태 표기

| 상태 | 의미 |
| --- | --- |
| 현재 구현 | 저장소 코드 또는 로컬 시험으로 확인할 수 있음 |
| 혼합 | 현재 구현과 목표 구조를 같은 문서에서 명시적으로 구분함 |
| 설계 기준 | 향후 적용할 target, 정책 또는 운영 기준이며 배포 완료를 뜻하지 않음 |
| 검토 결과 | 현재 코드에서 확인한 통제, 위험과 완료 조건 |
| 템플릿 | 실제 값과 증거를 채워 발행해야 하는 양식 |
| 빌드 소스 | PDF 생성에 사용되며 운영 기준의 canonical source는 아님 |

상태가 `혼합` 또는 `설계 기준`인 문서의 예시값을 실제 AWS 배포 결과나 운영 성과로 인용하지 않습니다.

## 전체 문서 목록

### 1. 탐색과 포트폴리오

| 파일 | 상태 | 역할과 관리 기준 |
| --- | --- | --- |
| [repository-structure.md](repository-structure.md) | 현재 구현 | 디렉터리별 책임, 코드 시작 위치와 면접 시 탐색 경로 |
| [portfolio-presentation.md](portfolio-presentation.md) | 빌드 소스 | 현재 `enterprise-cloud-portfolio.pdf`의 본문 canonical source |
| [portfolio-presentation-header.tex](portfolio-presentation-header.tex) | 빌드 소스 | PDF 글꼴, 여백, 머리말과 표 스타일. 운영 내용은 넣지 않음 |
| [portfolio-outline.md](portfolio-outline.md) | 설계 기준 | PDF의 아키텍처 중심 작성 기준과 10개 장 목차. 현재 PDF 내용 자체는 `portfolio-presentation.md`가 소유 |

### 2. 아키텍처와 접근 제어

| 파일 | 상태 | 역할과 관리 기준 |
| --- | --- | --- |
| [architecture.md](architecture.md) | 혼합 | 조직, 계정, 네트워크, 보안과 플랫폼의 전체 구조 요약 |
| [service-network-architecture.md](service-network-architecture.md) | 혼합 | IPAM, TGW, 서비스 5종·환경 3종 VPC와 state ownership 상세 |
| [identity-access.md](identity-access.md) | 설계 기준 | Corporate IdP, IAM Identity Center, permission set과 break-glass 기준 |
| [ai-platform.md](ai-platform.md) | 혼합 | 중앙 AI Gateway와 Tool Broker 목표 구조, 현재 Agent Runtime 경계 |

### 3. EKS와 관측성

| 파일 | 상태 | 역할과 관리 기준 |
| --- | --- | --- |
| [eks-operations.md](eks-operations.md) | 혼합 | EKS logging, QoS, 가용성, scaling, upgrade, backup과 Day-2 runbook의 canonical source |
| [monitoring.md](monitoring.md) | 혼합 | 공통 관측성 계층, 알림 채널과 workload 사례를 요약하는 진입 문서 |
| [monitoring-alert-policy.md](monitoring-alert-policy.md) | 설계 기준 | metric query, M/N 또는 `for`, Warning/Critical, missing data와 tuning의 canonical source |
| [observability-platform.md](observability-platform.md) | 설계 기준 | Mimir, OpenTelemetry, metric catalog, Adapter와 KEDA 확장 구조 |

문서 경계는 다음과 같습니다.

- EKS node, Pod, control-plane 운영 기준은 `eks-operations.md`가 소유합니다.
- CPU·memory·disk처럼 플랫폼 공통 임계값과 query는 `monitoring-alert-policy.md`가 소유합니다.
- `monitoring.md`는 두 문서의 상세 표를 복제하지 않고 공통 흐름과 사례만 설명합니다.
- Mimir와 OpenTelemetry 장기 목표 구조는 `observability-platform.md`가 소유합니다.

### 4. 공통 운영, 비용과 변경 통제

| 파일 | 상태 | 역할과 관리 기준 |
| --- | --- | --- |
| [operations.md](operations.md) | 혼합 | AWS Backup, scheduler, patch, CVE/EOS와 공통 운영 주기 |
| [finops.md](finops.md) | 설계 기준 | 태그, 예산, 비용 이상 탐지, rightsizing과 실현 절감 검증 |
| [terraform-change-management.md](terraform-change-management.md) | 설계 기준 | state ownership, plan 검토, 승인, 배포와 rollback |
| [security-review.md](security-review.md) | 검토 결과 | 구현 통제, 잔여 위험, 운영 적용 전 production gate |

`operations.md`는 EC2/RDS와 공통 AWS 운영을, `eks-operations.md`는 EKS 고유 lifecycle과 Kubernetes 정책을 소유합니다. 비용 기준은 `finops.md`, 보안 finding과 예외는 `security-review.md`에만 상세히 기록합니다.

### 5. Agent Runtime과 성과

| 파일 | 상태 | 역할과 관리 기준 |
| --- | --- | --- |
| [agent-incident-triage.md](agent-incident-triage.md) | 현재 구현 | read-only Monitoring Agent의 요청, query, 보안 경계, 실행과 report 검증 |
| [agent-value/README.md](agent-value/README.md) | 혼합 | Agent 가치 문서 묶음의 진입점과 성과 주장 경계 |
| [agent-value/business-outcomes.md](agent-value/business-outcomes.md) | 설계 기준 | 서비스 연속성, delivery, 비용, risk와 조직 확장성 |
| [agent-value/engineering-outcomes.md](agent-value/engineering-outcomes.md) | 설계 기준 | 장애, 변경, EKS, 보안, FinOps와 Agent 품질 KPI |
| [agent-value/measurement-reporting.md](agent-value/measurement-reporting.md) | 설계 기준 | evidence chain, 보고서 종류, cadence, 보존과 승인 |
| [agent-value/scorecard-template.md](agent-value/scorecard-template.md) | 템플릿 | 월간·분기 성과표. placeholder를 실제 값이나 `not_available`로 교체 후 발행 |

AI Platform의 계정·Gateway·Tool Broker 구조는 `ai-platform.md`, 현재 실행 가능한 Monitoring Agent MVP는 `agent-incident-triage.md`, 운영자 질문과 승인 흐름은 `agents/`, 성과 측정은 `agent-value/`가 각각 소유합니다.

사람이 발행하는 월간 플랫폼·장애 보고서 양식과 sanitized example은 [`reports/`](../reports/)에서 관리합니다. 보고서 종류, cadence, KPI 집계, 보존과 승인 기준은 `agent-value/measurement-reporting.md`를 복제하지 않고 참조합니다.

## 문서 추가와 변경 규칙

1. 새 파일을 만들기 전에 위 목록에서 같은 주제의 canonical 문서를 확인합니다.
2. 기존 문서에 한 절로 추가할 수 있으면 새 파일을 만들지 않습니다.
3. 새 문서가 필요하면 목적, 현재/목표 경계, owner, 관련 코드와 검증 방법을 첫 부분에 적습니다.
4. 같은 표나 임계값을 README, 운영 문서와 PDF 원고에 복사하지 않고 canonical 문서를 링크합니다.
5. 코드 값이 바뀌면 해당 canonical 문서와 PDF 원고에서 인용한 값도 함께 검토합니다.
6. `<...>`, example, target 값은 실제 성과나 배포 증거와 분리합니다.
7. 문서를 추가·이름 변경·이동하면 이 목록, 루트 README와 내부 상대 링크를 함께 갱신합니다.
8. PDF 관련 파일은 `portfolio-*`, 실제 운영 기준은 domain 이름을 사용해 구분합니다.

## 권장 문서 머리말

새 운영 문서는 다음 정보를 짧게 포함합니다.

```text
목적: 이 문서가 답하는 질문
상태: 현재 구현 | 혼합 | 설계 기준 | 검토 결과 | 템플릿
Canonical scope: 이 문서가 단독으로 소유하는 기준
Current evidence: 코드, 시험 또는 운영 증거
Target boundary: 아직 구현되지 않은 내용
Owner: 검토와 승인 책임
```

현재 파일을 물리적인 하위 디렉터리로 이동하는 작업은 기존 Markdown 링크, PDF source와 빌드 스크립트 경로를 함께 바꿔야 하므로 별도 변경으로 진행합니다. 우선 이 문서 인덱스를 기준으로 중복을 줄이고, 파일 수가 더 늘어날 때 `architecture/`, `operations/`, `platform/`, `portfolio/` 하위 구조로 승격합니다.
