#!/usr/bin/env python3

from pathlib import Path
import sys
from xml.sax.saxutils import escape


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / ".pdf-tools"))

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents


OUTPUT = REPO_ROOT / "enterprise-cloud-portfolio.pdf"
FONT_PATH = Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf")

INK = colors.HexColor("#17212B")
MUTED = colors.HexColor("#52606D")
TEAL = colors.HexColor("#087E8B")
BLUE = colors.HexColor("#2867B2")
AMBER = colors.HexColor("#C47B18")
RED = colors.HexColor("#B64545")
GREEN = colors.HexColor("#347A57")
LIGHT = colors.HexColor("#F3F6F8")
LINE = colors.HexColor("#D7DEE3")
WHITE = colors.white


def register_fonts():
    if not FONT_PATH.exists():
        raise FileNotFoundError(f"Korean font not found: {FONT_PATH}")
    pdfmetrics.registerFont(TTFont("Portfolio", str(FONT_PATH)))
    pdfmetrics.registerFont(TTFont("Portfolio-Bold", str(FONT_PATH)))
    pdfmetrics.registerFontFamily(
        "Portfolio",
        normal="Portfolio",
        bold="Portfolio-Bold",
        italic="Portfolio",
        boldItalic="Portfolio-Bold",
    )


class PortfolioDocTemplate(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(
            filename,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=19 * mm,
            bottomMargin=17 * mm,
            title="엔터프라이즈 클라우드 플랫폼 엔지니어링 포트폴리오",
            author="클라우드 플랫폼 엔지니어링 포트폴리오",
            subject="Terraform, AWS Organizations, EKS, 보안, 운영, 비용 관리, AI 에이전트",
        )
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="content",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        self.addPageTemplates(PageTemplate(id="portfolio", frames=[frame], onPage=draw_page))

    def beforeDocument(self):
        self._toc_chapter_number = None
        self._toc_section_number = 0

    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph) or not hasattr(flowable, "toc_level"):
            return

        level = flowable.toc_level
        title = flowable.getPlainText()
        if level == 0:
            chapter_number = getattr(flowable, "chapter_number", None)
            self._toc_chapter_number = chapter_number
            self._toc_section_number = 0
            key = getattr(flowable, "bookmark_key", f"chapter-{self.seq.nextf('chapter')}")
        else:
            self._toc_section_number += 1
            key = getattr(
                flowable,
                "bookmark_key",
                f"section-{self._toc_chapter_number or 'guide'}-{self._toc_section_number}",
            )

        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(title, key, level=level, closed=False)
        self.notify("TOCEntry", (level, title, self.page - 1, key))


def draw_page(canvas, doc):
    width, height = A4
    if doc.page == 1:
        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#F8FAF9"))
        canvas.rect(0, 0, width, height, stroke=0, fill=1)
        canvas.setFillColor(TEAL)
        canvas.rect(0, 0, 5 * mm, height, stroke=0, fill=1)
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.6)
        canvas.line(20 * mm, 24 * mm, width - 20 * mm, 24 * mm)
        canvas.setFillColor(AMBER)
        canvas.rect(width - 31 * mm, height - 22 * mm, 13 * mm, 2 * mm, stroke=0, fill=1)
        canvas.restoreState()
        return

    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(20 * mm, height - 12 * mm, width - 20 * mm, height - 12 * mm)
    canvas.setFont("Portfolio", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, height - 9 * mm, "엔터프라이즈 클라우드 플랫폼 엔지니어링 포트폴리오")
    canvas.drawRightString(width - 20 * mm, 9 * mm, f"{doc.page - 1:02d}")
    canvas.setFillColor(TEAL)
    canvas.rect(20 * mm, 8.3 * mm, 13 * mm, 1.2 * mm, stroke=0, fill=1)
    canvas.restoreState()


class ArchitectureDiagram(Flowable):
    def __init__(self, width=480, height=310):
        super().__init__()
        self.width = width
        self.height = height

    def draw_box(self, canvas, x, y, w, h, title, subtitle, fill, stroke=LINE):
        canvas.setFillColor(fill)
        canvas.setStrokeColor(stroke)
        canvas.roundRect(x, y, w, h, 5, stroke=1, fill=1)
        canvas.setFillColor(INK)
        canvas.setFont("Portfolio-Bold", 8.2)
        canvas.drawCentredString(x + w / 2, y + h - 13, title)
        canvas.setFillColor(MUTED)
        canvas.setFont("Portfolio", 6.6)
        subtitle_lines = subtitle.splitlines()
        if len(subtitle_lines) == 1:
            canvas.drawCentredString(x + w / 2, y + 9, subtitle_lines[0])
        else:
            for index, line in enumerate(subtitle_lines[:2]):
                canvas.drawCentredString(x + w / 2, y + 17 - (index * 9), line)

    def draw_arrow(self, canvas, x1, y1, x2, y2, color=TEAL):
        canvas.setStrokeColor(color)
        canvas.setFillColor(color)
        canvas.setLineWidth(1.2)
        canvas.line(x1, y1, x2, y2)
        canvas.line(x2, y2, x2 - 5, y2 + 3)
        canvas.line(x2, y2, x2 - 5, y2 - 3)

    def draw(self):
        c = self.canv
        self.draw_box(c, 35, 270, 410, 30, "AWS ORGANIZATIONS", "SCP + Tag Policy + Policy-Staging OU", colors.HexColor("#DCECEF"), TEAL)
        ous = [
            (35, "Security", "Audit / Log Archive"),
            (140, "Infrastructure", "Network / CI-CD"),
            (245, "Workloads", "Dev / Stg / Prod"),
            (350, "Sandbox", "Budget / Auto-stop"),
        ]
        for x, title, subtitle in ous:
            self.draw_box(c, x, 220, 95, 34, title, subtitle, WHITE)
            self.draw_arrow(c, x + 47, 270, x + 47, 255)

        self.draw_box(c, 35, 150, 125, 48, "CENTRAL SECURITY", "GuardDuty / Security Hub\nWAF / future firewall", colors.HexColor("#FBECEC"), RED)
        self.draw_box(c, 178, 150, 125, 48, "SHARED NETWORK", "TGW / DNS / endpoints\ninspection path", colors.HexColor("#FFF2DD"), AMBER)
        self.draw_box(c, 321, 150, 125, 48, "OBSERVABILITY", "CloudWatch / Flow Logs\nSNS / Cost alerts", colors.HexColor("#E8F1FB"), BLUE)

        self.draw_box(c, 35, 75, 125, 52, "DEV", "2 AZ / Spot EKS\ndry-run scheduler", LIGHT)
        self.draw_box(c, 178, 75, 125, 52, "STG", "2 AZ / single NAT\npromotion validation", LIGHT)
        self.draw_box(c, 321, 75, 125, 52, "PROD", "3 AZ / NAT per AZ\nVault Lock / HA", LIGHT)
        for x in (97, 240, 383):
            self.draw_arrow(c, x, 150, x, 128, BLUE)

        c.setFillColor(INK)
        c.setFont("Portfolio-Bold", 7.5)
        c.drawString(35, 48, "WORKLOAD VPC")
        c.setFont("Portfolio", 6.8)
        c.setFillColor(MUTED)
        c.drawString(105, 48, "public ingress -> private app/EKS -> isolated private DB")
        c.setStrokeColor(LINE)
        c.line(35, 40, 445, 40)
        c.setFillColor(MUTED)
        c.drawString(35, 25, "S3 gateway endpoint | interface endpoints | VPC Flow Logs | KMS encryption")


class HorizontalFlow(Flowable):
    def __init__(self, steps, colors_list=None, width=480, height=82):
        super().__init__()
        self.steps = steps
        self.colors_list = colors_list or [LIGHT] * len(steps)
        self.width = width
        self.height = height

    def draw(self):
        c = self.canv
        gap = 13
        box_w = (self.width - gap * (len(self.steps) - 1)) / len(self.steps)
        y = 20
        for index, step in enumerate(self.steps):
            x = index * (box_w + gap)
            c.setFillColor(self.colors_list[index])
            c.setStrokeColor(LINE)
            c.roundRect(x, y, box_w, 46, 5, stroke=1, fill=1)
            c.setFillColor(INK)
            c.setFont("Portfolio-Bold", 7.5)
            lines = step.split("\n")
            c.drawCentredString(x + box_w / 2, y + 29, lines[0])
            if len(lines) > 1:
                c.setFillColor(MUTED)
                c.setFont("Portfolio", 6.2)
                c.drawCentredString(x + box_w / 2, y + 14, lines[1])
            if index < len(self.steps) - 1:
                ax = x + box_w
                c.setStrokeColor(TEAL)
                c.setLineWidth(1.2)
                c.line(ax + 2, y + 23, ax + gap - 2, y + 23)
                c.line(ax + gap - 2, y + 23, ax + gap - 6, y + 26)
                c.line(ax + gap - 2, y + 23, ax + gap - 6, y + 20)


def styles():
    base = getSampleStyleSheet()
    return {
        "cover_eyebrow": ParagraphStyle(
            "cover_eyebrow", fontName="Portfolio-Bold", fontSize=9, textColor=TEAL, leading=13, spaceAfter=10
        ),
        "cover_title": ParagraphStyle(
            "cover_title", fontName="Portfolio-Bold", fontSize=30, textColor=INK, leading=38, spaceAfter=17
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle", fontName="Portfolio", fontSize=11.5, textColor=MUTED, leading=19, spaceAfter=17, wordWrap="CJK"
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta", fontName="Portfolio", fontSize=8.5, textColor=MUTED, leading=14, wordWrap="CJK"
        ),
        "cover_label": ParagraphStyle(
            "cover_label", fontName="Portfolio-Bold", fontSize=7.5, textColor=TEAL, leading=11, spaceAfter=4
        ),
        "cover_statement": ParagraphStyle(
            "cover_statement", fontName="Portfolio-Bold", fontSize=12, textColor=INK, leading=19,
            leftIndent=13, borderColor=TEAL, borderWidth=0, borderPadding=0, wordWrap="CJK"
        ),
        "cover_footer": ParagraphStyle(
            "cover_footer", fontName="Portfolio", fontSize=8, textColor=MUTED, leading=13, wordWrap="CJK"
        ),
        "h1": ParagraphStyle(
            "h1", fontName="Portfolio-Bold", fontSize=22, textColor=INK, leading=30, spaceAfter=14
        ),
        "chapter": ParagraphStyle(
            "chapter", fontName="Portfolio-Bold", fontSize=22, textColor=INK, leading=31,
            spaceBefore=7, spaceAfter=12, keepWithNext=True, wordWrap="CJK"
        ),
        "section": ParagraphStyle(
            "section", fontName="Portfolio-Bold", fontSize=14, textColor=TEAL, leading=21,
            spaceBefore=17, spaceAfter=8, keepWithNext=True, wordWrap="CJK"
        ),
        "subsection": ParagraphStyle(
            "subsection", fontName="Portfolio-Bold", fontSize=11, textColor=INK, leading=17,
            spaceBefore=10, spaceAfter=5, keepWithNext=True, wordWrap="CJK"
        ),
        "h2": ParagraphStyle(
            "h2", fontName="Portfolio-Bold", fontSize=12, textColor=TEAL, leading=17, spaceBefore=7, spaceAfter=6
        ),
        "body": ParagraphStyle(
            "body", fontName="Portfolio", fontSize=10.2, textColor=INK, leading=17,
            spaceAfter=10, wordWrap="CJK", allowWidows=0, allowOrphans=0
        ),
        "small": ParagraphStyle(
            "small", fontName="Portfolio", fontSize=8.2, textColor=MUTED, leading=13
        ),
        "callout": ParagraphStyle(
            "callout", fontName="Portfolio", fontSize=9.8, textColor=INK, leading=16.5,
            leftIndent=11, rightIndent=11, borderColor=TEAL, borderWidth=0, borderPadding=11,
            backColor=colors.HexColor("#EAF5F6"), spaceBefore=5, spaceAfter=12, wordWrap="CJK"
        ),
        "question": ParagraphStyle(
            "question", fontName="Portfolio", fontSize=9.8, textColor=INK, leading=16.5,
            leftIndent=11, rightIndent=11, borderColor=AMBER, borderWidth=0, borderPadding=11,
            backColor=colors.HexColor("#FFF5E5"), spaceAfter=15, keepWithNext=False, wordWrap="CJK"
        ),
        "caption": ParagraphStyle(
            "caption", fontName="Portfolio", fontSize=8, textColor=MUTED, leading=12,
            spaceBefore=4, spaceAfter=10, wordWrap="CJK"
        ),
        "bullet": ParagraphStyle(
            "bullet", fontName="Portfolio", fontSize=9.6, textColor=INK, leading=15.5,
            leftIndent=15, firstLineIndent=-8, bulletIndent=0, spaceAfter=5, wordWrap="CJK"
        ),
        "code": ParagraphStyle(
            "code", fontName="Courier", fontSize=7.4, leading=10.5, textColor=INK,
            backColor=colors.HexColor("#F3F6F8"), borderColor=LINE, borderWidth=0.5,
            borderPadding=9, spaceAfter=10
        ),
    }


def section_title(story, style_map, number, title, lead):
    story.append(Paragraph(f"{number:02d} / {title}", style_map["h1"]))
    story.append(Paragraph(lead, style_map["body"]))
    story.append(Spacer(1, 3 * mm))


def bullet(story, style_map, text, color=TEAL):
    story.append(Paragraph(text, style_map["bullet"], bulletText="-"))


