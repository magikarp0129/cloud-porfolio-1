#!/usr/bin/env python3

"""Build ten comparable PDF layout samples for the portfolio."""

from pathlib import Path
import sys
from xml.sax.saxutils import escape


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / ".pdf-tools"))

import build_portfolio_pdf as base
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


OUTPUT_DIR = REPO_ROOT / ".pdf-tools" / "samples" / "layout"


THEMES = [
    dict(slug="01-classic-report", name="01 클래식 리포트", mode="narrative", cover="rail",
         accent="#0A7C86", secondary="#C9851E", ink="#17212B", muted="#596672", paper="#FFFFFF", soft="#F2F6F7"),
    dict(slug="02-minimal-editorial", name="02 미니멀 에디토리얼", mode="editorial", cover="minimal",
         accent="#B64235", secondary="#222222", ink="#202020", muted="#6E6862", paper="#FCFAF5", soft="#F1EDE5"),
    dict(slug="03-technical-manual", name="03 기술 매뉴얼", mode="manual", cover="band",
         accent="#1769AA", secondary="#19A7A0", ink="#152536", muted="#536779", paper="#FFFFFF", soft="#EDF4F9"),
    dict(slug="04-card-dashboard", name="04 카드형 대시보드", mode="cards", cover="cards",
         accent="#00796B", secondary="#E67E22", ink="#18332F", muted="#55716C", paper="#FAFCFB", soft="#EAF4F1"),
    dict(slug="05-sidebar-navigation", name="05 사이드바 내비게이션", mode="rail", cover="sidebar",
         accent="#235789", secondary="#F1A208", ink="#1D2D3D", muted="#607183", paper="#FFFFFF", soft="#EEF3F8"),
    dict(slug="06-chapter-divider", name="06 챕터 디바이더", mode="chapter", cover="dark",
         accent="#F0B429", secondary="#3FA7D6", ink="#14213D", muted="#667085", paper="#FFFFFF", soft="#F4F6FA", dark=True),
    dict(slug="07-audit-report", name="07 감사 보고서", mode="audit", cover="outline",
         accent="#4A5568", secondary="#2D3748", ink="#20252B", muted="#68717B", paper="#FFFFFF", soft="#F3F4F5"),
    dict(slug="08-portfolio-magazine", name="08 포트폴리오 매거진", mode="magazine", cover="magazine",
         accent="#3155A6", secondary="#E24A3B", ink="#19213A", muted="#65708A", paper="#FBFCFF", soft="#EDF1FB"),
    dict(slug="09-operations-runbook", name="09 운영 런북", mode="runbook", cover="status",
         accent="#237A57", secondary="#D99A2B", ink="#183126", muted="#5F746A", paper="#FBFDFB", soft="#EAF5EF"),
    dict(slug="10-executive-brief", name="10 경영진 브리프", mode="brief", cover="executive",
         accent="#163A5F", secondary="#D4A72C", ink="#142C43", muted="#627386", paper="#FFFFFF", soft="#EEF2F6", dark=True),
]


CHAPTERS = [
    "프로젝트 개요",
    "전체 아키텍처와 책임 경계",
    "Terraform 구현과 변경 관리",
    "EKS 플랫폼 운영",
    "관측성과 장애 대응",
    "운영 자동화, 보안과 비용 관리",
    "사람 주도 AI 에이전트 도입",
    "비즈니스 성과와 엔지니어링 성과",
    "검증 결과와 남은 한계",
    "교훈과 다음 단계",
]


