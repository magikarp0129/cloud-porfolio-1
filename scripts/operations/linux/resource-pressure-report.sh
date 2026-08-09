#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../lib/common.sh
source "${script_dir}/../../lib/common.sh"

output_file=""
since="2 hours ago"
sample_seconds=5
top_count=15
disk_warning=80
inode_warning=80
fd_warning=80

usage() {
  cat <<'EOF'
Usage: resource-pressure-report.sh [options]

Collect read-only CPU, memory, file descriptor, disk and I/O pressure evidence.
The script does not kill processes, drop caches, change limits or resize storage.

Options:
  --output FILE          Save the report while also printing it.
  --since VALUE          Kernel journal time range (default: 2 hours ago).
  --sample-seconds COUNT vmstat interval, 1-60 (default: 5).
  --top COUNT            Process rows, 1-100 (default: 15).
  --disk-warning PCT     Disk capacity warning threshold (default: 80).
  --inode-warning PCT    Inode capacity warning threshold (default: 80).
  --fd-warning PCT       File descriptor warning threshold (default: 80).
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
    --sample-seconds)
      [[ $# -ge 2 ]] || ops_die "--sample-seconds requires a value"
      sample_seconds="$2"
      shift 2
      ;;
    --top)
      [[ $# -ge 2 ]] || ops_die "--top requires a value"
      top_count="$2"
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
    --fd-warning)
      [[ $# -ge 2 ]] || ops_die "--fd-warning requires a value"
      fd_warning="$2"
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
ops_require_command sort
ops_require_positive_integer "$sample_seconds" "sample seconds"
ops_require_positive_integer "$top_count" "top count"
ops_require_positive_integer "$disk_warning" "disk warning threshold"
ops_require_positive_integer "$inode_warning" "inode warning threshold"
ops_require_positive_integer "$fd_warning" "file descriptor warning threshold"
(( sample_seconds <= 60 )) || ops_die "sample seconds must not exceed 60"
(( top_count <= 100 )) || ops_die "top count must not exceed 100"
(( disk_warning <= 100 )) || ops_die "disk warning threshold must not exceed 100"
(( inode_warning <= 100 )) || ops_die "inode warning threshold must not exceed 100"
(( fd_warning <= 100 )) || ops_die "file descriptor warning threshold must not exceed 100"
ops_validate_output_file "$output_file"

collect_process_fd_rows() {
  local proc_dir pid fd_count soft_limit hard_limit usage_percent process_name fd_entry limits_line

  for proc_dir in /proc/[0-9]*; do
    [[ -d "$proc_dir/fd" && -r "$proc_dir/comm" ]] || continue
    pid="${proc_dir##*/}"
    fd_count=0
    for fd_entry in "$proc_dir"/fd/*; do
      [[ -e "$fd_entry" || -L "$fd_entry" ]] && ((fd_count += 1))
    done

    limits_line="$(
      awk '/^Max open files/ {print $(NF-2), $(NF-1); found=1} END {if (!found) print "unknown unknown"}' \
        "$proc_dir/limits" 2>/dev/null || true
    )"
    read -r soft_limit hard_limit <<< "${limits_line:-unknown unknown}"
    process_name="$(tr -cd '[:alnum:]_.:+@ -' < "$proc_dir/comm" 2>/dev/null || true)"
    usage_percent="-"
    if [[ "$soft_limit" =~ ^[0-9]+$ ]] && (( soft_limit > 0 )); then
      usage_percent="$(awk -v count="$fd_count" -v limit="$soft_limit" 'BEGIN {printf "%.1f", (count/limit)*100}')"
    fi
    printf '%d %s %s %s %s %s\n' "$fd_count" "$usage_percent" "$pid" "$soft_limit" "$hard_limit" "${process_name:-unknown}"
  done
}

collect_report() {
  local cpu_count load_one allocated unused maximum used

  printf '# Linux resource pressure report\n'
  printf 'data_classification: confidential\n'
  printf 'generated_at_utc: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  printf 'host: %s\n' "$(hostname -f 2>/dev/null || hostname)"
  printf 'disk_warning_percent: %s\n' "$disk_warning"
  printf 'inode_warning_percent: %s\n' "$inode_warning"
  printf 'fd_warning_percent: %s\n' "$fd_warning"
  printf 'interpretation: point-in-time evidence; confirm persistence in monitoring data\n'

  ops_section "Load, CPU count and normalized load"
  uptime 2>&1 || true
  cpu_count="$(nproc 2>/dev/null || awk '/^processor/ {count++} END {print count+0}' /proc/cpuinfo)"
  load_one="$(awk '{print $1}' /proc/loadavg)"
  printf 'logical_cpus: %s\nload_1m: %s\n' "$cpu_count" "$load_one"
  awk -v load="$load_one" -v cpus="$cpu_count" '
    BEGIN {
      ratio=(cpus > 0) ? load/cpus : 0
      printf "load_per_cpu: %.2f\n", ratio
      if (ratio >= 1) print "LOAD_WARNING runnable or blocked work is at least one per CPU"
    }
  '

  ops_section "Pressure Stall Information"
  for pressure_file in /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io; do
    if [[ -r "$pressure_file" ]]; then
      printf '[%s]\n' "${pressure_file##*/}"
      cat "$pressure_file"
    fi
  done

  ops_section "CPU, run queue, blocked tasks, paging and I/O sample"
  if command -v vmstat >/dev/null 2>&1; then
    printf 'The first row is since boot; the second row represents the sample interval.\n'
    vmstat "$sample_seconds" 2 2>&1 || true
  else
    printf 'vmstat is not installed\n'
  fi

  ops_section "Top snapshot"
  if command -v top >/dev/null 2>&1; then
    top -b -n 1 -w 160 2>&1 | head -n $((top_count + 7)) || true
  else
    printf 'top is not installed\n'
  fi

  ops_section "Top processes by CPU"
  ps -eo pid,ppid,user,%cpu,%mem,rss,vsz,nlwp,stat,etimes,comm --sort=-%cpu 2>/dev/null \
    | head -n $((top_count + 1)) || true

  ops_section "Top processes by resident memory"
  ps -eo pid,ppid,user,%cpu,%mem,rss,vsz,nlwp,stat,etimes,comm --sort=-rss 2>/dev/null \
    | head -n $((top_count + 1)) || true

  ops_section "Memory and swap"
  if command -v free >/dev/null 2>&1; then
    free -m
  fi
  awk '
    /^(MemTotal|MemAvailable|Buffers|Cached|SwapCached|SwapTotal|SwapFree|Dirty|Writeback|Slab|SReclaimable):/ {print}
  ' /proc/meminfo
  awk '
    /^MemTotal:/ {total=$2}
    /^MemAvailable:/ {available=$2}
    END {
      ratio=(total > 0) ? (available/total)*100 : 0
      printf "memory_available_percent: %.1f\n", ratio
      if (ratio < 10) print "MEMORY_CRITICAL available memory is below 10%"
      else if (ratio < 20) print "MEMORY_WARNING available memory is below 20%"
    }
  ' /proc/meminfo

  ops_section "Paging, major faults and OOM counters"
  awk '/^(pswpin|pswpout|pgmajfault|oom_kill|compact_stall|allocstall)/ {print}' /proc/vmstat 2>/dev/null || true

  ops_section "System-wide file descriptor capacity"
  if [[ -r /proc/sys/fs/file-nr ]]; then
    read -r allocated unused maximum < /proc/sys/fs/file-nr
    used=$((allocated - unused))
    (( used >= 0 )) || used=0
    awk -v used="$used" -v allocated="$allocated" -v maximum="$maximum" -v threshold="$fd_warning" '
      BEGIN {
        ratio=(maximum > 0) ? (used/maximum)*100 : 0
        printf "allocated: %d\nused_estimate: %d\nmax: %d\nusage_percent: %.1f\n", allocated, used, maximum, ratio
        if (ratio >= threshold) print "FD_SYSTEM_WARNING global file descriptor usage exceeded threshold"
      }
    '
  else
    printf '/proc/sys/fs/file-nr is not readable\n'
  fi

  ops_section "Top processes by open file descriptor count"
  printf 'FD-Count Usage-vs-Soft-Limit-Percent PID Soft-Limit Hard-Limit Process\n'
  collect_process_fd_rows | sort -k1,1nr | head -n "$top_count" || true
  printf 'A dash in usage means the process soft limit was unavailable or unlimited.\n'

  ops_section "Filesystem capacity and inode usage"
  df -P -x tmpfs -x devtmpfs 2>/dev/null || df -P
  df -Pi -x tmpfs -x devtmpfs 2>/dev/null || df -Pi

  ops_section "Filesystem capacity warnings"
  df -P -x tmpfs -x devtmpfs 2>/dev/null | awk -v threshold="$disk_warning" '
    NR > 1 {usage=$5; gsub(/%/, "", usage); if (usage+0 >= threshold) print "DISK_WARNING mount=" $6 " usage=" usage "%"}
  ' || true
  df -Pi -x tmpfs -x devtmpfs 2>/dev/null | awk -v threshold="$inode_warning" '
    NR > 1 {usage=$5; gsub(/%/, "", usage); if (usage+0 >= threshold) print "INODE_WARNING mount=" $6 " usage=" usage "%"}
  ' || true

  ops_section "Extended block device latency and queue sample"
  if command -v iostat >/dev/null 2>&1; then
    iostat -xz 1 2 2>&1 || true
  else
    printf 'iostat is not installed; use vmstat wa/b columns and storage metrics as the fallback\n'
  fi

  ops_section "Deleted but still open files"
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP +L1 2>&1 | head -n $((top_count + 1)) || true
  else
    printf 'lsof is not installed\n'
  fi

  ops_section "Recent kernel OOM, hung task and storage error evidence"
  if command -v journalctl >/dev/null 2>&1; then
    journalctl --dmesg --since "$since" --no-pager --output=short-iso 2>&1 \
      | grep -Ei 'out of memory|oom-kill|killed process|hung task|blocked for more than|i/o error|ext4-fs error|xfs.*error|nvme.*error' \
      | tail -n 100 || true
  else
    printf 'journalctl is not installed\n'
  fi
}

ops_emit_report "$output_file" collect_report
