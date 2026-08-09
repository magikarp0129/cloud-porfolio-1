#!/usr/bin/env python3

"""Build the enterprise service Landing Zone architecture portfolio PDF."""

from __future__ import annotations

import math
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / ".pdf-tools"))

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


OUTPUT = REPO_ROOT / "enterprise-service-landing-zone-architecture.pdf"
FONT_PATH = Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf")
PAGE_W, PAGE_H = landscape(A4)
TOTAL_PAGES = 10

NAVY = colors.HexColor("#12263A")
INK = colors.HexColor("#172B4D")
MUTED = colors.HexColor("#5E6C84")
PAPER = colors.HexColor("#F7F9FC")
WHITE = colors.white
LINE = colors.HexColor("#D7DEE8")
BLUE = colors.HexColor("#0052CC")
TEAL = colors.HexColor("#00875A")
PURPLE = colors.HexColor("#6554C0")
AMBER = colors.HexColor("#B76E00")
RED = colors.HexColor("#BF2600")
CYAN = colors.HexColor("#008DA6")
SOFT_BLUE = colors.HexColor("#DEEBFF")
SOFT_TEAL = colors.HexColor("#E3FCEF")
SOFT_PURPLE = colors.HexColor("#EAE6FF")
SOFT_AMBER = colors.HexColor("#FFF0B3")
SOFT_RED = colors.HexColor("#FFEBE6")
SOFT_CYAN = colors.HexColor("#E6FCFF")
SOFT_GRAY = colors.HexColor("#EBECF0")


SERVICES = [
    {
        "name": "commerce",
        "pool": "10.64.0.0/13",
        "dev": "10.64.0.0/20",
        "stg": "10.64.32.0/19",
        "prod": "10.65.0.0/16",
        "profile": "High-growth EKS/API",
        "reason": "Pod·ALB·campaign peak와 blue/green 동시 운영",
        "color": TEAL,
        "soft": SOFT_TEAL,
    },
    {
        "name": "payments",
        "pool": "10.72.0.0/14",
        "dev": "10.72.0.0/22",
        "stg": "10.72.8.0/21",
        "prod": "10.73.0.0/18",
        "profile": "Regulated transactional",
        "reason": "API·data 격리, DR·parallel migration 여유",
        "color": BLUE,
        "soft": SOFT_BLUE,
    },
    {
        "name": "analytics",
        "pool": "10.76.0.0/14",
        "dev": "10.76.0.0/20",
        "stg": "10.76.64.0/18",
        "prod": "10.77.0.0/16",
        "profile": "High-IP batch/EKS",
        "reason": "대규모 node·Pod·batch의 순간 scale-out",
        "color": PURPLE,
        "soft": SOFT_PURPLE,
    },
    {
        "name": "customer-profile",
        "pool": "10.80.0.0/14",
        "dev": "10.80.0.0/22",
        "stg": "10.80.8.0/21",
        "prod": "10.81.0.0/19",
        "profile": "Medium API/data",
        "reason": "API·cache·database 확장과 교체 subnet",
        "color": CYAN,
        "soft": SOFT_CYAN,
    },
    {
        "name": "internal-admin",
        "pool": "10.84.0.0/16",
        "dev": "10.84.0.0/22",
        "stg": "10.84.4.0/22",
        "prod": "10.84.16.0/20",
        "profile": "Small internal",
        "reason": "소규모지만 3 AZ·migration reserve 유지",
        "color": AMBER,
        "soft": SOFT_AMBER,
    },
]


def register_font() -> None:
    if not FONT_PATH.exists():
        raise FileNotFoundError(f"Korean font not found: {FONT_PATH}")
    pdfmetrics.registerFont(TTFont("Portfolio", str(FONT_PATH)))


def text_width(text: str, size: float) -> float:
    return pdfmetrics.stringWidth(str(text), "Portfolio", size)


def wrap(text: str, max_width: float, size: float) -> list[str]:
    words = str(text).split()
    if not words:
        return []
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if text_width(candidate, size) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def draw_wrapped(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    size: float = 8,
    leading: float = 11,
    color=INK,
    max_lines: int | None = None,
) -> float:
    lines = wrap(text, max_width, size)
    if max_lines is not None:
        lines = lines[:max_lines]
    c.setFont("Portfolio", size)
    c.setFillColor(color)
    for index, line in enumerate(lines):
        c.drawString(x, y - index * leading, line)
    return y - len(lines) * leading


def badge(c: canvas.Canvas, x, y, w, h, label, stroke, fill) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, h / 2, stroke=1, fill=1)
    c.setFont("Portfolio", 6.6)
    c.setFillColor(stroke)
    c.drawCentredString(x + w / 2, y + h / 2 - 2.2, label)


