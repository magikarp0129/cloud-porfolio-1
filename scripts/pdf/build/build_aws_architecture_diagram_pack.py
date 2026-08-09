#!/usr/bin/env python3

"""Build a vector AWS network architecture diagram pack from repository facts."""

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / ".pdf-tools"))

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


OUTPUT = REPO_ROOT / "aws-architecture-diagram-pack.pdf"
FONT_PATH = Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf")

PAGE_W, PAGE_H = landscape(A4)
INK = colors.HexColor("#17212B")
MUTED = colors.HexColor("#596672")
LINE = colors.HexColor("#CDD6DD")
PAPER = colors.HexColor("#FBFCFD")
WHITE = colors.white
TEAL = colors.HexColor("#087E8B")
BLUE = colors.HexColor("#2867B2")
GREEN = colors.HexColor("#347A57")
AMBER = colors.HexColor("#C47B18")
RED = colors.HexColor("#B64545")
PURPLE = colors.HexColor("#6A4FA3")
SOFT_BLUE = colors.HexColor("#EAF2F8")
SOFT_TEAL = colors.HexColor("#E7F2F2")
SOFT_GREEN = colors.HexColor("#EAF3ED")
SOFT_AMBER = colors.HexColor("#F8F0E3")
SOFT_RED = colors.HexColor("#F8EDED")
SOFT_GRAY = colors.HexColor("#F0F3F5")


ENVIRONMENTS = {
    "dev": {
        "vpc": "10.10.0.0/16",
        "azs": 2,
        "public": ["10.10.0.0/24", "10.10.1.0/24"],
        "app": ["10.10.10.0/24", "10.10.11.0/24"],
        "db": ["10.10.20.0/24", "10.10.21.0/24"],
        "nat": "없음",
        "endpoints": "S3 Gateway만",
        "endpoint_summary": "S3 Gateway endpoint",
        "accent": TEAL,
        "soft": SOFT_TEAL,
        "status": "구현",
        "note": "비용 최소화 구성. NAT와 interface endpoint가 없어 EKS node/workload의 AWS API·image pull egress를 실환경에서 확인해야 한다.",
    },
    "stg": {
        "vpc": "10.15.0.0/16",
        "azs": 2,
        "public": ["10.15.0.0/24", "10.15.1.0/24"],
        "app": ["10.15.10.0/24", "10.15.11.0/24"],
        "db": ["10.15.20.0/24", "10.15.21.0/24"],
        "nat": "첫 AZ에 1개",
        "endpoints": "ECR API/DKR · Logs · SSM · SSMMessages · S3",
        "endpoint_summary": "5 interface + S3 Gateway",
        "accent": BLUE,
        "soft": SOFT_BLUE,
        "status": "구현",
        "note": "비용과 운영 검증의 균형. 두 번째 AZ의 internet egress가 첫 AZ NAT를 사용하므로 cross-AZ 의존성과 비용을 감수한다.",
    },
    "prod": {
        "vpc": "10.20.0.0/16",
        "azs": 3,
        "public": ["10.20.0.0/24", "10.20.1.0/24", "10.20.2.0/24"],
        "app": ["10.20.10.0/24", "10.20.11.0/24", "10.20.12.0/24"],
        "db": ["10.20.20.0/24", "10.20.21.0/24", "10.20.22.0/24"],
        "nat": "AZ마다 1개",
        "endpoints": "ECR API/DKR · EC2 · Logs · Monitoring · SSM · SSMMessages · STS · S3",
        "endpoint_summary": "8 interface + S3 Gateway",
        "accent": GREEN,
        "soft": SOFT_GREEN,
        "status": "구현",
        "note": "3개 AZ와 AZ별 NAT로 가용성을 우선한다. DB route table에는 NAT/IGW default route가 없고, EKS는 private app subnet을 사용한다.",
    },
}


def register_font():
    if not FONT_PATH.exists():
        raise FileNotFoundError(f"Korean font not found: {FONT_PATH}")
    pdfmetrics.registerFont(TTFont("Diagram", str(FONT_PATH)))


def width(text, size):
    return pdfmetrics.stringWidth(str(text), "Diagram", size)


