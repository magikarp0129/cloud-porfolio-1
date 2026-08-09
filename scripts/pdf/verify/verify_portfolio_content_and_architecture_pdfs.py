#!/usr/bin/env python3

"""Verify and render the ten content strategies and AWS diagram pack."""

from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / ".pdf-tools"))

from PIL import Image, ImageChops, ImageDraw
from pypdf import PdfReader


CONTENT_DIR = REPO_ROOT / ".pdf-tools" / "samples" / "content-strategy"
ARCHITECTURE_PDF = REPO_ROOT / "aws-architecture-diagram-pack.pdf"
RENDER_ROOT = REPO_ROOT / ".pdf-tools" / "review" / "content-and-architecture"

STRATEGY_TOKENS = {
    "01-engineering-report.pdf": ["문제와 범위", "설계 원칙", "구현", "검증", "한계와 다음 단계"],
    "02-problem-solving-case-study.pdf": ["상황", "제약", "검토한 선택지", "선택과 실행", "회고"],
    "03-architecture-decision-pack.pdf": ["ADR-001", "ADR-002", "ADR-003", "ADR-004", "재검토"],
    "04-interview-portfolio.pdf": ["90초 요약", "왜 이렇게 했나요?", "예상 질문", "Q ·", "A ·"],
    "05-production-readiness-review.pdf": ["판정 요약", "필수 gate", "준비도 매트릭스", "Go/No-Go", "CONDITIONAL"],
    "06-evidence-led-audit.pdf": ["주장 등록부", "증적 매핑", "책임 매핑", "예외와 한계", "잔여 위험"],
    "07-business-outcome-narrative.pdf": ["사업 문제", "플랫폼 능력", "성과 가설", "측정 설계", "투자 로드맵"],
    "08-platform-product-document.pdf": ["사용자와 요구", "서비스 카탈로그", "Golden path", "서비스 수준", "제품 로드맵"],
    "09-incident-scenario-runbook.pdf": ["사건", "탐지", "진단", "복구", "예방"],
    "10-maturity-roadmap.pdf": ["Stage 0", "Stage 1", "Stage 2", "Stage 3", "Stage 4"],
}

COMMON_TOKENS = [
    "환경 3",
    "Terraform 모듈 15",
    "Terraform 검증 10/10",
    "에이전트 시험 24/24",
    "실계정",
    "상세목차",
]

ARCHITECTURE_TOKENS = [
    "AWS Organizations와 계정 배치",
    "Landing Zone Transit Gateway 목표 구조",
    "TGW 미구현",
    "10.10.0.0/16",
    "10.15.0.0/16",
    "10.20.0.0/16",
    "10.20.22.0/24",
    "AZ마다 1개",
    "Private DB routing",
    "account 간 east-west",
]


def normalized_text(reader):
    return " ".join(
        " ".join((page.extract_text() or "").split())
        for page in reader.pages
    )


def clean_render_dir(path):
    path.mkdir(parents=True, exist_ok=True)
    for old in path.glob("*.png"):
        old.unlink()


def render_pdf(pdf, render_dir, prefix):
    subprocess.run(
        ["pdftoppm", "-png", "-r", "90", str(pdf), str(render_dir / prefix)],
        check=True,
        capture_output=True,
        text=True,
    )
    return sorted(render_dir.glob(f"{prefix}-*.png"))


def assert_page_has_content(image_path, label):
    image = Image.open(image_path).convert("RGB")
    background = Image.new("RGB", image.size, "white")
    difference = ImageChops.difference(image, background).convert("L")
    difference = difference.point(lambda value: 255 if value > 12 else 0)
    bbox = difference.getbbox()
    if bbox is None:
        raise RuntimeError(f"{label}: rendered page appears blank")
    histogram = difference.histogram()
    non_white = histogram[255]
    if non_white / (image.width * image.height) < 0.008:
        raise RuntimeError(f"{label}: rendered page has too little visible content")