def page_base(c: canvas.Canvas, page: int, section: str, title: str, subtitle: str = "") -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 7 * mm, PAGE_W, 7 * mm, stroke=0, fill=1)
    c.setFont("Portfolio", 7.2)
    c.setFillColor(BLUE)
    c.drawString(16 * mm, PAGE_H - 17 * mm, section)
    title_size = 21.0
    max_title_width = PAGE_W - 16 * mm - 72 * mm
    while text_width(title, title_size) > max_title_width and title_size > 15:
        title_size -= 0.5
    c.setFont("Portfolio", title_size)
    c.setFillColor(INK)
    c.drawString(16 * mm, PAGE_H - 29 * mm, title)
    if subtitle:
        c.setFont("Portfolio", 8)
        c.setFillColor(MUTED)
        c.drawString(16 * mm, PAGE_H - 36 * mm, subtitle)
    badge(
        c,
        PAGE_W - 66 * mm,
        PAGE_H - 27 * mm,
        50 * mm,
        8 * mm,
        "CODE VALIDATED · NOT DEPLOYED",
        AMBER,
        SOFT_AMBER,
    )
    c.setStrokeColor(LINE)
    c.line(16 * mm, 12 * mm, PAGE_W - 16 * mm, 12 * mm)
    c.setFont("Portfolio", 6.8)
    c.setFillColor(MUTED)
    c.drawString(16 * mm, 7 * mm, "Enterprise Cloud Portfolio · ap-northeast-2 · repository evidence")
    c.drawRightString(PAGE_W - 16 * mm, 7 * mm, f"{page:02d} / {TOTAL_PAGES:02d}")


def box(
    c: canvas.Canvas,
    x,
    y,
    w,
    h,
    title,
    lines: list[str] | None = None,
    fill=WHITE,
    stroke=LINE,
    title_color=INK,
    dashed=False,
    status: str | None = None,
    title_size=9.5,
    body_size=7.4,
) -> None:
    c.saveState()
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(1)
    if dashed:
        c.setDash(5, 3)
    c.roundRect(x, y, w, h, 5, stroke=1, fill=1)
    c.restoreState()
    c.setFont("Portfolio", title_size)
    c.setFillColor(title_color)
    c.drawString(x + 9, y + h - 15, title)
    if status:
        stroke_color = TEAL if status == "구현" else AMBER
        fill_color = SOFT_TEAL if status == "구현" else SOFT_AMBER
        badge(c, x + w - 44, y + h - 20, 36, 12, status, stroke_color, fill_color)
    cursor = y + h - 29
    for line in lines or []:
        cursor = draw_wrapped(c, line, x + 9, cursor, w - 18, body_size, body_size + 3, MUTED) - 2


def arrow(c: canvas.Canvas, x1, y1, x2, y2, label: str | None = None, color=BLUE, dashed=False) -> None:
    c.saveState()
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(1.3)
    if dashed:
        c.setDash(5, 3)
    c.line(x1, y1, x2, y2)
    angle = math.atan2(y2 - y1, x2 - x1)
    length = 7
    for delta in (2.65, -2.65):
        c.line(x2, y2, x2 - length * math.cos(angle + delta), y2 - length * math.sin(angle + delta))
    c.restoreState()
    if label:
        label_width = text_width(label, 6.5) + 8
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        c.setFillColor(PAPER)
        c.rect(mid_x - label_width / 2, mid_y - 3, label_width, 10, stroke=0, fill=1)
        c.setFont("Portfolio", 6.5)
        c.setFillColor(color)
        c.drawCentredString(mid_x, mid_y, label)


def metric(c: canvas.Canvas, x, y, w, value, label, note, color, fill) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(color)
    c.roundRect(x, y, w, 29 * mm, 7, stroke=1, fill=1)
    c.setFont("Portfolio", 22)
    c.setFillColor(color)
    c.drawString(x + 10, y + 17 * mm, value)
    c.setFont("Portfolio", 8.2)
    c.setFillColor(INK)
    c.drawString(x + 10, y + 10 * mm, label)
    draw_wrapped(c, note, x + 10, y + 6 * mm, w - 20, 6.5, 8, MUTED, 2)


def table(
    c: canvas.Canvas,
    x,
    y_top,
    widths: list[float],
    headers: list[str],
    rows: list[list[str]],
    row_h=12 * mm,
    header_h=10 * mm,
    font_size=7,
) -> float:
    total_w = sum(widths)
    c.setFillColor(NAVY)
    c.roundRect(x, y_top - header_h, total_w, header_h, 4, stroke=0, fill=1)
    cursor_x = x
    c.setFont("Portfolio", 7.2)
    c.setFillColor(WHITE)
    for width, header in zip(widths, headers):
        c.drawString(cursor_x + 6, y_top - header_h / 2 - 2.5, header)
        cursor_x += width
    y = y_top - header_h
    for row_index, row in enumerate(rows):
        fill = WHITE if row_index % 2 == 0 else colors.HexColor("#F1F4F8")
        c.setFillColor(fill)
        c.setStrokeColor(LINE)
        c.rect(x, y - row_h, total_w, row_h, stroke=1, fill=1)
        cursor_x = x
        for width, value in zip(widths, row):
            draw_wrapped(c, value, cursor_x + 6, y - 10, width - 12, font_size, font_size + 2.4, INK, 3)
            cursor_x += width
        y -= row_h
    return y


