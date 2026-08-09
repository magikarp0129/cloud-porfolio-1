#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../lib/common.sh
source "${script_dir}/../../lib/common.sh"

line_limit=120
output_file=""

usage() {
  cat <<'EOF'
Usage: patch-readiness.sh [options]

Inspect cached package metadata, available updates, and reboot indicators.
The script does not refresh repositories, install packages, or reboot Linux.

Options:
  --lines COUNT          Maximum package lines to print (default: 120).
  --output FILE          Save the report while also printing it.
  -h, --help             Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --lines)
      [[ $# -ge 2 ]] || ops_die "--lines requires a value"
      line_limit="$2"
      shift 2
      ;;
    --output)
      [[ $# -ge 2 ]] || ops_die "--output requires a value"
      output_file="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      ops_die "unknown argument: $1"
      ;;
  esac
done

ops_require_linux
ops_require_positive_integer "$line_limit" "line count"
(( line_limit <= 2000 )) || ops_die "line count must not exceed 2000"
ops_validate_output_file "$output_file"

print_limited() {
  sed -n "1,${line_limit}p"
}

report_apt() {
  local updates
  updates="$(apt list --upgradable 2>/dev/null || true)"
  printf 'package_manager: apt\n'
  printf 'metadata_policy: local cache only; no apt update was executed\n'
  printf '%s\n' "$updates" | print_limited
  printf 'available_update_count: %s\n' "$(printf '%s\n' "$updates" | awk 'NR > 1 && /upgradable/ {count++} END {print count + 0}')"
  printf 'security_update_count: %s\n' "$(printf '%s\n' "$updates" | awk 'NR > 1 && /security/ {count++} END {print count + 0}')"
}

report_dnf() {
  local updates security_updates status
  set +e
  updates="$(dnf -q --cacheonly check-update 2>&1)"
  status=$?
  set -e
  [[ $status -eq 0 || $status -eq 100 ]] || ops_log "dnf check-update returned status ${status}"
  security_updates="$(dnf -q --cacheonly updateinfo list security updates 2>&1 || true)"
  printf 'package_manager: dnf\n'
  printf 'metadata_policy: local cache only; no metadata refresh was executed\n'
  printf '%s\n' "$updates" | print_limited
  ops_section "Cached security advisories"
  printf '%s\n' "$security_updates" | print_limited
}

report_yum() {
  local updates status
  set +e
  updates="$(yum -q --cacheonly check-update 2>&1)"
  status=$?
  set -e
  [[ $status -eq 0 || $status -eq 100 ]] || ops_log "yum check-update returned status ${status}"
  printf 'package_manager: yum\n'
  printf 'metadata_policy: local cache only; no metadata refresh was executed\n'
  printf '%s\n' "$updates" | print_limited
  ops_section "Cached security advisories"
  yum -q --cacheonly updateinfo list security updates 2>&1 | print_limited || true
}

report_zypper() {
  printf 'package_manager: zypper\n'
  printf 'metadata_policy: local cache only; no repository refresh was executed\n'
  zypper --non-interactive --no-refresh list-updates 2>&1 | print_limited || true
}

collect_report() {
  printf '# Linux patch readiness report\n'
  printf 'data_classification: internal\n'
  printf 'generated_at_utc: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  printf 'host: %s\n' "$(hostname -f 2>/dev/null || hostname)"

  ops_section "Available updates from cached metadata"
  if command -v apt >/dev/null 2>&1; then
    report_apt
  elif command -v dnf >/dev/null 2>&1; then
    report_dnf
  elif command -v yum >/dev/null 2>&1; then
    report_yum
  elif command -v zypper >/dev/null 2>&1; then
    report_zypper
  else
    ops_die "supported package manager not found: apt, dnf, yum, or zypper"
  fi

  ops_section "Reboot indicators"
  if [[ -f /var/run/reboot-required ]]; then
    printf 'reboot_required: true\n'
    [[ -r /var/run/reboot-required.pkgs ]] && sed -n "1,${line_limit}p" /var/run/reboot-required.pkgs
  elif command -v needs-restarting >/dev/null 2>&1; then
    if needs-restarting -r >/dev/null 2>&1; then
      printf 'reboot_required: false\n'
    else
      printf 'reboot_required: true\n'
    fi
  else
    printf 'reboot_required: unknown\n'
    printf 'reason: no distribution-specific reboot indicator is available\n'
  fi

  ops_section "Operator gate"
  printf 'Review package provenance, maintenance window, backup state, service redundancy, and rollback plan before patching.\n'
}

ops_emit_report "$output_file" collect_report