def make_table(data, col_widths, header=True, font_size=7.2):
    """Render structured data as readable text blocks instead of a dense grid."""
    row_style = ParagraphStyle(
        "narrative-row",
        fontName="Portfolio",
        fontSize=max(9.2, font_size + 1.8),
        leading=max(15, font_size + 8),
        textColor=INK,
        wordWrap="CJK",
    )
    headers = [str(value) for value in data[0]] if header else []
    source_rows = data[1:] if header else data
    wrapped = []

    for row in source_rows:
        values = [escape(str(value)) for value in row]
        if header and values:
            details = []
            for index, value in enumerate(values[1:], start=1):
                label = escape(headers[index]) if index < len(headers) else "설명"
                details.append(f'<font color="#087E8B"><b>{label}</b></font>&nbsp;&nbsp;{value}')
            body = "<br/>".join(details)
            content = f'<font size="10.5"><b>{values[0]}</b></font>'
            if body:
                content += f"<br/>{body}"
        else:
            content = "<br/>".join(values)
        wrapped.append([Paragraph(content, row_style)])

    table = Table(wrapped, colWidths=[sum(col_widths)], hAlign="LEFT", splitByRow=1)
    table_style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE),
    ]
    for row_index in range(len(wrapped)):
        if row_index % 2 == 1:
            table_style.append(("BACKGROUND", (0, row_index), (0, row_index), colors.HexColor("#F8FAFB")))
    table.setStyle(TableStyle(table_style))
    return table


def metric_cards(metrics):
    cells = []
    for value, label, color in metrics:
        cells.append(Paragraph(
            f'<font size="18" color="{color.hexval()}"><b>{value}</b></font><br/><font size="7" color="#52606D">{label}</font>',
            ParagraphStyle("metric", fontName="Portfolio", alignment=TA_CENTER, leading=18),
        ))
    table = Table([cells], colWidths=[120] * len(cells), rowHeights=[58])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return table


