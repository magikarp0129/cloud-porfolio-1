#!/usr/bin/env python3

"""Build a text-first PDF variant without competing with the primary PDF job."""

from xml.sax.saxutils import escape

import build_portfolio_pdf as base


OUTPUT = base.REPO_ROOT / "enterprise-cloud-portfolio-readable.pdf"


def readable_styles():
    style_map = base.styles()
    updates = {
        "h1": dict(fontSize=22, leading=30, spaceAfter=14),
        "chapter": dict(fontSize=22, leading=31, spaceBefore=7, spaceAfter=12),
        "section": dict(fontSize=14, leading=21, spaceBefore=17, spaceAfter=8),
        "subsection": dict(fontSize=11, leading=17, spaceBefore=10, spaceAfter=5),
        "body": dict(fontSize=10.2, leading=17, spaceAfter=10, allowWidows=0, allowOrphans=0),
        "small": dict(fontSize=8.2, leading=13),
        "callout": dict(fontSize=9.8, leading=16.5, leftIndent=11, rightIndent=11,
                        borderPadding=11, spaceBefore=5, spaceAfter=12),
        "question": dict(fontSize=9.8, leading=16.5, leftIndent=11, rightIndent=11,
                         borderPadding=11, spaceAfter=15),
        "caption": dict(fontSize=8, leading=12, spaceBefore=4, spaceAfter=10),
        "bullet": dict(fontSize=9.6, leading=15.5, leftIndent=15,
                       firstLineIndent=-8, spaceAfter=5),
        "code": dict(fontSize=7.4, leading=10.5, borderPadding=9, spaceAfter=10),
    }
    for name, values in updates.items():
        for attribute, value in values.items():
            setattr(style_map[name], attribute, value)
    return style_map


def narrative_table(data, col_widths, header=True, font_size=7.2):
    row_style = base.ParagraphStyle(
        "readable-narrative-row",
        fontName="Portfolio",
        fontSize=max(9.2, font_size + 1.8),
        leading=max(15, font_size + 8),
        textColor=base.INK,
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
            content = f'<font size="10.5"><b>{values[0]}</b></font>'
            if details:
                content += "<br/>" + "<br/>".join(details)
        else:
            content = "<br/>".join(values)
        wrapped.append([base.Paragraph(content, row_style)])

    table = base.Table(wrapped, colWidths=[sum(col_widths)], hAlign="LEFT", splitByRow=1)
    table_style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, base.LINE),
    ]
    for row_index in range(len(wrapped)):
        if row_index % 2 == 1:
            table_style.append(
                ("BACKGROUND", (0, row_index), (0, row_index), base.colors.HexColor("#F8FAFB"))
            )
    table.setStyle(base.TableStyle(table_style))
    return table


def readable_report_chapter(story, style_map, number, title, question):
    if number > 1:
        story.append(base.PageBreak())
    story.chapter_number = number
    story.section_number = 0
    heading = base.Paragraph(f"{number}. {title}", style_map["chapter"])
    heading.toc_level = 0
    heading.chapter_number = number
    heading.bookmark_key = f"chapter-{number}"
    story.append(heading)
    story.append(base.Paragraph(
        f"<b>이 장에서 답하는 질문</b><br/>{question}",
        style_map["question"],
    ))


def readable_toc(start_chapter, end_chapter, include_guide=False):
    toc = base.configure_toc(base.ChapterRangeTableOfContents(
        start_chapter,
        end_chapter,
        include_guide=include_guide,
    ))
    chapter_style, section_style = toc.levelStyles
    chapter_style.fontSize = 10.2
    chapter_style.leading = 14.5
    chapter_style.spaceBefore = 5
    section_style.fontSize = 9.2
    section_style.leading = 12
    return toc


