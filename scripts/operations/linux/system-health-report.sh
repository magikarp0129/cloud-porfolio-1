#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../lib/common.sh
source "${script_dir}/../../lib/common.sh"

output_file=""
since="1 hour ago"
disk_warning=80
inode_warning=80

usage() {
  cat <<'EOF'
Usage: system-health-report.sh [options]

Collect a read-only Linux host health report. The script does not restart
services, install packages, or change system configuration.

Options:
  --output FILE          Save the report while also printing it.
  --since VALUE          journalctl time range (default: 1 hour ago).
  --disk-warning PCT     Disk usage warning threshold (default: 80).
  --inode-warning PCT    Inode usage warning threshold (default: 80).
  -h, --help             Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      [[ $# -ge 2 ]] || ops_die "--output requires a value"
      output_file="$2"
      shift 2
      ;;
    --since)
      [[ $# -ge 2 ]] || ops_die "--since requires a value"
      since="$2"
      shift 2
      ;;
    --disk-warning)
      [[ $# -ge 2 ]] || ops_die "--disk-warning requires a value"
      disk_warning="$2"
      shift 2
      ;;
    --inode-warning)
      [[ $# -ge 2 ]] || ops_die "--inode-warning requires a value"
      inode_warning="$2"
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
ops_require_command awk
ops_require_command df
ops_require_command ps
ops_require_positive_integer "$disk_warning" "disk warning threshold"
ops_require_positive_integer "$inode_warning" "inode warning threshold"
(( disk_warning <= 100 )) || ops_die "disk warning threshold must not exceed 100"
(( inode_warning <= 100 )) || ops_die "inode warning threshold must not exceed 100"
ops_validate_output_file "$output_file"

collect_report() {
  local host_name
  host_name="$(hostname -f 2>/dev/null || hostname)"

  printf '# Linux system health report\n'
  printf 'data_classification: internal\n'
  printf 'generated_at_utc: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  printf 'host: %s\n' "$host_name"
  printf 'kernel: %s\n' "$(uname -r)"

  ops_section "Operating system and uptime"
  if [[ -r /etc/os-release ]]; then
    awk -F= '/^(PRETTY_NAME|ID|VERSION_ID)=/ {gsub(/^"|"$/, "", $2); print $1 ": " $2}' /etc/os-release
  fi
  uptime || true

  ops_section "CPU and memory"
  if command -v nproc >/dev/null 2>&1; then
    printf 'logical_cpus: %s\n' "$(nproc)"
  fi
  if command -v free >/dev/null 2>&1; then
    free -m
  elif [[ -r /proc/meminfo ]]; then
    awk '/^(MemTotal|MemAvailable|SwapTotal|SwapFree):/ {print}' /proc/meminfo
  fi

  ops_section "Filesystem capacity"
  df -P -x tmpfs -x devtmpfs 2>/dev/null || df -P
  ops_section "Filesystem inode capacity"
  df -Pi -x tmpfs -x devtmpfs 2>/dev/null || df -Pi

  ops_section "Capacity warnings"
  df -P -x tmpfs -x devtmpfs 2>/dev/null | awk -v threshold="$disk_warning" '
    NR > 1 { usage=$5; gsub(/%/, "", usage); if (usage + 0 >= threshold) print "DISK_WARNING mount=" $6 " usage=" usage "%" }
  ' || true
  df -Pi -x tmpfs -x devtmpfs 2>/dev/null | awk -v threshold="$inode_warning" '
    NR > 1 { usage=$5; gsub(/%/, "", usage); if (usage + 0 >= threshold) print "INODE_WARNING mount=" $6 " usage=" usage "%" }
  ' || true

  ops_section "Top processes by CPU"
  ps -eo pid,ppid,user,%cpu,%mem,stat,etimes,comm --sort=-%cpu 2>/dev/null | sed -n '1,16p' || true

  ops_section "Failed systemd units"
  if command -v systemctl >/dev/null 2>&1; then
    systemctl --failed --no-legend --no-pager 2>&1 || true
  else
    printf 'systemctl is not installed\n'
  fi

  ops_section "Listening TCP sockets"
  if command -v ss >/dev/null 2>&1; then
    ss -lnt 2>&1 || true
  else
    printf 'ss is not installed\n'
  fi

  ops_section "Recent error-level journal entries"
  if command -v journalctl >/dev/null 2>&1; then
    journalctl --priority=err..alert --since "$since" --no-pager -n 100 --output=short-iso 2>&1 || true
  else
    printf 'journalctl is not installed\n'
  fi
}

ops_emit_report "$output_file" collect_report