METRICS = [
    dict(value="3", label="환경", title="환경 3",
         criteria="논리 workload 환경인 dev, stg, prod를 셉니다.",
         scope="각 환경은 AWS 공통 기반 root와 별도의 Kubernetes platform root를 가지며 가용 영역, NAT, 보존 기간과 운영 보호 입력이 다릅니다.",
         limit="실제 AWS 계정 3개에 배포가 완료됐거나 운영 중이라는 뜻은 아닙니다."),
    dict(value="15", label="Terraform 모듈", title="Terraform 모듈 15",
         criteria="terraform/modules의 16개 디렉터리 중 실제 .tf 구현이 있는 15개를 셉니다.",
         scope="조직·정책, 네트워크, EKS·Kubernetes, 보안, 관측성, 운영, IAM, 비용과 에이전트 접근 모듈이 포함됩니다. compute는 향후 EC2/ECS용 예약 자리라 제외합니다.",
         limit="15개가 모두 실제 계정에 적용됐거나 운영 준비를 마쳤다는 뜻은 아닙니다."),
    dict(value="10/10", label="Terraform 검증", title="Terraform 검증 10/10",
         criteria="스크립트에 등록된 10개 대상이 init -backend=false와 validate를 모두 통과했습니다.",
         scope="7개 배포 root는 organization, dev/stg/prod AWS 기반, dev/stg/prod platform이고 3개 독립 모듈은 security-group, route-policy, waf입니다. fmt와 scheduler.py 문법도 확인합니다.",
         limit="15개 모듈 각각의 plan/apply나 실제 계정의 권한·용량·비용은 증명하지 않습니다."),
    dict(value="24/24", label="에이전트 시험", title="에이전트 시험 24/24",
         criteria="agent-runtime 자동화 시험 24건이 모두 통과했습니다.",
         scope="요청 계약 9건, 보안 경계 8건, 장애 분석 5건, Terraform 권한 경계 2건으로 구성됩니다.",
         limit="모의 입력과 로컬 시험이므로 live AWS/EKS 연결, 장애 정확도, MTTR 개선과 운영 권한 안전성을 완전히 증명하지 않습니다."),
]


def color(value):
    return colors.HexColor(value)


def sample_styles(theme):
    ink = color(theme["ink"])
    muted = color(theme["muted"])
    accent = color(theme["accent"])
    dark_cover = theme.get("dark", False)
    return {
        "cover_eyebrow": ParagraphStyle(
            "cover-eyebrow", fontName="Portfolio-Bold", fontSize=9,
            textColor=colors.white if dark_cover else accent, leading=13, spaceAfter=12,
        ),
        "cover_title": ParagraphStyle(
            "cover-title", fontName="Portfolio-Bold",
            fontSize=32 if theme["mode"] not in ("editorial", "magazine") else 36,
            leading=41, textColor=colors.white if dark_cover else ink, spaceAfter=17,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover-subtitle", fontName="Portfolio", fontSize=11, leading=18,
            textColor=colors.HexColor("#E7EDF3") if dark_cover else muted, spaceAfter=20,
        ),
        "h1": ParagraphStyle(
            "sample-h1", fontName="Portfolio-Bold", fontSize=23, leading=31,
            textColor=ink, spaceAfter=14, wordWrap="CJK",
        ),
        "h2": ParagraphStyle(
            "sample-h2", fontName="Portfolio-Bold", fontSize=14, leading=21,
            textColor=accent, spaceBefore=10, spaceAfter=7, wordWrap="CJK",
        ),
        "body": ParagraphStyle(
            "sample-body", fontName="Portfolio", fontSize=9.6, leading=16,
            textColor=ink, spaceAfter=8, wordWrap="CJK",
        ),
        "small": ParagraphStyle(
            "sample-small", fontName="Portfolio", fontSize=7.8, leading=12,
            textColor=muted, wordWrap="CJK",
        ),
        "label": ParagraphStyle(
            "sample-label", fontName="Portfolio-Bold", fontSize=8.3, leading=12,
            textColor=accent, wordWrap="CJK",
        ),
        "metric": ParagraphStyle(
            "sample-metric", fontName="Portfolio", fontSize=8, leading=13,
            alignment=TA_CENTER, textColor=muted,
        ),
        "toc": ParagraphStyle(
            "sample-toc", fontName="Portfolio", fontSize=9.3, leading=14,
            textColor=ink, wordWrap="CJK",
        ),
        "toc_number": ParagraphStyle(
            "sample-toc-number", fontName="Portfolio-Bold", fontSize=11, leading=14,
            textColor=accent, alignment=TA_CENTER,
        ),
    }