def build_story(style_map):
    story = []

    story.extend([
        Spacer(1, 42 * mm),
        Paragraph("CLOUD PLATFORM ENGINEERING / 2026", style_map["cover_eyebrow"]),
        Paragraph("Enterprise Cloud Platform<br/>Engineering Portfolio", style_map["cover_title"]),
        Paragraph("AWS Landing Zone와 EKS Day-2 운영을 코드, 검증, runbook으로 연결한 사례<br/>Terraform, Security, Observability, FinOps<br/>Human-led AI Agent Operations with explicit production boundaries", style_map["cover_subtitle"]),
        Spacer(1, 17 * mm),
        Paragraph("10 AGENT PROFILES&nbsp;&nbsp;|&nbsp;&nbsp;15 MODULES&nbsp;&nbsp;|&nbsp;&nbsp;10 TF TARGETS&nbsp;&nbsp;|&nbsp;&nbsp;24 AGENT TESTS", style_map["cover_meta"]),
        Spacer(1, 34 * mm),
        Paragraph("Scope: AWS / Terraform / Kubernetes / Security / Observability / Cost Governance", style_map["cover_meta"]),
        Paragraph("Baseline date: 2026-08-08", style_map["cover_meta"]),
        PageBreak(),
    ])

    section_title(story, style_map, 1, "Executive Summary", "설계도만 제시하는 포트폴리오가 아니라 platform boundary, Terraform implementation, EKS Day-2, 운영 통제와 검증 evidence를 하나의 lifecycle로 연결했습니다.")
    story.append(metric_cards([
        ("3", "ENVIRONMENTS", TEAL),
        ("15", "TF MODULES", BLUE),
        ("10/10", "TF TARGETS", GREEN),
        ("24/24", "AGENT TESTS", AMBER),
    ]))
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph("What this portfolio demonstrates", style_map["h2"]))
    story.append(make_table([
        ["Theme", "Engineering decision", "Evidence"],
        ["Platform product", "State split by lifecycle and blast radius", "15 modules; 3 envs; 10 TF targets"],
        ["EKS Day-2", "Logs, QoS, capacity, upgrade, recovery gates", "Current/Target matrix + runbooks"],
        ["Enterprise controls", "SCP/IAM/KMS/network + owner/approval", "HCL + policy + residual-risk review"],
        ["AI Agent adoption", "Human-led templates, read-only MVP, staged delegation", "11 profiles; schemas; 24 tests"],
    ], [88, 257, 135], font_size=6.2))
    story.append(Paragraph("Interview discussion path", style_map["h2"]))
    story.append(make_table([
        ["Audience", "Recommended sections", "Question answered"],
        ["Engineering leader", "Value / Validation / Roadmap", "가치와 현재 증적"],
        ["Cloud/Platform", "Landing Zone / Terraform / EKS", "State와 module 경계"],
        ["SRE/Operations", "EKS Ops / Monitoring / Automation", "장애, capacity, recovery"],
        ["Security/Governance", "Identity / AI / IAM / Review", "권한, 승인, residual risk"],
    ], [105, 235, 140], font_size=6.3))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("검증 경계: repository 코드와 fixture는 증명했지만 AWS account에서 plan/apply, live incident query, restore drill과 business KPI baseline/actual은 아직 production gate입니다. 구현, 정의, target을 구분해 읽어야 합니다.", style_map["callout"]))
    story.append(PageBreak())

    section_title(story, style_map, 2, "Human-Led Multi-Agent Operating Model", "기업이 production 운영을 즉시 Agent에게 위임하기 어렵다는 전제에서 역할별 질의, evidence, 독립 review와 사람 승인을 먼저 표준화했습니다.")
    story.append(HorizontalFlow([
        "Architecture\nrequirements",
        "Governance\nOU / SCP",
        "Terraform\nmodules",
        "Security\nreview",
        "CI-CD\nvalidation",
    ], [colors.HexColor("#E8F1FB"), colors.HexColor("#FFF2DD"), colors.HexColor("#EAF5F6"), colors.HexColor("#FBECEC"), LIGHT]))
    agents = [
        ["Agent", "Primary responsibility", "Output"],
        ["Architecture", "Landing zone, boundaries, ADR", "Target architecture"],
        ["Terraform", "Reusable modules, roots, state", "HCL implementation"],
        ["Governance", "Organizations, SCP, tag policy", "Guardrail catalog"],
        ["Security", "IAM, KMS, network, runtime", "Security baseline"],
        ["Monitoring", "Metrics, logs, alarms, runbook", "Alert architecture"],
        ["Operations", "Backup, schedule, patch, EOS", "Operations policy"],
        ["FinOps", "Budget, anomaly, commitment", "Optimization report"],
        ["CI/CD", "fmt, validate, plan, approval", "Release gate"],
        ["Reviewer", "Risk and regression review", "Findings backlog"],
        ["Documentation", "README and portfolio PDF", "Decision narrative"],
    ]
    story.append(make_table(agents, [82, 235, 163], font_size=6.8))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("현재 가치: 역할별 template과 review 책임으로 판단 편차와 handoff 누락을 줄이는 것. 미래 가치: 증적이 축적된 저위험 use case만 supervised/bounded delegation으로 승격하는 것. Production mutation은 Agent가 직접 수행하지 않습니다.", style_map["callout"]))
    story.append(PageBreak())

    section_title(story, style_map, 3, "Operator Guide", "운영자는 목적에 맞는 Agent와 mode를 선택하고 모든 변경을 ticket, artifact, 사람 승인으로 통제합니다.")
    story.append(HorizontalFlow([
        "Request\nticket + scope",
        "Gateway\nidentity + policy",
        "Agent\nread/draft/plan",
        "Review\nrisk + evidence",
        "CI-CD\nprotected apply",
        "Verify\nmetric + record",
    ], [LIGHT, colors.HexColor("#E8F1FB"), colors.HexColor("#EAF5F6"), colors.HexColor("#FFF2DD"), colors.HexColor("#FBECEC"), LIGHT]))
    story.append(Paragraph("Agent modes", style_map["h2"]))
    story.append(make_table([
        ["Mode", "Allowed", "Prohibited"],
        ["read", "Repository, metric, log, inventory analysis", "File or cloud changes"],
        ["draft", "Code patch, document, runbook proposal", "Merge, deploy, cloud API mutation"],
        ["plan", "fmt, validate, plan, impact and rollback", "Apply, restart, delete, purchase"],
        ["review", "Independent code, plan, policy review", "Self-approval or deployment"],
    ], [70, 245, 165]))
    story.append(Paragraph("Workflow routing", style_map["h2"]))
    story.append(make_table([
        ["Workflow", "Agent sequence"],
        ["Infrastructure", "Architecture/Governance -> Terraform -> Security -> Reviewer -> CI/CD"],
        ["Incident", "Monitoring -> Operations -> Security if needed -> permanent fix"],
        ["CVE/EOS", "Security -> Operations -> Terraform/CI-CD -> Reviewer"],
        ["Backup restore", "Operations -> Security -> Monitoring -> Reviewer -> human execution"],
        ["FinOps", "FinOps -> Operations -> Terraform -> Reviewer -> FinOps owner"],
    ], [110, 370]))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("`apply`는 Agent mode가 아닙니다. Agent는 자신의 결과를 승인할 수 없으며, production은 ticket, plan hash, 2인 review, rollback owner가 일치하는 protected CI/CD만 실행합니다. 새 session은 이전 대화를 자동으로 기억한다고 가정하지 않고 PR, ticket, handoff artifact를 source of truth로 사용합니다.", style_map["callout"]))
    story.append(PageBreak())

    section_title(story, style_map, 4, "Agent Value: Business Outcomes", "Agent 활동량이 아니라 engineering behavior, service outcome, business value와 검증 evidence의 연결로 투자 효과를 평가합니다.")
    story.append(HorizontalFlow([
        "Agent capability\nread + draft",
        "Engineering\ntime + quality",
        "Service outcome\nreliability + delivery",
        "Business value\ncontinuity + cost",
        "Evidence\nowner validation",
    ], [LIGHT, colors.HexColor("#E8F1FB"), colors.HexColor("#EAF5F6"), colors.HexColor("#FFF2DD"), colors.HexColor("#FBECEC")]))
    story.append(Paragraph("Business outcome map", style_map["h2"]))
    story.append(make_table([
        ["Outcome", "Engineering driver", "Business KPI", "Claim boundary"],
        ["Service continuity", "Evidence/recovery speed, restore drill", "Impact minutes, SLO breach", "Finance-approved impact model"],
        ["Delivery speed", "Change lead time and quality", "Release wait, environment time", "Failure rate must not worsen"],
        ["Cost efficiency", "Toil removal, normalized rightsizing", "Capacity returned, realized saving", "Recommendation is not saving"],
        ["Risk reduction", "Policy/evidence review, exception expiry", "Critical risk, audit lead time", "Finding is not remediation"],
        ["Organization scale", "Template, runbook, common handoff", "Coverage, onboarding, engineer scope", "Quality guardrails required"],
    ], [86, 145, 125, 124], font_size=6.1))
    story.append(Paragraph("Value claim status", style_map["h2"]))
    story.append(make_table([
        ["Status", "Evidence state", "Allowed portfolio wording"],
        ["Defined", "KPI, owner, calculation", "Measurement criteria defined"],
        ["Instrumented", "Source/event connected", "Measurable path implemented"],
        ["Measured", "Baseline and actual sample", "Observed within disclosed scope"],
        ["Validated", "Domain/business owner approved", "Verified improvement with guardrail"],
        ["Realized", "Repeated operational/financial result", "Realized outcome"],
    ], [75, 170, 235], font_size=6.4))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("현재 Human-led 모델과 KPI는 정의되었고 Monitoring fixture report 경로는 구현되었습니다. 그러나 live baseline/actual과 business owner 검증이 없으므로 MTTR 개선, 절감액 또는 인력 효과를 실적으로 주장하지 않습니다.", style_map["callout"]))
    story.append(PageBreak())

    section_title(story, style_map, 5, "Agent Value: Engineering Outcomes", "Incident, change, reliability, security, cost와 Agent safety를 동일 evidence chain에서 측정하고 속도와 품질 guardrail을 함께 봅니다.")
    story.append(make_table([
        ["Domain", "Primary KPI", "Evidence", "Required guardrail"],
        ["Incident", "Evidence duration, MTTR, coverage", "Report/query/ticket timeline", "Partial and simulation excluded"],
        ["Change", "Lead time, failure, rollback", "PR, plan hash, CI, deployment", "Unexpected destroy blocked"],
        ["Reliability/EKS", "SLO, OOM/eviction, Pending, restore", "Metric/log/K8s/drill", "QoS or backup object is not proof"],
        ["Security/Gov", "Finding age, exception, policy test", "Finding/simulation/approval", "Disposition and expiry required"],
        ["FinOps", "Allocation, unit cost, realized saving", "CUR/invoice + service KPI", "Traffic and price normalized"],
        ["Knowledge", "Runbook coverage, onboarding", "Inventory and ticket usage", "Document existence is not use"],
        ["Agent safety", "Human correction, deny, scope attempt", "Gateway/tool/review audit", "Unsafe event target is zero"],
    ], [82, 140, 133, 125], font_size=5.9))
    story.append(Paragraph("Measurement and reporting", style_map["h2"]))
    story.append(HorizontalFlow([
        "Baseline\nsame definition",
        "Agent event\nrequest + trace",
        "Human review\ndisposition",
        "Outcome\npost-check",
        "Validation\nowner + evidence",
    ], [LIGHT, colors.HexColor("#E8F1FB"), colors.HexColor("#FFF2DD"), colors.HexColor("#EAF5F6"), colors.HexColor("#FBECEC")]))
    story.append(make_table([
        ["Cadence", "Decision focus", "Output"],
        ["Per request", "Facts, risk, approval, immediate result", "report.json/md + audit"],
        ["Weekly", "Change/EKS health, repeated gap", "Engineering review"],
        ["Monthly", "KPI, FinOps, human correction, safety", "Agent value scorecard"],
        ["Quarterly", "Business outcome, investment, maturity", "Validated decision record"],
    ], [75, 245, 160], font_size=6.4))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("request_id와 trace_id가 ticket, PR/plan, approval, action, post-check, CUR/invoice까지 연결되어야 합니다. 속도 개선은 change failure, policy violation, evidence coverage와 human correction rate가 악화되지 않을 때만 성과로 인정합니다.", style_map["callout"]))
    story.append(PageBreak())

    section_title(story, style_map, 6, "Workforce Identity and AWS Access", "장기 IAM access key 없이 Corporate IdP, IAM Identity Center, group-based permission set으로 account 접근을 통제합니다.")
    story.append(HorizontalFlow([
        "Corporate IdP\nMFA + device",
        "Identity Center\nSAML + SCIM",
        "IdP Group\nteam entitlement",
        "Permission Set\nshort session",
        "AWS Account\ndev/stg/prod",
    ], [colors.HexColor("#E8F1FB"), colors.HexColor("#EAF5F6"), LIGHT, colors.HexColor("#FFF2DD"), colors.HexColor("#FBECEC")]))
    story.append(Paragraph("Access model", style_map["h2"]))
    story.append(make_table([
        ["Corporate group", "Account scope", "Permission", "Approval"],
        ["AWS-Developers", "Dev accounts", "Developer", "Manager / owner"],
        ["AWS-Platform-ReadOnly", "Shared + all workloads", "ReadOnly", "Platform owner"],
        ["AWS-Stg-Operators", "Selected stg", "StagingOperator", "Ticket"],
        ["AWS-Prod-Operators", "Selected prod", "ProductionOperator / 1h", "Ticket + JIT"],
        ["AWS-Security-Audit", "Organization scope", "SecurityAudit", "Security owner"],
    ], [125, 115, 145, 95], font_size=6.8))
    story.append(Paragraph("Control decisions", style_map["h2"]))
    for item in [
        "Corporate IdP is the source of truth; SCIM provisions users and groups, while Terraform manages permission sets and account assignments.",
        "Production defaults to read-only; elevated access uses ticketed, time-bounded JIT group membership and MFA.",
        "Closed networks use approved PAW/VDI, VPN or Direct Connect, and Console Private Access where applicable.",
        "Break-glass requires hardware MFA, dual approval, CloudTrail alerting, post-use credential rotation and review.",
    ]:
        bullet(story, style_map, item)
    story.append(PageBreak())

    section_title(story, style_map, 7, "Private AI Platform and Agent Runtime", "모델과 tool 사용을 중앙 AI Gateway에서 인증, 정책, 비용, data protection 기준으로 통제합니다.")
    story.append(HorizontalFlow([
        "User / Workload\nSSO or identity",
        "Private Gateway\npolicy + quota",
        "Model Router\napproved alias",
        "Agent Runtime\npinned profile",
        "Tool Broker\nscoped credential",
    ], [LIGHT, colors.HexColor("#E8F1FB"), colors.HexColor("#FFF2DD"), colors.HexColor("#EAF5F6"), colors.HexColor("#FBECEC")]))
    story.append(Paragraph("Platform controls", style_map["h2"]))
    story.append(make_table([
        ["Component", "Responsibility", "Key control"],
        ["AI Gateway", "Identity, model routing, request policy", "Model/tool allowlist, data class, quota"],
        ["Agent Runtime", "Role-specific prompt and workflow", "Pinned profile, no prod mutation"],
        ["Tool Broker", "Repository, query, scanner, CI tools", "Schema validation, short-lived credential"],
        ["Usage pipeline", "Token, latency, status, estimated cost", "request_id/trace_id, CUR reconciliation"],
        ["Security telemetry", "Denied model, PII/secret, privileged tool", "Central audit and restricted investigation"],
    ], [100, 205, 175]))
    story.append(Paragraph("Data and cost policy", style_map["h2"]))
    for item in [
        "Raw prompt and response logging is disabled by default; troubleshooting samples require redaction, approval, encryption and short retention.",
        "Bedrock uses interface VPC endpoints; external providers use centralized inspected egress with approved data residency.",
        "User, team, application and Agent enforce token, concurrency and monthly USD quotas with 50/80/100 percent alerts.",
        "Provider usage is normalized and reconciled daily with CUR or invoice data; no automatic fallback to an unapproved provider.",
    ]:
        bullet(story, style_map, item)
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("현재 repository에는 AI Gateway runtime 자체가 구현되어 있지 않습니다. 이 페이지는 Terraform module과 platform product로 확장할 target operating model이며, 실제 command channel이 도입되기 전에도 동일한 approval contract를 적용합니다.", style_map["callout"]))
    story.append(PageBreak())

    section_title(story, style_map, 8, "AWS Landing Zone Architecture", "계정, 네트워크, 보안, workload를 분리하고 정책 상속과 중앙 관측성을 조직 경계에 배치합니다.")
    story.append(ArchitectureDiagram())
    story.append(Spacer(1, 2 * mm))
    story.append(make_table([
        ["Account / OU", "Responsibility", "Control"],
        ["Security", "Audit, log archive, findings", "Delegated admin, immutable retention"],
        ["Infrastructure", "Network, DNS, CI/CD", "TGW route ownership, shared endpoints"],
        ["Workloads", "Dev, Stg, Prod applications", "Inherited SCP, environment budget"],
        ["Sandbox", "Experiment and learning", "Strict budget, night/weekend stop"],
    ], [100, 210, 170]))
    story.append(PageBreak())

    section_title(story, style_map, 9, "Terraform Architecture", "root module은 조립만 담당하고 실제 resource logic은 재사용 module에 둡니다.")
    tree = """terraform/
|-- organization/                    # OU, SCP, Tag Policy state
|-- environments/
|   `-- dev|stg|prod/                # AWS foundation state
|       |-- platform/                # Helm/Kubernetes state
|       `-- network-policy/          # optional separate lifecycle
`-- modules/
    |-- workload-environment         # composition
    |-- network | security-group | route-policy
    |-- security | iam
    |-- observability | operations | cost
    `-- eks | kubernetes-platform | waf"""
    story.append(Preformatted(tree, style_map["code"])); story.append(Spacer(1, 3 * mm))
    story.append(HorizontalFlow([
        "Organization\ncoarse guardrails",
        "Foundation\nAWS resources",
        "Policy\nSG rules + routes",
        "Platform\nHelm + K8s",
    ], [colors.HexColor("#FFF2DD"), colors.HexColor("#E8F1FB"), colors.HexColor("#EAF5F6"), LIGHT]))
    story.append(Paragraph("State boundary", style_map["h2"]))
    story.append(make_table([
        ["State", "Contents", "Why separated"],
        ["organization", "OU, SCP, Tag Policy", "Organization-wide blast radius"],
        ["foundation", "VPC, KMS, IAM, EKS, backup, cost", "AWS API and account lifecycle"],
        ["network/service policy", "Standalone SG rules and additional routes", "Only if owner, permission or lifecycle differs"],
        ["platform", "Istio, Prometheus, Grafana, policy", "Requires a reachable, ready Kubernetes API"],
    ], [105, 215, 160], font_size=6.7))
    story.append(PageBreak())

    section_title(story, style_map, 10, "Organizations, SCP and IAM", "SCP는 권한을 부여하지 않는 maximum-permission guardrail이며, identity policy와 함께 평가합니다.")
    story.append(make_table([
        ["Guardrail", "Scope", "Implementation note"],
        ["DenyLeaveOrganization", "Security, Infrastructure, Workloads, Sandbox", "Member account escape prevention"],
        ["DenyDisableAuditServices", "Workloads", "CloudTrail, Config, GuardDuty, Security Hub, Flow Logs, KMS"],
        ["DenyUnapprovedRegions", "Workloads", "Global-service NotAction exceptions"],
        ["DenyDeletePublicAccessControls", "Workloads", "Security automation role exception"],
        ["EnterpriseTagPolicy", "Workloads, Sandbox", "Environment and ManagedBy value standard"],
    ], [120, 120, 240]))
    story.append(Paragraph("IAM trust decisions", style_map["h2"]))
    for item in [
        "GitHub OIDC requires explicit aud and repository/environment sub claims; an empty subject allowlist fails precondition.",
        "Deployment policy ARNs are environment inputs; the module grants no implicit administrator permission.",
        "Audit role combines ReadOnlyAccess and SecurityAudit. Break-glass is optional, MFA-enforced, one-hour maximum.",
        "SCP rollout starts in Policy-Staging OU, then moves accounts in small batches after service-last-accessed review.",
    ]:
        bullet(story, style_map, item)
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("Tag Policy는 key/value 표준을 검사하지만 필수 태그 누락을 완전히 차단하지 않습니다. CI policy와 AWS Config required-tags rule을 함께 사용해야 합니다.", style_map["callout"]))
    story.append(PageBreak())

    section_title(story, style_map, 11, "Network and Security Baseline", "public ingress, private application, private database tier를 AZ 단위로 분리하고 outbound와 audit path를 명시합니다.")
    story.append(make_table([
        ["Layer", "Dev", "Stg", "Prod"],
        ["Availability Zones", "2", "2", "3"],
        ["NAT", "Disabled", "Single", "Per AZ"],
        ["DB default internet route", "None", "None", "None"],
        ["Private endpoints", "S3 gateway", "ECR/Logs/SSM", "ECR/EC2/Logs/SSM/STS"],
        ["Flow Logs retention", "90 days", "90 days", "365 days"],
        ["Schedule", "Office hours / dry-run", "Office hours / dry-run", "Always on"],
    ], [135, 110, 110, 125]))
    story.append(Paragraph("Security controls", style_map["h2"]))
    for item in [
        "Account S3 public access block, rotating customer-managed KMS key, EBS encryption by default.",
        "GuardDuty with S3, EKS audit, and EBS malware protection; Security Hub and Inspector v2.",
        "WAF baseline with rate limit, Common, Known Bad Inputs, IP Reputation, SQLi managed rules and request logging.",
        "VPC Flow Logs one-minute aggregation and rejected-flow alarm; DB route table has no NAT default route.",
    ]:
        bullet(story, style_map, item)
    story.append(Paragraph("Central inspection VPC, Transit Gateway appliance mode, AWS Network Firewall/UTM routing은 Network account ID와 traffic matrix가 확정된 후 별도 state로 구현합니다.", style_map["callout"]))
    story.append(PageBreak())

    section_title(story, style_map, 12, "EKS Foundation", "control plane, worker node, add-on 권한을 분리하고 cluster creator의 영구 관리자 권한을 제거했습니다.")
    story.append(HorizontalFlow([
        "Private API\nAccess Entry",
        "Control plane\nKMS + 5 logs",
        "AL2023 nodes\nIMDSv2 + gp3",
        "Managed add-ons\ncompatible version",
        "Pod Identity\nCNI + EBS CSI",
    ], [colors.HexColor("#E8F1FB"), colors.HexColor("#EAF5F6"), LIGHT, colors.HexColor("#FFF2DD"), colors.HexColor("#FBECEC")]))
    story.append(Paragraph("Node group policy", style_map["h2"]))
    story.append(make_table([
        ["Decision", "Implementation"],
        ["Operating system", "AL2023_x86_64_STANDARD; EKS 1.32 was last AL2 AMI version"],
        ["Metadata security", "IMDSv2 required, metadata tags disabled"],
        ["Volume", "Encrypted gp3 with KMS, daily backup tag"],
        ["Scaling", "desired_size drift ignored; autoscaler controller is planned"],
        ["Upgrade", "max unavailable dev 50%, stg/prod 25%; dev -> stg -> prod"],
        ["Add-ons", "CNI, CoreDNS, kube-proxy, Pod Identity, EBS CSI, CloudWatch"],
        ["Log retention", "Control 90/90/365d; Container Insights 30/90/365d"],
    ], [125, 355]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Private endpoint를 사용하므로 Terraform platform stage와 kubectl 운영은 VPN, Direct Connect, SSM-connected runner 또는 VPC 내부 self-hosted runner에서 수행합니다.", style_map["callout"]))
    story.append(PageBreak())

    section_title(story, style_map, 13, "EKS Logging and Retention", "control plane, node/runtime, workload log를 분리 수집하고 hot search와 장기 감사 archive의 lifecycle을 명시합니다.")
    story.append(HorizontalFlow([
        "Sources\ncontrol + node + app",
        "Collect\nFluent Bit + CW",
        "Protect\nmask + encrypt",
        "Hot search\nLogs Insights",
        "Archive\nS3 + Athena",
    ], [LIGHT, colors.HexColor("#E8F1FB"), colors.HexColor("#FBECEC"), colors.HexColor("#FFF2DD"), colors.HexColor("#EAF5F6")]))
    story.append(make_table([
        ["Plane", "Current", "Target", "Key control"],
        ["Control plane", "5 logs + KMS; 90/90/365d", "central archive by source/class", "RBAC/change investigation"],
        ["Node/runtime", "CW add-on/Fluent Bit; 30/90/365d", "coverage/drop/archive evidence", "kubelet, containerd, OOM/pressure"],
        ["Application", "App log group + Istio stdout", "JSON/PII filter/reconciliation", "request/trace/release correlation"],
        ["Metrics", "Prometheus 7/15/30d", "recording rules/managed backend", "Not log retention"],
    ], [82, 135, 145, 118], font_size=6.2))
    story.append(Paragraph("Pipeline release gate", style_map["h2"]))
    for item in [
        "Secret, token, cookie, phone number and message body are removed before ingestion; raw Kubernetes Secret values are never logged.",
        "CloudWatch is the hot alert/search tier; subscription or Firehose sends required audit data to the Log Archive account S3 lifecycle.",
        "Dropped/retried records, ingestion bytes, query scan bytes and high-cardinality fields are monitored as reliability and FinOps signals.",
        "IaC resources are implemented; runtime coverage, masking, dropped-record and archive search evidence remain production gates.",
    ]:
        bullet(story, style_map, item)
    story.append(PageBreak())

    section_title(story, style_map, 14, "EKS QoS, Scaling and Recovery", "Current는 namespace quota/LimitRange와 3개 PriorityClass이며, PDB/HPA/topology/autoscaler는 workload별 Target gate입니다.")
    story.append(make_table([
        ["Workload", "QoS / priority", "Mandatory controls"],
        ["Cluster critical", "Guaranteed / platform-critical", "request=limit for all containers, >=2 replicas, PDB, AZ spread"],
        ["Business critical", "Guaranteed or Burstable / high", "requests, memory limit, HPA, probes, PDB, topology"],
        ["Standard service", "Burstable / default", "LimitRange, ResourceQuota, sizing evidence"],
        ["Batch / CI", "Burstable / low non-preempting", "quota, concurrency, retry, Spot tolerance"],
        ["Diagnostic", "BestEffort by exception", "No permanent prod use, owner and time limit"],
    ], [92, 145, 243], font_size=6.4))
    story.append(Paragraph("Capacity ownership", style_map["h2"]))
    story.append(HorizontalFlow([
        "Requests\nscheduler truth",
        "HPA / KEDA\npod replicas",
        "VPA audit\nright sizing",
        "CA / Karpenter\nnode capacity",
        "SLO + quota\nsafety boundary",
    ], [LIGHT, colors.HexColor("#E8F1FB"), colors.HexColor("#FFF2DD"), colors.HexColor("#EAF5F6"), colors.HexColor("#FBECEC")]))
    story.append(Paragraph("Backup and change evidence", style_map["h2"]))
    for item in [
        "Git/Terraform/Helm and image digest are desired state; EKS backup protects supported cluster state and persistent volumes, not every external dependency.",
        "Monthly namespace restore and quarterly cluster rebuild/restore prove object order, storage/AZ, identity, secrets, checksum, synthetic transaction and measured RPO/RTO.",
        "Upgrade gate checks deprecated APIs, add-on compatibility, PDB/topology, IP/node headroom and service SLI before one-minor control-plane and node promotion.",
    ]:
        bullet(story, style_map, item)
    story.append(Paragraph("QoS는 node-pressure eviction에 영향을 주지만 PriorityClass와 PodDisruptionBudget (PDB)를 대체하지 않습니다. PDB는 voluntary disruption을 제한할 뿐 node/AZ 장애를 막지 않으므로 replica와 topology 분산이 함께 필요합니다.", style_map["callout"]))
    story.append(PageBreak())

    section_title(story, style_map, 15, "Helm, Istio and Observability", "클러스터 준비 이후 별도 state에서 atomic Helm release와 revision-based mesh lifecycle을 관리합니다.")
    story.append(HorizontalFlow([
        "Install base\nIstio CRDs",
        "New revision\nistiod 1.30.1",
        "Label namespace\nistio.io/rev",
        "Roll workloads\nverify telemetry",
        "Remove old\ncontrol plane",
    ], [LIGHT, colors.HexColor("#E8F1FB"), colors.HexColor("#FFF2DD"), colors.HexColor("#EAF5F6"), colors.HexColor("#FBECEC")]))
    story.append(Paragraph("Platform components", style_map["h2"]))
    story.append(make_table([
        ["Component", "Management", "Operational rule"],
        ["Istio base / istiod", "Pinned Helm chart + revision", "Control plane canary, data plane rolling restart"],
        ["Ingress gateway", "Separate Helm release", "WAF/ALB attachment after traffic validation"],
        ["PeerAuthentication", "Terraform Kubernetes manifest", "Strict mTLS per enrolled namespace"],
        ["Namespace policy", "Terraform Kubernetes resources", "Quota, LimitRange, PriorityClass catalog"],
        ["Prometheus", "kube-prometheus-stack", "7/15/30-day environment retention"],
        ["Alertmanager", "kube-prometheus-stack", "Enabled; receiver and route are planned"],
        ["Grafana", "Persistent volume", "Bootstrap secret must move to external secret store"],
    ], [105, 170, 205]))
    story.append(Paragraph("Chart version은 Git에 고정하고 dev 검증 결과를 stg와 prod로 승격합니다. Istio patch는 지원 minor 내 최신 security patch를 우선하며, revision 전환 전 deprecated API와 PDB를 검사합니다.", style_map["callout"]))
    story.append(PageBreak())

    section_title(story, style_map, 16, "Monitoring and Alerting", "AWS native telemetry와 Kubernetes metrics를 중앙 alarm topic과 severity routing으로 연결합니다.")
    story.append(HorizontalFlow([
        "Sources\nAWS + EKS + App",
        "Collection\nCW + Prometheus",
        "Detection\nAlarm + Alertmanager",
        "Routing\nSNS / on-call",
        "Response\nRunbook + ticket",
    ], [LIGHT, colors.HexColor("#E8F1FB"), colors.HexColor("#FFF2DD"), colors.HexColor("#FBECEC"), colors.HexColor("#EAF5F6")]))
    story.append(make_table([
        ["Severity", "Examples", "Target"],
        ["Critical", "Service down, DB unavailable, sustained 5xx", "PagerDuty/on-call + Slack + Email"],
        ["Warning", "Latency, rejected flow spike, budget 80%", "Slack + Email"],
        ["Info", "Deployment, forecast budget 50%", "Operations channel"],
    ], [85, 270, 125]))
    story.append(Paragraph("VPC Flow Logs troubleshooting", style_map["h2"]))
    for item in [
        "REJECT: security group, NACL, route table, destination port를 source/destination tuple로 확인합니다.",
        "ACCEPT but timeout: application listener, asymmetric routing, return path, DNS를 확인합니다.",
        "NODATA: interface existence, flow-log status, aggregation delay를 확인합니다.",
        "Cost spike: NAT, cross-AZ, internet egress byte volume을 destination별로 집계합니다.",
    ]:
        bullet(story, style_map, item)
    story.append(PageBreak())

    section_title(story, style_map, 17, "Peak Notification Workload", "예약 발송 시간의 Nginx - application - queue - Kakao API 경로를 traffic, error, latency, saturation으로 관측합니다.")
    story.append(HorizontalFlow([
        "ALB / WAF\nrequest rate",
        "Nginx\nconnection + FD",
        "App / Queue\nlag + retry",
        "Kakao API\n429 + 5xx",
        "Independent on-call\nPagerDuty + Slack",
    ], [LIGHT, colors.HexColor("#E8F1FB"), colors.HexColor("#FFF2DD"), colors.HexColor("#EAF5F6"), colors.HexColor("#FBECEC")]))
    story.append(make_table([
        ["Layer", "Primary signals", "Initial threshold example"],
        ["End-to-end", "Synthetic success, completion rate", "No success for 5m or completion below 99%"],
        ["Nginx quality", "499/502/503/504, p95/p99 latency", "At least 100 requests: 5xx 2% warn, 5% critical"],
        ["Nginx capacity", "Active/capacity, accepted-handled, listen overflow", "70/85% capacity; any sustained drop"],
        ["File descriptor", "Nginx process FD/limit, host FD", "70% for 10m; 85% for 5m"],
        ["TCP / host", "SYN_RECV, TIME_WAIT, retransmit, conntrack", "3x normal peak; drop/error; 70/85% capacity"],
        ["Queue / worker", "Oldest age, publish/consume, retry, DLQ", "Age exceeds delivery SLO or DLQ above 0"],
        ["Kakao API", "Latency, 2xx/429/5xx, rejection, quota", "429/5xx above 2%; quota 70/90%"],
    ], [88, 205, 187], font_size=6.4))
    story.append(Paragraph("Incident checks", style_map["h2"]))
    story.append(Preformatted("""curl -s http://127.0.0.1/nginx_status     # active/reading/writing/waiting
ss -s; ss -tan state syn-recv             # socket summary and backlog symptom
cat /proc/$(cat /run/nginx.pid)/limits    # effective open-file limit
ls /proc/$(cat /run/nginx.pid)/fd | wc -l # current Nginx process FD
journalctl -u nginx --since '15 min ago'  # correlate error timeline""", style_map["code"]))
    story.append(Paragraph("stub_status는 status code와 upstream latency를 제공하지 않으므로 structured access log 또는 log exporter/OpenTelemetry가 필요합니다. 고객용 Kakao 경로는 Critical 운영 알람의 유일한 채널이 될 수 없으며 별도 provider와 network path의 on-call 채널을 병행합니다.", style_map["callout"]))
    story.append(PageBreak())

    section_title(story, style_map, 18, "Operations Automation", "backup, office-hours scheduling, patch, CVE/EOS를 tag와 environment policy로 연결합니다.")
    story.append(make_table([
        ["Control", "Implementation", "Safety"],
        ["Daily backup", "BackupPolicy=daily + Environment tag selection", "KMS vault, retention, prod Vault Lock"],
        ["EC2/RDS schedule", "EventBridge Scheduler -> Lambda", "dev/stg only, dry-run default, prod runtime deny"],
        ["Patch", "Ubuntu/RHEL/AL2023 SSM baseline", "Security patches after approval delay"],
        ["Vulnerability", "Inspector EC2/ECR/Lambda", "Critical 7d, High 14d, Medium 30d"],
        ["EOS/EOL", "Inventory and migration milestone", "6/3/1-month planning gates"],
    ], [100, 210, 170]))
    story.append(Paragraph("Scheduler defense in depth", style_map["h2"]))
    for item in [
        "Terraform precondition blocks scheduler creation in prod.",
        "Lambda runtime rejects Environment=prod even if invoked manually.",
        "Discovery and IAM resource conditions both require Environment and Schedule=office-hours tags.",
        "Dry-run is true by default; intended target list is reviewed in CloudWatch Logs before activation.",
        "EKS node groups are excluded to avoid Terraform/autoscaler ownership conflict.",
    ]:
        bullet(story, style_map, item)
    story.append(Paragraph("Backup 완료만으로 복구 가능성을 증명할 수 없습니다. 월간 stg restore drill과 분기별 RPO/RTO evidence가 production gate입니다.", style_map["callout"]))
    story.append(PageBreak())

    section_title(story, style_map, 19, "FinOps", "비용은 예산 알림뿐 아니라 tagging, schedule, architecture, commitment 순서로 관리합니다.")
    story.append(make_table([
        ["Stage", "Control", "Decision rule"],
        ["Allocation", "Environment, Owner, Service, CostCenter", "Untagged cost is governance debt"],
        ["Detection", "Budget 50/80/100%, service anomaly", "SNS to environment owners"],
        ["Elimination", "Office-hours, idle EBS/EIP/LB review", "Waste removal before commitment"],
        ["Optimization", "Rightsizing, NAT/endpoints, storage retention", "Measure 30-day baseline"],
        ["Commitment", "Compute Savings Plans / Standard RI", "Stable prod baseline only"],
    ], [90, 205, 185]))
    story.append(Paragraph("Environment cost posture", style_map["h2"]))
    story.append(make_table([
        ["Environment", "Monthly budget", "Compute", "Availability"],
        ["Dev", "$300", "Spot, office-hours", "2 AZ, NAT disabled"],
        ["Stg", "$1,000", "On-demand, office-hours", "2 AZ, single NAT"],
        ["Prod", "$5,000", "On-demand baseline", "3 AZ, NAT per AZ"],
    ], [95, 110, 140, 135]))
    story.append(Paragraph("RI/Savings Plans는 dev/stg에 먼저 적용하지 않습니다. 자동 중지와 right sizing 후 30일 이상 안정적인 prod 24x7 baseline만 commitment 후보로 분류합니다.", style_map["callout"]))
    story.append(PageBreak())

    section_title(story, style_map, 20, "Validation and Evidence", "면접에서 재현 가능한 evidence와 아직 검증하지 못한 production gate를 같은 페이지에 공개합니다.")
    story.append(metric_cards([
        ("PASS", "FMT RECURSIVE", GREEN),
        ("10/10", "TF TARGETS", GREEN),
        ("24/24", "AGENT TESTS", GREEN),
        ("22", "PDF PAGES QA", BLUE),
    ]))
    story.append(Spacer(1, 5 * mm))
    story.append(make_table([
        ["Residual risk", "Current boundary", "Production gate"],
        ["Central audit", "Org Trail/Config aggregator deferred", "Security and Log Archive account IDs"],
        ["SCP lockout", "Code only, not attached in AWS", "Policy-Staging and break-glass rehearsal"],
        ["Private EKS", "No public API path", "Private runner/VPN connectivity"],
        ["Grafana secret", "Sensitive Terraform state", "Secrets Manager + External Secrets"],
        ["WAF", "ACL module not attached", "Count observation and false-positive review"],
        ["Runtime proof", "No AWS credentials in build", "Sandbox plan/apply/restore/destroy evidence"],
    ], [100, 190, 190]))
    story.append(Paragraph("Reproducible validation", style_map["h2"]))
    story.append(Preformatted("./scripts/validation/validate-terraform.sh\npython3 -m unittest discover -s agent-runtime/tests -v\npython3 scripts/pdf/verify/verify_portfolio_pdf.py enterprise-cloud-portfolio.pdf", style_map["code"]))
    story.append(Paragraph("Verified now: fmt, 7 deployment roots + 3 standalone modules, scheduler syntax, 24 request/security/read-only Agent tests, PDF text/render QA. Not verified here: account-specific plan/apply, live AWS/EKS queries, restore/failover and realized business outcomes.", style_map["callout"]))
    story.append(PageBreak())

    section_title(story, style_map, 21, "Roadmap and Lessons", "현재 구현은 실무 적용 가능한 baseline이며, account-specific 정보와 runtime evidence가 필요한 항목은 production gate로 남겼습니다.")
    story.append(Paragraph("Next implementation", style_map["h2"]))
    for item in [
        "Sandbox organization에서 plan, apply, restore, destroy evidence 생성",
        "Organization CloudTrail, Config aggregator, immutable central log archive root 구현",
        "AWS Load Balancer Controller, ingress ARN, WAF association, count-to-block promotion",
        "Karpenter/Cluster Autoscaler, namespace NetworkPolicy, Istio AuthorizationPolicy 구현",
        "IAM Identity Center permission set/account assignment와 private AI Gateway module 구현",
        "Ticket/PR/CI/Monitoring/CUR event를 연결한 Agent value scorecard pilot",
        "Trivy/Checkov, OPA policy, cost estimation을 pull request gate에 추가",
    ]:
        bullet(story, style_map, item)
    story.append(Paragraph("Lessons learned", style_map["h2"]))
    story.append(make_table([
        ["Lesson", "Practical implication"],
        ["Module depth is not file count", "Clear ownership, typed input, conservative defaults, useful output matter"],
        ["Kubernetes is a second control plane", "AWS foundation and Helm state need different reachability and rollback"],
        ["Guardrails can cause outages", "SCP and WAF require staged observation before broad enforcement"],
        ["Automation needs escape hatches", "Dry-run, tag scope, prod deny, alarm and runbook are one feature"],
        ["Backup is not recovery", "Restore evidence and measured RTO/RPO complete the control"],
    ], [135, 345]))
    story.append(Paragraph("References", style_map["h2"]))
    refs = [
        "AWS Organizations - Service control policies: docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html",
        "Amazon EKS - Kubernetes version lifecycle: docs.aws.amazon.com/eks/latest/userguide/versioning.html",
        "Amazon EKS - Control plane logs: docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html",
        "AWS Backup - Amazon EKS backups: docs.aws.amazon.com/aws-backup/latest/devguide/eks-backups.html",
        "Kubernetes - Pod QoS classes: kubernetes.io/docs/concepts/workloads/pods/pod-qos/",
        "Istio - Supported releases: istio.io/latest/docs/releases/supported-releases/",
        "AWS IAM Identity Center: docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html",
        "Amazon Bedrock VPC endpoints: docs.aws.amazon.com/bedrock/latest/userguide/vpc-interface-endpoints.html",
        "Repository source of truth: README.md and docs/security-review.md",
        "Agent value source of truth: docs/agent-value/README.md",
    ]
    for ref in refs:
        bullet(story, style_map, ref, color=MUTED)
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("Outcome: a reviewable enterprise cloud platform baseline with explicit implementation, ownership, controls, validation, and remaining production gates.", style_map["callout"]))

    return story


def report_chapter(story, style_map, number, title, question):
    story.chapter_number = number
    story.section_number = 0
    heading = Paragraph(f"{number}. {title}", style_map["chapter"])
    heading.toc_level = 0
    heading.chapter_number = number
    heading.bookmark_key = f"chapter-{number}"
    story.append(heading)
    story.append(Paragraph(f"<b>이 장에서 답하는 질문</b><br/>{question}", style_map["question"]))


def report_section(story, style_map, title, include_in_toc=True):
    heading_text = title
    if include_in_toc and story.chapter_number is not None:
        story.section_number += 1
        heading_text = f"{story.chapter_number}.{story.section_number} {title}"

    heading = Paragraph(heading_text, style_map["section"])
    if include_in_toc:
        heading.toc_level = 1
        if story.chapter_number is None:
            heading.bookmark_key = "document-guide-method"
        else:
            heading.bookmark_key = f"section-{story.chapter_number}-{story.section_number}"
    story.append(heading)


def report_paragraph(story, style_map, text):
    story.append(Paragraph(text, style_map["body"]))


class ReportStory(list):
    def __init__(self):
        super().__init__()
        self.chapter_number = None
        self.section_number = 0


class ChapterRangeTableOfContents(TableOfContents):
    def __init__(self, start_chapter, end_chapter, include_guide=False):
        super().__init__()
        self.start_chapter = start_chapter
        self.end_chapter = end_chapter
        self.include_guide = include_guide
        self._include_current = False

    def beforeBuild(self):
        super().beforeBuild()
        self._include_current = False

    def addEntry(self, level, text, pageNum, key=None):
        if level == 0:
            if text == "문서 안내":
                self._include_current = self.include_guide
            else:
                prefix = text.split(".", 1)[0]
                self._include_current = (
                    prefix.isdigit()
                    and self.start_chapter <= int(prefix) <= self.end_chapter
                )
        if self._include_current:
            super().addEntry(level, text, pageNum, key)


def configure_toc(toc):
    toc.levelStyles = [
        ParagraphStyle(
            "목차-장", fontName="Portfolio-Bold", fontSize=7.8, leading=9.2,
            leftIndent=0, firstLineIndent=0, textColor=INK,
            spaceBefore=0.5, spaceAfter=0.1,
        ),
        ParagraphStyle(
            "목차-절", fontName="Portfolio", fontSize=6.9, leading=7.3,
            leftIndent=16, firstLineIndent=0, textColor=MUTED,
            spaceBefore=0, spaceAfter=0,
        ),
    ]
    toc.tableStyle = TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ])
    toc.dotsMinLevel = 0
    return toc