def wrap(text, max_width, size):
    words = str(text).split()
    if not words:
        return []
    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if width(candidate, size) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def text_block(c, text, x, y, max_width, size=8, leading=11, color=INK, max_lines=None):
    lines = wrap(text, max_width, size)
    if max_lines is not None:
        lines = lines[:max_lines]
    c.setFont("Diagram", size)
    c.setFillColor(color)
    for index, line in enumerate(lines):
        c.drawString(x, y - index * leading, line)
    return y - len(lines) * leading


def page_base(c, page, kicker, title, status=None):
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setFillColor(TEAL)
    c.rect(0, PAGE_H - 5 * mm, PAGE_W, 5 * mm, stroke=0, fill=1)
    c.setFont("Diagram", 7.5)
    c.setFillColor(TEAL)
    c.drawString(18 * mm, PAGE_H - 16 * mm, kicker)
    c.setFont("Diagram", 22)
    c.setFillColor(INK)
    c.drawString(18 * mm, PAGE_H - 28 * mm, title)
    c.setStrokeColor(LINE)
    c.line(18 * mm, 13 * mm, PAGE_W - 18 * mm, 13 * mm)
    c.setFont("Diagram", 7)
    c.setFillColor(MUTED)
    c.drawString(18 * mm, 8 * mm, "AWS 네트워크 아키텍처 구성도 · repository evidence 기준")
    c.drawRightString(PAGE_W - 18 * mm, 8 * mm, f"{page:02d} / 08")
    if status:
        badge(c, PAGE_W - 54 * mm, PAGE_H - 24 * mm, 35 * mm, 8 * mm, status, TEAL, SOFT_TEAL)


def badge(c, x, y, w, h, label, stroke=TEAL, fill=SOFT_TEAL):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.roundRect(x, y, w, h, h / 2, stroke=1, fill=1)
    c.setFont("Diagram", 7)
    c.setFillColor(stroke)
    c.drawCentredString(x + w / 2, y + h / 2 - 2.4, label)


def box(c, x, y, w, h, title, lines=None, fill=WHITE, stroke=LINE, dashed=False,
        title_color=INK, status=None, center=False, radius=5):
    c.saveState()
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(1)
    if dashed:
        c.setDash(5, 3)
    c.roundRect(x, y, w, h, radius, stroke=1, fill=1)
    c.restoreState()
    c.setFont("Diagram", 10)
    c.setFillColor(title_color)
    if center:
        c.drawCentredString(x + w / 2, y + h - 15, title)
    else:
        c.drawString(x + 10, y + h - 15, title)
    if status:
        status_color = GREEN if status == "구현" else AMBER
        status_fill = SOFT_GREEN if status == "구현" else SOFT_AMBER
        badge(c, x + w - 47, y + h - 21, 38, 13, status, status_color, status_fill)
    if lines:
        cursor = y + h - 31
        for item in lines:
            cursor = text_block(c, item, x + 10, cursor, w - 20, 7.5, 10.5, MUTED) - 1


def arrow(c, x1, y1, x2, y2, label=None, color=TEAL, dashed=False, label_dx=0, label_dy=0):
    c.saveState()
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(1.5)
    if dashed:
        c.setDash(5, 3)
    c.line(x1, y1, x2, y2)
    import math
    angle = math.atan2(y2 - y1, x2 - x1)
    length = 7
    for delta in (2.6, -2.6):
        c.line(
            x2,
            y2,
            x2 - length * math.cos(angle + delta),
            y2 - length * math.sin(angle + delta),
        )
    c.restoreState()
    if label:
        size = 6.8
        label_w = width(label, size) + 8
        lx = (x1 + x2) / 2 - label_w / 2 + label_dx
        ly = (y1 + y2) / 2 - 4 + label_dy
        c.setFillColor(PAPER)
        c.rect(lx, ly - 1, label_w, 10, stroke=0, fill=1)
        c.setFont("Diagram", size)
        c.setFillColor(color)
        c.drawCentredString(lx + label_w / 2, ly + 1, label)