class SampleDocTemplate(BaseDocTemplate):
    def __init__(self, filename, theme):
        self.theme = theme
        left = 31 * mm if theme["cover"] == "sidebar" else 20 * mm
        super().__init__(
            filename,
            pagesize=A4,
            leftMargin=left,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=18 * mm,
            title=f"포트폴리오 PDF 레이아웃 시안 - {theme['name']}",
            author="클라우드 플랫폼 엔지니어링 포트폴리오",
        )
        frame = Frame(
            self.leftMargin, self.bottomMargin, self.width, self.height,
            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        )
        self.addPageTemplates(PageTemplate(
            id="sample", frames=[frame], onPage=self.draw_page,
        ))

    def draw_page(self, canvas, doc):
        theme = self.theme
        width, height = A4
        accent = color(theme["accent"])
        secondary = color(theme["secondary"])
        paper = color(theme["paper"])
        ink = color(theme["ink"])
        muted = color(theme["muted"])

        canvas.saveState()
        canvas.setFillColor(paper)
        canvas.rect(0, 0, width, height, stroke=0, fill=1)

        if doc.page == 1:
            cover = theme["cover"]
            if theme.get("dark"):
                canvas.setFillColor(ink)
                canvas.rect(0, 0, width, height, stroke=0, fill=1)
            if cover == "rail":
                canvas.setFillColor(accent)
                canvas.rect(0, 0, 6 * mm, height, stroke=0, fill=1)
                canvas.setFillColor(secondary)
                canvas.rect(width - 32 * mm, height - 24 * mm, 14 * mm, 2 * mm, stroke=0, fill=1)
            elif cover == "minimal":
                canvas.setStrokeColor(accent)
                canvas.setLineWidth(1.2)
                canvas.line(20 * mm, height - 26 * mm, width - 20 * mm, height - 26 * mm)
                canvas.setFillColor(accent)
                canvas.circle(width - 27 * mm, 25 * mm, 5 * mm, stroke=0, fill=1)
            elif cover == "band":
                canvas.setFillColor(ink)
                canvas.rect(0, height - 48 * mm, width, 48 * mm, stroke=0, fill=1)
                canvas.setFillColor(accent)
                canvas.rect(0, height - 51 * mm, width, 3 * mm, stroke=0, fill=1)
            elif cover == "cards":
                for x, y, w, h, fill in (
                    (width - 72 * mm, height - 45 * mm, 52 * mm, 22 * mm, accent),
                    (width - 61 * mm, height - 73 * mm, 41 * mm, 20 * mm, secondary),
                    (width - 84 * mm, height - 98 * mm, 64 * mm, 17 * mm, color(theme["soft"])),
                ):
                    canvas.setFillColor(fill)
                    canvas.roundRect(x, y, w, h, 5, stroke=0, fill=1)
            elif cover == "sidebar":
                canvas.setFillColor(accent)
                canvas.rect(0, 0, 26 * mm, height, stroke=0, fill=1)
                canvas.setFillColor(secondary)
                canvas.rect(26 * mm, 0, 3 * mm, height, stroke=0, fill=1)
            elif cover == "dark":
                canvas.setFillColor(accent)
                canvas.setFont("Portfolio-Bold", 92)
                canvas.drawRightString(width - 18 * mm, height - 48 * mm, "06")
                canvas.setFillColor(secondary)
                canvas.rect(20 * mm, 28 * mm, 55 * mm, 2 * mm, stroke=0, fill=1)
            elif cover == "outline":
                canvas.setStrokeColor(accent)
                canvas.setLineWidth(1)
                canvas.rect(14 * mm, 14 * mm, width - 28 * mm, height - 28 * mm, stroke=1, fill=0)
                canvas.setFont("Courier", 8)
                canvas.setFillColor(muted)
                canvas.drawRightString(width - 20 * mm, height - 21 * mm, "CONTROLLED DOCUMENT")
            elif cover == "magazine":
                canvas.setFillColor(accent)
                canvas.rect(0, height - 19 * mm, width, 19 * mm, stroke=0, fill=1)
                canvas.setFillColor(secondary)
                canvas.rect(width - 42 * mm, 0, 42 * mm, 92 * mm, stroke=0, fill=1)
            elif cover == "status":
                canvas.setFillColor(accent)
                canvas.rect(0, 0, width, 7 * mm, stroke=0, fill=1)
                canvas.setFillColor(color(theme["soft"]))
                canvas.roundRect(width - 70 * mm, height - 35 * mm, 50 * mm, 12 * mm, 6 * mm, stroke=0, fill=1)
                canvas.setFillColor(accent)
                canvas.setFont("Portfolio-Bold", 8)
                canvas.drawCentredString(width - 45 * mm, height - 31 * mm, "STATUS · REVIEWABLE")
            elif cover == "executive":
                canvas.setFillColor(ink)
                canvas.rect(0, 0, width, height, stroke=0, fill=1)
                canvas.setFillColor(secondary)
                canvas.rect(20 * mm, height - 31 * mm, width - 40 * mm, 2 * mm, stroke=0, fill=1)
                canvas.rect(20 * mm, 25 * mm, 36 * mm, 2 * mm, stroke=0, fill=1)
            canvas.restoreState()
            return

        if theme["cover"] == "sidebar":
            canvas.setFillColor(accent)
            canvas.rect(0, 0, 24 * mm, height, stroke=0, fill=1)
            canvas.setFillColor(colors.white)
            canvas.setFont("Portfolio-Bold", 8)
            canvas.saveState()
            canvas.translate(10 * mm, 28 * mm)
            canvas.rotate(90)
            canvas.drawString(0, 0, theme["name"])
            canvas.restoreState()
        elif theme["cover"] == "band":
            canvas.setFillColor(ink)
            canvas.rect(0, height - 14 * mm, width, 14 * mm, stroke=0, fill=1)
            canvas.setFillColor(colors.white)
            canvas.setFont("Portfolio", 7.5)
            canvas.drawString(20 * mm, height - 9 * mm, theme["name"])
        elif theme["cover"] == "outline":
            canvas.setStrokeColor(color("#D0D4D8"))
            canvas.rect(13 * mm, 13 * mm, width - 26 * mm, height - 26 * mm, stroke=1, fill=0)
            canvas.setFont("Courier", 7)
            canvas.setFillColor(muted)
            canvas.drawString(20 * mm, height - 10 * mm, "PORTFOLIO / REVIEW COPY")
        else:
            canvas.setStrokeColor(color("#D8DEE4"))
            canvas.line(self.leftMargin, height - 12 * mm, width - 20 * mm, height - 12 * mm)
            canvas.setFont("Portfolio", 7)
            canvas.setFillColor(muted)
            canvas.drawString(self.leftMargin, height - 9 * mm, theme["name"])
        canvas.setFillColor(accent)
        canvas.rect(self.leftMargin, 8 * mm, 14 * mm, 1.3 * mm, stroke=0, fill=1)
        canvas.setFillColor(muted)
        canvas.setFont("Portfolio", 7)
        canvas.drawRightString(width - 20 * mm, 9 * mm, f"{doc.page:02d}")
        canvas.restoreState()


