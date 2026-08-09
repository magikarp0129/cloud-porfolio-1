#!/usr/bin/env bash

# Shared helpers for read-only infrastructure operations scripts.

umask 077

ops_die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

ops_log() {
  printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"
}

ops_section() {
  printf '\n## %s\n' "$*"
}

ops_require_command() {
  command -v "$1" >/dev/null 2>&1 || ops_die "required command not found: $1"
}

ops_require_linux() {
  [[ "$(uname -s)" == "Linux" ]] || ops_die "this script must run on Linux"
}

ops_require_positive_integer() {
  local value="$1"
  local label="$2"
  [[ "$value" =~ ^[1-9][0-9]*$ ]] || ops_die "${label} must be a positive integer without a leading zero"
}

ops_validate_output_file() {
  local output_file="$1"
  local output_dir

  [[ -n "$output_file" ]] || return 0
  output_dir="$(dirname "$output_file")"
  [[ -d "$output_dir" ]] || ops_die "output directory does not exist: ${output_dir}"
  [[ ! -L "$output_file" ]] || ops_die "output path must not be a symbolic link: ${output_file}"
  [[ ! -e "$output_file" || -f "$output_file" ]] || ops_die "output path is not a regular file: ${output_file}"
}

ops_emit_report() {
  local output_file="$1"
  shift

  if [[ -n "$output_file" ]]; then
    "$@" > "$output_file"
    cat "$output_file"
  else
    "$@"
  fi
}