def line_arrow(c, points, label=None, color=TEAL, dashed=False):
    for idx in range(len(points) - 1):
        x1, y1 = points[idx]
        x2, y2 = points[idx + 1]
        if idx == len(points) - 2:
            arrow(c, x1, y1, x2, y2, label=label, color=color, dashed=dashed)
        else:
            c.saveState()
            c.setStrokeColor(color)
            c.setLineWidth(1.5)
            if dashed:
                c.setDash(5, 3)
            c.line(x1, y1, x2, y2)
            c.restoreState()


def legend(c, x, y):
    items = [
        (GREEN, SOFT_GREEN, False, "현재 Terraform 구현"),
        (BLUE, SOFT_BLUE, False, "문서화된 설계"),
        (AMBER, SOFT_AMBER, True, "목표/Backlog · 미구현"),
    ]
    cursor = x
    for stroke, fill, dashed, label in items:
        c.saveState()
        c.setFillColor(fill)
        c.setStrokeColor(stroke)
        if dashed:
            c.setDash(4, 2)
        c.roundRect(cursor, y, 18, 10, 3, stroke=1, fill=1)
        c.restoreState()
        c.setFont("Diagram", 7)
        c.setFillColor(MUTED)
        c.drawString(cursor + 23, y + 1.5, label)
        cursor += 120


def cover(c):
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setFillColor(TEAL)
    c.rect(0, 0, 9 * mm, PAGE_H, stroke=0, fill=1)
    c.setFillColor(SOFT_TEAL)
    c.rect(PAGE_W - 85 * mm, 0, 85 * mm, PAGE_H, stroke=0, fill=1)
    c.setFont("Diagram", 8)
    c.setFillColor(TEAL)
    c.drawString(27 * mm, PAGE_H - 37 * mm, "AWS ARCHITECTURE DIAGRAM PACK · CURRENT CODE + TARGET LANDING ZONE")
    c.setFont("Diagram", 31)
    c.setFillColor(INK)
    c.drawString(27 * mm, PAGE_H - 57 * mm, "AWS 네트워크 아키텍처 구성도")
    c.setFont("Diagram", 13)
    c.setFillColor(MUTED)
    c.drawString(27 * mm, PAGE_H - 70 * mm, "계정 · TGW · VPC CIDR · AZ · Subnet · Routing · EKS 통신 경계")
    box(
        c, 27 * mm, 61 * mm, 155 * mm, 44 * mm,
        "이 구성도가 구분하는 것",
        [
            "실선 녹색: 현재 Terraform에 resource와 값이 존재",
            "실선 파란색: 문서에 정의된 설계 원칙",
            "점선 주황색: account ID·TGW·inspection 확정 후 구현할 목표 구조",
        ],
        fill=WHITE, stroke=LINE,
    )
    legend(c, 27 * mm, 48 * mm)
    c.setFont("Diagram", 8)
    c.setFillColor(MUTED)
    c.drawString(27 * mm, 26 * mm, "근거: terraform/environments · terraform/modules/network · terraform/organization · docs/architecture.md · docs/security-review.md")
    c.setFont("Diagram", 8)
    c.setFillColor(TEAL)
    c.drawRightString(PAGE_W - 20 * mm, 18 * mm, "2026-08-08")
    c.showPage()


