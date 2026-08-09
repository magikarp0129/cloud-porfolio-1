#!/usr/bin/env python3
"""Verify the generated enterprise service Landing Zone PDF."""

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / ".pdf-tools"))

from pypdf import PdfReader


PDF_PATH = REPO_ROOT / "enterprise-service-landing-zone-architecture.pdf"
REQUIRED = [
    "Enterprise Service Landing Zone",
    "10.64.0.0/10",
    "commerce",
    "payments",
    "analytics",
    "customer-profile",
    "internal-admin",
    "10.65.0.0/16",
    "10.73.0.0/18",
    "10.77.0.0/16",
    "10.81.0.0/19",
    "10.84.16.0/20",
    "apne2-az1",
    "10.65.255.160/28",
    "10.65.255.208/28",
    "28/28",
    "NOT DEPLOYED",
    "IP exhaustion",
]


def main() -> int:
    if not PDF_PATH.exists():
        print(f"PDF not found: {PDF_PATH}", file=sys.stderr)
        return 1

    reader = PdfReader(str(PDF_PATH))
    errors: list[str] = []
    if len(reader.pages) != 10:
        errors.append(f"expected 10 pages, got {len(reader.pages)}")

    page_texts = []
    for index, page in enumerate(reader.pages, start=1):
        media = page.mediabox
        if float(media.width) <= float(media.height):
            errors.append(f"page {index} is not landscape")
        text = page.extract_text() or ""
        if len(text.strip()) < 100:
            errors.append(f"page {index} has too little extractable text")
        page_texts.append(text)

    full_text = "\n".join(page_texts)
    for token in REQUIRED:
        if token not in full_text:
            errors.append(f"required text missing: {token}")

    if errors:
        print("Enterprise service Landing Zone PDF verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"PDF verification complete: {PDF_PATH.relative_to(REPO_ROOT)}")
    print(f"- pages: {len(reader.pages)} landscape A4")
    print(f"- required evidence tokens: {len(REQUIRED)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
