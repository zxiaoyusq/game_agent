#!/usr/bin/env bash
# find-assets.sh — Catalogue assets in a recovered Cocos Creator project.
#
# Prints a summary: counts per asset kind, file-size breakdown, unknown types.
set -euo pipefail

if [[ $# -lt 1 || "$1" == "-h" || "$1" == "--help" ]]; then
  cat <<EOF
Usage: find-assets.sh <assets-dir>

Catalogue a recovered Cocos Creator assets/ directory. Counts files by extension
and by detected asset kind (scene, prefab, sprite-frame, audio, animation,
Spine, DragonBones, texture, material, effect, mesh, particle, font, …).
EOF
  exit 0
fi

ROOT="$1"
if [[ ! -d "$ROOT" ]]; then
  echo "Error: not a directory: $ROOT" >&2
  exit 1
fi

echo "=== Asset catalogue for: $ROOT ==="
echo

total=$(find "$ROOT" -type f | wc -l | tr -d ' ')
total_size=$(du -sh "$ROOT" 2>/dev/null | awk '{print $1}')
echo "Total files: $total"
echo "Total size:  $total_size"
echo

echo "--- By extension ---"
# shellcheck disable=SC2016
find "$ROOT" -type f | sed -E 's/.*\.([A-Za-z0-9]+)$/\1/' | tr '[:upper:]' '[:lower:]' \
  | sort | uniq -c | sort -rn | head -20

echo
echo "--- By asset kind ---"

count_in() {
  local label="$1"; shift
  local total=0
  for d in "$@"; do
    if [[ -d "$ROOT/$d" ]]; then
      local c
      c=$(find "$ROOT/$d" -type f | wc -l | tr -d ' ')
      total=$((total + c))
    fi
  done
  printf "  %-20s %6d\n" "$label" "$total"
}

count_ext() {
  local label="$1"; shift
  local pattern="$1"
  local c
  c=$(find "$ROOT" -type f -name "$pattern" | wc -l | tr -d ' ')
  printf "  %-20s %6d\n" "$label" "$c"
}

count_ext "Scene (.fire)"        "*.fire"
count_ext "Scene (.scene)"       "*.scene"
count_ext "Prefab (.prefab)"     "*.prefab"
count_ext "Animation (.anim)"    "*.anim"
count_ext "Effect (.effect)"     "*.effect"
count_ext "Material (.mtl)"      "*.mtl"
count_ext "Mesh bin (.bin)"      "*.bin"
count_ext "CCON binary (.cconb)" "*.cconb"
count_ext "CCON text (.ccon)"    "*.ccon"
count_in  "Textures"             "Texture" "texture" "Textures"
count_in  "Audio"                "Audio" "audio"
count_in  "Spine"                "Spine" "spine"
count_in  "DragonBones"          "DragonBones" "dragonbones"
count_in  "Scripts"              "Scripts" "scripts"
count_in  "Resources bundle"     "resources"
count_in  "Main bundle"          "main"
count_in  "Internal bundle"      "internal"

echo
echo "--- Suspicious / unknown ---"
# .jsc still present = something wasn't decrypted
jsc_count=$(find "$ROOT" -type f -name '*.jsc' | wc -l | tr -d ' ')
if (( jsc_count > 0 )); then
  echo "  [WARN] $jsc_count .jsc files still present — decryption incomplete"
fi
# empty files
empty=$(find "$ROOT" -type f -empty | wc -l | tr -d ' ')
if (( empty > 0 )); then
  echo "  [WARN] $empty empty files"
fi
# huge binaries
echo "  Top 5 largest files:"
find "$ROOT" -type f -printf '%s %p\n' 2>/dev/null \
  | sort -rn | head -5 | awk '{
      size=$1; $1="";
      if (size > 1048576) printf "    %.1f MB  %s\n", size/1048576, $0;
      else if (size > 1024) printf "    %.1f KB  %s\n", size/1024, $0;
      else printf "    %d B   %s\n", size, $0;
    }'

echo
echo "Done."