def bullet_list(c: canvas.Canvas, items: list[str], x, y, width, color=INK, size=7.5, leading=10.5) -> float:
    cursor = y
    for item in items:
        c.setFillColor(color)
        c.circle(x + 2, cursor + 1.5, 1.6, stroke=0, fill=1)
        lines = wrap(item, width - 12, size)
        c.setFont("Portfolio", size)
        c.setFillColor(MUTED)
        for index, line in enumerate(lines):
            c.drawString(x + 9, cursor - index * leading, line)
        cursor -= len(lines) * leading + 4
    return cursor


def draw_cover(c: canvas.Canvas) -> None:
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setFillColor(BLUE)
    c.circle(PAGE_W - 55 * mm, PAGE_H - 32 * mm, 40 * mm, stroke=0, fill=1)
    c.setFillColor(PURPLE)
    c.circle(PAGE_W - 20 * mm, PAGE_H - 10 * mm, 24 * mm, stroke=0, fill=1)
    c.setFont("Portfolio", 8)
    c.setFillColor(colors.HexColor("#79F2C0"))
    c.drawString(17 * mm, PAGE_H - 22 * mm, "TERRAFORM · ENTERPRISE NETWORK ARCHITECTURE")
    c.setFont("Portfolio", 30)
    c.setFillColor(WHITE)
    c.drawString(17 * mm, PAGE_H - 46 * mm, "Enterprise Service Landing Zone")
    c.setFont("Portfolio", 15)
    c.setFillColor(colors.HexColor("#B3D4FF"))
    c.drawString(17 * mm, PAGE_H - 59 * mm, "5개 서비스 · 15개 VPC · 중앙 IPAM/TGW · 환경별 독립 state")
    draw_wrapped(
        c,
        "현재 저장소에 구현된 Terraform 구조와 IP 계산을 기준으로 작성했습니다. 실제 AWS account ID, RAM principal, attachment ID, inspection VPC와 plan/apply 증적은 배포 입력 전이므로 설계·코드와 운영 완료를 구분해 표시합니다.",
        17 * mm,
        PAGE_H - 76 * mm,
        230 * mm,
        9,
        13,
        colors.HexColor("#DCE6F1"),
    )

    start_x = 17 * mm
    gap = 5 * mm
    card_w = (PAGE_W - 34 * mm - gap * 3) / 4
    metrics = [
        ("10.64.0.0/10", "기업 Regional pool", "서울 리전 서비스 주소의 상위 경계", colors.HexColor("#79F2C0"), colors.HexColor("#183D4D")),
        ("5 × 3", "서비스 × 환경", "commerce 외 4개 · dev/stg/prod", colors.HexColor("#B3D4FF"), colors.HexColor("#18324F")),
        ("18", "구현 Terraform 모듈", "main.tf가 있는 reusable module", colors.HexColor("#C0B6F2"), colors.HexColor("#2E2A55")),
        ("28/28", "Terraform validate", "등록 root·독립 모듈 전체 통과", colors.HexColor("#FFD37A"), colors.HexColor("#4C3A18")),
    ]
    for index, (value, label, note, color, fill) in enumerate(metrics):
        x = start_x + index * (card_w + gap)
        c.setFillColor(fill)
        c.setStrokeColor(color)
        c.roundRect(x, 42 * mm, card_w, 35 * mm, 7, stroke=1, fill=1)
        c.setFont("Portfolio", 18 if index else 13)
        c.setFillColor(color)
        c.drawString(x + 10, 65 * mm, value)
        c.setFont("Portfolio", 7.8)
        c.setFillColor(WHITE)
        c.drawString(x + 10, 56 * mm, label)
        draw_wrapped(c, note, x + 10, 50 * mm, card_w - 20, 6.2, 8, colors.HexColor("#B8C7D9"), 2)

    badge(c, 17 * mm, 22 * mm, 42 * mm, 8 * mm, "GREEN · IMPLEMENTED", TEAL, colors.HexColor("#173E35"))
    badge(c, 63 * mm, 22 * mm, 42 * mm, 8 * mm, "BLUE · DESIGN RULE", colors.HexColor("#579DFF"), colors.HexColor("#18324F"))
    badge(c, 109 * mm, 22 * mm, 58 * mm, 8 * mm, "AMBER · DEPLOYMENT INPUT REQUIRED", colors.HexColor("#FFD37A"), colors.HexColor("#4C3A18"))
    c.setFont("Portfolio", 7)
    c.setFillColor(colors.HexColor("#9FB2C6"))
    c.drawRightString(PAGE_W - 17 * mm, 9 * mm, "01 / 10")