def cover_story(theme, styles):
    mode = theme["mode"]
    top = 43 * mm if mode not in ("chapter", "brief") else 55 * mm
    align = TA_CENTER if mode == "editorial" else TA_LEFT
    for key in ("cover_eyebrow", "cover_title", "cover_subtitle"):
        styles[key].alignment = align
    return [
        Spacer(1, top),
        Paragraph("CLOUD PLATFORM ENGINEERING · LAYOUT SAMPLE", styles["cover_eyebrow"]),
        Paragraph(theme["name"], styles["cover_title"]),
        Paragraph(
            "엔터프라이즈 클라우드 플랫폼 설계 포트폴리오<br/>"
            "동일한 내용으로 정보 위계와 읽기 흐름을 비교하는 시안",
            styles["cover_subtitle"],
        ),
        Spacer(1, 28 * mm),
        Paragraph(
            "비교 범위&nbsp;&nbsp; 표지 · 목차 · 프로젝트 개요 · 숫자 상세 해설 · 본문 예시",
            styles["small"],
        ),
        PageBreak(),
    ]


def contents_story(theme, styles):
    flowables = [
        Paragraph("문서 구성 미리보기", styles["h1"]),
        Paragraph(
            "10개 시안은 같은 장과 같은 문장을 사용합니다. 제목의 위계, 목차 탐색성, 숫자 설명 방식과 본문 밀도를 중심으로 비교해 주세요.",
            styles["body"],
        ),
        Spacer(1, 3 * mm),
    ]
    rows = []
    for index, title in enumerate(CHAPTERS, 1):
        number = Paragraph(f"{index:02d}", styles["toc_number"])
        text = Paragraph(title, styles["toc"])
        rows.append([number, text, Paragraph(str(index + 3), styles["toc_number"])])

    if theme["mode"] in ("cards", "magazine", "brief"):
        cells = []
        for index, title in enumerate(CHAPTERS, 1):
            cell = Paragraph(
                f'<font color="{theme["accent"]}" size="12"><b>{index:02d}</b></font><br/>{escape(title)}',
                ParagraphStyle(
                    f"toc-card-{index}", parent=styles["toc"], fontSize=8.8, leading=13,
                ),
            )
            cells.append(cell)
        grid = [[cells[row * 2], cells[row * 2 + 1]] for row in range(5)]
        table = Table(grid, colWidths=[120 * mm / 2, 120 * mm / 2], hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), color(theme["soft"])),
            ("BOX", (0, 0), (-1, -1), 0.6, color("#D8DEE4")),
            ("INNERGRID", (0, 0), (-1, -1), 0.6, color("#D8DEE4")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
    else:
        table = Table(rows, colWidths=[16 * mm, 132 * mm, 12 * mm], hAlign="LEFT")
        table.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, color("#D8DEE4")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
    flowables.extend([table, PageBreak()])
    return flowables


def metric_strip(theme, styles):
    cells = []
    for item in METRICS:
        cells.append(Paragraph(
            f'<font size="19" color="{theme["accent"]}"><b>{item["value"]}</b></font><br/>'
            f'<font size="7.5" color="{theme["muted"]}">{item["label"]}</font>',
            styles["metric"],
        ))
    table = Table([cells], colWidths=[40 * mm] * 4, rowHeights=[18 * mm], hAlign="LEFT")
    mode = theme["mode"]
    table_style = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.6, color("#D6DEE4")),
        ("INNERGRID", (0, 0), (-1, -1), 0.6, color("#D6DEE4")),
    ]
    if mode in ("cards", "brief", "magazine"):
        table_style.append(("BACKGROUND", (0, 0), (-1, -1), color(theme["soft"])))
    elif mode == "audit":
        table_style.extend([
            ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            ("LINEABOVE", (0, 0), (-1, 0), 1.2, color(theme["accent"])),
            ("LINEBELOW", (0, 0), (-1, 0), 1.2, color(theme["accent"])),
        ])
    else:
        table_style.append(("BACKGROUND", (0, 0), (-1, -1), color(theme["soft"])))
    table.setStyle(TableStyle(table_style))
    return table


