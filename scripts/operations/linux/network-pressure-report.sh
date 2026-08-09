#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../lib/common.sh
source "${script_dir}/../../lib/common.sh"

output_file=""
sample_seconds=5
top_count=15
listen_queue_warning=80
socket_queue_warning_bytes=1048576

usage() {
  cat <<'EOF'
Usage: network-pressure-report.sh [options]

Collect read-only Linux network saturation evidence: interface throughput,
socket states, listen/established queues, retransmits, drops and conntrack.
The script does not change sysctl, firewall, interface or application state.

Options:
  --output FILE                 Save the report while also printing it.
  --sample-seconds COUNT        Throughput sample interval, 1-60 (default: 5).
  --top COUNT                   Queued socket rows, 1-100 (default: 15).
  --listen-queue-warning PCT    Listen backlog warning ratio (default: 80).
  --socket-queue-warning BYTES  Established queue warning bytes (default: 1048576).
  -h, --help                    Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      [[ $# -ge 2 ]] || ops_die "--output requires a value"
      output_file="$2"
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
    --listen-queue-warning)
      [[ $# -ge 2 ]] || ops_die "--listen-queue-warning requires a value"
      listen_queue_warning="$2"
      shift 2
      ;;
    --socket-queue-warning)
      [[ $# -ge 2 ]] || ops_die "--socket-queue-warning requires a value"
      socket_queue_warning_bytes="$2"
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
ops_require_command head
ops_require_command sort
ops_require_positive_integer "$sample_seconds" "sample seconds"
ops_require_positive_integer "$top_count" "top count"
ops_require_positive_integer "$listen_queue_warning" "listen queue warning threshold"
ops_require_positive_integer "$socket_queue_warning_bytes" "socket queue warning bytes"
(( sample_seconds <= 60 )) || ops_die "sample seconds must not exceed 60"
(( top_count <= 100 )) || ops_die "top count must not exceed 100"
(( listen_queue_warning <= 100 )) || ops_die "listen queue warning threshold must not exceed 100"
ops_validate_output_file "$output_file"

read_interface_totals() {
  awk '
    NR > 2 {
      interface=$1
      gsub(/:/, "", interface)
      if (interface != "lo") {
        rx_bytes += $2
        tx_bytes += $10
      }
    }
    END {printf "%.0f %.0f\n", rx_bytes, tx_bytes}
  ' /proc/net/dev
}

collect_throughput_sample() {
  local rx_before tx_before rx_after tx_after

  read -r rx_before tx_before < <(read_interface_totals)
  sleep "$sample_seconds"
  read -r rx_after tx_after < <(read_interface_totals)

  awk -v rx_before="$rx_before" -v tx_before="$tx_before" \
      -v rx_after="$rx_after" -v tx_after="$tx_after" \
      -v seconds="$sample_seconds" '
    BEGIN {
      rx_delta=rx_after-rx_before
      tx_delta=tx_after-tx_before
      if (rx_delta < 0 || tx_delta < 0) {
        print "counter_reset_detected: true"
        exit
      }
      printf "sample_seconds: %d\n", seconds
      printf "receive_bytes_per_second: %.0f\n", rx_delta/seconds
      printf "transmit_bytes_per_second: %.0f\n", tx_delta/seconds
      printf "receive_megabits_per_second: %.3f\n", (rx_delta*8)/(seconds*1000000)
      printf "transmit_megabits_per_second: %.3f\n", (tx_delta*8)/(seconds*1000000)
    }
  '
}

collect_softnet_stats() {
  local cpu_index=0 processed_hex dropped_hex squeezed_hex remainder

  while read -r processed_hex dropped_hex squeezed_hex remainder; do
    printf 'cpu=%d processed=%d dropped=%d time_squeeze=%d\n' \
      "$cpu_index" "$((16#${processed_hex}))" "$((16#${dropped_hex}))" "$((16#${squeezed_hex}))"
    ((cpu_index += 1))
  done < /proc/net/softnet_stat
}

collect_report() {
  local conntrack_count conntrack_max

  printf '# Linux network pressure report\n'
  printf 'data_classification: confidential\n'
  printf 'generated_at_utc: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  printf 'host: %s\n' "$(hostname -f 2>/dev/null || hostname)"
  printf 'listen_queue_warning_percent: %s\n' "$listen_queue_warning"
  printf 'socket_queue_warning_bytes: %s\n' "$socket_queue_warning_bytes"
  printf 'interpretation: point-in-time evidence; compare with baseline and monitoring window\n'

  ops_section "Aggregate interface throughput sample"
  collect_throughput_sample

  ops_section "Interface counters, errors and drops"
  if command -v ip >/dev/null 2>&1; then
    ip -s link show 2>&1 || true
  else
    awk 'NR > 2 {print}' /proc/net/dev
  fi

  ops_section "Socket summary"
  if command -v ss >/dev/null 2>&1; then
    ss -s 2>&1 || true

    ops_section "TCP state counts"
    ss -antH 2>/dev/null | awk '{count[$1]++} END {for (state in count) print state, count[state]}' | sort || true

    ops_section "Listening sockets and accept queues"
    printf 'State Recv-Q Send-Q Local-Address Peer-Address Process\n'
    ss -lntpH 2>&1 || ss -lntH 2>&1 || true

    ops_section "Listen queue warnings"
    ss -lntH 2>/dev/null | awk -v threshold="$listen_queue_warning" '
      {
        current=$2+0
        maximum=$3+0
        if (maximum > 0) {
          ratio=(current/maximum)*100
          if (ratio >= threshold) {
            printf "LISTEN_QUEUE_WARNING local=%s current=%d maximum=%d ratio=%.1f%%\n", $4, current, maximum, ratio
          }
        }
      }
    ' || true

    ops_section "Top established socket queues"
    printf 'Recv-Q-Bytes Send-Q-Bytes State Local-Address Peer-Address\n'
    ss -ntH 2>/dev/null | awk '$1 == "ESTAB" {print $2, $3, $1, $4, $5}' \
      | sort -k1,1nr -k2,2nr | head -n "$top_count" || true

    ops_section "Established queue warnings"
    ss -ntH 2>/dev/null | awk -v threshold="$socket_queue_warning_bytes" '
      $1 == "ESTAB" && (($2+0) >= threshold || ($3+0) >= threshold) {
        printf "SOCKET_QUEUE_WARNING local=%s peer=%s receive_bytes=%d send_bytes=%d\n", $4, $5, $2, $3
      }
    ' || true
  elif command -v netstat >/dev/null 2>&1; then
    printf 'ss is unavailable; using netstat fallback\n'
    netstat -s 2>&1 || true
    netstat -lnt 2>&1 || true
  else
    printf 'neither ss nor netstat is installed\n'
  fi

  ops_section "TCP retransmit, listen drop and backlog counters"
  if command -v nstat >/dev/null 2>&1; then
    nstat -az 2>&1 | awk '
      /^(TcpRetransSegs|TcpExtListenOverflows|TcpExtListenDrops|TcpExtTCPBacklogDrop|TcpExtTCPSynRetrans|IpExtInNoRoutes|IpExtInTruncatedPkts)/ {print}
    ' || true
  elif command -v netstat >/dev/null 2>&1; then
    netstat -s 2>&1 | grep -Ei 'retrans|listen|overflow|drop|backlog' || true
  else
    printf 'nstat and netstat are unavailable; inspect /proc/net/netstat manually\n'
  fi

  ops_section "Kernel socket allocation"
  [[ -r /proc/net/sockstat ]] && cat /proc/net/sockstat
  [[ -r /proc/net/sockstat6 ]] && cat /proc/net/sockstat6

  ops_section "Network softirq backlog"
  printf 'Fields are cumulative since boot; increasing dropped or time_squeeze requires interval comparison.\n'
  if [[ -r /proc/net/softnet_stat ]]; then
    collect_softnet_stats
  else
    printf '/proc/net/softnet_stat is not readable\n'
  fi

  ops_section "Conntrack capacity"
  if [[ -r /proc/sys/net/netfilter/nf_conntrack_count && -r /proc/sys/net/netfilter/nf_conntrack_max ]]; then
    conntrack_count="$(< /proc/sys/net/netfilter/nf_conntrack_count)"
    conntrack_max="$(< /proc/sys/net/netfilter/nf_conntrack_max)"
    awk -v count="$conntrack_count" -v maximum="$conntrack_max" '
      BEGIN {
        ratio=(maximum > 0) ? (count/maximum)*100 : 0
        printf "count: %d\nmax: %d\nusage_percent: %.1f\n", count, maximum, ratio
        if (ratio >= 80) print "CONNTRACK_WARNING usage is at least 80%"
      }
    '
  else
    printf 'conntrack counters are not available\n'
  fi

  ops_section "Read-only queue-related kernel settings"
  if command -v sysctl >/dev/null 2>&1; then
    sysctl net.core.somaxconn net.ipv4.tcp_max_syn_backlog net.ipv4.ip_local_port_range 2>&1 || true
  else
    printf 'sysctl is not installed\n'
  fi
}

ops_emit_report "$output_file" collect_report
