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
    if len(reader.pages) < 10 or len(reader.pages) > 18:
        raise RuntimeError(f"Expected a concise 10-18 page portfolio, got {len(reader.pages)}")

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
        "프로젝트 개요",
        "프로젝트 배경",
        "랜딩 존 아키텍처",
        "Terraform 아키텍처",
        "모니터링 및 관측성 아키텍처",
        "EKS 아키텍처",
        "보안 아키텍처",
        "서비스 아키텍처",
        "거버넌스",
        "비용 관리",
        "10.64.0.0/10",
        "15개 VPC",
        "EKS 1.35",
        "ResourceQuota",
        "LB subnet",
        "EKS Node subnet",
        "VPC CNI Pod subnet",
        "AZ별 ENIConfig",
        "Landing Zone TGW",
        "internal annotation",
        "90 / 90 / 365",
        "30 / 90 / 365",
        "Karpenter 미설치",
        "Cluster Autoscaler 미설치",
        "서비스별 EKS cluster 미구현",
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
        "1 프로젝트 개요",
        "2 프로젝트 배경",
        "3 랜딩 존 아키텍처",
        "4 Terraform 아키텍처",
        "5 모니터링 및 관측성 아키텍처",
        "6 EKS 아키텍처",
        "7 보안 아키텍처",
        "8 서비스 아키텍처",
        "9 거버넌스",
        "10 비용 관리",
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