def account_page(c):
    page_base(c, 2, "01 · LANDING ZONE AND ACCOUNT BOUNDARY", "AWS Organizations와 계정 배치", "현행 OU + 목표 계정")
    legend(c, 18 * mm, PAGE_H - 40 * mm)
    x0 = 18 * mm
    box(c, x0 + 75 * mm, 132 * mm, 110 * mm, 23 * mm, "Management Account", ["AWS Organizations · IAM Identity Center"], SOFT_BLUE, BLUE, status="문서화")
    ou_y = 89 * mm
    ou_w = 57 * mm
    gap = 7 * mm
    ous = [
        ("Security OU", ["목표 account: Identity", "Log Archive · Security tooling"], BLUE, SOFT_BLUE),
        ("Infrastructure OU", ["목표 account: Network / TGW", "AI Platform · CI/CD"], BLUE, SOFT_BLUE),
        ("Workloads OU", ["Dev OU", "Stg OU", "Prod OU"], GREEN, SOFT_GREEN),
        ("Sandbox / Policy-Staging", ["실험", "SCP 승격 시험"], GREEN, SOFT_GREEN),
    ]
    centers = []
    for i, (title, lines, stroke, fill) in enumerate(ous):
        x = x0 + i * (ou_w + gap)
        box(c, x, ou_y, ou_w, 30 * mm, title, lines, fill, stroke, status="구현")
        centers.append(x + ou_w / 2)
        line_arrow(c, [(x0 + 130 * mm, 132 * mm), (x0 + 130 * mm, 124 * mm), (x + ou_w / 2, 124 * mm), (x + ou_w / 2, ou_y + 30 * mm)], color=BLUE)

    acct_y = 45 * mm
    acct_w = 48 * mm
    workload_center = centers[2]
    workload_x = workload_center - (3 * acct_w + 2 * 5 * mm) / 2
    accounts = [
        ("Dev workload", "10.10.0.0/16"),
        ("Stg workload", "10.15.0.0/16"),
        ("Prod workload", "10.20.0.0/16"),
    ]
    for i, (name, cidr) in enumerate(accounts):
        x = workload_x + i * (acct_w + 5 * mm)
        box(c, x, acct_y, acct_w, 24 * mm, name, [cidr, "account ID 미지정"], WHITE, GREEN, dashed=True, status="목표")
        line_arrow(c, [(workload_center, ou_y), (workload_center, 76 * mm), (x + acct_w / 2, 76 * mm), (x + acct_w / 2, acct_y + 24 * mm)], color=AMBER, dashed=True)

    box(c, 18 * mm, 20 * mm, 248 * mm, 16 * mm, "해석", ["OU와 SCP는 구현되어 있지만 member account 생성·배치와 account ID는 아직 Terraform 입력으로 확정되지 않았다. 환경 3은 현재 논리 root 수이며 실제 계정 3개 운영 완료를 뜻하지 않는다."], SOFT_AMBER, AMBER)
    c.showPage()


def tgw_page(c):
    page_base(c, 3, "02 · CROSS-ACCOUNT CONNECTIVITY", "Landing Zone Transit Gateway 목표 구조", "TGW 미구현")
    legend(c, 18 * mm, PAGE_H - 40 * mm)
    cx, cy = PAGE_W / 2, PAGE_H / 2 - 3 * mm
    box(c, cx - 30 * mm, cy - 15 * mm, 60 * mm, 30 * mm, "Transit Gateway", ["Network account 소유", "route table 분리"], SOFT_AMBER, AMBER, dashed=True, status="목표", center=True)
    nodes = [
        (24 * mm, 102 * mm, 53 * mm, 29 * mm, "Inspection VPC", ["CIDR TBD", "AZ별 inspection subnet", "Network Firewall/UTM · appliance mode"], AMBER, SOFT_AMBER, True),
        (24 * mm, 45 * mm, 53 * mm, 27 * mm, "Shared Services", ["DNS · package mirror", "central endpoints"], AMBER, SOFT_AMBER, True),
        (218 * mm, 105 * mm, 51 * mm, 25 * mm, "Dev VPC", ["10.10.0.0/16"], GREEN, SOFT_GREEN, False),
        (218 * mm, 70 * mm, 51 * mm, 25 * mm, "Stg VPC", ["10.15.0.0/16"], GREEN, SOFT_GREEN, False),
        (218 * mm, 35 * mm, 51 * mm, 25 * mm, "Prod VPC", ["10.20.0.0/16"], GREEN, SOFT_GREEN, False),
        (115 * mm, 23 * mm, 64 * mm, 24 * mm, "Security / Log Archive", ["중앙 audit · long-term log"], AMBER, SOFT_AMBER, True),
        (108 * mm, 139 * mm, 78 * mm, 20 * mm, "AI Platform / Tool Broker", ["Private Gateway · read-only role"], AMBER, SOFT_AMBER, True),
    ]
    for x, y, w, h, title, lines, stroke, fill, dashed in nodes:
        status = "구현" if "VPC" in title and title not in ("Inspection VPC",) else "목표"
        box(c, x, y, w, h, title, lines, fill, stroke, dashed=dashed, status=status)
        nx, ny = x + w / 2, y + h / 2
        if nx < cx - 30 * mm:
            arrow(c, x + w, ny, cx - 30 * mm, cy, color=AMBER, dashed=True)
        elif nx > cx + 30 * mm:
            arrow(c, x, ny, cx + 30 * mm, cy, color=AMBER, dashed=True)
        elif ny > cy:
            arrow(c, nx, y, cx, cy + 15 * mm, color=AMBER, dashed=True)
        else:
            arrow(c, nx, y + h, cx, cy - 15 * mm, color=AMBER, dashed=True)

    box(c, 86 * mm, 55 * mm, 44 * mm, 17 * mm, "route-policy 모듈", ["TGW route 입력 지원"], SOFT_GREEN, GREEN, status="구현")
    arrow(c, 130 * mm, 63 * mm, cx - 30 * mm, cy - 4 * mm, "route만", GREEN, dashed=False)
    box(c, 18 * mm, 17 * mm, 72 * mm, 21 * mm, "현재 코드의 정확한 경계", ["TGW resource·attachment·route table은 없음. Network account와 Inspection VPC CIDR도 TBD."], SOFT_RED, RED)
    box(c, 196 * mm, 17 * mm, 73 * mm, 21 * mm, "권장 통신 원칙", ["환경 간 기본 차단. 승인된 prefix만 propagation. inspection egress와 east-west를 route table로 분리."], SOFT_BLUE, BLUE)
    c.showPage()


