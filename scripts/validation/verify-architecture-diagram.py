#!/usr/bin/env python3
"""Terraform 환경 값과 draw.io AWS 구성도의 동기화를 검증한다."""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DIAGRAM_PATH = REPOSITORY_ROOT / "terraform/diagrams/aws-infrastructure.drawio"
TREE_PATH = REPOSITORY_ROOT / "terraform/diagrams/aws-infrastructure-tree.md"
MERMAID_PATH = REPOSITORY_ROOT / "terraform/diagrams/aws-infrastructure-diagram.md"
EXPECTED_PAGES = [
    "01 조직과 환경 경계",
    "02 환경별 AWS 상세 구성",
    "03 EKS 플랫폼과 운영 흐름",
    "04 서비스 Landing Zone과 TGW",
    "05 서비스 IPAM과 VPC 크기",
    "06 서비스 VPC Subnet 상세",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assignment(text: str, key: str) -> str:
    pattern = rf'^\s*{re.escape(key)}\s*=\s*(?:"([^"]+)"|([0-9]+)|(true|false))\s*$'
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        raise ValueError(f"Terraform assignment not found: {key}")
    return next(value for value in match.groups() if value is not None)


def variable_default(text: str, variable_name: str) -> str:
    pattern = rf'variable\s+"{re.escape(variable_name)}"\s*\{{(?P<body>.*?)\n\}}'
    match = re.search(pattern, text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Terraform variable not found: {variable_name}")
    return assignment(match.group("body"), "default")


def bool_value(raw: str) -> bool:
    if raw not in {"true", "false"}:
        raise ValueError(f"Expected Terraform boolean, got: {raw}")
    return raw == "true"


def cell_text(root: ET.Element) -> str:
    return "\n".join(
        cell.attrib.get("value", "") for cell in root.findall(".//mxCell")
    )


def require(text: str, expected: str, errors: list[str], source: str) -> None:
    if expected not in text:
        errors.append(f"{source}에 Terraform 기준 문구가 없습니다: {expected}")


def verify_environment(
    environment: str,
    document_text: str,
    errors: list[str],
    source: str,
) -> None:
    root_dir = REPOSITORY_ROOT / "terraform/environments" / environment
    foundation = read(root_dir / "main.tf")
    variables = read(root_dir / "variables.tf")
    platform = read(root_dir / "platform/main.tf")

    vpc_cidr = assignment(foundation, "vpc_cidr")
    az_count = assignment(foundation, "az_count")
    control_days = assignment(foundation, "eks_control_plane_log_retention_days")
    container_days = assignment(foundation, "eks_container_log_retention_days")
    backup_days = assignment(foundation, "backup_retention_days")
    scheduler_enabled = bool_value(assignment(foundation, "enable_instance_scheduler"))
    vault_lock = bool_value(assignment(foundation, "enable_backup_vault_lock"))
    eks_version = variable_default(variables, "eks_cluster_version")
    prometheus_days = assignment(platform, "prometheus_retention").removesuffix("d")

    scheduler_label = "업무시간 Scheduler 사용" if scheduler_enabled else "Scheduler 미사용"

    for expected in (
        f"VPC {vpc_cidr} · {az_count} AZ",
        "Landing Zone TGW",
        f"EKS {eks_version}",
        f"Control/Container 로그 {control_days}/{container_days}일",
        f"Prometheus {prometheus_days}일 · Backup {backup_days}일",
        scheduler_label,
    ):
        require(document_text, expected, errors, source)

    if vault_lock:
        require(document_text, "Vault Lock", errors, source)


def main() -> int:
    errors: list[str] = []

    try:
        tree = ET.parse(DIAGRAM_PATH)
    except (FileNotFoundError, ET.ParseError) as exc:
        print(f"구성도 XML을 읽을 수 없습니다: {exc}", file=sys.stderr)
        return 1

    root = tree.getroot()
    if root.tag != "mxfile":
        errors.append(f"draw.io root element가 mxfile이 아닙니다: {root.tag}")

    diagrams = root.findall("diagram")
    page_names = [diagram.attrib.get("name", "") for diagram in diagrams]
    if page_names != EXPECTED_PAGES:
        errors.append(f"페이지 구성이 다릅니다: expected={EXPECTED_PAGES}, actual={page_names}")

    diagram_text = cell_text(root)
    try:
        tree_text = read(TREE_PATH)
    except FileNotFoundError as exc:
        print(f"Markdown 구성 트리를 읽을 수 없습니다: {exc}", file=sys.stderr)
        return 1

    try:
        mermaid_text = read(MERMAID_PATH)
    except FileNotFoundError as exc:
        print(f"Mermaid 구성도를 읽을 수 없습니다: {exc}", file=sys.stderr)
        return 1

    if tree_text.count("```") % 2 != 0:
        errors.append("Markdown 구성 트리의 fenced code block이 닫히지 않았습니다.")
    if mermaid_text.count("```") % 2 != 0:
        errors.append("Mermaid 구성도의 fenced code block이 닫히지 않았습니다.")
    if mermaid_text.count("```mermaid") != 7:
        errors.append("Mermaid 구성도는 7개의 다이어그램을 포함해야 합니다.")

    for source, document_text in (
        ("draw.io 구성도", diagram_text),
        ("Markdown 구성 트리", tree_text),
        ("Mermaid 구성도", mermaid_text),
    ):
        for environment in ("dev", "stg", "prod"):
            try:
                verify_environment(environment, document_text, errors, source)
            except ValueError as exc:
                errors.append(f"{environment} Terraform 파싱 실패: {exc}")

    for expected in (
        "AWS Organizations",
        "사설 API endpoint",
        "EKS Managed Add-on",
        "VPC CNI Pod Subnet",
        "AZ별 ENIConfig",
        "Agent의 prod 직접 apply 금지",
        "현재 환경 root에 없음",
        "현재 controller 미구현",
        "10.64.0.0/10",
        "Enterprise TGW",
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
        "Pod 10.65.0.0/19",
        "Node 10.65.128.0/20",
        "AP 10.65.176.0/21",
        "DB 10.65.200.0/22",
        "LB 10.65.212.0/22",
        "TGW 10.65.255.160/28",
        "EKS x-ENI 10.65.255.208/28",
    ):
        require(diagram_text, expected, errors, "draw.io 구성도")

    for expected in (
        "전체 구성",
        "환경 root의 공통 조립 구조",
        "환경별 차이",
        "네트워크 통신 트리",
        "EKS 구성과 상태 소유권",
        "관측·운영 흐름",
        "현재 구현이 아닌 항목",
        "aws_organizations_account",
        "VPC CNI custom networking",
        "desired_size",
    ):
        require(tree_text, expected, errors, "Markdown 구성 트리")

    for expected in (
        "flowchart TB",
        "flowchart LR",
        "AWS Organizations와 환경 경계",
        "환경별 VPC와 통신 흐름",
        "EKS 상태와 플랫폼 소유권",
        "관측·운영·변경 통제 흐름",
        "aws_organizations_account",
        "AWS Load Balancer Controller",
        "Agent의 prod 직접 apply 금지",
        "서비스 Landing Zone과 Transit Gateway",
        "IPAM과 서비스별 VPC 크기",
        "서비스 VPC의 AZ별 Subnet 예시",
        "10.64.0.0/10",
        "Enterprise TGW",
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
        "Pod 10.65.0.0/19",
        "Node 10.65.128.0/20",
        "EKS x-ENI 10.65.255.208/28",
    ):
        require(mermaid_text, expected, errors, "Mermaid 구성도")

    if errors:
        print("AWS 구성도 검증 실패:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"AWS 구성도 검증 완료: {DIAGRAM_PATH.relative_to(REPOSITORY_ROOT)}")
    print(f"- Mermaid: {MERMAID_PATH.relative_to(REPOSITORY_ROOT)}")
    print(f"- Markdown: {TREE_PATH.relative_to(REPOSITORY_ROOT)}")
    print(f"- 페이지: {len(diagrams)}")
    print("- Terraform 환경 값 동기화: dev, stg, prod")
    print("- 서비스 Landing Zone 동기화: 5 services, 15 VPCs, IPAM/TGW/subnet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