def draw_repository(c: canvas.Canvas) -> None:
    page_base(c, 2, "01 · REPOSITORY & STATE", "디렉터리가 곧 책임과 배포 경계입니다", "Landing Zone, 서비스 VPC, 중앙 route policy를 서로 다른 state로 분리")
    top = PAGE_H - 48 * mm
    box(c, 16 * mm, top - 47 * mm, 78 * mm, 47 * mm, "terraform/landing-zone/", [
        "ipam/ · 10.64.0.0/10, service pools",
        "network-hub/ · TGW, RAM, 4 route tables",
        "connectivity/ · association, allowed_routes",
    ], SOFT_BLUE, BLUE, status="구현")
    box(c, 109 * mm, top - 47 * mm, 78 * mm, 47 * mm, "terraform/modules/", [
        "service-vpc/ · VPC, 5 subnet tiers/AZ, NAT, TGW attachment",
        "transit-gateway-hub/",
        "transit-gateway-routing/",
    ], SOFT_PURPLE, PURPLE, status="구현")
    box(c, 202 * mm, top - 47 * mm, 79 * mm, 47 * mm, "terraform/services/", [
        "commerce/{dev,stg,prod}",
        "payments · analytics",
        "customer-profile · internal-admin",
        "총 15개 독립 root/state",
    ], SOFT_TEAL, TEAL, status="구현")

    arrow(c, 94 * mm, top - 23 * mm, 108 * mm, top - 23 * mm, "module", PURPLE)
    arrow(c, 187 * mm, top - 23 * mm, 201 * mm, top - 23 * mm, "call", TEAL)

    table(
        c,
        16 * mm,
        top - 58 * mm,
        [55 * mm, 55 * mm, 55 * mm, 105 * mm],
        ["STATE OWNER", "생성 범위", "전달하는 최소 ID", "왜 분리하는가"],
        [
            ["landing-zone/ipam", "IPAM과 service pool", "CIDR catalog", "주소 승인·중복 방지를 Network 책임으로 고정"],
            ["landing-zone/network-hub", "TGW·RAM·route table", "TGW/route table ID", "중앙 네트워크 수명주기와 workload 변경 분리"],
            ["services/<svc>/<env>", "VPC·subnet·NAT·attachment", "VPC/CIDR/attachment ID", "서비스별 blast radius와 승인 단위 축소"],
            ["landing-zone/connectivity", "association·static route", "배포 artifact 입력", "서비스가 중앙 route table을 직접 수정하지 않음"],
        ],
        row_h=13 * mm,
    )
    box(c, 16 * mm, 18 * mm, 265 * mm, 22 * mm, "명명 규칙", [
        "사용자 제안의 prd는 저장소 기존 표준과 맞추기 위해 prod로 통일했습니다. state key: services/<service>/<environment>/terraform.tfstate",
    ], SOFT_AMBER, AMBER, status="설계 규칙")


def draw_topology(c: canvas.Canvas) -> None:
    page_base(c, 3, "02 · TARGET TOPOLOGY", "Landing Zone TGW가 서비스 계정 사이의 유일한 중앙 경로입니다", "TGW attachment가 존재해도 route table에 승인 경로가 없으면 서비스 간 통신하지 않음")
    top = PAGE_H - 48 * mm
    box(c, 98 * mm, top - 27 * mm, 101 * mm, 27 * mm, "Network account · Landing Zone", [
        "VPC IPAM 10.64.0.0/10 · TGW RAM share",
        "default association/propagation OFF",
    ], SOFT_BLUE, BLUE, status="구현")
    box(c, 109 * mm, top - 65 * mm, 79 * mm, 27 * mm, "Enterprise TGW", [
        "nonprod · prod · shared · inspection",
        "명시적 allowed_routes",
    ], SOFT_AMBER, AMBER, status="구현")
    arrow(c, 148.5 * mm, top - 27 * mm, 148.5 * mm, top - 38 * mm, "owns", BLUE)

    card_y = 54 * mm
    card_h = 43 * mm
    card_w = 50 * mm
    gap = 5 * mm
    start_x = 14 * mm
    for index, service in enumerate(SERVICES):
        x = start_x + index * (card_w + gap)
        box(c, x, card_y, card_w, card_h, service["name"], [
            f"dev · {service['dev']}",
            f"stg · {service['stg']}",
            f"prod · {service['prod']}",
            "3 TGW attachments",
        ], service["soft"], service["color"], status="구현", body_size=6.7)

    bus_y = card_y + card_h + 4 * mm
    c.setStrokeColor(MUTED)
    c.setLineWidth(1)
    c.line(start_x + card_w / 2, bus_y, start_x + 4 * (card_w + gap) + card_w / 2, bus_y)
    arrow(c, 148.5 * mm, top - 65 * mm, 148.5 * mm, bus_y, color=AMBER)
    for index, service in enumerate(SERVICES):
        x = start_x + index * (card_w + gap)
        arrow(c, x + card_w / 2, bus_y, x + card_w / 2, card_y + card_h, color=service["color"])

    box(c, 16 * mm, 19 * mm, 76 * mm, 24 * mm, "Shared services", [
        "DNS · directory · artifact · observability",
        "return route는 중앙 connectivity가 소유",
    ], SOFT_GRAY, MUTED, dashed=True, status="배포 입력")
    box(c, 111 * mm, 19 * mm, 76 * mm, 24 * mm, "Inspection VPC", [
        "Network Firewall · egress inspection",
        "default route 연결은 attachment ID 필요",
    ], SOFT_RED, RED, dashed=True, status="배포 입력")
    box(c, 206 * mm, 19 * mm, 75 * mm, 24 * mm, "Corporate / other accounts", [
        "Landing Zone 경유 · 직접 peering 금지",
        "승인 route와 DNS 정책 필요",
    ], SOFT_GRAY, MUTED, dashed=True, status="설계 규칙")