def build_korean_report_story(style_map):
    story = ReportStory()

    # 표지
    story.extend([
        Spacer(1, 28 * mm),
        Paragraph("클라우드 플랫폼 엔지니어링 · 2026", style_map["cover_eyebrow"]),
        Paragraph("엔터프라이즈<br/>클라우드 플랫폼<br/>설계 포트폴리오", style_map["cover_title"]),
        Table([[""]], colWidths=[48 * mm], rowHeights=[1.7 * mm], hAlign="LEFT", style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), TEAL),
            ("BOX", (0, 0), (-1, -1), 0, TEAL),
        ])),
        Spacer(1, 8 * mm),
        Paragraph(
            "계정과 네트워크부터 EKS 운영, 보안, 관측성, 비용 관리와<br/>"
            "사람 주도 AI 에이전트 도입까지 하나의 운영 체계로 연결한 설계안",
            style_map["cover_subtitle"],
        ),
        Paragraph(
            "제가 엔터프라이즈 환경의 아키텍처를 구성한다면,<br/>"
            "변경 책임과 운영 증적이 분명한 구조로 설계하겠습니다.",
            style_map["cover_statement"],
        ),
        Spacer(1, 38 * mm),
        Paragraph("설계 범위", style_map["cover_label"]),
        Paragraph(
            "AWS 다중 계정 · Terraform · EKS · Kubernetes · 보안 · 관측성 · 비용 관리 · AI 에이전트 운영",
            style_map["cover_meta"],
        ),
        Spacer(1, 7 * mm),
        Paragraph("작성 기준  2026.08.08&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;저장소 기반 설계 및 로컬 검증", style_map["cover_footer"]),
        PageBreak(),
    ])

    # 문서 안내와 목차
    guide_heading = Paragraph("문서 안내", style_map["h1"])
    guide_heading.toc_level = 0
    guide_heading.bookmark_key = "document-guide"
    story.append(guide_heading)
    report_paragraph(
        story,
        style_map,
        "이 문서는 작성자가 엔터프라이즈 클라우드 아키텍처를 직접 구성한다면 계정, 네트워크, 보안, EKS 운영과 AI 에이전트 도입을 어떤 원칙과 책임 경계로 설계할 것인지 제안한 포트폴리오입니다. 실제 회사의 운영 환경을 이미 구축했다는 주장이 아니라, 저장소에 구현한 코드와 로컬 검증 결과를 근거로 설계 역량과 운영 관점을 설명합니다.",
    )
    report_section(story, style_map, "작성 방법과 책임")
    story.append(make_table([
        ["구분", "내용", "책임 경계"],
        ["작성자", "목표 아키텍처, 책임 분리, 보안·운영 기준과 최종 설계 판단", "선택의 이유와 결과에 대한 최종 책임"],
        ["AI 작성 보조", "Codex · GPT-5.6-Sol · 추론 수준 xhigh", "저장소 분석, 코드·문서 초안, 일관성 점검과 PDF 제작 보조"],
        ["검증 방식", "Terraform 정적 검증, 에이전트 시험, 문서·코드 대조와 PDF 렌더링", "자동 생성 결과를 그대로 채택하지 않고 작성자가 증적과 표현을 확인"],
    ], [85, 205, 190], font_size=7.0))
    report_paragraph(
        story,
        style_map,
        "AI 에이전트는 설계자를 대신한 의사결정 주체가 아니라 분석과 작성의 보조 수단으로 사용했습니다. 문서에서 ‘구현’은 저장소 코드와 시험으로 확인된 항목, ‘정의’는 정책과 측정 기준이 문서화된 상태, ‘목표’는 실제 계정 정보나 운영 환경 증적이 있어야 완료되는 항목을 뜻합니다.",
    )
    story.append(PageBreak())
    story.append(Paragraph("상세 목차", style_map["h1"]))
    story.append(configure_toc(TableOfContents()))
    story.append(PageBreak())

    # 1장
    report_chapter(
        story,
        style_map,
        1,
        "프로젝트 개요",
        "이 포트폴리오는 어떤 운영 문제를 해결하려고 했으며, 현재 무엇까지 확인되었는가?",
    )
    story.append(metric_cards([
        ("3", "환경", TEAL),
        ("15", "Terraform 모듈", BLUE),
        ("10/10", "Terraform 검증", GREEN),
        ("24/24", "에이전트 시험", AMBER),
    ]))
    report_section(story, style_map, "해결하려는 문제")
    report_paragraph(
        story,
        style_map,
        "엔터프라이즈 클라우드에서는 계정, 네트워크, 권한, Kubernetes 플랫폼, 백업과 비용 정책이 서로 다른 생명주기를 갖습니다. 이를 하나의 상태와 한 번의 배포에 묶으면 작은 변경도 넓은 장애 범위를 만들고, 환경별 설정 차이와 책임 공백이 누적됩니다.",
    )
    report_paragraph(
        story,
        style_map,
        "이 프로젝트는 조직 정책과 공통 기반, 서비스별 네트워크 정책, Kubernetes 플랫폼을 분리하고, 개발·검증·운영 환경이 같은 모듈 조합을 사용하도록 설계했습니다. 운영 관점에서는 EKS 로그, 자원 품질, 가용성, 확장, 업그레이드와 복구를 코드와 운영 절차에 함께 연결했습니다.",
    )
    story.append(make_table([
        ["관점", "핵심 판단", "현재 증적"],
        ["플랫폼 구조", "생명주기와 장애 범위에 따라 상태와 책임을 분리", "15개 모듈, 3개 환경, 상태 분리 구조"],
        ["EKS 운영", "구축 이후의 로그·용량·장애·복구 기준을 배포 조건으로 관리", "Terraform 객체, 현재/목표 표, 운영 점검표"],
        ["보안과 거버넌스", "권한과 정책 변경은 독립 검토와 사람 승인 뒤에 실행", "SCP, IAM, KMS, 네트워크 통제와 잔여 위험 검토"],
        ["AI 에이전트", "즉시 자율 운영하지 않고 질문·증적·검토부터 표준화", "11개 역할, 요청 양식, 읽기 전용 장애 분석 최소 기능 구현"],
    ], [95, 245, 140], font_size=6.9))
    report_section(story, style_map, "현재 도달 수준")
    story.append(make_table([
        ["상태", "포함 내용", "포트폴리오 표현"],
        ["구현", "Terraform 기준선, 환경 조합, EKS 운영 일부, 읽기 전용 장애 보고서", "코드와 시험으로 확인했다고 표현"],
        ["정의", "사람 주도 에이전트 운영, 성과 지표, 보고·승인 기준", "운영 기준을 설계했다고 표현"],
        ["목표", "중앙 감사 계정, 실제 AI 게이트웨이, 장기 지표 저장소, 운영 자동 복구", "향후 운영 환경 검증 과제로 표현"],
    ], [70, 265, 145], font_size=7.0))
    story.append(Paragraph(
        "저장소 코드와 로컬 시험은 확인했지만 실제 AWS 계정의 실행 계획·적용, 실시간 장애 조회, 복구 훈련과 사업 성과 기준값은 아직 완료 증적이 아닙니다. 이 경계를 숨기지 않는 것이 문서의 신뢰 기준입니다.",
        style_map["callout"],
    ))
    # 2장
    report_chapter(
        story,
        style_map,
        2,
        "전체 아키텍처와 책임 경계",
        "계정, 네트워크, 보안과 Kubernetes를 어떤 기준으로 나누었으며 변경 책임은 어디에 있는가?",
    )
    report_section(story, style_map, "설계 원칙")
    report_paragraph(
        story,
        style_map,
        "아키텍처의 중심은 서비스 수가 아니라 변경 책임입니다. 조직 전체에 영향을 주는 정책, 계정별 공통 기반, 서비스 단위 네트워크 규칙, Kubernetes 내부 객체는 권한과 배포 주기가 다르므로 같은 상태에서 관리하지 않습니다.",
    )
    story.append(HorizontalFlow([
        "조직 정책\nOU·SCP",
        "공통 기반\nVPC·IAM·EKS",
        "서비스 정책\n보안그룹·경로",
        "Kubernetes\nHelm·정책",
        "운영 증적\n알람·복구",
    ], [colors.HexColor("#FFF2DD"), colors.HexColor("#E8F1FB"), colors.HexColor("#EAF5F6"), LIGHT, colors.HexColor("#FBECEC")]))
    story.append(Paragraph("그림 1. 변경 생명주기에 따른 상태와 운영 책임의 분리", style_map["caption"]))
    story.append(make_table([
        ["계층", "주요 구성", "분리 이유"],
        ["조직 정책", "OU, SCP, 태그 정책", "조직 전체 장애 범위와 별도 승인"],
        ["공통 기반", "VPC, KMS, IAM, EKS, 백업, 비용", "AWS 자원과 계정 생명주기"],
        ["서비스 정책", "보안그룹 규칙과 추가 경로", "변경 빈도와 담당자가 다를 때 선택 분리"],
        ["Kubernetes 플랫폼", "Helm, 네임스페이스 정책, 관측 도구", "접근 가능한 Kubernetes API와 별도 원복"],
    ], [100, 220, 160], font_size=7.0))
    report_section(story, style_map, "계정과 조직 정책")
    report_paragraph(
        story,
        style_map,
        "보안, 공통 인프라, 업무, 실험 계정을 조직 단위로 구분하고 정책을 상속합니다. SCP는 권한을 주는 수단이 아니라 최대 권한 범위를 제한하는 안전 통제로 사용합니다. 광범위한 정책은 정책 검증용 OU에서 먼저 관찰하고, 비상 접근과 서비스 사용 이력을 확인한 뒤 단계적으로 확대합니다.",
    )
    story.append(make_table([
        ["계정·OU", "책임", "주요 통제"],
        ["보안", "감사, 중앙 로그, 보안 결과", "위임 관리자와 장기 보존"],
        ["공통 인프라", "네트워크, DNS, 배포 기반", "공유 경로와 중앙 연결 책임"],
        ["업무", "개발·검증·운영 서비스", "상속된 SCP와 환경별 예산"],
        ["실험", "학습과 단기 검증", "강한 예산과 업무 외 시간 중지"],
    ], [100, 205, 175], font_size=7.0))
    report_section(story, style_map, "네트워크와 보안 기본선")
    report_paragraph(
        story,
        style_map,
        "외부 진입, 내부 애플리케이션, 데이터 계층을 가용 영역 단위로 나누고 데이터베이스 경로에는 기본 인터넷 경로를 두지 않습니다. EKS API는 사설 접근을 기본으로 하며 운영 도구는 VPN, 전용선 또는 VPC 내부 실행기를 사용합니다.",
    )
    story.append(make_table([
        ["항목", "개발", "검증", "운영"],
        ["가용 영역", "2개", "2개", "3개"],
        ["NAT", "사용 안 함", "1개", "가용 영역별"],
        ["데이터베이스 인터넷 경로", "없음", "없음", "없음"],
        ["흐름 로그 보존", "90일", "90일", "365일"],
        ["운영 시간", "업무 시간", "업무 시간", "상시"],
    ], [150, 110, 110, 110], font_size=7.1))
    report_paragraph(
        story,
        style_map,
        "중앙 검사 VPC, Transit Gateway, Network Firewall 경로는 계정 식별자와 실제 통신 행렬이 확정되어야 구현할 수 있으므로 목표 구조로 남겨 두었습니다. 존재하지 않는 운영 통제를 구현된 것처럼 표현하지 않습니다.",
    )
    # 3장
    report_chapter(
        story,
        style_map,
        3,
        "Terraform 구현과 변경 관리",
        "모듈을 어떻게 재사용하면서도 환경별 차이와 상태 충돌을 줄였으며, 변경을 어떻게 검증하는가?",
    )
    report_section(story, style_map, "코드 저장소 탐색 지도")
    report_paragraph(
        story,
        style_map,
        "저장소는 인프라 코드, 에이전트 운영 기준, 실행 코드, 데이터 계약, 문서와 검증 자동화를 분리합니다. 처음 보는 검토자가 전체 파일을 읽지 않아도 아래 구조와 탐색 표를 통해 설계 판단에서 코드와 시험까지 이동할 수 있도록 구성했습니다.",
    )
    tree = """cloud-portfolio/
|-- terraform/
|   |-- organization/
|   |-- environments/
|   |   |-- dev/  `-- platform/
|   |   |-- stg/  `-- platform/
|   |   `-- prod/ `-- platform/
|   `-- modules/
|-- agents/              `-- request-templates/
|-- agent-runtime/       |-- src/cloud_portfolio_agents/  `-- tests/
|-- schemas/             `-- config/monitoring/
|-- docs/                `-- agent-value/
|-- scripts/             |-- agent/  |-- validation/
|                        |-- operations/  |-- pdf/  `-- tests/
`-- .github/workflows/"""
    story.append(Preformatted(tree, style_map["code"]))
    story.append(Paragraph("그림 2. 설계, 구현, 계약, 검증을 연결하는 저장소 디렉터리 구조", style_map["caption"]))
    story.append(make_table([
        ["경로", "확인할 내용", "대표 증적"],
        ["terraform/environments", "개발·검증·운영 환경의 동일 모듈 조합과 입력 차이", "환경별 main.tf와 platform root"],
        ["terraform/modules", "네트워크, 보안, EKS, 운영, 비용의 재사용 자원 논리", "15개 구현 모듈과 compute 예약 경계"],
        ["agents", "역할별 책임, 요청 양식, 사람 승인과 단계적 위임", "운영자 안내서와 요청 템플릿"],
        ["agent-runtime", "읽기 전용 장애 분석, 증적 마스킹과 보고서 생성", "실행 코드와 24개 시험"],
        ["schemas / config", "요청·보고서 데이터 계약과 허용된 관측 조회", "JSON Schema와 조회 목록"],
        ["scripts / workflows", "Terraform, 에이전트, PDF의 반복 가능한 검증", "로컬 스크립트와 CI 작업"],
    ], [115, 235, 130], font_size=6.7))
    report_section(story, style_map, "Terraform 상태와 모듈 경계")
    report_paragraph(
        story,
        style_map,
        "최상위 구성은 조립과 입력만 담당하고 실제 자원 논리는 재사용 모듈에 둡니다. 개발·검증·운영 환경은 같은 조합 모듈을 사용하며 가용성, 용량, 로그 보존, 예산과 운영 시간만 입력으로 다르게 설정합니다. Kubernetes API 접근이 필요한 platform root는 AWS 공통 기반 상태와 분리합니다.",
    )
    report_section(story, style_map, "핵심 구현 판단")
    story.append(make_table([
        ["판단", "구현 방식", "효과와 상충 관계"],
        ["환경 일관성", "동일 조합 모듈과 환경별 입력", "구조 차이를 줄이지만 입력 계약 관리가 중요"],
        ["상태 분리", "조직·공통 기반·서비스 정책·Kubernetes 상태 분리", "장애 범위를 줄이지만 적용 순서가 필요"],
        ["보수적 기본값", "사설 EKS, KMS, IMDSv2, 데이터 계층 경로 격리", "초기 연결 준비가 늘지만 운영 위험 감소"],
        ["소유권 충돌 방지", "노드 desired_size 변경은 향후 자동 확장기에 양보", "현재 자동 확장 제어기는 별도 구현 필요"],
    ], [105, 220, 155], font_size=6.9))
    report_section(story, style_map, "변경과 승인 흐름")
    story.append(HorizontalFlow([
        "요청\n티켓·범위",
        "코드\n최소 변경",
        "검증\n형식·유효성",
        "검토\n보안·비용",
        "승인·배포\n보호된 CI/CD",
    ], [LIGHT, colors.HexColor("#E8F1FB"), colors.HexColor("#EAF5F6"), colors.HexColor("#FFF2DD"), colors.HexColor("#FBECEC")]))
    story.append(Paragraph("그림 3. 사람이 승인하는 Terraform 변경 흐름", style_map["caption"]))
    report_paragraph(
        story,
        style_map,
        "운영 변경은 티켓, 원본 개정, 실행 계획 해시, 보안·비용 영향, 원복 책임자와 배포 후 확인 지표가 연결되어야 합니다. 예상하지 않은 삭제·교체, 상태 저장소 변경, 공개 경로 확대 또는 권한 증가는 중단 조건입니다.",
    )
    report_section(story, style_map, "현재 검증 결과")
    story.append(make_table([
        ["검증", "대상", "결과"],
        ["형식 검사", "저장소 전체 Terraform", "통과"],
        ["구성 유효성", "조직 1개, 환경 기반 3개, Kubernetes 플랫폼 3개", "7개 배포 루트 통과"],
        ["독립 모듈", "보안그룹, 경로 정책, WAF", "3개 모듈 통과"],
        ["운영 코드", "EC2/RDS 일정 조정 Lambda 문법", "통과"],
    ], [110, 260, 110], font_size=7.0))
    story.append(Paragraph(
        "현재 검증은 공급자 스키마 기준의 초기화와 유효성 검사입니다. 계정별 변수로 생성한 실제 실행 계획, 적용, 복구와 삭제 증적은 별도 샌드박스에서 확인해야 합니다.",
        style_map["callout"],
    ))
    # 4장
    report_chapter(
        story,
        style_map,
        4,
        "EKS 플랫폼 운영",
        "클러스터를 만드는 것에서 끝나지 않고 로그, 자원 품질, 가용성, 확장, 업그레이드와 복구를 어떻게 운영하는가?",
    )
    report_section(story, style_map, "기반 구성")
    story.append(HorizontalFlow([
        "사설 API\n접근 항목",
        "제어 영역\nKMS·5종 로그",
        "AL2023 노드\nIMDSv2·gp3",
        "관리형 추가 기능\n버전 호환",
        "Pod Identity\nCNI·EBS CSI",
    ], [colors.HexColor("#E8F1FB"), colors.HexColor("#EAF5F6"), LIGHT, colors.HexColor("#FFF2DD"), colors.HexColor("#FBECEC")]))
    story.append(Paragraph("그림 4. EKS 제어 영역, 노드와 추가 기능의 책임 분리", style_map["caption"]))
    story.append(make_table([
        ["항목", "현재 구현", "운영 의미"],
        ["접근", "사설 API와 접근 항목", "클러스터 생성자의 영구 관리자 권한 제거"],
        ["암호화", "제어 영역과 로그 전용 KMS", "키 책임과 보존 정책 분리"],
        ["노드", "AL2023, IMDSv2, 암호화 gp3", "불변 이미지 교체를 기본 패치 방식으로 사용"],
        ["추가 기능", "CNI, CoreDNS, kube-proxy, Pod Identity, EBS CSI, CloudWatch", "제어 영역·노드 버전과 호환성 검증 필요"],
        ["업데이트", "개발 50%, 검증·운영 25% 최대 비가용", "개발에서 운영 순서로 승격"],
    ], [95, 235, 150], font_size=6.9))
    report_section(story, style_map, "로그 수집과 보존")
    report_paragraph(
        story,
        style_map,
        "제어 영역, 노드·실행 환경, 애플리케이션 로그는 원인과 책임이 다르므로 구분해 수집합니다. CloudWatch는 즉시 검색하는 계층으로 사용하고, 중앙 S3 보관과 불변성은 별도 감사 계정이 확정된 후 구현하는 목표입니다.",
    )
    story.append(make_table([
        ["영역", "현재", "환경별 보존", "남은 검증"],
        ["제어 영역", "API, 감사, 인증, 제어기, 스케줄러", "90/90/365일", "수집 지연·권한·검색 시험"],
        ["노드와 실행 환경", "CloudWatch Observability와 Fluent Bit", "30/90/365일", "모든 노드·taint와 누락률"],
        ["애플리케이션", "전용 로그 그룹과 Istio 표준 출력", "30/90/365일", "JSON, 개인정보 마스킹, 전달 실패"],
        ["메트릭", "Prometheus", "7/15/30일", "로그 보존과 혼동하지 않음"],
    ], [90, 180, 95, 115], font_size=6.7))
    report_section(story, style_map, "자원 품질과 가용성")
    story.append(make_table([
        ["업무 등급", "자원 품질 기준", "가용성 기준"],
        ["중요 서비스", "보장형 또는 검증된 가변형, 요청량 필수, 메모리 상한 필수", "복제본, 상태 확인, PDB, 분산 배치, HPA"],
        ["일반 서비스", "가변형, LimitRange 기본값과 ResourceQuota", "업무 영향에 따른 PDB와 확장"],
        ["배치·실험", "가변형 또는 최소 보장 없음, 낮은 우선순위", "중단 허용 조건과 비용 한도"],
    ], [95, 230, 155], font_size=6.9))
    report_paragraph(
        story,
        style_map,
        "현재 네임스페이스 LimitRange, ResourceQuota와 세 개의 PriorityClass가 구현되어 있습니다. 실제 PDB 인스턴스, HPA/VPA, 분산 배치와 노드 자동 확장 제어기는 업무별 배포에 포함해야 하는 목표입니다. 자원 품질 등급이 높다고 퇴거나 선점을 절대 방지하는 것은 아니며, PDB도 자발적 중단 중심의 보호입니다.",
    )
    report_section(story, style_map, "확장, 업그레이드와 복구")
    report_paragraph(
        story,
        style_map,
        "확장은 HPA가 Pod 수요를, 노드 자동 확장기가 미배치 Pod와 노드 용량을 담당하도록 층을 나눕니다. 운영 환경 승격 전에는 지원 종료 API, 제어 영역·노드·추가 기능·컨트롤러 호환성, PDB와 노드 안전 축출 영향을 확인합니다.",
    )
    story.append(make_table([
        ["작업", "필수 증적", "현재 상태"],
        ["클러스터·추가 기능·노드 업그레이드", "호환성, deprecated API, 백업, PDB, 원복", "절차 정의, 실제 승격 증적 필요"],
        ["백업", "상위·하위 복구 지점, 저장소·외부 의존성", "Terraform 선택 정책, 실제 복구 지점 확인 필요"],
        ["복구 훈련", "격리 대상, 무결성 해시, 합성 거래, 측정 RPO/RTO", "월간·분기 기준 정의, 실제 훈련 필요"],
        ["지역 장애", "별도 클러스터, 데이터 복제, DNS 전환, 원래 지역 복귀", "목표 구조"],
    ], [120, 235, 125], font_size=6.8))
    # 5장
    report_chapter(
        story,
        style_map,
        5,
        "관측성과 장애 대응",
        "문제가 발생했을 때 어떤 신호를 보고, 사실과 가설을 어떻게 구분하며, 복구 판단을 어떻게 남기는가?",
    )
    report_section(story, style_map, "신호와 알람")
    story.append(HorizontalFlow([
        "AWS 신호\nCloudWatch",
        "Kubernetes\nPrometheus",
        "정규화\n공통 이름",
        "심각도\n영향 기준",
        "대응\n담당자·운영 절차",
    ], [LIGHT, colors.HexColor("#E8F1FB"), colors.HexColor("#EAF5F6"), colors.HexColor("#FFF2DD"), colors.HexColor("#FBECEC")]))
    story.append(Paragraph("그림 5. 신호 수집에서 담당자 대응까지의 흐름", style_map["caption"]))
    story.append(make_table([
        ["영역", "주요 신호", "운영 질문"],
        ["서비스 품질", "오류율, 지연, 처리 성공률", "고객 영향이 있는가?"],
        ["Kubernetes", "NotReady, Pending, 재시작, OOM, 퇴거", "배포 문제인가, 용량 문제인가?"],
        ["네트워크", "거부 흐름, NAT, 가용 영역 간 전송", "경로·보안·비용 중 어디가 원인인가?"],
        ["저장소", "PVC 연결, 지연, 복구 상태", "데이터 무결성과 RPO/RTO에 영향이 있는가?"],
        ["AI 운영", "요청 비용, 지연, 도구 실패, 정책 거부", "권한 또는 데이터 통제를 위반했는가?"],
    ], [100, 220, 160], font_size=7.0))
    report_section(story, style_map, "예약 알림 서비스 사례")
    report_paragraph(
        story,
        style_map,
        "트래픽이 특정 시각에 몰리는 알림 서비스는 평균 지표보다 최고 구간의 병목을 봐야 합니다. ALB/WAF, Nginx 연결과 파일 기술자, 애플리케이션과 대기열, 외부 메시지 API를 하나의 시간축으로 연결합니다.",
    )
    story.append(make_table([
        ["구간", "확인 신호", "판단 기준"],
        ["전체 거래", "합성 거래 성공률과 완료율", "업무 성공이 실제로 유지되는가"],
        ["Nginx", "499/502/503/504, 지연, 연결, 파일 기술자", "앞단 포화와 upstream 문제를 구분"],
        ["대기열·작업자", "최고 대기 시간, 소비율, 재시도, DLQ", "처리 지연이 업무 SLO를 넘는가"],
        ["외부 메시지 API", "429, 5xx, 지연, 할당량", "내부 장애와 외부 제한을 구분"],
        ["당직 경로", "독립 호출 채널", "고객용 메시지 경로를 유일한 당직 채널로 사용하지 않음"],
    ], [105, 220, 155], font_size=6.9))
    report_section(story, style_map, "읽기 전용 장애 분석 보고서")
    report_paragraph(
        story,
        style_map,
        "현재 구현된 모니터링 에이전트는 읽기 전용 최소 기능 단계이며 운영자가 지정한 임의 명령을 실행하지 않습니다. 서버가 소유한 조회 목록에서 허용된 ID만 선택하고, 결과를 마스킹한 뒤 사실, 가설, 누락 증적과 인계 항목을 보고서로 만듭니다.",
    )
    story.append(HorizontalFlow([
        "요청 검증\n환경·시간·비용",
        "고정 조회\n허용 목록",
        "마스킹\n비밀·개인정보",
        "보고서\n사실·가설·누락",
        "사람 판단\n복구·인계",
    ], [LIGHT, colors.HexColor("#E8F1FB"), colors.HexColor("#FBECEC"), colors.HexColor("#EAF5F6"), colors.HexColor("#FFF2DD")]))
    story.append(Paragraph("그림 6. 읽기 전용 장애 증적 수집과 사람 판단", style_map["caption"]))
    story.append(make_table([
        ["산출물", "용도", "주의"],
        ["report.json", "다른 시스템과 에이전트가 읽는 구조화 결과", "스키마와 상태 검증"],
        ["report.md", "운영자가 읽는 장애 분석 보고서", "사실과 가설 분리"],
        ["audit.jsonl", "요청·정책·도구 호출·마스킹 감사", "추가 전용 저장 필요"],
        ["모의 실행 상태", "모의 입력을 사용한 안전 검증", "실제 운영 증적으로 합산하지 않음"],
    ], [100, 235, 145], font_size=7.0))
    # 6장
    report_chapter(
        story,
        style_map,
        6,
        "운영 자동화, 보안과 비용 관리",
        "반복 운영을 어디까지 자동화하고, 보안과 비용 판단을 어떤 승인 경계 안에 두는가?",
    )
    report_section(story, style_map, "운영 자동화")
    story.append(make_table([
        ["통제", "구현", "안전 장치"],
        ["일일 백업", "환경·백업 정책 태그 선택", "KMS, 보존, 운영 Vault Lock"],
        ["EC2/RDS 일정", "EventBridge Scheduler와 Lambda", "개발·검증만, 기본 모의 실행, 운영 이중 차단"],
        ["패치", "Ubuntu/RHEL/AL2023 SSM 기준선", "승인 지연과 불변 이미지 교체 원칙"],
        ["취약점", "Inspector EC2/ECR/Lambda", "심각도별 조치 기한과 책임자"],
        ["지원 종료", "자산 목록과 전환 이정표", "6/3/1개월 사전 계획"],
    ], [105, 225, 150], font_size=7.0))
    report_section(story, style_map, "읽기 전용 운영 점검 스크립트")
    report_paragraph(
        story,
        style_map,
        "운영 자동화는 변경 실행보다 현재 상태를 재현 가능한 증적으로 만드는 단계에서 시작합니다. 스크립트는 대상 서버, Kubernetes context와 AWS region을 명시적으로 받고 Secret·프로세스 환경과 변경 명령을 조회 대상에서 제외합니다. 보고서는 소유자 전용 권한으로 생성하고 발견 사항은 티켓에 연결한 뒤 Terraform 또는 보호된 운영 절차로 전달합니다.",
    )
    story.append(make_table([
        ["스크립트", "수집 증적", "안전 경계"],
        ["system-health-report.sh", "CPU·메모리·디스크·inode·프로세스·systemd·오류 journal", "Linux 읽기 전용, 임계치 경고"],
        ["service-triage.sh", "서비스 상태·MainPID·자원·소켓·journal", "재시작·설정 변경 없음"],
        ["patch-readiness.sh", "캐시된 업데이트·보안 권고·재부팅 지표", "저장소 갱신·설치·재부팅 없음"],
        ["eks-cluster-health.sh", "노드·비정상 Pod·PDB·HPA·PVC·이벤트", "context 필수, Secret 미조회"],
        ["audit-cloudwatch-log-retention.sh", "로그 보존·KMS·정책 위반 수", "AWS 조회 API만 사용"],
    ], [155, 215, 110], font_size=6.4))
    story.append(Paragraph(
        "Bash 구문, 도움말의 무부작용 실행과 eval 금지 규칙은 operations-scripts-test CI에서 확인합니다. 실제 Linux 배포판, 사설 EKS와 AWS 계정 통합 시험은 비운영 환경에서 추가해야 합니다.",
        style_map["callout"],
    ))
    report_paragraph(
        story,
        style_map,
        "일정 조정기는 Terraform 조건과 Lambda 실행 시점 검사를 모두 사용해 운영 환경을 차단합니다. EKS 노드 그룹은 Terraform과 향후 자동 확장기의 소유권 충돌을 피하기 위해 일정 조정 대상에서 제외합니다.",
    )
    report_section(story, style_map, "보안과 승인")
    story.append(make_table([
        ["변경", "필수 검토", "최종 실행"],
        ["운영 인프라", "Terraform, 보안, 독립 검토", "보호된 운영 CI/CD"],
        ["SCP·태그 정책", "거버넌스, 보안, 잠금 위험 검토", "조직 정책 파이프라인"],
        ["IAM 권한 증가", "최소 권한, 자원 책임자, 보안 책임자", "보호된 파이프라인"],
        ["백업 복구", "운영, 보안, 데이터 책임자", "승인된 운영자와 절차"],
        ["비상 작업", "Incident Commander 승인과 사후 보안 검토", "지정된 비상 운영자"],
    ], [110, 245, 125], font_size=6.9))
    report_paragraph(
        story,
        style_map,
        "SCP, WAF, IAM과 네트워크 정책은 보안을 높이지만 잘못 적용하면 운영 중단을 만들 수 있습니다. 따라서 사전 관찰, 부정 시험, 소규모 승격, 비상 접근과 원복을 하나의 기능으로 봅니다.",
    )
    report_section(story, style_map, "비용 관리")
    report_paragraph(
        story,
        style_map,
        "비용 관리는 예산 경보에서 끝나지 않습니다. 먼저 서비스·환경·비용 중심·책임자 태그로 비용을 배부하고, 이상을 탐지한 뒤 낭비 제거, 크기 조정, 아키텍처 개선과 장기 약정 순서로 진행합니다.",
    )
    story.append(make_table([
        ["단계", "통제", "판단 기준"],
        ["배부", "Environment, Owner, Service, CostCenter", "미할당 비용을 거버넌스 부채로 관리"],
        ["탐지", "예산 50/80/100%, 서비스 이상 비용", "환경 책임자에게 알림"],
        ["낭비 제거", "업무 시간, 미사용 EBS/EIP/LB", "장기 약정 전에 제거"],
        ["최적화", "크기 조정, NAT/VPC 엔드포인트, 보존 기간", "30일 기준값과 SLO를 함께 확인"],
        ["약정", "Savings Plans 또는 RI", "안정적인 운영 24시간 기준 부하만 후보"],
    ], [90, 220, 170], font_size=6.9))
    story.append(Paragraph(
        "예상 절감액은 성과가 아닙니다. 서비스 사용량과 가격 변화를 보정한 기준 비용에서 적용 후 실제 비용과 일회성 비용을 제외하고, FinOps 또는 재무 책임자가 확인한 값만 실현 절감으로 기록합니다.",
        style_map["callout"],
    ))
    # 7장
    report_chapter(
        story,
        style_map,
        7,
        "사람 주도 AI 에이전트 도입",
        "기업이 인프라 운영을 즉시 에이전트에게 맡기기 어려운 상황에서 어떤 순서로 안전하게 도입할 수 있는가?",
    )
    report_section(story, style_map, "도입 판단")
    report_paragraph(
        story,
        style_map,
        "초기 목표는 사람을 대체하는 것이 아니라 운영자의 질문, 증적 확인, 변경 초안과 검토를 표준화하는 것입니다. 운영자가 역할별 요청 양식으로 질문하고 에이전트가 사실과 가설, 선택지, 위험과 추가 확인 항목을 정리합니다. 실행과 최종 책임은 운영자와 보호된 CI/CD에 남습니다.",
    )
    story.append(make_table([
        ["역할", "주요 책임", "대표 산출물"],
        ["아키텍처", "요구사항과 전체 경계", "아키텍처 결정 기록과 목표 구조"],
        ["Terraform", "모듈, 환경, 상태와 변경안", "코드 수정안과 실행 계획 요약"],
        ["거버넌스·보안", "조직 정책, 권한, 암호화, 위험", "정책 제안과 검토 결과"],
        ["모니터링·운영", "신호, 장애, 백업, 패치, EKS 운영", "장애 보고서와 운영 절차"],
        ["비용·CI/CD", "비용 분석, 검증, 승인과 승격", "최적화 목록과 배포 조건"],
        ["독립 검토·문서화", "누락 위험과 산출물 일관성", "검토 결과와 포트폴리오"],
    ], [105, 235, 140], font_size=6.9))
    report_section(story, style_map, "업무별 성숙도")
    story.append(make_table([
        ["단계", "에이전트가 하는 일", "사람의 책임"],
        ["0단계: 비운영 평가", "문서·모의 입력으로 분류와 초안 평가", "정답과 실패 기준 작성"],
        ["1단계: 읽기 전용 자문", "승인된 정보로 사실·가설·선택지 제시", "근거 검증과 모든 실행"],
        ["2단계: 산출물 작성", "코드·실행 계획·운영 절차·보고서 초안", "검토, 승인, 병합과 배포"],
        ["3단계: 감독 자동화", "정의된 저위험 작업 흐름 호출", "실행 시작과 결과 확인"],
        ["4단계: 제한 위임", "승인된 범위와 임계값 안에서 실행·중지·원복", "정책 소유, 예외 승인과 정기 감사"],
    ], [115, 225, 140], font_size=6.8))
    report_paragraph(
        story,
        style_map,
        "성숙도는 에이전트 전체가 아니라 업무와 환경의 조합으로 관리합니다. 같은 모니터링 에이전트라도 로그 요약은 읽기 전용으로 허용할 수 있지만 재시작과 알람 억제는 별도 권한과 훈련 없이는 허용하지 않습니다.",
    )
    report_section(story, style_map, "운영자 요청과 검증")
    story.append(HorizontalFlow([
        "운영자\n티켓·요청 양식",
        "게이트웨이\n신원·정책·비용",
        "에이전트\n조회·초안·검토",
        "사람 검증\n근거·위험·승인",
        "보호된 실행\nCI/CD·운영 절차",
    ], [LIGHT, colors.HexColor("#E8F1FB"), colors.HexColor("#EAF5F6"), colors.HexColor("#FFF2DD"), colors.HexColor("#FBECEC")]))
    story.append(Paragraph("그림 7. 사람 주도 에이전트 요청과 실행 경계", style_map["caption"]))
    report_paragraph(
        story,
        style_map,
        "모든 결과는 요청 범위, 확인된 사실과 출처, 가정과 불확실성, 제안, 검증 결과, 보안·가용성·비용 영향, 원복, 필요한 승인과 다음 작업을 포함해야 합니다. 대화 기억은 운영 기록이 아니며 티켓, 변경 요청, 실행 계획과 보고서를 사실 기준으로 사용합니다.",
    )
    story.append(Paragraph(
        "현재 실제 실행 가능한 범위는 모니터링 에이전트의 읽기 전용 장애 증적 수집 최소 기능 구현입니다. 중앙 AI 게이트웨이, 내부 포털, 도구 중개기와 모델 실행 환경은 목표 구조이며 구현된 것으로 표현하지 않습니다.",
        style_map["callout"],
    ))
    # 8장
    report_chapter(
        story,
        style_map,
        8,
        "비즈니스 성과와 엔지니어링 성과",
        "AI 에이전트와 플랫폼 투자가 회사와 엔지니어링 조직에 어떤 결과를 만들어야 하며, 이를 어떻게 과장 없이 측정하는가?",
    )
    report_section(story, style_map, "가치 연결 구조")
    story.append(HorizontalFlow([
        "에이전트 기능\n조회·초안",
        "엔지니어링 변화\n시간·품질",
        "서비스 결과\n안정성·배포",
        "비즈니스 가치\n연속성·비용",
        "검증\n증적·책임자",
    ], [LIGHT, colors.HexColor("#E8F1FB"), colors.HexColor("#EAF5F6"), colors.HexColor("#FFF2DD"), colors.HexColor("#FBECEC")]))
    story.append(Paragraph("그림 8. 에이전트 기능에서 검증된 비즈니스 결과까지의 연결", style_map["caption"]))
    story.append(make_table([
        ["비즈니스 성과", "엔지니어링 동인", "측정 지표", "검증 책임"],
        ["서비스 연속성", "빠른 증적 수집과 복구 훈련", "고객 영향 시간, SLO 위반", "서비스 책임자"],
        ["변경·출시 속도", "표준 변경안과 검토 흐름", "변경 준비·승인·배포 시간", "플랫폼·CI/CD 책임자"],
        ["비용 효율", "반복 작업 감소와 정상화된 최적화", "회수 시간, 단위 비용, 실현 절감", "FinOps·재무 책임자"],
        ["위험 감소", "정책 시험, 증적, 예외 만료", "중요 위험, 감사 준비 시간", "보안·거버넌스 책임자"],
        ["조직 확장성", "요청 양식, 보고서, 운영 절차", "관리 범위, 온보딩, 표준 적용률", "엔지니어링 책임자"],
    ], [100, 170, 120, 90], font_size=6.6))
    report_section(story, style_map, "엔지니어링 지표")
    story.append(make_table([
        ["영역", "주요 지표", "안전 지표"],
        ["장애 대응", "증적 수집 시간, MTTR, 증적 범위", "부분·차단 보고서와 재발률"],
        ["변경", "변경 소요 시간, 실패율, 원복률", "예상 밖 삭제·교체와 사후 확인"],
        ["EKS·안정성", "SLO, OOM, 퇴거, 미배치, 복구 성공", "자원 품질·백업 객체 존재를 성공으로 간주하지 않음"],
        ["보안·거버넌스", "위험 나이, 예외, 정책 시험 범위", "권한 초과와 승인 우회 0건"],
        ["비용", "배부율, 단위 비용, 실현 절감", "SLO와 용량 악화 여부"],
        ["에이전트 품질", "근거가 있는 사실 비율, 사람 수정률", "정책 거부, 범위 확대, 비밀정보 노출"],
    ], [105, 225, 150], font_size=6.8))
    report_section(story, style_map, "성과 주장 단계")
    story.append(make_table([
        ["상태", "필요 증적", "허용되는 표현"],
        ["정의", "지표, 계산식, 책임자", "측정 기준을 정의했다"],
        ["수집 가능", "원본 사건과 데이터 연결", "측정 가능한 구조를 만들었다"],
        ["측정", "기준값과 실측 표본", "공개한 범위에서 관측했다"],
        ["검증", "업무·비즈니스 책임자의 보정 승인", "안전 지표와 함께 개선을 확인했다"],
        ["실현", "반복 확인된 운영·재무 결과", "실현된 결과로 확인했다"],
    ], [80, 225, 175], font_size=6.9))
    report_paragraph(
        story,
        style_map,
        "현재 공통 성과 지표는 ‘정의’ 상태입니다. 읽기 전용 모의 입력 보고서는 기술 경로를 증명하지만 운영 MTTR이나 비용 절감 실적은 아닙니다. 실제 수치에는 기간, 범위, 표본 수, 보정 방법과 사람 책임자의 승인이 필요합니다.",
    )
    report_section(story, style_map, "보고 주기")
    story.append(make_table([
        ["주기", "목적", "주요 독자"],
        ["요청·변경별", "사실, 위험, 승인, 즉시 결과", "운영자, 검토자, 승인자"],
        ["주간", "변경 품질, EKS 상태, 반복 누락", "엔지니어링 책임자"],
        ["월간", "엔지니어링 지표, 비용, 사람 수정과 안전", "플랫폼·보안·FinOps"],
        ["분기", "비즈니스 결과, 투자, 성숙도 승격", "기술·사업 책임자"],
    ], [90, 245, 145], font_size=7.0))
    # 9장
    report_chapter(
        story,
        style_map,
        9,
        "검증 결과와 남은 한계",
        "무엇을 실제로 재현할 수 있으며, 운영 적용 전에 어떤 검증이 더 필요한가?",
    )
    story.append(metric_cards([
        ("통과", "Terraform 형식", GREEN),
        ("10/10", "Terraform 대상", GREEN),
        ("24/24", "에이전트 시험", GREEN),
        ("통과", "PDF 렌더링", BLUE),
    ]))
    report_section(story, style_map, "재현 명령")
    story.append(Preformatted(
        "./scripts/validation/validate-terraform.sh\n"
        "python3 -m unittest discover -s agent-runtime/tests -v\n"
        "bash scripts/tests/validate-operations-scripts.sh\n"
        "python3 scripts/pdf/verify/verify_portfolio_pdf.py enterprise-cloud-portfolio.pdf",
        style_map["code"],
    ))
    story.append(make_table([
        ["확인 영역", "현재 확인된 내용", "아직 필요한 내용"],
        ["Terraform", "형식, 7개 배포 루트, 3개 독립 모듈", "계정별 실행 계획·적용·복구·삭제"],
        ["에이전트 계약", "요청 검증, 변경 모드 거부, 환경·자원 범위", "실제 게이트웨이와 신원 연계"],
        ["보안 경계", "비밀정보 마스킹, 셸·변경 명령 차단, 주소 제한", "샌드박스 IAM 정책 시험과 침투 시험"],
        ["장애 보고", "모의 입력 보고서, 감사 기록, 부분·차단 상태", "실시간 AWS/EKS 조회와 운영자 승인 흐름"],
        ["운영 스크립트", "5개 도구의 Bash 구문, 도움말, eval 금지", "Linux 배포판·사설 EKS·AWS 비운영 통합 시험"],
        ["PDF", "텍스트, 필수 문구, 전체 페이지 렌더링", "향후 변경 시 같은 검증 반복"],
    ], [100, 225, 155], font_size=6.9))
    report_section(story, style_map, "주요 잔여 위험")
    story.append(make_table([
        ["위험", "현재 경계", "운영 적용 조건"],
        ["중앙 감사", "조직 Trail과 Config 집계기 미구현", "보안·로그 보관 계정 식별자"],
        ["SCP 잠금", "코드만 있고 실제 조직에 미부착", "정책 검증 OU와 비상 접근 훈련"],
        ["사설 EKS", "공개 API 없음", "사설 실행기 또는 VPN 연결 증적"],
        ["Grafana 비밀", "민감 값이 Terraform 상태에 존재 가능", "Secrets Manager와 External Secrets"],
        ["WAF", "모듈은 있으나 실제 ingress에 미연결", "관찰 모드와 오탐 검토 후 차단 승격"],
        ["복구 증명", "백업 정책과 태그 선택 구현", "격리 복구, 무결성 해시, 합성 거래와 RPO/RTO"],
        ["사업 성과", "지표 정의만 완료", "기준값, 실측값, 표본, 보정과 책임자 승인"],
    ], [100, 205, 175], font_size=6.7))
    story.append(Paragraph(
        "검증 통과는 운영 준비의 일부입니다. 실제 계정의 네트워크·권한·용량·데이터와 장애 상황에서 같은 결과가 나오는지 확인하기 전에는 ‘운영 완료’라고 표현하지 않습니다.",
        style_map["callout"],
    ))
    # 10장
    report_chapter(
        story,
        style_map,
        10,
        "교훈과 다음 단계",
        "이 설계에서 얻은 실무 교훈은 무엇이며, 운영 환경으로 발전시키려면 무엇을 먼저 해야 하는가?",
    )
    report_section(story, style_map, "핵심 교훈")
    story.append(make_table([
        ["교훈", "실무 의미"],
        ["모듈 수보다 책임 경계가 중요", "입력 계약, 보수적 기본값, 단일 상태 소유자가 재사용성을 결정"],
        ["Kubernetes는 두 번째 제어 영역", "AWS 기반과 Helm/Kubernetes 객체는 접근, 원복과 배포 시점이 다름"],
        ["안전 정책도 장애를 만들 수 있음", "SCP, WAF, IAM은 관찰과 부정 시험 뒤 단계적으로 적용"],
        ["자동화는 중단 경로까지 한 기능", "모의 실행, 대상 태그, 운영 차단, 경보와 운영 절차를 함께 구현"],
        ["백업은 복구 증명이 아님", "격리 복구와 실제 RPO/RTO가 있어야 통제가 완료"],
        ["AI 에이전트의 가치는 자율성보다 검증 가능성", "근거, 사람 수정, 승인, 도구 경계와 보고서가 먼저"],
    ], [145, 335], font_size=7.0))
    report_section(story, style_map, "우선순위가 높은 다음 작업")
    for item in [
        "샌드박스 조직과 계정에서 실행 계획, 적용, 복구와 삭제 증적을 생성합니다.",
        "Organization CloudTrail, Config 집계기와 불변 중앙 로그 보관 상태를 구현합니다.",
        "EKS ingress와 WAF 연결, AWS Load Balancer Controller 권한을 실제 자원에 검증합니다.",
        "노드 자동 확장기, NetworkPolicy, 실제 PDB/HPA와 장애·용량 훈련을 구현합니다.",
        "운영 백업 복구와 EKS 네임스페이스/PVC 복구에서 무결성 해시와 RPO/RTO를 측정합니다.",
        "중앙 AI 게이트웨이, 도구 중개기, 신원·정책·비용 사건을 연결한 읽기 전용 운영 시험을 진행합니다.",
        "티켓, PR, CI, 모니터링과 CUR를 연결해 월간 성과표의 기준값과 실측값을 수집합니다.",
    ]:
        bullet(story, style_map, item)
    report_section(story, style_map, "면접에서 논의할 수 있는 설계 질문")
    story.append(make_table([
        ["질문", "문서에서 확인할 판단"],
        ["왜 하나의 Terraform 상태로 관리하지 않았는가?", "장애 범위, 권한, 생명주기와 원복 책임"],
        ["왜 EKS API를 사설로 두었는가?", "공격면과 운영 연결 복잡성의 상충 관계"],
        ["왜 AI 에이전트에게 운영 권한을 바로 주지 않았는가?", "기업 승인, 증적 품질, 제한 위임의 단계"],
        ["백업이 있는데 왜 복구를 미완료로 보는가?", "복구 지점, 외부 의존성, 무결성 해시와 RPO/RTO"],
        ["현재 구현과 목표 구조를 어떻게 구분했는가?", "코드·시험·운영 증적의 주장 단계"],
    ], [220, 260], font_size=7.0))
    report_section(story, style_map, "참고 자료")
    for ref in [
        "AWS Organizations SCP: docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html",
        "Amazon EKS 버전 생명주기: docs.aws.amazon.com/eks/latest/userguide/versioning.html",
        "Amazon EKS 제어 영역 로그: docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html",
        "AWS Backup의 EKS 백업: docs.aws.amazon.com/aws-backup/latest/devguide/eks-backups.html",
        "Kubernetes Pod 자원 품질 등급: kubernetes.io/docs/concepts/workloads/pods/pod-qos/",
        "저장소 기준 문서: README.md, docs/eks-operations.md, docs/agent-value/README.md",
    ]:
        bullet(story, style_map, ref, color=MUTED)
    story.append(Paragraph(
        "이 포트폴리오의 핵심 결과는 많은 서비스를 나열한 것이 아니라, 구현과 목표의 경계를 공개하면서 플랫폼 설계, 운영 통제, 검증과 다음 투자를 하나의 설명 가능한 흐름으로 만든 것입니다.",
        style_map["callout"],
    ))

    return story


def main():
    register_fonts()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = PortfolioDocTemplate(str(OUTPUT))
    document.multiBuild(build_korean_report_story(styles()))
    print(OUTPUT)


if __name__ == "__main__":
    main()
