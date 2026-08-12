#!/usr/bin/env python3
"""Verify and render the canonical portfolio PDF with Poppler only."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile


def run(*command: str) -> str:
    return subprocess.run(command, check=True, capture_output=True, text=True).stdout


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value)


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise RuntimeError(f"Invalid rendered PNG: {path}")
    return struct.unpack(">II", header[16:24])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument(
        "--render-dir",
        type=Path,
        default=Path(tempfile.gettempdir()) / "cloud-portfolio-pdf-review",
    )
    args = parser.parse_args()

    for tool in ("pdfinfo", "pdftotext", "pdftoppm"):
        if not shutil.which(tool):
            raise RuntimeError(f"Required Poppler tool is missing: {tool}")

    pdf_path = args.pdf.resolve()
    if not pdf_path.is_file():
        raise RuntimeError(f"PDF does not exist: {pdf_path}")

    info = run("pdfinfo", str(pdf_path))
    page_match = re.search(r"^Pages:\s+(\d+)$", info, re.MULTILINE)
    if not page_match:
        raise RuntimeError("Could not read PDF page count")
    page_count = int(page_match.group(1))
    if not 12 <= page_count <= 24:
        raise RuntimeError(f"Expected a readable 12-24 page portfolio, got {page_count}")

    full_text = run("pdftotext", "-layout", str(pdf_path), "-")
    compact_text = compact(full_text)
    required_text = [
        "상세 목차",
        "프로젝트 개요",
        "숫자의 의미",
        "증거와 완료 상태를 읽는 방법",
        "Target Cloud Architecture",
        "Landing Zone",
        "서비스 네트워크와 IP 설계",
        "Terraform 구조와 변경 관리",
        "Private EKS와 Kubernetes Platform",
        "Monitoring, Security and Governance",
        "Operations and FinOps",
        "협업과 승인 경계",
        "저장소 탐색",
        "다음 단계",
        "10.64.0.0/10",
        "서비스 5",
        "VPC 15",
        "subnet tier 7",
        "module 17",
        "Private EKS 1.35",
        "실제 AWS plan 없음",
        "Production promotion gate",
    ]
    missing = [token for token in required_text if compact(token) not in compact_text]
    if missing:
        raise RuntimeError(f"Required portfolio text missing: {missing}")

    forbidden_text = [
        "25개 통과",
        "Monitoring Agent MVP",
        "config/monitoring",
        "schemas/",
        "agent-runtime/",
        "monitoring-agent-access",
        "28/28",
    ]
    stale = [token for token in forbidden_text if compact(token) in compact_text]
    if stale:
        raise RuntimeError(f"Removed or stale portfolio claims found: {stale}")

    for page in range(1, page_count + 1):
        page_text = run(
            "pdftotext",
            "-f",
            str(page),
            "-l",
            str(page),
            str(pdf_path),
            "-",
        ).strip()
        if len(page_text) < 30:
            raise RuntimeError(f"Page {page} has insufficient extractable text")

    render_dir = args.render_dir.resolve()
    render_dir.mkdir(parents=True, exist_ok=True)
    for old_render in render_dir.glob("portfolio-page-*.png"):
        old_render.unlink()

    prefix = render_dir / "portfolio-page"
    subprocess.run(
        ["pdftoppm", "-png", "-r", "120", str(pdf_path), str(prefix)],
        check=True,
        capture_output=True,
        text=True,
    )

    pages = sorted(render_dir.glob("portfolio-page-*.png"))
    if len(pages) != page_count:
        raise RuntimeError(f"Rendered {len(pages)} pages for {page_count}-page PDF")

    for page in pages:
        width, height = png_size(page)
        if width < 900 or height < 1200 or page.stat().st_size < 10_000:
            raise RuntimeError(
                f"Rendered page looks incomplete: {page} ({width}x{height}, {page.stat().st_size} bytes)"
            )

    print(f"pages={page_count}")
    print(f"render_dir={render_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
