#!/usr/bin/env python3

from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / ".pdf-tools"))

from PIL import Image, ImageDraw
from pypdf import PdfReader


SAMPLE_DIR = REPO_ROOT / ".pdf-tools" / "samples" / "layout"
RENDER_DIR = REPO_ROOT / ".pdf-tools" / "review" / "layout-samples"


def main():
    pdfs = sorted(SAMPLE_DIR.glob("*.pdf"))
    if len(pdfs) != 10:
        raise RuntimeError(f"Expected 10 layout samples, got {len(pdfs)}")

    required = [
        "프로젝트 개요",
        "환경 3",
        "Terraform 모듈 15",
        "Terraform 검증 10/10",
        "에이전트 시험 24/24",
        "산정 기준",
        "1.1 해결하려는 문제",
    ]
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    for old in RENDER_DIR.glob("*.png"):
        old.unlink()

    rendered = []
    for pdf in pdfs:
        reader = PdfReader(str(pdf))
        if len(reader.pages) != 4:
            raise RuntimeError(f"{pdf.name}: expected 4 pages, got {len(reader.pages)}")
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        normalized_text = " ".join(text.split())
        missing = [token for token in required if token not in normalized_text]
        if "증명하지 않는 것" not in normalized_text and "해석 제한" not in normalized_text:
            missing.append("증명하지 않는 것/해석 제한")
        if missing:
            raise RuntimeError(f"{pdf.name}: missing text {missing}")

        prefix = RENDER_DIR / pdf.stem
        subprocess.run(
            ["pdftoppm", "-png", "-r", "90", str(pdf), str(prefix)],
            check=True,
            capture_output=True,
            text=True,
        )
        pages = sorted(RENDER_DIR.glob(f"{pdf.stem}-*.png"))
        if len(pages) != 4:
            raise RuntimeError(f"{pdf.name}: rendered {len(pages)} pages")
        rendered.extend((pdf.stem, page_number, path) for page_number, path in enumerate(pages, 1))

    thumb_w, thumb_h = 220, 311
    gap_x, gap_y = 14, 28
    cols = 5
    rows = (len(rendered) + cols - 1) // cols
    sheet = Image.new(
        "RGB",
        (cols * (thumb_w + gap_x) + gap_x, rows * (thumb_h + gap_y) + gap_y),
        "#D9DEE3",
    )
    draw = ImageDraw.Draw(sheet)
    for index, (stem, page_number, path) in enumerate(rendered):
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_w, thumb_h))
        x = gap_x + (index % cols) * (thumb_w + gap_x)
        y = gap_y + (index // cols) * (thumb_h + gap_y)
        sheet.paste(image, (x, y))
        draw.text((x, y - 17), f"{stem} / p{page_number}", fill="#17212B")

    contact_sheet = RENDER_DIR / "layout-samples-contact-sheet.png"
    sheet.save(contact_sheet)
    print(f"samples={len(pdfs)}")
    print(f"pages={len(rendered)}")
    print(f"contact_sheet={contact_sheet}")


if __name__ == "__main__":
    main()