def explanation_html(item, theme):
    return (
        f'<font size="11"><b>{escape(item["title"])}</b></font><br/>'
        f'<font color="{theme["accent"]}"><b>산정 기준</b></font>&nbsp;&nbsp;{escape(item["criteria"])}<br/>'
        f'<font color="{theme["accent"]}"><b>구체적인 범위</b></font>&nbsp;&nbsp;{escape(item["scope"])}<br/>'
        f'<font color="{theme["secondary"]}"><b>증명하지 않는 것</b></font>&nbsp;&nbsp;{escape(item["limit"])}'
    )


def explanation_blocks(items, theme, styles, start_index):
    mode = theme["mode"]
    accent = color(theme["accent"])
    secondary = color(theme["secondary"])
    soft = color(theme["soft"])
    line = color("#D7DEE4")
    block_style = ParagraphStyle(
        f"block-{theme['slug']}-{start_index}", parent=styles["body"], fontSize=9, leading=14.5,
    )

    if mode in ("cards", "magazine"):
        cards = [[Paragraph(explanation_html(item, theme), block_style) for item in items]]
        table = Table(cards, colWidths=[79 * mm] * len(items), hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), soft),
            ("BOX", (0, 0), (-1, -1), 0.7, line),
            ("INNERGRID", (0, 0), (-1, -1), 0.7, line),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        return [table]

    if mode == "rail":
        rows = []
        for item in items:
            value = Paragraph(
                f'<font size="22" color="{theme["accent"]}"><b>{item["value"]}</b></font><br/>'
                f'<font size="7" color="{theme["muted"]}">{item["label"]}</font>',
                styles["metric"],
            )
            rows.append([value, Paragraph(explanation_html(item, theme), block_style)])
        table = Table(rows, colWidths=[28 * mm, 130 * mm], hAlign="LEFT")
        table.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 0.6, line),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        return [table]

    if mode == "audit":
        rows = [[
            Paragraph("항목", styles["label"]),
            Paragraph("산정 기준과 범위", styles["label"]),
            Paragraph("해석 제한", styles["label"]),
        ]]
        for item in items:
            rows.append([
                Paragraph(f'<b>{escape(item["title"])}</b><br/><font color="#4A5568">PASS / DEFINED</font>', block_style),
                Paragraph(f'{escape(item["criteria"])}<br/>{escape(item["scope"])}', block_style),
                Paragraph(escape(item["limit"]), block_style),
            ])
        table = Table(rows, colWidths=[35 * mm, 78 * mm, 47 * mm], repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), color(theme["soft"])),
            ("GRID", (0, 0), (-1, -1), 0.6, line),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        return [table]

    if mode == "runbook":
        flowables = []
        for offset, item in enumerate(items, start_index):
            tag = Paragraph(
                f'<font color="{theme["accent"]}"><b>CHECK {offset:02d}</b></font>&nbsp;&nbsp;'
                f'<b>{escape(item["title"])}</b>',
                styles["body"],
            )
            body = Paragraph(explanation_html(item, theme), block_style)
            table = Table([[tag], [body]], colWidths=[158 * mm], hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), soft),
                ("BOX", (0, 0), (-1, -1), 0.7, accent),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]))
            flowables.extend([table, Spacer(1, 4 * mm)])
        return flowables

    flowables = []
    for item in items:
        paragraph = Paragraph(explanation_html(item, theme), block_style)
        if mode == "editorial":
            table_style = [
                ("LINEBELOW", (0, 0), (-1, -1), 0.7, accent),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 20),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
            ]
        elif mode == "manual":
            table_style = [
                ("BACKGROUND", (0, 0), (-1, -1), soft),
                ("LINEBEFORE", (0, 0), (0, -1), 3, accent),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        elif mode == "chapter":
            table_style = [
                ("LINEABOVE", (0, 0), (-1, -1), 1.3, secondary),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        elif mode == "brief":
            table_style = [
                ("BACKGROUND", (0, 0), (-1, -1), soft),
                ("BOX", (0, 0), (-1, -1), 0.7, line),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        else:
            table_style = [
                ("BACKGROUND", (0, 0), (-1, -1), soft),
                ("LINEBELOW", (0, 0), (-1, -1), 0.6, line),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        table = Table([[paragraph]], colWidths=[158 * mm], hAlign="LEFT")
        table.setStyle(TableStyle(table_style))
        flowables.extend([table, Spacer(1, 4 * mm)])
    return flowables


def overview_story(theme, styles):
    question_style = ParagraphStyle(
        f"question-{theme['slug']}", parent=styles["body"],
        backColor=color(theme["soft"]), borderPadding=10,
        textColor=color(theme["ink"]), spaceAfter=10,
    )
    callout_style = ParagraphStyle(
        f"callout-{theme['slug']}", parent=styles["body"],
        backColor=color(theme["soft"]), borderPadding=10,
        textColor=color(theme["ink"]), spaceBefore=5, spaceAfter=10,
    )
    flowables = [
        Paragraph("1. 프로젝트 개요", styles["h1"]),
        Paragraph(
            "<b>이 장에서 답하는 질문</b><br/>이 포트폴리오는 어떤 운영 문제를 해결하려고 했으며, 현재 무엇까지 확인되었는가?",
            question_style,
        ),
        metric_strip(theme, styles),
        Spacer(1, 5 * mm),
        Paragraph("숫자 요약을 읽는 방법", styles["h2"]),
        Paragraph(
            "3·15는 설계와 코드의 범위를, 10/10·24/24는 현재 자동 검증 집합의 통과 상태를 나타냅니다. 같은 내용을 서로 다른 정보 구조로 비교합니다.",
            styles["body"],
        ),
    ]
    flowables.extend(explanation_blocks(METRICS[:2], theme, styles, 1))
    flowables.append(PageBreak())
    flowables.extend([
        Paragraph("1. 프로젝트 개요 · 숫자 해설", styles["h1"]),
        Paragraph(
            "검증 분모는 저장소의 스크립트와 시험 모음에 명시적으로 등록된 대상을 뜻하며, 실제 운영 환경 전체를 의미하지 않습니다.",
            styles["body"],
        ),
    ])
    flowables.extend(explanation_blocks(METRICS[2:], theme, styles, 3))
    flowables.extend([
        Paragraph(
            "<b>해석 원칙</b><br/>자동 검증 통과와 운영 완료를 구분합니다. 실제 계정의 plan/apply, 복구 훈련, 실시간 장애 대응과 사업 성과는 별도 증적이 필요합니다.",
            callout_style,
        ),
        Paragraph("1.1 해결하려는 문제", styles["h2"]),
        Paragraph(
            "계정, 네트워크, 권한, Kubernetes 플랫폼, 백업과 비용 정책은 서로 다른 생명주기를 갖습니다. 이를 하나의 상태와 한 번의 배포에 묶으면 작은 변경도 넓은 장애 범위를 만들 수 있습니다.",
            styles["body"],
        ),
    ])
    return flowables


def build_sample(theme):
    styles = sample_styles(theme)
    story = []
    story.extend(cover_story(theme, styles))
    story.extend(contents_story(theme, styles))
    story.extend(overview_story(theme, styles))
    path = OUTPUT_DIR / f"{theme['slug']}.pdf"
    document = SampleDocTemplate(str(path), theme)
    document.multiBuild(story)
    return path


def main():
    base.register_fonts()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        print(build_sample(theme))


if __name__ == "__main__":
    main()
