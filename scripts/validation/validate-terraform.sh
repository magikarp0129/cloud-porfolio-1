#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

terraform -chdir="${repo_root}" fmt -check -recursive

python3 "${repo_root}/scripts/validation/verify-architecture-diagram.py"
python3 "${repo_root}/scripts/validation/verify-service-network-plan.py"

roots=(
  "terraform/organization"
  "terraform/environments/dev"
  "terraform/environments/stg"
  "terraform/environments/prod"
  "terraform/environments/dev/platform"
  "terraform/environments/stg/platform"
  "terraform/environments/prod/platform"
  "terraform/modules/security-group"
  "terraform/modules/route-policy"
  "terraform/modules/waf"
  "terraform/landing-zone/ipam"
  "terraform/landing-zone/network-hub"
  "terraform/landing-zone/connectivity"
)

while IFS= read -r service_root; do
  roots+=("${service_root#"${repo_root}/"}")
done < <(find "${repo_root}/terraform/services" -mindepth 2 -maxdepth 2 -type d | sort)

for root in "${roots[@]}"; do
  plugin_args=()
  case "${root}" in
    terraform/environments/*/platform)
      local_provider_mirror="${repo_root}/terraform/environments/dev/platform/.terraform/providers"
      ;;
    terraform/environments/*)
      local_provider_mirror="${repo_root}/terraform/environments/dev/.terraform/providers"
      ;;
    *)
      local_provider_mirror="${repo_root}/terraform/organization/.terraform/providers"
      ;;
  esac
  if [[ -d "${local_provider_mirror}/registry.terraform.io" ]]; then
    plugin_args+=("-plugin-dir=${local_provider_mirror}")
  fi

  echo "Validating ${root}"
  terraform -chdir="${repo_root}/${root}" init -backend=false -input=false -no-color "${plugin_args[@]}"
  terraform -chdir="${repo_root}/${root}" validate -no-color
done

python3 -c 'compile(open("terraform/modules/operations/src/scheduler.py", encoding="utf-8").read(), "scheduler.py", "exec")'
