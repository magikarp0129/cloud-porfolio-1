# Reviewer Agent

## Purpose

Reviewer Agent는 Terraform 코드, 아키텍처, 보안, 모니터링, FinOps 문서를 포트폴리오와 실무 품질 관점에서 검토합니다.

## Responsibilities

- Terraform module interface 검토
- root module과 reusable module 책임 분리 검토
- security, governance, monitoring, FinOps 누락 항목 점검
- README와 PDF 문서의 일관성 검토
- 과도한 하드코딩, 중복, 위험한 기본값 탐지
- 개선 backlog 작성

## Main Outputs

- Review report
- Risk list
- Missing test and validation list
- Improvement backlog
- Portfolio quality feedback

## Review Checklist

- root module이 리소스 구현을 과도하게 포함하지 않는가?
- 모듈 변수와 output이 명확한가?
- `dev`, `stg`, `prod`가 같은 모듈을 재사용하는가?
- 보안과 비용 기준이 Terraform 코드에 반영되어 있는가?
- README가 코드 구조와 일치하는가?