def draw_ipam(c: canvas.Canvas) -> None:
    page_base(c, 4, "03 · IPAM HIERARCHY", "큰 풀을 먼저 예약하고 VPC는 서비스별 경계 안에서만 할당합니다", "CIDR은 현재 사용량이 아니라 3년 peak, migration, 신규 cluster와 AZ 교체를 포함해 결정")
    box(c, 72 * mm, PAGE_H - 72 * mm, 153 * mm, 25 * mm, "ap-northeast-2 enterprise pool · 10.64.0.0/10", [
        "서비스 supernet을 먼저 분리 · 미할당 공간은 신규 서비스·추가 리전·M&A migration용",
    ], SOFT_BLUE, BLUE, status="구현")
    table(
        c,
        16 * mm,
        PAGE_H - 82 * mm,
        [42 * mm, 40 * mm, 49 * mm, 49 * mm, 49 * mm, 45 * mm],
        ["SERVICE", "SUPERNET", "DEV", "STG", "PROD", "PROFILE"],
        [[s["name"], s["pool"], s["dev"], s["stg"], s["prod"], s["profile"]] for s in SERVICES],
        row_h=15 * mm,
        font_size=7.1,
    )
    box(c, 16 * mm, 18 * mm, 126 * mm, 22 * mm, "예약 원칙", [
        "한 서비스의 신규 VPC·secondary CIDR은 해당 service supernet 안에서만 승인합니다. 다른 서비스로 주소를 빌려주지 않습니다.",
    ], SOFT_TEAL, TEAL, status="설계 규칙")
    box(c, 155 * mm, 18 * mm, 126 * mm, 22 * mm, "미할당 공간", [
        "10.85.0.0 이후를 즉시 VPC에 배정하지 않아 신규 서비스·regional expansion·renumbering 선택지를 보존합니다.",
    ], SOFT_AMBER, AMBER, status="설계 규칙")


def draw_sizing(c: canvas.Canvas) -> None:
    page_base(c, 5, "04 · CIDR SIZING", "모든 서비스에 /16을 주지 않고 IP 소비 특성에 맞춰 크기를 다르게 잡았습니다", "표의 주소 수는 CIDR의 이론적 전체 크기이며 subnet별 AWS 예약 주소를 뺀 usable 수가 아님")
    prefix_rows = [
        ["/16", "65,536", "commerce-prod · analytics-prod", "고밀도 EKS/Pod와 batch surge"],
        ["/18", "16,384", "payments-prod · analytics-stg", "격리 계층·DR·대형 staging"],
        ["/19", "8,192", "commerce-stg · customer-profile-prod", "중간 규모 API/data와 교체 여유"],
        ["/20", "4,096", "commerce-dev · analytics-dev · internal-admin-prod", "2 AZ 개발 또는 소규모 3 AZ 운영"],
        ["/21", "2,048", "payments-stg · customer-profile-stg", "중간 검증 환경"],
        ["/22", "1,024", "소형 dev/stg", "작은 환경이지만 5개 subnet tier 유지"],
    ]
    table(c, 16 * mm, PAGE_H - 48 * mm, [28 * mm, 34 * mm, 105 * mm, 107 * mm], ["PREFIX", "전체 주소", "적용 VPC", "의도"], prefix_rows, row_h=12.5 * mm, font_size=7.2)

    factors = [
        ("EKS", "node·Pod·warm prefix·upgrade surge·control-plane x-ENI", PURPLE, SOFT_PURPLE),
        ("EDGE", "ALB/NLB ENI·NAT·blue/green 동시 운영", BLUE, SOFT_BLUE),
        ("DATA", "RDS/cache replica·failover·migration copy", TEAL, SOFT_TEAL),
        ("GROWTH", "추가 AZ·새 cluster/VPC·secondary CIDR·M&A", AMBER, SOFT_AMBER),
    ]
    start_x = 16 * mm
    card_w = 64.5 * mm
    for index, (title, note, color, fill) in enumerate(factors):
        box(c, start_x + index * 69.5 * mm, 20 * mm, card_w, 26 * mm, title, [note], fill, color, status="산정 입력", body_size=7)