def ip_plan_page(c):
    page_base(c, 4, "03 · IP ADDRESS PLAN", "VPC·AZ·Subnet 주소 계획", "현재 코드 계산값")
    legend(c, 18 * mm, PAGE_H - 40 * mm)
    columns = [23, 31, 15, 48, 48, 48, 42]
    scale = mm
    x = 12 * mm
    y_top = 122 * mm
    headers = ["환경", "VPC CIDR", "AZ", "Public /24", "Private App /24", "Private DB /24", "NAT"]
    row_h = 27 * mm
    header_h = 11 * mm
    total_w = sum(columns) * mm
    c.setFillColor(INK)
    c.rect(x, y_top - header_h, total_w, header_h, stroke=0, fill=1)
    cursor = x
    for label, col in zip(headers, columns):
        c.setFont("Diagram", 7)
        c.setFillColor(WHITE)
        c.drawString(cursor + 5, y_top - 7.4 * mm, label)
        cursor += col * mm
    y = y_top - header_h
    for env_name in ("dev", "stg", "prod"):
        env = ENVIRONMENTS[env_name]
        cursor = x
        c.setFillColor(env["soft"])
        c.rect(x, y - row_h, total_w, row_h, stroke=0, fill=1)
        c.setStrokeColor(LINE)
        c.rect(x, y - row_h, total_w, row_h, stroke=1, fill=0)
        values = [
            env_name.upper(), env["vpc"], f"{env['azs']}개",
            "\n".join(env["public"]), "\n".join(env["app"]), "\n".join(env["db"]), env["nat"],
        ]
        for value, col in zip(values, columns):
            c.setStrokeColor(LINE)
            c.line(cursor, y, cursor, y - row_h)
            c.setFont("Diagram", 7.3)
            c.setFillColor(INK)
            lines = str(value).split("\n")
            for idx, line in enumerate(lines):
                c.drawString(cursor + 5, y - 10 - idx * 11, line)
            cursor += col * mm
        c.line(x + total_w, y, x + total_w, y - row_h)
        y -= row_h

    box(c, 12 * mm, 18 * mm, 88 * mm, 22 * mm, "Subnet 계산 규칙", ["cidrsubnet(VPC /16, newbits=8, index). Public=0~2, App=10~12, DB=20~22 → 모두 /24."], SOFT_GREEN, GREEN, status="구현")
    box(c, 105 * mm, 18 * mm, 82 * mm, 22 * mm, "AZ 선택 규칙", ["data.aws_availability_zones의 첫 N개 이름을 사용. dev/stg=2, prod=3. 명시적 2a/2b/2c pin은 아님."], SOFT_AMBER, AMBER, status="주의")
    box(c, 192 * mm, 18 * mm, 93 * mm, 22 * mm, "Production 권장 보완", ["계정마다 AZ 이름의 물리 zone 매핑이 달라질 수 있으므로 cross-account 설계에는 AZ ID 기준 pinning을 검토."], SOFT_BLUE, BLUE, status="권장")
    c.showPage()


