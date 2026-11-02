#!/usr/bin/env bash
# find-jsc-key.sh — Extract the XXTEA key used to encrypt .jsc files in a
# Cocos Creator build.
#
# Output: zero or more `KEY=<value>` lines on stdout plus diagnostics on stderr.
set -euo pipefail

if [[ $# -lt 1 || "$1" == "-h" || "$1" == "--help" ]]; then
  cat <<EOF
Usage: find-jsc-key.sh <path>

Search for XXTEA keys in a Cocos Creator build. Tries both 2.x (main.js) and
3.x (application.js / src/settings.json) key locations, and reconstructs keys
stored as byte arrays.
EOF
  exit 0
fi

ROOT="$1"
if [[ ! -d "$ROOT" ]]; then
  echo "Error: not a directory: $ROOT" >&2
  exit 1
fi

echo "=== Scanning for XXTEA keys in: $ROOT ===" >&2

CANDIDATE_FILES=()
for rel in \
    main.js \
    src/main.js \
    application.js \
    src/settings.json \
    cocos-js/cocos-js.js \
    cocos-js/bundle.js; do
  [[ -f "$ROOT/$rel" ]] && CANDIDATE_FILES+=("$ROOT/$rel")
done
# Also pull any top-level .js the build may ship.
while IFS= read -r -d '' f; do
  CANDIDATE_FILES+=("$f")
done < <(find "$ROOT" -maxdepth 2 -type f -name '*.js' -print0 2>/dev/null | head -z -n 50)

# Deduplicate
mapfile -t CANDIDATE_FILES < <(printf '%s\n' "${CANDIDATE_FILES[@]}" | awk '!seen[$0]++')

found_keys=()

add_key() {
  local k="$1"
  # Trim whitespace
  k="${k#"${k%%[![:space:]]*}"}"
  k="${k%"${k##*[![:space:]]}"}"
  [[ -z "$k" ]] && return
  # Ignore keys that are clearly placeholders
  case "$k" in
    "YOUR_KEY_HERE"|"xxteaKey"|"null"|"undefined") return ;;
  esac
  # Deduplicate
  for existing in "${found_keys[@]-}"; do
    [[ "$existing" == "$k" ]] && return
  done
  found_keys+=("$k")
}

scan_file() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  echo "[scan] $file" >&2

  # Pattern: xxteaKey = "…" / encryptKey = "…" / XXTEA_KEY = "…" / key: "…"
  while IFS= read -r line; do
    # shellcheck disable=SC2001
    val=$(echo "$line" | sed -E 's/.*["'"'"']([^"'"'"']{4,64})["'"'"'].*/\1/')
    add_key "$val"
  done < <(grep -aE '(xxteaKey|encryptKey|XXTEA_KEY|encryptionKey|xxtea_key)\s*[:=]\s*["'"'"'][^"'"'"']+["'"'"']' "$file" 2>/dev/null || true)

  # Pattern: bare UUID-shaped string near the word jsc/xxtea (common default)
  while IFS= read -r line; do
    val=$(echo "$line" | grep -aoE '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' | head -1)
    add_key "$val"
  done < <(grep -aE -A2 -B2 'jsc|xxtea|encrypt' "$file" 2>/dev/null | grep -aE '[0-9a-f]{8}-[0-9a-f]{4}' || true)

  # Pattern: short-UUID (first segment only), as used by Cocos 2.x default
  while IFS= read -r line; do
    val=$(echo "$line" | sed -E 's/.*["'"'"']([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{2,})["'"'"'].*/\1/')
    add_key "$val"
  done < <(grep -aE '["'"'"'][0-9a-f]{8}-[0-9a-f]{4}' "$file" 2>/dev/null | head -20 || true)

  # Pattern: byte-array key — reconstruct it
  # Matches  foo = [0x61, 0x62, ...]  or  foo = [97, 98, ...]  limited to len 8..64
  while IFS= read -r match; do
    # Pull the array body
    body=$(echo "$match" | sed -E 's/.*\[([^]]+)\].*/\1/')
    # Count commas to gate length
    count=$(echo "$body" | tr -cd ',' | wc -c)
    if (( count >= 7 && count <= 63 )); then
      # Convert to bytes
      key=""
      IFS=',' read -ra parts <<<"$body"
      valid=true
      for p in "${parts[@]}"; do
        p=$(echo "$p" | tr -d '[:space:]')
        if [[ "$p" =~ ^0x[0-9a-fA-F]{1,2}$ ]]; then
          byte=$((p))
        elif [[ "$p" =~ ^[0-9]+$ ]]; then
          byte=$p
        else
          valid=false; break
        fi
        if (( byte < 32 || byte > 126 )); then
          valid=false; break
        fi
        # shellcheck disable=SC2059
        key+=$(printf "\\$(printf '%03o' "$byte")")
      done
      if [[ "$valid" == true ]] && [[ ${#key} -ge 8 ]]; then
        add_key "$key"
      fi
    fi
  done < <(grep -aE '\[\s*(0x[0-9a-fA-F]{1,2}|[0-9]{1,3})\s*(,\s*(0x[0-9a-fA-F]{1,2}|[0-9]{1,3})){7,}\s*\]' "$file" 2>/dev/null || true)
}

for f in "${CANDIDATE_FILES[@]}"; do
  scan_file "$f"
done

echo "---" >&2
if [[ ${#found_keys[@]} -eq 0 ]]; then
  echo "No key found." >&2
  echo "Tip: grep manually — the key may be embedded inside a minified helper." >&2
  echo "     grep -aE '[0-9a-f]{8}-[0-9a-f]{4}' $ROOT/main.js" >&2
  exit 1
fi

echo "Found ${#found_keys[@]} candidate key(s):" >&2
for k in "${found_keys[@]}"; do
  echo "KEY=$k"
  echo "  - $k" >&2
done