def draw_routing(c: canvas.Canvas) -> None:
    page_base(c, 6, "05 · TGW ROUTING", "연결과 허용을 분리해 prod/nonprod의 full mesh를 막습니다", "VPC attachment는 서비스 state, association·route는 중앙 connectivity state가 소유")
    center_x = 121 * mm
    route_tables = [
        ("nonprod RT", "dev·stg attachment", "approved nonprod/shared routes", BLUE, SOFT_BLUE, 21 * mm),
        ("prod RT", "prod attachment", "approved prod/shared routes", TEAL, SOFT_TEAL, 76 * mm),
        ("shared RT", "shared services attachment", "15개 VPC return routes", PURPLE, SOFT_PURPLE, 186 * mm),
        ("inspection RT", "inspection attachment", "spoke return routes", RED, SOFT_RED, 241 * mm),
    ]
    tgw_y = 132 * mm
    box(c, center_x, tgw_y, 55 * mm, 27 * mm, "Enterprise TGW", [
        "default association OFF",
        "default propagation OFF",
        "static allowed_routes",
    ], SOFT_AMBER, AMBER, status="구현")
    for title, line1, line2, color, fill, x in route_tables:
        y = 98 * mm
        box(c, x, y, 45 * mm, 24 * mm, title, [line1, line2], fill, color, status="구현", body_size=6.3)
        arrow(c, center_x + 27.5 * mm, tgw_y, x + 22.5 * mm, y + 24 * mm, color=color)

    table(c, 16 * mm, 90 * mm, [52 * mm, 52 * mm, 60 * mm, 110 * mm], ["SOURCE", "ASSOCIATION", "DESTINATION", "DECISION"], [
        ["dev / stg", "nonprod", "shared service CIDR", "필요 route만 승인 · prod 경로 없음"],
        ["prod", "prod", "shared service CIDR", "업무 dependency별 route change 승인"],
        ["prod / nonprod", "각 도메인", "0.0.0.0/0", "inspection attachment 준비 후에만 활성화"],
        ["shared / inspection", "각 전용 RT", "service VPC CIDR", "대칭 return route를 중앙에서 생성"],
    ], row_h=10 * mm, font_size=6.8)
    box(c, 16 * mm, 18 * mm, 265 * mm, 19 * mm, "VPC route 원칙", [
        "private app·private data·EKS cluster: 10.64.0.0/10 → TGW · public subnet: enterprise route 없음 · VPC local route가 더 구체적이므로 동일 VPC 통신은 TGW를 우회",
    ], SOFT_GRAY, MUTED, status="구현", body_size=6.8)


def draw_commerce(c: canvas.Canvas) -> None:
    page_base(c, 7, "06 · VPC DETAIL", "commerce-prod · 10.65.0.0/16 · 3 AZ", "stable AZ ID: apne2-az1 / apne2-az2 / apne2-az3 · prod는 AZ별 NAT")
    azs = [
        ("AZ-1 · apne2-az1", ["App 10.65.0.0/19", "Data 10.65.128.0/20", "Public 10.65.192.0/21", "TGW 10.65.255.160/28", "EKS x-ENI 10.65.255.208/28", "NAT Gateway"], BLUE, SOFT_BLUE),
        ("AZ-2 · apne2-az2", ["App 10.65.32.0/19", "Data 10.65.144.0/20", "Public 10.65.200.0/21", "TGW 10.65.255.176/28", "EKS x-ENI 10.65.255.224/28", "NAT Gateway"], PURPLE, SOFT_PURPLE),
        ("AZ-3 · apne2-az3", ["App 10.65.64.0/19", "Data 10.65.160.0/20", "Public 10.65.208.0/21", "TGW 10.65.255.192/28", "EKS x-ENI 10.65.255.240/28", "NAT Gateway"], CYAN, SOFT_CYAN),
    ]
    y = PAGE_H - 128 * mm
    start_x = 16 * mm
    card_w = 82 * mm
    for index, (title, lines, color, fill) in enumerate(azs):
        box(c, start_x + index * 90 * mm, y, card_w, 76 * mm, title, lines, fill, color, status="구현", body_size=7.2)
    box(c, 99 * mm, 45 * mm, 99 * mm, 29 * mm, "Landing Zone TGW", [
        "App/Data/EKS: 10.64.0.0/10 → TGW",
        "attachment subnet은 데이터 workload를 배치하지 않는 전용 /28",
    ], SOFT_AMBER, AMBER, status="구현")
    for index in range(3):
        x = start_x + index * 90 * mm + card_w / 2
        arrow(c, x, y, 148.5 * mm, 74 * mm, color=azs[index][2])
    box(c, 16 * mm, 18 * mm, 79 * mm, 20 * mm, "Contiguous reserve", [
        "App 10.65.96.0/19 · Data 10.65.176.0/20 · Public 10.65.216.0/21",
    ], SOFT_TEAL, TEAL, status="설계 규칙", body_size=6.6)
    box(c, 202 * mm, 18 * mm, 79 * mm, 20 * mm, "Egress boundary", [
        "public → IGW · private app/EKS → AZ NAT · data에는 default route 없음",
    ], SOFT_GRAY, MUTED, status="구현", body_size=6.6)


