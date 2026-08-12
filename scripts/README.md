# PDF Build Tools

이 디렉터리는 최종 포트폴리오 PDF를 생성하고 렌더링 검수하는 두 개의 진입점만 유지합니다.

```text
scripts/pdf/
├── build/build_portfolio_presentation_pdf.py
└── verify/verify_portfolio_pdf.py
```

## Build

```bash
python3 scripts/pdf/build/build_portfolio_presentation_pdf.py
```

입력은 `docs/portfolio-presentation.md`와 `docs/portfolio-presentation-header.tex`, 출력은 저장소 최상위 `enterprise-cloud-portfolio.pdf`입니다. `pandoc`, `xelatex`와 한글 글꼴이 필요합니다.

## Verify

```bash
python3 scripts/pdf/verify/verify_portfolio_pdf.py enterprise-cloud-portfolio.pdf
```

검수기는 Poppler의 `pdfinfo`, `pdftotext`, `pdftoppm`을 사용해 페이지 수, 필수 문구, 빈 페이지와 전체 PNG 렌더링을 확인합니다. 기본 렌더링 경로는 시스템 임시 디렉터리이므로 저장소 내부에 `tmp/`를 만들지 않습니다.

비교용 PDF builder, 운영 점검 스크립트와 프로젝트 전용 validation wrapper는 2026-08-12 저장소 단순화에서 제거했습니다. Terraform 검증은 각 root에서 표준 `terraform fmt`, `terraform init -backend=false`, `terraform validate`, `terraform plan` 순서로 다시 설계합니다.
