#!/usr/bin/env python3
"""Validate the enterprise service CIDR catalog and service Terraform roots."""

from __future__ import annotations

import ipaddress
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICES_ROOT = REPO_ROOT / "terraform" / "services"
IPAM_ROOT = REPO_ROOT / "terraform" / "landing-zone" / "ipam" / "main.tf"

ENTERPRISE_POOL = ipaddress.ip_network("10.64.0.0/10")
SERVICE_POOLS = {
    "commerce": ipaddress.ip_network("10.64.0.0/13"),
    "payments": ipaddress.ip_network("10.72.0.0/14"),
    "analytics": ipaddress.ip_network("10.76.0.0/14"),
    "customer-profile": ipaddress.ip_network("10.80.0.0/14"),
    "internal-admin": ipaddress.ip_network("10.84.0.0/16"),
}
EXPECTED = {
    "commerce": {
        "dev": "10.64.0.0/20",
        "stg": "10.64.32.0/19",
        "prod": "10.65.0.0/16",
    },
    "payments": {
        "dev": "10.72.0.0/22",
        "stg": "10.72.8.0/21",
        "prod": "10.73.0.0/18",
    },
    "analytics": {
        "dev": "10.76.0.0/20",
        "stg": "10.76.64.0/18",
        "prod": "10.77.0.0/16",
    },
    "customer-profile": {
        "dev": "10.80.0.0/22",
        "stg": "10.80.8.0/21",
        "prod": "10.81.0.0/19",
    },
    "internal-admin": {
        "dev": "10.84.0.0/22",
        "stg": "10.84.4.0/22",
        "prod": "10.84.16.0/20",
    },
}


def assignment(text: str, key: str) -> str:
    pattern = rf'^\s*{re.escape(key)}\s*=\s*(?:"([^"]+)"|([0-9]+)|(true|false))\s*$'
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        raise ValueError(f"Terraform assignment not found: {key}")
    return next(group for group in match.groups() if group is not None)


def subnet_layout(vpc: ipaddress.IPv4Network, az_count: int) -> dict[str, list[ipaddress.IPv4Network]]:
    by_newbits = {
        newbits: list(vpc.subnets(prefixlen_diff=newbits))
        for newbits in (3, 4, 5, 6)
    }

    fixed_28 = list(vpc.subnets(new_prefix=28))
    return {
        "pod": by_newbits[3][0:az_count],
        "node": by_newbits[4][8:8 + az_count],
        "ap": by_newbits[5][22:22 + az_count],
        "db": by_newbits[6][50:50 + az_count],
        "lb": by_newbits[6][53:53 + az_count],
        "tgw": fixed_28[-(2 * az_count):-az_count],
        "eks_cluster": fixed_28[-az_count:],
    }


def main() -> int:
    errors: list[str] = []
    discovered: list[tuple[str, str, ipaddress.IPv4Network]] = []
    ipam_text = IPAM_ROOT.read_text(encoding="utf-8")

    for service, environments in EXPECTED.items():
        pool = SERVICE_POOLS[service]
        if not pool.subnet_of(ENTERPRISE_POOL):
            errors.append(f"{service}: pool {pool} is outside {ENTERPRISE_POOL}")
        if str(pool) not in ipam_text:
            errors.append(f"{service}: IPAM root is missing service pool {pool}")

        for environment, expected_cidr in environments.items():
            path = SERVICES_ROOT / service / environment / "main.tf"
            if not path.exists():
                errors.append(f"missing service root: {path.relative_to(REPO_ROOT)}")
                continue
            text = path.read_text(encoding="utf-8")
            try:
                actual_service = assignment(text, "service_name")
                actual_environment = assignment(text, "environment")
                actual_cidr = assignment(text, "vpc_cidr")
                az_count = int(assignment(text, "az_count"))
            except ValueError as exc:
                errors.append(f"{path.relative_to(REPO_ROOT)}: {exc}")
                continue

            if actual_service != service or actual_environment != environment:
                errors.append(f"{path.relative_to(REPO_ROOT)}: service/environment labels do not match the path")
            if actual_cidr != expected_cidr:
                errors.append(f"{service}/{environment}: expected {expected_cidr}, got {actual_cidr}")
            if expected_cidr not in ipam_text:
                errors.append(f"{service}/{environment}: IPAM catalog is missing {expected_cidr}")

            network = ipaddress.ip_network(actual_cidr)
            if not network.subnet_of(pool):
                errors.append(f"{service}/{environment}: {network} is outside service pool {pool}")
            expected_azs = 3 if environment == "prod" else 2
            if az_count != expected_azs:
                errors.append(f"{service}/{environment}: expected {expected_azs} AZs, got {az_count}")
            expected_zone_ids = [f"apne2-az{index}" for index in range(1, expected_azs + 1)]
            if not all(zone_id in text for zone_id in expected_zone_ids):
                errors.append(f"{service}/{environment}: stable AZ IDs are missing or incomplete")
            if "enable_nat_gateway" in text or "one_nat_gateway_per_az" in text:
                errors.append(f"{service}/{environment}: workload VPC must not define an internet/NAT strategy")

            layout = subnet_layout(network, az_count)
            subnets = [subnet for tier in layout.values() for subnet in tier]
            for subnet in subnets:
                if not subnet.subnet_of(network):
                    errors.append(f"{service}/{environment}: subnet {subnet} is outside {network}")
            for index, subnet in enumerate(subnets):
                for other in subnets[index + 1:]:
                    if subnet.overlaps(other):
                        errors.append(f"{service}/{environment}: subnet overlap {subnet} and {other}")
            discovered.append((service, environment, network))

    for index, (service, environment, network) in enumerate(discovered):
        for other_service, other_environment, other_network in discovered[index + 1:]:
            if network.overlaps(other_network):
                errors.append(
                    f"VPC overlap: {service}/{environment} {network} and "
                    f"{other_service}/{other_environment} {other_network}"
                )

    if len(discovered) != 15:
        errors.append(f"expected 15 service environment roots, found {len(discovered)}")

    if errors:
        print("Service network plan verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Service network plan verification complete")
    print(f"- enterprise pool: {ENTERPRISE_POOL}")
    print(f"- service pools: {len(SERVICE_POOLS)}")
    print(f"- VPC roots: {len(discovered)}")
    print("- overlap: none")
    print("- subnet tiers per AZ: LB, AP, DB, EKS-node, VPC-CNI-Pod, TGW, EKS-cluster")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
