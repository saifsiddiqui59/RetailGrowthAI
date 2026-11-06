#!/usr/bin/env bash
# One-time operator provisioning only. Never call from an HTTP request or CI
# without an explicitly approved network/cost/rights gate. Model stays private.
set -euo pipefail
if [[ $# -ne 1 || ! -n "${1:-}" || "${1}" != /* ]]; then
  echo 'Usage: provision-pinned-kokoro-models.sh /absolute/private/cache' >&2
  exit 2
fi
command -v curl >/dev/null || { echo 'curl unavailable' >&2; exit 2; }
command -v sha256sum >/dev/null || { echo 'sha256sum unavailable' >&2; exit 2; }
CACHE="$1"
umask 077
mkdir -p -- "$CACHE"
[[ -d "$CACHE" && ! -L "$CACHE" ]] || { echo 'Unsafe cache directory' >&2; exit 2; }
base='https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1'
verify() {
  local file="$1" length="$2" digest="$3" actual
  [[ -f "$file" && ! -L "$file" ]] || return 1
  actual="$(wc -c < "$file" | tr -d '[:space:]')"
  [[ "$actual" == "$length" ]] || return 1
  printf '%s  %s\n' "$digest" "$file" | sha256sum --check --status
}
get_one() {
  local name="$1" expected_bytes="$2" expected_sha="$3" target="$CACHE/$1" temp
  if [[ -e "$target" || -L "$target" ]]; then
    if verify "$target" "$expected_bytes" "$expected_sha"; then
      echo "Verified existing private cache: $name"
      return 0
    fi
    echo "Existing $name invalid; refusing to overwrite" >&2
    return 1
  fi
  temp="$(mktemp "$CACHE/.download-XXXXXX")"
  if ! curl --fail --location --silent --show-error --proto '=https' \
    --tlsv1.2 --retry 2 --connect-timeout 20 --max-time 900 \
    --output "$temp" "$base/$name"; then
    rm -f -- "$temp"
    return 1
  fi
  if ! verify "$temp" "$expected_bytes" "$expected_sha"; then
    rm -f -- "$temp"
    echo "Official file mismatch for $name; cached nothing" >&2
    return 1
  fi
  chmod 600 "$temp"
  mv -n -- "$temp" "$target"
  rm -f -- "$temp"
  verify "$target" "$expected_bytes" "$expected_sha"
  echo "Verified new pinned model in private cache: $name"
}
get_one 'kokoro-v1.0.int8.onnx' '114119327' \
  'ae315a79b623f244700e4afb9246c46a26066782e049ba174bf3ba433970ee9c'
get_one 'voices-v1.0.bin' '28214398' \
  'bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d'
echo 'CPU model cache ready. No inference or commercial license acceptance was performed.'
