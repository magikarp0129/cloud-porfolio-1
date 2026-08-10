#!/usr/bin/env python3

import argparse
from pathlib import Path
import re
import subprocess
import sys
import tempfile


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / ".pdf-tools"))

from PIL import Image, ImageDraw
from pypdf import PdfReader


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument(
        "--render-dir",
        type=Path,
        default=Path(tempfile.gettempdir()) / "cloud-portfolio-pdf-review",
    )
    args = parser.parse_args()

    pdf_path = args.pdf.resolve()
    render_dir = args.render_dir.resolve()
    render_dir.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(pdf_path))
    if len(reader.pages) < 15 or len(reader.pages) > 24:
        raise RuntimeError(f"Expected a readable 15-24 page portfolio, got {len(reader.pages)}")

    empty_pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if len(text) < 30:
            empty_pages.append(number)
    if empty_pages:
        raise RuntimeError(f"Pages with insufficient text: {empty_pages}")

    full_text = "\n".join((page.extract_text() or "") for page in reader.pages)

    def compact(text):
        return re.sub(r"\s+", "", text)

    compact_full_text = compact(full_text)
    required_text = [
        "README 기반 독자판",
        "프로젝트 목표",
        "설계 영역별 Target Scope",
        "AWS 클라우드 및 네트워크",
        "Terraform과 IaC",
        "FinOps 및 Cost Governance",
        "AI Platform 및 Multi-Agent",
        "Documentation 및 Validation",
        "범위와 증거를 읽는 방법",
        "저장소 구조와 권장 탐색 순서",
        "Multi-Agent Operating Model",
        "Cloud Platform Manager Agent",
        "Strategy, Architecture and Governance",
        "Platform Engineering and Delivery",
        "Reliability and Operations",
        "Assurance and Knowledge",
        "Manager 1개와 전문 역할 10개",
        "Target Cloud Architecture",
        "Landing Zone과 서비스 네트워크",
        "Terraform Implementation Strategy",
        "EKS와 Kubernetes Platform",
        "Monitoring and Alerting",
        "Operations Strategy",
        "FinOps Strategy",
        "Security and Governance",
        "현재 구현과 검증 상태",
        "다음 구현 단계",
        "Definition of Done과 Production Promotion Gate",
        "Current, Defined, Target, Evidence",
        "Human-led, Agent-assisted",
        "apply는 Agent mode가 아닙니다",
        "10.64.0.0/10",
        "15개 독립 VPC root",
        "Private EKS 1.35",
        "28개 validation target",
        "25개 통과",
        "ResourceQuota",
        "LB subnet",
        "EKS Node subnet",
        "VPC CNI Pod subnet",
        "AZ별 ENIConfig",
        "90 / 90 / 365",
        "30 / 90 / 365",
        "Karpenter, Cluster Autoscaler, workload HPA/KEDA 미구현",
        "28/28 validate 성공을 주장하지 않음",
        "실제 청구 데이터와 실현 절감액은 포함되어 있지 않습니다",
        "protected CI/CD",
    ]
    missing_text = [token for token in required_text if compact(token) not in compact_full_text]
    if missing_text:
        raise RuntimeError(f"Required portfolio presentation text missing: {missing_text}")

    forbidden_text = [
        "설계 원칙과 책임 경계",
        "AI Agent 기반 인프라 운영",
        "비즈니스 성과와 엔지니어링 성과",
        "주요 Architecture Decision과 다음 단계",
        "Terraform 검증 10/10",
        "EKS (Kubernetes 1.29)",
        "3계정 분리 (Landing Zone / Service / Operations)",
        "internet-facing annotation",
        "단일 NAT",
        "AZ별 NAT",
    ]
    stale = [token for token in forbidden_text if compact(token) in compact_full_text]
    if stale:
        raise RuntimeError(f"Stale portfolio claims found: {stale}")

    toc_text = reader.pages[0].extract_text() or ""
    required_toc_entries = [
        "1 프로젝트 목표",
        "2 범위와 증거를 읽는 방법",
        "3 저장소 구조와 권장 탐색 순서",
        "4 Multi-Agent Operating Model",
        "5 Target Cloud Architecture",
        "6 Landing Zone과 서비스 네트워크",
        "7 Terraform Implementation Strategy",
        "8 EKS와 Kubernetes Platform",
        "9 Monitoring and Alerting",
        "10 Operations Strategy",
        "11 FinOps Strategy",
        "12 Security and Governance",
        "13 현재 구현과 검증 상태",
        "14 다음 구현 단계",
        "15 Definition of Done과 Production Promotion Gate",
    ]
    compact_toc_text = compact(toc_text)
    missing_toc_entries = [token for token in required_toc_entries if compact(token) not in compact_toc_text]
    if missing_toc_entries:
        raise RuntimeError(f"Presentation table of contents entries missing: {missing_toc_entries}")

    if compact("목차") not in compact_toc_text:
        raise RuntimeError("Expected the presentation table of contents on page 1")

    def flatten_outline(items, level=0):
        entries = []
        for item in items:
            if isinstance(item, list):
                entries.extend(flatten_outline(item, level + 1))
            else:
                entries.append((level, getattr(item, "title", str(item))))
        return entries

    outline_entries = flatten_outline(reader.outline)
    outline_titles = [title for _, title in outline_entries]
    compact_outline_titles = [compact(title) for title in outline_titles]
    missing_outline = [
        entry for entry in required_toc_entries
        if compact(re.sub(r"^\d+\s*", "", entry)) not in compact_outline_titles
    ]
    if missing_outline:
        raise RuntimeError(
            "Expected every portfolio chapter in PDF bookmarks; "
            f"missing={missing_outline}"
        )

    for old_render in render_dir.glob("portfolio-page-*.png"):
        old_render.unlink()

    prefix = render_dir / "portfolio-page"
    subprocess.run(
        ["pdftoppm", "-png", "-r", "110", str(pdf_path), str(prefix)],
        check=True,
        capture_output=True,
        text=True,
    )

    pages = sorted(render_dir.glob("portfolio-page-*.png"))
    if len(pages) != len(reader.pages):
        raise RuntimeError(f"Rendered {len(pages)} pages for {len(reader.pages)}-page PDF")

    thumb_w, thumb_h = 260, 368
    cols = 4
    rows = (len(pages) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (thumb_w + 16) + 16, rows * (thumb_h + 32) + 16), "#D7DEE3")
    draw = ImageDraw.Draw(sheet)

    for index, path in enumerate(pages):
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_w, thumb_h))
        x = 16 + (index % cols) * (thumb_w + 16)
        y = 16 + (index // cols) * (thumb_h + 32)
        sheet.paste(image, (x, y))
        draw.text((x, y + thumb_h + 5), f"Page {index + 1}", fill="#17212B")

    contact_sheet = render_dir / "portfolio-contact-sheet.png"
    sheet.save(contact_sheet)
    print(f"pages={len(reader.pages)}")
    print(f"contact_sheet={contact_sheet}")


if __name__ == "__main__":
    main()