def vpc_page(c, page, env_name):
    env = ENVIRONMENTS[env_name]
    page_base(c, page, f"04 · {env_name.upper()} VPC DETAIL", f"{env_name.upper()} VPC · AZ와 Subnet 상세", f"{env['vpc']} · {env['azs']} AZ")
    accent = env["accent"]
    soft = env["soft"]
    left = 17 * mm
    bottom = 32 * mm
    vpc_w = 264 * mm
    vpc_h = 98 * mm
    c.setFillColor(WHITE)
    c.setStrokeColor(accent)
    c.setLineWidth(1.4)
    c.roundRect(left, bottom, vpc_w, vpc_h, 8, stroke=1, fill=1)
    c.setFont("Diagram", 8)
    c.setFillColor(accent)
    c.drawString(left + 8, bottom + vpc_h - 13, f"VPC {env['vpc']} · DNS support/hostnames enabled · public IP auto-assign false")

    az_gap = 5 * mm
    inner_x = left + 8
    inner_y = bottom + 22 * mm
    inner_w = vpc_w - 16
    az_w = (inner_w - (env["azs"] - 1) * az_gap) / env["azs"]
    az_h = 67 * mm
    for index in range(env["azs"]):
        x = inner_x + index * (az_w + az_gap)
        c.setFillColor(SOFT_GRAY)
        c.setStrokeColor(LINE)
        c.roundRect(x, inner_y, az_w, az_h, 5, stroke=1, fill=1)
        c.setFont("Diagram", 7.5)
        c.setFillColor(MUTED)
        c.drawString(x + 7, inner_y + az_h - 12, f"AZ-{index + 1} · provider가 반환한 {index + 1}번째 available AZ")
        subnet_specs = [
            ("Public", env["public"][index], SOFT_BLUE, BLUE),
            ("Private App · EKS", env["app"][index], soft, accent),
            ("Private DB", env["db"][index], SOFT_AMBER, AMBER),
        ]
        sy = inner_y + az_h - 28
        for tier, cidr, fill, stroke in subnet_specs:
            c.setFillColor(fill)
            c.setStrokeColor(stroke)
            c.roundRect(x + 7, sy - 13, az_w - 14, 15, 4, stroke=1, fill=1)
            c.setFont("Diagram", 6.8)
            c.setFillColor(INK)
            c.drawString(x + 13, sy - 5, f"{tier}  {cidr}")
            sy -= 18
        if env_name == "prod" or (env_name == "stg" and index == 0):
            badge(c, x + az_w - 41, inner_y + 5, 34, 12, "NAT Gateway", GREEN, SOFT_GREEN)
        elif env_name == "stg":
            badge(c, x + az_w - 47, inner_y + 5, 40, 12, "NAT → AZ-1", AMBER, SOFT_AMBER)
        else:
            badge(c, x + az_w - 38, inner_y + 5, 31, 12, "NAT 없음", RED, SOFT_RED)

    box(c, left + 5, bottom + 2, 58 * mm, 18 * mm, "Internet Gateway", ["Public RT: 0.0.0.0/0"], SOFT_BLUE, BLUE, status="구현")
    box(c, left + 67 * mm, bottom + 2, 75 * mm, 18 * mm, "Private App routing", [f"Internet default: {env['nat']}"], soft, accent, status="구현")
    box(c, left + 146 * mm, bottom + 2, 55 * mm, 18 * mm, "Private DB routing", ["NAT/IGW default 없음"], SOFT_AMBER, AMBER, status="구현")
    box(c, left + 205 * mm, bottom + 2, 54 * mm, 18 * mm, "VPC endpoints", [env["endpoint_summary"]], SOFT_GREEN, GREEN, status="구현")
    box(c, 17 * mm, 16 * mm, 264 * mm, 13 * mm, "환경별 판단", [env["note"]], SOFT_GRAY, accent)
    c.showPage()