def draw_subnet_policy(c: canvas.Canvas) -> None:
    page_base(c, 8, "07 · SUBNET POLICY", "VPC 크기가 달라도 동일한 계산 규칙을 적용합니다", "첫 7/8은 app·data·edge, 마지막 1/8은 endpoint·migration·AZ 교체 reserve")
    segments = [
        ("1/2", "Private app", "EKS node·Pod", TEAL, 126),
        ("1/4", "Private data", "DB·cache", BLUE, 63),
        ("1/8", "Public edge", "NAT·ALB", PURPLE, 31.5),
        ("1/8", "Reserve", "endpoint·migration", AMBER, 31.5),
    ]
    x = 22 * mm
    y = PAGE_H - 66 * mm
    total = 0
    for ratio, title, note, color, width_mm in segments:
        w = width_mm * mm
        c.setFillColor(colors.Color(color.red, color.green, color.blue, alpha=0.15))
        c.setStrokeColor(color)
        c.rect(x + total, y, w, 25 * mm, stroke=1, fill=1)
        c.setFont("Portfolio", 9)
        c.setFillColor(color)
        c.drawCentredString(x + total + w / 2, y + 16 * mm, f"{ratio} · {title}")
        c.setFont("Portfolio", 6.5)
        c.setFillColor(MUTED)
        c.drawCentredString(x + total + w / 2, y + 8 * mm, note)
        total += w

    box(c, 22 * mm, y - 28 * mm, 123 * mm, 18 * mm, "VPC 끝의 고정 subnet", [
        "AZ별 TGW attachment /28 + EKS cluster x-ENI /28",
    ], SOFT_RED, RED, status="구현", body_size=7)
    box(c, 152 * mm, y - 28 * mm, 123 * mm, 18 * mm, "3 AZ 분할", [
        "각 pool을 4등분해 3개 사용 · 네 번째 조각은 교체/AZ 추가용",
    ], SOFT_CYAN, CYAN, status="설계 규칙", body_size=7)

    table(c, 16 * mm, y - 40 * mm, [48 * mm, 48 * mm, 48 * mm, 48 * mm, 82 * mm], ["PROD VPC", "APP / AZ", "DATA / AZ", "PUBLIC / AZ", "운영 해석"], [
        ["commerce /16", "/19", "/20", "/21", "고밀도 EKS·campaign peak"],
        ["payments /18", "/21", "/22", "/23", "규제 workload·DR"],
        ["analytics /16", "/19", "/20", "/21", "batch/Pod burst"],
        ["customer-profile /19", "/22", "/23", "/24", "중간 API/data"],
        ["internal-admin /20", "/23", "/24", "/25", "소형 3 AZ"],
    ], row_h=11 * mm, font_size=7)


def draw_migration(c: canvas.Canvas) -> None:
    page_base(c, 9, "08 · MIGRATION & SCALE", "주소 부족을 CIDR 확장 한 번으로 해결할 수 없으므로 병렬 이전 경로를 설계했습니다", "서비스 supernet의 reserve와 TGW route change를 이용한 blue/green VPC migration")
    steps = [
        ("01", "RESERVE", "IPAM에서 비중복 CIDR 승인", BLUE, SOFT_BLUE),
        ("02", "BUILD", "새 VPC·subnet·TGW attachment 병렬 생성", PURPLE, SOFT_PURPLE),
        ("03", "ROUTE", "return route·allowed route 추가", AMBER, SOFT_AMBER),
        ("04", "MIGRATE", "데이터 복제·DNS/traffic weight 전환", TEAL, SOFT_TEAL),
        ("05", "OBSERVE", "rollback 기간 동안 구·신 VPC 공존", CYAN, SOFT_CYAN),
        ("06", "RETIRE", "old route→attachment→VPC 제거·CIDR quarantine", RED, SOFT_RED),
    ]
    start_x = 13 * mm
    y = PAGE_H - 85 * mm
    card_w = 42 * mm
    gap = 5 * mm
    for index, (number, title, note, color, fill) in enumerate(steps):
        x = start_x + index * (card_w + gap)
        box(c, x, y, card_w, 35 * mm, f"{number} · {title}", [note], fill, color, status="runbook", title_size=8.2, body_size=6.7)
        if index < len(steps) - 1:
            arrow(c, x + card_w, y + 17.5 * mm, x + card_w + gap, y + 17.5 * mm, color=color)

    box(c, 16 * mm, 60 * mm, 126 * mm, 49 * mm, "IP exhaustion 대응 순서", [
        "1. 기존 reserve에서 subnet 추가",
        "2. AvailableIpAddressCount·CNI metrics로 조기 경보",
        "3. service supernet 안 secondary CIDR 또는 새 VPC",
        "4. 대규모 EKS는 IPv6 우선 검토",
    ], SOFT_TEAL, TEAL, status="설계 규칙")
    box(c, 155 * mm, 60 * mm, 126 * mm, 49 * mm, "겹치는 M&A / on-prem CIDR", [
        "TGW에 겹치는 prefix를 그대로 광고하지 않습니다.",
        "Private NAT · PrivateLink · VPC Lattice · 단계적 renumbering 중 dependency에 맞는 경로를 선택합니다.",
        "DNS·보안 정책과 rollback 기준을 함께 승인합니다.",
    ], SOFT_AMBER, AMBER, status="의사결정")
    box(c, 16 * mm, 18 * mm, 265 * mm, 25 * mm, "Migration gate", [
        "전환 전: route symmetry·security group·DNS·data lag·capacity 확인 · 전환 후: flow log·error rate·latency·dependency 0 확인 · CIDR은 즉시 재사용하지 않음",
    ], SOFT_GRAY, MUTED, status="운영 증적 필요")


