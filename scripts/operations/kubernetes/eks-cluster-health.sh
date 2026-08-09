#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../../lib/common.sh
source "${script_dir}/../../lib/common.sh"

context=""
namespace=""
event_limit=40
output_file=""

usage() {
  cat <<'EOF'
Usage: eks-cluster-health.sh --context NAME [options]

Collect a read-only Kubernetes/EKS health report. Secrets and ConfigMaps are
not queried, and the script does not apply, patch, scale, cordon, or drain.

Options:
  --context NAME         Explicit kubeconfig context to inspect.
  --namespace NAME       Limit namespaced queries; default is all namespaces.
  --events COUNT         Maximum recent events (default: 40).
  --output FILE          Save the report while also printing it.
  -h, --help             Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --context)
      [[ $# -ge 2 ]] || ops_die "--context requires a value"
      context="$2"
      shift 2
      ;;
    --namespace)
      [[ $# -ge 2 ]] || ops_die "--namespace requires a value"
      namespace="$2"
      shift 2
      ;;
    --events)
      [[ $# -ge 2 ]] || ops_die "--events requires a value"
      event_limit="$2"
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

ops_require_command kubectl
[[ -n "$context" ]] || ops_die "--context is required to prevent accidental cluster selection"
[[ "$context" =~ ^[A-Za-z0-9_.:/@-]+$ ]] || ops_die "context contains unsupported characters"
if [[ -n "$namespace" ]]; then
  [[ "$namespace" =~ ^[a-z0-9]([-a-z0-9]*[a-z0-9])?$ ]] || ops_die "namespace is not a valid DNS label"
fi
ops_require_positive_integer "$event_limit" "event count"
(( event_limit <= 500 )) || ops_die "event count must not exceed 500"
ops_validate_output_file "$output_file"

kubectl config get-contexts "$context" -o name 2>/dev/null | grep -Fx "$context" >/dev/null \
  || ops_die "kubeconfig context not found: ${context}"

kube_scope=()
if [[ -n "$namespace" ]]; then
  kube_scope=(--namespace "$namespace")
else
  kube_scope=(--all-namespaces)
fi

run_kubectl() {
  kubectl --context "$context" "$@" 2>&1 || true
}

collect_report() {
  printf '# EKS and Kubernetes cluster health report\n'
  printf 'data_classification: internal\n'
  printf 'generated_at_utc: %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  printf 'context: %s\n' "$context"
  printf 'namespace_scope: %s\n' "${namespace:-all}"

  ops_section "Identity and API reachability"
  run_kubectl auth can-i get nodes
  run_kubectl cluster-info

  ops_section "Nodes"
  run_kubectl get nodes -o wide

  ops_section "Non-running pods"
  run_kubectl get pods "${kube_scope[@]}" \
    --field-selector=status.phase!=Running,status.phase!=Succeeded \
    -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,PHASE:.status.phase,REASON:.status.reason,NODE:.spec.nodeName

  ops_section "Workload controllers"
  run_kubectl get deployments,statefulsets,daemonsets "${kube_scope[@]}" -o wide

  ops_section "Disruption budgets and autoscaling"
  run_kubectl get poddisruptionbudgets,horizontalpodautoscalers "${kube_scope[@]}" -o wide

  ops_section "Persistent volume claims"
  run_kubectl get persistentvolumeclaims "${kube_scope[@]}" -o wide

  ops_section "Recent events"
  run_kubectl get events "${kube_scope[@]}" --sort-by=.lastTimestamp | tail -n "$event_limit"
}

ops_emit_report "$output_file" collect_report