def make_contact_sheets(items, render_dir, stem, per_sheet=25):
    outputs = []
    thumb_w, thumb_h = 230, 163
    gap_x, gap_y = 12, 28
    cols = 5
    for sheet_index, start in enumerate(range(0, len(items), per_sheet), 1):
        chunk = items[start:start + per_sheet]
        rows = (len(chunk) + cols - 1) // cols
        sheet = Image.new(
            "RGB",
            (cols * (thumb_w + gap_x) + gap_x, rows * (thumb_h + gap_y) + gap_y),
            "#D8DEE3",
        )
        draw = ImageDraw.Draw(sheet)
        for index, (label, path) in enumerate(chunk):
            page = Image.open(path).convert("RGB")
            page.thumbnail((thumb_w, thumb_h))
            x = gap_x + (index % cols) * (thumb_w + gap_x)
            y = gap_y + (index // cols) * (thumb_h + gap_y)
            sheet.paste(page, (x, y))
            draw.text((x, y - 17), label, fill="#17212B")
        output = render_dir / f"{stem}-{sheet_index}.png"
        sheet.save(output)
        outputs.append(output)
    return outputs


def verify_content_samples():
    pdfs = sorted(CONTENT_DIR.glob("*.pdf"))
    if len(pdfs) != 10:
        raise RuntimeError(f"Expected 10 content strategy PDFs, got {len(pdfs)}")
    render_dir = RENDER_ROOT / "content-strategies"
    clean_render_dir(render_dir)
    rendered_items = []
    for pdf in pdfs:
        reader = PdfReader(str(pdf))
        if len(reader.pages) != 5:
            raise RuntimeError(f"{pdf.name}: expected 5 pages, got {len(reader.pages)}")
        text = normalized_text(reader)
        missing = [token for token in COMMON_TOKENS + STRATEGY_TOKENS[pdf.name] if token not in text]
        if missing:
            raise RuntimeError(f"{pdf.name}: missing {missing}")
        outlines = reader.outline
        if len(outlines) < 4:
            raise RuntimeError(f"{pdf.name}: expected at least 4 PDF bookmarks, got {len(outlines)}")
        images = render_pdf(pdf, render_dir, pdf.stem)
        if len(images) != 5:
            raise RuntimeError(f"{pdf.name}: rendered {len(images)} pages")
        for page_number, image_path in enumerate(images, 1):
            assert_page_has_content(image_path, f"{pdf.name} page {page_number}")
            rendered_items.append((f"{pdf.stem} / p{page_number}", image_path))
    sheets = make_contact_sheets(rendered_items, render_dir, "content-strategies-contact-sheet")
    return len(pdfs), len(rendered_items), sheets


def verify_architecture_pack():
    if not ARCHITECTURE_PDF.exists():
        raise RuntimeError(f"Missing {ARCHITECTURE_PDF}")
    reader = PdfReader(str(ARCHITECTURE_PDF))
    if len(reader.pages) != 8:
        raise RuntimeError(f"Expected 8 architecture pages, got {len(reader.pages)}")
    text = normalized_text(reader)
    missing = [token for token in ARCHITECTURE_TOKENS if token not in text]
    if missing:
        raise RuntimeError(f"Architecture pack missing {missing}")
    for index, page in enumerate(reader.pages, 1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        if width <= height:
            raise RuntimeError(f"Architecture page {index}: expected landscape page")
    render_dir = RENDER_ROOT / "architecture"
    clean_render_dir(render_dir)
    images = render_pdf(ARCHITECTURE_PDF, render_dir, "architecture")
    if len(images) != 8:
        raise RuntimeError(f"Architecture pack rendered {len(images)} pages")
    items = []
    for page_number, image_path in enumerate(images, 1):
        assert_page_has_content(image_path, f"architecture page {page_number}")
        items.append((f"architecture / p{page_number}", image_path))
    sheets = make_contact_sheets(items, render_dir, "architecture-contact-sheet", per_sheet=10)
    return len(images), sheets


def main():
    content_count, content_pages, content_sheets = verify_content_samples()
    architecture_pages, architecture_sheets = verify_architecture_pack()
    print(f"content_samples={content_count}")
    print(f"content_pages={content_pages}")
    print(f"architecture_pages={architecture_pages}")
    for sheet in content_sheets + architecture_sheets:
        print(f"contact_sheet={sheet}")


if __name__ == "__main__":
    main()