def metric_explanation_flowables(style_map):
    data = [
        ["표시", "산정 기준", "구체적인 범위", "이 숫자가 증명하지 않는 것"],
        [
            "환경 3",
            "논리적인 workload 환경인 dev, stg, prod를 셉니다.",
            "각 환경은 AWS 공통 기반 root와 별도의 Kubernetes platform root를 가지며 같은 모듈 조합에 서로 다른 가용 영역, NAT, 보존 기간과 운영 보호 입력을 적용합니다.",
            "실제 AWS 계정 3개에 배포가 끝났거나 세 환경이 운영 중이라는 뜻은 아닙니다.",
        ],
        [
            "Terraform 모듈 15",
            "terraform/modules 아래 16개 디렉터리 중 실제 .tf 구현이 있는 15개를 셉니다.",
            "organization, scp-policy, network, security-group, route-policy, workload-environment, eks, kubernetes-platform, security, waf, observability, operations, iam, cost, monitoring-agent-access가 포함됩니다. compute는 향후 EC2 Auto Scaling 또는 ECS용 예약 디렉터리라 제외합니다.",
            "15개 모듈이 모두 실제 계정에 적용됐거나 운영 준비가 완료됐다는 뜻은 아닙니다.",
        ],
        [
            "Terraform 검증 10/10",
            "검증 스크립트에 등록된 10개 대상이 모두 terraform init -backend=false와 terraform validate를 통과했다는 뜻입니다.",
            "7개 배포 root는 organization, dev/stg/prod AWS 기반, dev/stg/prod platform이며, 3개 독립 모듈은 security-group, route-policy, waf입니다. 전체 저장소 fmt 검사와 scheduler.py 문법 검사도 함께 실행합니다.",
            "모든 15개 구현 모듈을 각각 plan/apply했다는 뜻이 아니며, 계정별 권한·용량·비용·실자원 동작은 증명하지 않습니다.",
        ],
        [
            "에이전트 시험 24/24",
            "agent-runtime의 자동화 시험 24건이 모두 통과했다는 뜻입니다.",
            "요청 계약 9건은 read-only mode, 환경·리전·시간·데이터 범위를 검사합니다. 보안 경계 8건은 비밀·개인정보 마스킹, 셸/AWS/Kubernetes 변경 차단, URL·DNS·런타임 신원·EKS endpoint 결합을 검사합니다. 장애 분석 5건은 fixture simulation, 보고서·감사 기록, 무증적 차단과 live policy pin을 검사하고, Terraform 경계 2건은 AWS deny guardrail과 Kubernetes 읽기 전용 권한을 검사합니다.",
            "모의 입력과 로컬 단위 시험이므로 실제 장애에서의 정확도, MTTR 개선, live AWS/EKS 연결 또는 운영 권한의 안전성을 완전히 증명하지 않습니다.",
        ],
    ]
    return [
        base.Paragraph("프로젝트 범위 숫자 해설", style_map["section"]),
        base.Paragraph(
            "표지의 숫자는 운영 성과가 아니라 현재 저장소에서 확인할 수 있는 구조와 자동 검증 범위를 요약합니다. 분자는 통과하거나 구현된 수, 분모는 검증 스크립트 또는 시험 모음에 명시적으로 등록된 전체 대상을 뜻합니다.",
            style_map["body"],
        ),
        narrative_table(data, [480], font_size=7.5),
        base.Paragraph(
            "따라서 3·15는 설계와 코드의 범위이고, 10/10·24/24는 현재 자동 검증 집합의 통과 상태입니다. 실제 계정의 plan/apply, 복구 훈련, 실시간 장애 대응과 사업 성과는 별도의 운영 증적이 필요합니다.",
            style_map["callout"],
        ),
    ]


def insert_metric_explanations(story, style_map):
    for index, flowable in enumerate(story):
        if isinstance(flowable, base.Paragraph) and flowable.getPlainText() == "1.1 해결하려는 문제":
            story[index:index] = metric_explanation_flowables(style_map)
            return story
    raise RuntimeError("Chapter 1 detail heading was not found")


def split_detailed_toc(story, style_map):
    for index, flowable in enumerate(story):
        if isinstance(flowable, base.Paragraph) and flowable.getPlainText() == "상세 목차":
            replacement = [
                base.Paragraph("상세 목차 · 1-5장", style_map["h1"]),
                readable_toc(1, 5, include_guide=True),
                base.PageBreak(),
                base.Paragraph("상세 목차 · 6-10장", style_map["h1"]),
                readable_toc(6, 10),
            ]
            story[index:index + 2] = replacement
            return story
    raise RuntimeError("Detailed table of contents placeholder was not found")


def main():
    base.register_fonts()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    base.make_table = narrative_table
    base.report_chapter = readable_report_chapter
    style_map = readable_styles()
    story = base.build_korean_report_story(style_map)
    story = insert_metric_explanations(story, style_map)
    story = split_detailed_toc(story, style_map)

    document = base.PortfolioDocTemplate(str(OUTPUT))
    document.multiBuild(story)
    print(OUTPUT)


if __name__ == "__main__":
    main()
