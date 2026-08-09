#!/usr/bin/env python3
"""Build the primary portfolio PDF in the concise presentation-report style."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SOURCE = REPOSITORY_ROOT / "docs/portfolio-presentation.md"
HEADER = REPOSITORY_ROOT / "docs/portfolio-presentation-header.tex"
OUTPUT = REPOSITORY_ROOT / "enterprise-cloud-portfolio.pdf"


def main() -> int:
    pandoc = shutil.which("pandoc")
    xelatex = shutil.which("xelatex")
    if not pandoc or not xelatex:
        missing = [name for name, path in (("pandoc", pandoc), ("xelatex", xelatex)) if not path]
        raise RuntimeError(f"Required PDF tools are missing: {', '.join(missing)}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    command = [
        pandoc,
        str(SOURCE),
        "--from=markdown+raw_tex+pipe_tables+fenced_code_blocks",
        "--standalone",
        "--toc",
        "--toc-depth=1",
        "--number-sections",
        f"--include-in-header={HEADER}",
        "--pdf-engine=xelatex",
        "--variable=mainfont:AppleGothic",
        "--variable=sansfont:AppleGothic",
        "--variable=monofont:AppleGothic",
        "--variable=colorlinks:true",
        "--metadata=title-meta:엔터프라이즈 클라우드 플랫폼 엔지니어링 포트폴리오",
        "--metadata=author-meta:클라우드 플랫폼 엔지니어링 포트폴리오",
        f"--resource-path={REPOSITORY_ROOT}",
        f"--output={OUTPUT}",
    ]
    subprocess.run(command, cwd=REPOSITORY_ROOT, check=True)
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
