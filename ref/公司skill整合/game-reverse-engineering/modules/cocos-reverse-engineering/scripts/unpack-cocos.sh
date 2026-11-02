#!/usr/bin/env bash
# unpack-cocos.sh — Drive cc-reverse to reverse a Cocos Creator build.
#
# Handles engine-version autodetection, XXTEA decryption, and output layout.
set -euo pipefail

usage() {
  cat <<EOF
Usage: unpack-cocos.sh [OPTIONS] <path>

Reverse a Cocos Creator build into an editable project.

Arguments:
  <path>                Path to the build directory.

Options:
  -o, --output DIR      Output directory (default: <name>-extracted)
  -k, --key KEY         XXTEA key for decrypting .jsc files
      --version-hint V  Force engine version: 2.3.x, 2.4.x, or 3.x
      --bundle NAME     3.x only; unpack only this bundle (repeatable)
      --assets-only     Skip script pass
      --scripts-only    Skip asset pass
      --verbose         Verbose output
      --cc-reverse-bin PATH  Override which cc-reverse to run
  -h, --help            Show this help

Environment:
  CC_REVERSE_HOME  Path to a cc-reverse clone (used if cc-reverse is not on PATH).
EOF
  exit 0
}

OUTPUT_DIR=""
KEY=""
VERSION_HINT=""
BUNDLES=()
ASSETS_ONLY=false
SCRIPTS_ONLY=false
VERBOSE=false
CC_REVERSE_BIN=""
INPUT_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)         OUTPUT_DIR="$2"; shift 2 ;;
    -k|--key)            KEY="$2"; shift 2 ;;
    --version-hint)      VERSION_HINT="$2"; shift 2 ;;
    --bundle)            BUNDLES+=("$2"); shift 2 ;;
    --assets-only)       ASSETS_ONLY=true; shift ;;
    --scripts-only)      SCRIPTS_ONLY=true; shift ;;
    --verbose)           VERBOSE=true; shift ;;
    --cc-reverse-bin)    CC_REVERSE_BIN="$2"; shift 2 ;;
    -h|--help)           usage ;;
    -*)                  echo "Unknown option: $1" >&2; usage ;;
    *)                   INPUT_PATH="$1"; shift ;;
  esac
done

if [[ -z "$INPUT_PATH" ]]; then
  echo "Error: no input path given" >&2
  usage
fi

if [[ ! -d "$INPUT_PATH" ]]; then
  echo "Error: not a directory: $INPUT_PATH" >&2
  exit 1
fi

INPUT_PATH=$(cd "$INPUT_PATH" && pwd)
BASENAME=$(basename "$INPUT_PATH")
[[ -z "$OUTPUT_DIR" ]] && OUTPUT_DIR="${BASENAME}-extracted"

# --- Resolve cc-reverse binary ---
if [[ -z "$CC_REVERSE_BIN" ]]; then
  if command -v cc-reverse &>/dev/null; then
    CC_REVERSE_BIN="cc-reverse"
  elif [[ -n "${CC_REVERSE_HOME:-}" ]] && [[ -f "$CC_REVERSE_HOME/bin/cc-reverse.js" ]]; then
    CC_REVERSE_BIN="node $CC_REVERSE_HOME/bin/cc-reverse.js"
  elif [[ -f "$(pwd)/bin/cc-reverse.js" ]]; then
    CC_REVERSE_BIN="node $(pwd)/bin/cc-reverse.js"
  else
    echo "Error: cc-reverse not found. Install with: npm install -g cc-reverse" >&2
    echo "  or set CC_REVERSE_HOME to a local clone of https://github.com/Crain99/cc-reverse" >&2
    exit 1
  fi
fi

echo "=== cc-reverse unpack ==="
echo "Input:   $INPUT_PATH"
echo "Output:  $OUTPUT_DIR"
echo "Engine:  ${VERSION_HINT:-auto}"
echo "Key:     $([[ -n "$KEY" ]] && echo '[provided]' || echo '[none / auto-extract]')"
[[ ${#BUNDLES[@]} -gt 0 ]] && echo "Bundles: ${BUNDLES[*]}"
echo

# --- Build cc-reverse args ---
ARGS=(--path "$INPUT_PATH" --output "$OUTPUT_DIR")
[[ -n "$KEY"           ]] && ARGS+=(--key "$KEY")
[[ -n "$VERSION_HINT"  ]] && ARGS+=(--version-hint "$VERSION_HINT")
[[ "$VERBOSE" == true  ]] && ARGS+=(--verbose)
[[ "$ASSETS_ONLY" == true  ]] && ARGS+=(--assets-only)
[[ "$SCRIPTS_ONLY" == true ]] && ARGS+=(--scripts-only)
for b in "${BUNDLES[@]-}"; do
  [[ -n "$b" ]] && ARGS+=(--bundle "$b")
done

echo "Running: $CC_REVERSE_BIN ${ARGS[*]}"
echo
# shellcheck disable=SC2086
$CC_REVERSE_BIN "${ARGS[@]}"
RC=$?

if (( RC != 0 )); then
  echo
  echo "*** cc-reverse exited with status $RC ***" >&2
  exit $RC
fi

# --- Post: emit the recovery report if cc-reverse didn't ---
REPORT="$OUTPUT_DIR/RECOVERY_REPORT.md"
if [[ ! -f "$REPORT" ]]; then
  {
    echo "# Recovery Report"
    echo
    echo "- Input: \`$INPUT_PATH\`"
    echo "- Engine hint: ${VERSION_HINT:-auto}"
    echo "- Key supplied: $([[ -n "$KEY" ]] && echo yes || echo no)"
    echo
    echo "## Output tree"
    echo
    (cd "$OUTPUT_DIR" && find . -maxdepth 3 -type d | head -40 | sed 's|^\./||')
  } > "$REPORT"
fi

echo
echo "=== Done. Output: $OUTPUT_DIR ==="
echo "Report: $REPORT"