def draw_evidence(c: canvas.Canvas) -> None:
    page_base(c, 10, "09 · EVIDENCE & NEXT GATE", "코드로 확인한 것과 AWS에서 아직 확인하지 않은 것을 분리합니다", "포트폴리오의 숫자는 무엇을 세었는지와 증명하지 않는 범위를 함께 읽어야 함")
    metric(c, 16 * mm, PAGE_H - 81 * mm, 61 * mm, "5", "서비스", "서로 다른 workload profile", TEAL, SOFT_TEAL)
    metric(c, 84 * mm, PAGE_H - 81 * mm, 61 * mm, "15", "서비스 VPC root", "5 services × dev/stg/prod", BLUE, SOFT_BLUE)
    metric(c, 152 * mm, PAGE_H - 81 * mm, 61 * mm, "18", "구현 모듈", "main.tf가 있는 reusable module", PURPLE, SOFT_PURPLE)
    metric(c, 220 * mm, PAGE_H - 81 * mm, 61 * mm, "28/28", "Terraform 검증", "등록된 validate 대상 전체", AMBER, SOFT_AMBER)

    box(c, 16 * mm, 72 * mm, 126 * mm, 55 * mm, "현재 확인된 evidence", [
        "Terraform fmt 및 28개 대상 validate 통과",
        "15개 VPC CIDR의 enterprise/service pool 포함 확인",
        "15개 VPC 상호 overlap 없음",
        "AZ별 5개 subnet tier 계산과 overlap 없음",
        "draw.io 6페이지와 Terraform 값 동기화",
    ], SOFT_TEAL, TEAL, status="검증 완료")
    box(c, 155 * mm, 72 * mm, 126 * mm, 55 * mm, "아직 필요한 deployment evidence", [
        "실제 account ID·RAM principal·TGW/attachment ID",
        "AWS provider plan과 designated approver",
        "Inspection/Shared Services 실제 attachment",
        "route symmetry·DNS·throughput·failover 시험",
        "비용 추정·Flow Logs·운영 dashboard",
    ], SOFT_AMBER, AMBER, dashed=True, status="배포 입력")

    table(c, 16 * mm, 68 * mm, [63 * mm, 66 * mm, 69 * mm, 76 * mm], ["NEXT GATE", "OWNER", "INPUT", "PASS CONDITION"], [
        ["1 · account binding", "Governance / Security", "account IDs·RAM principals", "OU/SCP/permission set 확인"],
        ["2 · plan", "CI/CD / Terraform", "backend·provider role·TGW ID", "reviewed plan artifact"],
        ["3 · connectivity test", "Network / Operations", "test endpoints·DNS", "양방향 route·latency·failure 확인"],
    ], row_h=8.5 * mm, font_size=6.3)
    c.setFont("Portfolio", 8)
    c.setFillColor(INK)
    c.drawString(16 * mm, 27 * mm, "Primary artifacts")
    draw_wrapped(c, "terraform/landing-zone · terraform/services · terraform/modules/service-vpc · docs/service-network-architecture.md · terraform/diagrams/aws-infrastructure.drawio", 16 * mm, 22 * mm, 265 * mm, 6.8, 9, MUTED, 2)


def build() -> Path:
    register_font()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    c.setTitle("Enterprise Service Landing Zone Architecture")
    c.setAuthor("Cloud Portfolio")
    pages = [
        draw_cover,
        draw_repository,
        draw_topology,
        draw_ipam,
        draw_sizing,
        draw_routing,
        draw_commerce,
        draw_subnet_policy,
        draw_migration,
        draw_evidence,
    ]
    for draw in pages:
        draw(c)
        c.showPage()
    c.save()
    return OUTPUT


if __name__ == "__main__":
    path = build()
    print(path)
