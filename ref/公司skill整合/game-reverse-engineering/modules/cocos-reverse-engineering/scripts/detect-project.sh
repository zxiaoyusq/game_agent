#!/usr/bin/env bash
# detect-project.sh — Detect Cocos Creator engine version and project layout.
# Emits ENGINE=, ENCRYPTED=, BUNDLES=, WEB_MOBILE= machine-readable lines.
set -euo pipefail

usage() {
  cat <<EOF
Usage: detect-project.sh <path>

Detect the Cocos Creator engine version (2.3.x / 2.4.x / 3.x) and report key
paths for a compiled game build.

Arguments:
  <path>   Path to the build directory (or a subdir containing the build).

Output (machine-readable):
  ENGINE=2.3.x|2.4.x|3.x|unknown
  ENCRYPTED=yes|no
  BUNDLES=<csv>       # 3.x only
  WEB_MOBILE=yes|no
  KEY_PATHS=<csv>     # candidate files where xxtea keys may live
  SCRIPT_PATHS=<csv>
  ASSET_PATHS=<csv>
EOF
  exit 0
}

if [[ $# -lt 1 || "$1" == "-h" || "$1" == "--help" ]]; then
  usage
fi

TARGET="$1"
if [[ ! -e "$TARGET" ]]; then
  echo "Error: path not found: $TARGET" >&2
  exit 1
fi

# If a file was passed, use its directory.
if [[ -f "$TARGET" ]]; then
  TARGET=$(dirname "$TARGET")
fi

TARGET=$(cd "$TARGET" && pwd)
echo "=== Cocos Creator Project Detection ==="
echo "Target: $TARGET"
echo

ENGINE="unknown"
ENCRYPTED="no"
BUNDLES=""
WEB_MOBILE="no"
KEY_PATHS=()
SCRIPT_PATHS=()
ASSET_PATHS=()

# If user pointed at the parent (e.g. an APK extract root), scan one level down
# for a directory that looks like a build.
probe_candidates() {
  local candidates=("$TARGET")
  for sub in assets build-templates src/cocos-project .; do
    [[ -d "$TARGET/$sub" ]] && candidates+=("$TARGET/$sub")
  done
  # Also walk one level deep
  while IFS= read -r -d '' d; do
    candidates+=("$d")
  done < <(find "$TARGET" -mindepth 1 -maxdepth 1 -type d -print0 2>/dev/null)

  # Deduplicate
  printf '%s\n' "${candidates[@]}" | awk '!seen[$0]++'
}

best_root=""
best_engine="unknown"
# 3.x / bundle-style markers first — they're unambiguous (neither 2.3 nor legacy
# 2.4 produces a per-bundle config.json).
has_bundle_config() {
  local root="$1"
  [[ -d "$root/assets" ]] || return 1
  while IFS= read -r -d '' cfg; do
    return 0
  done < <(find "$root/assets" -mindepth 2 -maxdepth 2 -name 'config.json' -print0 2>/dev/null)
  return 1
}
for root in $(probe_candidates); do
  if has_bundle_config "$root" || [[ -f "$root/application.js" ]] || [[ -f "$root/src/settings.json" ]] || [[ -d "$root/cocos-js" ]]; then
    best_root="$root"; best_engine="3.x"; break
  fi
done
if [[ -z "$best_root" ]]; then
  for root in $(probe_candidates); do
    if [[ -f "$root/src/settings.js" && -f "$root/src/project.js" && -d "$root/res" ]]; then
      best_root="$root"; best_engine="2.3.x"; break
    fi
  done
fi
if [[ -z "$best_root" ]]; then
  for root in $(probe_candidates); do
    if [[ -f "$root/main.js" ]] && { [[ -f "$root/settings.js" ]] || [[ -f "$root/src/settings.js" ]]; } && { [[ -d "$root/assets" ]] || [[ -d "$root/res" ]]; }; then
      best_root="$root"; best_engine="2.4.x"; break
    fi
  done
fi

ROOT="${best_root:-$TARGET}"
ENGINE="$best_engine"

echo "Root:   $ROOT"
echo "Engine: $ENGINE"

# Web-mobile marker
if [[ -f "$ROOT/index.html" ]]; then
  WEB_MOBILE="yes"
fi

# Populate paths per engine
case "$ENGINE" in
  2.3.x)
    [[ -f "$ROOT/src/settings.js" ]] && SCRIPT_PATHS+=("$ROOT/src/settings.js")
    [[ -f "$ROOT/src/project.js"  ]] && SCRIPT_PATHS+=("$ROOT/src/project.js")
    [[ -f "$ROOT/main.js"         ]] && SCRIPT_PATHS+=("$ROOT/main.js")
    [[ -d "$ROOT/res"             ]] && ASSET_PATHS+=("$ROOT/res")
    [[ -f "$ROOT/main.js"         ]] && KEY_PATHS+=("$ROOT/main.js")
    [[ -f "$ROOT/src/main.js"     ]] && KEY_PATHS+=("$ROOT/src/main.js")
    ;;
  2.4.x)
    [[ -f "$ROOT/settings.js"     ]] && SCRIPT_PATHS+=("$ROOT/settings.js")
    [[ -f "$ROOT/src/settings.js" ]] && SCRIPT_PATHS+=("$ROOT/src/settings.js")
    [[ -f "$ROOT/project.js"      ]] && SCRIPT_PATHS+=("$ROOT/project.js")
    [[ -f "$ROOT/main.js"         ]] && SCRIPT_PATHS+=("$ROOT/main.js")
    [[ -d "$ROOT/assets"          ]] && ASSET_PATHS+=("$ROOT/assets")
    [[ -d "$ROOT/res"             ]] && ASSET_PATHS+=("$ROOT/res")
    [[ -d "$ROOT/subpackages"     ]] && ASSET_PATHS+=("$ROOT/subpackages")
    [[ -f "$ROOT/main.js"         ]] && KEY_PATHS+=("$ROOT/main.js")
    [[ -f "$ROOT/src/main.js"     ]] && KEY_PATHS+=("$ROOT/src/main.js")
    ;;
  3.x)
    # 3.x bundles live under assets/<bundle>/ each with a config.json
    if [[ -d "$ROOT/assets" ]]; then
      bundle_list=""
      while IFS= read -r -d '' cfg; do
        name=$(basename "$(dirname "$cfg")")
        bundle_list+="${name},"
        ASSET_PATHS+=("$(dirname "$cfg")")
      done < <(find "$ROOT/assets" -mindepth 2 -maxdepth 2 -name 'config.json' -print0 2>/dev/null)
      BUNDLES="${bundle_list%,}"
    fi
    [[ -f "$ROOT/application.js"     ]] && SCRIPT_PATHS+=("$ROOT/application.js")
    [[ -d "$ROOT/cocos-js"           ]] && SCRIPT_PATHS+=("$ROOT/cocos-js")
    [[ -f "$ROOT/src/settings.json"  ]] && SCRIPT_PATHS+=("$ROOT/src/settings.json")
    [[ -f "$ROOT/src/import-map.json" ]] && SCRIPT_PATHS+=("$ROOT/src/import-map.json")
    # Key candidates in 3.x
    [[ -f "$ROOT/application.js"     ]] && KEY_PATHS+=("$ROOT/application.js")
    [[ -f "$ROOT/src/settings.json"  ]] && KEY_PATHS+=("$ROOT/src/settings.json")
    [[ -d "$ROOT/cocos-js"           ]] && KEY_PATHS+=("$ROOT/cocos-js")
    ;;
esac

# Scan for .jsc presence
if find "$ROOT" -type f -name '*.jsc' -print -quit 2>/dev/null | grep -q .; then
  ENCRYPTED="yes"
fi

# --- Emit ---
echo
echo "ENGINE=$ENGINE"
echo "ENCRYPTED=$ENCRYPTED"
if [[ -n "$BUNDLES" ]]; then echo "BUNDLES=$BUNDLES"; fi
echo "WEB_MOBILE=$WEB_MOBILE"
echo "KEY_PATHS=$(IFS=,; echo "${KEY_PATHS[*]-}")"
echo "SCRIPT_PATHS=$(IFS=,; echo "${SCRIPT_PATHS[*]-}")"
echo "ASSET_PATHS=$(IFS=,; echo "${ASSET_PATHS[*]-}")"

if [[ "$ENGINE" == "unknown" ]]; then
  echo
  echo "*** Could not identify a Cocos Creator build layout. ***"
  echo "Expected one of:"
  echo "  2.3.x: src/settings.js + src/project.js + res/"
  echo "  2.4.x: main.js + settings.js + assets/"
  echo "  3.x:   assets/<bundle>/config.json (or application.js + cocos-js/)"
  exit 1
fi
