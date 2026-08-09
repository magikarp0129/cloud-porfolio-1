#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

operations_scripts=(
  "scripts/operations/linux/system-health-report.sh"
  "scripts/operations/linux/network-pressure-report.sh"
  "scripts/operations/linux/resource-pressure-report.sh"
  "scripts/operations/linux/service-triage.sh"
  "scripts/operations/linux/patch-readiness.sh"
  "scripts/operations/kubernetes/eks-cluster-health.sh"
  "scripts/operations/aws/audit-cloudwatch-log-retention.sh"
)

syntax_targets=(
  "scripts/lib/common.sh"
  "scripts/tests/validate-operations-scripts.sh"
  "${operations_scripts[@]}"
)

for relative_path in "${syntax_targets[@]}"; do
  bash -n "${repo_root}/${relative_path}"
  printf 'syntax: PASS %s\n' "$relative_path"
done

for relative_path in "${operations_scripts[@]}"; do
  help_text="$(bash "${repo_root}/${relative_path}" --help)"
  grep -F "Usage:" <<< "$help_text" >/dev/null
  printf 'help:   PASS %s\n' "$relative_path"
done

if grep -REn '(^|[;&|[:space:]])eval[[:space:]]' \
  "${repo_root}/scripts/operations/linux" \
  "${repo_root}/scripts/operations/kubernetes" \
  "${repo_root}/scripts/operations/aws"; then
  printf 'unsafe eval usage detected\n' >&2
  exit 1
fi

printf 'policy: PASS no eval in operational scripts\n'

set +e
aws_audit_output="$(PATH="${repo_root}/scripts/tests/fakes:${PATH}" \
  bash "${repo_root}/scripts/operations/aws/audit-cloudwatch-log-retention.sh" \
  --region ap-northeast-2 \
  --prefix /aws/eks/ \
  --minimum-days 90 \
  --require-kms \
  --fail-on-findings 2>&1)"
aws_audit_status=$?
set -e
[[ $aws_audit_status -eq 2 ]] || {
  printf 'expected CloudWatch audit status 2, got %s\n%s\n' "$aws_audit_status" "$aws_audit_output" >&2
  exit 1
}
grep -F 'finding_count: 2' <<< "$aws_audit_output" >/dev/null
printf 'fixture: PASS CloudWatch retention and KMS findings\n'

eks_health_output="$(PATH="${repo_root}/scripts/tests/fakes:${PATH}" \
  bash "${repo_root}/scripts/operations/kubernetes/eks-cluster-health.sh" \
  --context test-eks \
  --namespace payments)"
grep -F 'context: test-eks' <<< "$eks_health_output" >/dev/null
grep -F 'api-pending' <<< "$eks_health_output" >/dev/null
printf 'fixture: PASS explicit EKS context and health evidence\n'

printf 'operations script validation completed\n'