def traffic_page(c):
    page_base(c, 8, "05 · TRAFFIC PATHS AND IMPLEMENTATION GAPS", "주요 통신 흐름과 현재 구현 경계", "현행 + 목표 비교")
    legend(c, 18 * mm, PAGE_H - 40 * mm)
    flows = [
        (
            105 * mm,
            "A · 외부 ingress",
            [
                ("Internet", "외부 사용자", BLUE, SOFT_BLUE, False),
                ("WAF / ALB", "attachment 미구현", AMBER, SOFT_AMBER, True),
                ("EKS workload", "Private App subnet", GREEN, SOFT_GREEN, False),
            ],
            "목표: WAF/ALB에서 private workload로 전달. 현재 WAF module은 있으나 ingress resource와 attachment는 없다.",
        ),
        (
            73 * mm,
            "B · private egress",
            [
                ("EKS / App", "Private App", GREEN, SOFT_GREEN, False),
                ("VPC endpoint", "AWS service 우선", GREEN, SOFT_GREEN, False),
                ("NAT → IGW", "stg 1개 · prod AZ별", GREEN, SOFT_GREEN, False),
            ],
            "현행: S3 Gateway endpoint는 모든 환경. stg/prod는 interface endpoint와 NAT. dev는 NAT·interface endpoint가 없어 실환경 bootstrap 검증 필요.",
        ),
        (
            41 * mm,
            "C · account 간 east-west",
            [
                ("Source VPC", "승인 prefix", GREEN, SOFT_GREEN, False),
                ("TGW + Inspection", "route table / firewall", AMBER, SOFT_AMBER, True),
                ("Destination VPC", "환경 기본 격리", GREEN, SOFT_GREEN, False),
            ],
            "목표: Network account TGW와 Inspection VPC를 경유. 현재 route-policy가 TGW route를 받을 수 있지만 TGW·attachment·inspection은 미구현.",
        ),
    ]
    for y, label, nodes, note in flows:
        c.setFont("Diagram", 9)
        c.setFillColor(INK)
        c.drawString(18 * mm, y + 18 * mm, label)
        start_x = 18 * mm
        node_w = 47 * mm
        gap = 17 * mm
        for index, (title, subtitle, stroke, fill, dashed) in enumerate(nodes):
            x = start_x + index * (node_w + gap)
            box(c, x, y, node_w, 15 * mm, title, [subtitle], fill, stroke, dashed=dashed, status="목표" if dashed else "구현")
            if index:
                prev_x = start_x + (index - 1) * (node_w + gap)
                arrow(c, prev_x + node_w, y + 7.5 * mm, x, y + 7.5 * mm, color=AMBER if dashed else TEAL, dashed=dashed)
        box(c, 214 * mm, y, 69 * mm, 15 * mm, "해석", [note], SOFT_GRAY, LINE)

    box(c, 18 * mm, 15 * mm, 126 * mm, 18 * mm, "사람과 CI/CD의 private 접근", ["Corporate IdP → IAM Identity Center → short-lived role. Private EKS API는 VPN/DX/SSM-connected runner 또는 self-hosted runner 경로가 필요."], SOFT_BLUE, BLUE, status="문서화")
    box(c, 151 * mm, 15 * mm, 132 * mm, 18 * mm, "최종 PDF에 함께 표기할 것", ["각 화살표에 source/destination CIDR, route table owner, security control, 구현 상태, evidence 경로를 붙여 ‘그림=운영 완료’ 오해를 방지."], SOFT_AMBER, AMBER, status="원칙")
    c.showPage()


def build():
    register_font()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(
        str(OUTPUT),
        pagesize=landscape(A4),
        pageCompression=1,
        invariant=1,
        title="AWS 네트워크 아키텍처 구성도",
        author="클라우드 플랫폼 엔지니어링 포트폴리오",
        subject="AWS Organizations, Landing Zone, TGW, VPC, AZ, subnet and routing diagrams",
    )
    cover(c)
    account_page(c)
    tgw_page(c)
    ip_plan_page(c)
    vpc_page(c, 5, "dev")
    vpc_page(c, 6, "stg")
    vpc_page(c, 7, "prod")
    traffic_page(c)
    c.save()
    print(OUTPUT)


if __name__ == "__main__":
    build()
