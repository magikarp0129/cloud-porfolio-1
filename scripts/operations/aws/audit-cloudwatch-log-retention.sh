#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../lib/common.sh
source "${script_dir}/../../lib/common.sh"

region=""
profile=""
prefix="/aws/"
minimum_days=90
require_kms=false
fail_on_findings=false
output_file=""

usage() {
  cat <<'EOF'
Usage: audit-cloudwatch-log-retention.sh --region REGION [options]

Audit CloudWatch Logs retention and optional KMS configuration using read-only
AWS APIs. The script never creates or changes a log group.

Options:
  --region REGION        AWS region to inspect.
  --profile PROFILE      Optional named AWS CLI profile.
  --prefix PREFIX        Log group name prefix (default: /aws/).
  --minimum-days COUNT   Required minimum retention (default: 90).
  --require-kms          Report a finding when a log group has no KMS key.
  --fail-on-findings     Exit with status 2 when findings exist.
  --output FILE          Save the report while also printing it.
  -h, --help             Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --region)
      [[ $# -ge 2 ]] || ops_die "--region requires a value"
      region="$2"
      shift 2
      ;;
    --profile)
      [[ $# -ge 2 ]] || ops_die "--profile requires a value"
      profile="$2"
      shift 2
      ;;
    --prefix)
      [[ $# -ge 2 ]] || ops_die "--prefix requires a value"
      prefix="$2"
      shift 2
      ;;
    --minimum-days)
      [[ $# -ge 2 ]] || ops_die "--minimum-days requires a value"
      minimum_days="$2"
      shift 2
      ;;
    --require-kms)
      require_kms=true
      shift
      ;;
    --fail-on-findings)
      fail_on_findings=true
      shift
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

ops_require_command aws
[[ -n "$region" ]] || ops_die "--region is required"
[[ "$region" =~ ^[a-z]{2}(-[a-z]+)+-[0-9]+$ ]] || ops_die "invalid AWS region format"
[[ "$prefix" =~ ^[A-Za-z0-9_./#-]+$ ]] || ops_die "log group prefix contains unsupported characters"
if [[ -n "$profile" ]]; then
  [[ "$profile" =~ ^[A-Za-z0-9_.@-]+$ ]] || ops_die "profile contains unsupported characters"
fi
ops_require_positive_integer "$minimum_days" "minimum retention"
ops_validate_output_file "$output_file"

aws_args=(--region "$region" --no-cli-pager)
if [[ -n "$profile" ]]; then
  aws_args+=(--profile "$profile")
fi

findings=0

collect_report() {
  local listing name retention kms_key stored_bytes retention_state kms_state

  listing="$(aws "${aws_args[@]}" logs describe-log-groups \
    --log-group-name-prefix "$prefix" \
    --query 'logGroups[].[logGroupName,retentionInDays,kmsKeyId,storedBytes]' \
    --output text)" || ops_die "CloudWatch Logs query failed"

  printf '# CloudWatch Logs retention audit\n'
  printf 'data_classification: internal\n'
  printf 'generated_at_utc: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  printf 'region: %s\n' "$region"
  printf 'profile: %s\n' "${profile:-default credential chain}"
  printf 'prefix: %s\n' "$prefix"
  printf 'minimum_retention_days: %s\n' "$minimum_days"
  printf 'require_kms: %s\n' "$require_kms"

  ops_section "Log groups"
  printf '%-55s %-10s %-12s %s\n' "NAME" "RETENTION" "KMS" "STORED_BYTES"
  if [[ -z "$listing" ]]; then
    printf 'No log group matched the prefix.\n'
    return 0
  fi

  while IFS=$'\t' read -r name retention kms_key stored_bytes; do
    retention_state="OK"
    kms_state="CONFIGURED"

    if [[ -z "$retention" || "$retention" == "None" ]]; then
      retention_state="FINDING:no-expiry"
      findings=$((findings + 1))
    elif [[ "$retention" =~ ^[0-9]+$ ]] && (( retention < minimum_days )); then
      retention_state="FINDING:${retention}d"
      findings=$((findings + 1))
    else
      retention_state="${retention}d"
    fi

    if [[ -z "$kms_key" || "$kms_key" == "None" ]]; then
      kms_state="NOT_CONFIGURED"
      if [[ "$require_kms" == true ]]; then
        kms_state="FINDING:no-kms"
        findings=$((findings + 1))
      fi
    fi

    printf '%-55s %-18s %-18s %s\n' "$name" "$retention_state" "$kms_state" "${stored_bytes:-0}"
  done <<< "$listing"

  ops_section "Summary"
  printf 'finding_count: %s\n' "$findings"
  printf 'This audit is read-only. Apply retention or KMS changes through reviewed Terraform.\n'
}

ops_emit_report "$output_file" collect_report

if [[ "$fail_on_findings" == true ]] && (( findings > 0 )); then
  exit 2
fi
