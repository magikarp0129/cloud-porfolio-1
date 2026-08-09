#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../lib/common.sh
source "${script_dir}/../../lib/common.sh"

service_name=""
since="2 hours ago"
line_limit=200
output_file=""

usage() {
  cat <<'EOF'
Usage: service-triage.sh --service NAME [options]

Collect read-only systemd service status, process information, sockets, and
journal evidence. The script never restarts or changes the service.

Options:
  --service NAME         systemd unit name to inspect.
  --since VALUE          journalctl time range (default: 2 hours ago).
  --lines COUNT          Maximum journal lines (default: 200).
  --output FILE          Save the report while also printing it.
  -h, --help             Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --service)
      [[ $# -ge 2 ]] || ops_die "--service requires a value"
      service_name="$2"
      shift 2
      ;;
    --since)
      [[ $# -ge 2 ]] || ops_die "--since requires a value"
      since="$2"
      shift 2
      ;;
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
ops_require_command systemctl
ops_require_command journalctl
[[ -n "$service_name" ]] || ops_die "--service is required"
[[ "$service_name" =~ ^[A-Za-z0-9@_.:-]+$ ]] || ops_die "service name contains unsupported characters"
ops_require_positive_integer "$line_limit" "line count"
(( line_limit <= 2000 )) || ops_die "line count must not exceed 2000"
ops_validate_output_file "$output_file"

collect_report() {
  local main_pid

  printf '# systemd service triage report\n'
  printf 'data_classification: confidential\n'
  printf 'generated_at_utc: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  printf 'host: %s\n' "$(hostname -f 2>/dev/null || hostname)"
  printf 'service: %s\n' "$service_name"

  ops_section "Unit state"
  systemctl show "$service_name" --no-pager \
    --property=Id,LoadState,ActiveState,SubState,UnitFileState,MainPID,ExecMainCode,ExecMainStatus,Result,RestartUSec 2>&1 || true

  ops_section "Status"
  systemctl status "$service_name" --no-pager --full 2>&1 || true

  main_pid="$(systemctl show "$service_name" --property=MainPID --value 2>/dev/null || true)"
  if [[ "$main_pid" =~ ^[0-9]+$ ]] && (( main_pid > 0 )); then
    ops_section "Main process"
    ps -p "$main_pid" -o pid,ppid,user,%cpu,%mem,stat,etimes,lstart,comm 2>&1 || true

    if [[ -r "/proc/${main_pid}/status" ]]; then
      ops_section "Process limits and memory state"
      awk '/^(Name|State|Threads|VmPeak|VmSize|VmRSS|VmSwap|FDSize|voluntary_ctxt_switches|nonvoluntary_ctxt_switches):/ {print}' "/proc/${main_pid}/status" || true
    fi

    if command -v ss >/dev/null 2>&1; then
      ops_section "Sockets associated with the main process"
      ss -lntp 2>/dev/null | grep "pid=${main_pid}," || printf 'no visible listening TCP socket for pid %s\n' "$main_pid"
    fi
  else
    ops_section "Main process"
    printf 'no running MainPID reported by systemd\n'
  fi

  ops_section "Recent journal evidence"
  journalctl --unit "$service_name" --since "$since" -n "$line_limit" --no-pager --output=short-iso 2>&1 || true
}

ops_emit_report "$output_file" collect_report
