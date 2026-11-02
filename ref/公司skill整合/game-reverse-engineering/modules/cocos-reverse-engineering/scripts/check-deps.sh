#!/usr/bin/env bash
# check-deps.sh — Verify dependencies for Cocos Creator reverse engineering.
# Emits machine-readable INSTALL_REQUIRED:<dep> / INSTALL_OPTIONAL:<dep> lines.
set -euo pipefail

REQUIRED_NODE_MAJOR=16
errors=0
missing_required=()
missing_optional=()

echo "=== Cocos Creator Reverse Engineering: Dependency Check ==="
echo

# --- Node.js ---
if command -v node &>/dev/null; then
  node_version=$(node --version | sed 's/v//' | cut -d. -f1)
  if [[ -n "$node_version" ]] && (( node_version >= REQUIRED_NODE_MAJOR )); then
    echo "[OK] Node.js $(node --version) detected"
  else
    echo "[WARN] Node.js $(node --version) detected but below required v$REQUIRED_NODE_MAJOR"
    errors=$((errors + 1))
    missing_required+=("node")
  fi
else
  echo "[MISSING] Node.js not installed or not in PATH"
  errors=$((errors + 1))
  missing_required+=("node")
fi

# --- npm ---
if command -v npm &>/dev/null; then
  echo "[OK] npm $(npm --version) detected"
else
  echo "[MISSING] npm not found (usually ships with Node.js)"
  errors=$((errors + 1))
  missing_required+=("npm")
fi

# --- cc-reverse ---
cc_reverse_ok=false
if command -v cc-reverse &>/dev/null; then
  cc_reverse_version=$(cc-reverse --version 2>/dev/null || echo "unknown")
  echo "[OK] cc-reverse $cc_reverse_version detected"
  cc_reverse_ok=true
else
  # Allow running without a global install if the user is sitting in a local clone.
  if [[ -n "${CC_REVERSE_HOME:-}" ]] && [[ -f "$CC_REVERSE_HOME/bin/cc-reverse.js" ]]; then
    echo "[OK] cc-reverse local clone at $CC_REVERSE_HOME"
    cc_reverse_ok=true
  elif [[ -f "$(pwd)/bin/cc-reverse.js" ]]; then
    echo "[OK] cc-reverse detected in current directory (local clone)"
    cc_reverse_ok=true
  else
    echo "[MISSING] cc-reverse not found — install with: npm install -g cc-reverse"
    errors=$((errors + 1))
    missing_required+=("cc-reverse")
  fi
fi

# --- Optional: 7z / unzip ---
if command -v unzip &>/dev/null; then
  echo "[OK] unzip detected"
else
  echo "[MISSING] unzip not found (optional — needed for ZIP/WAR archives)"
  missing_optional+=("unzip")
fi

if command -v 7z &>/dev/null; then
  echo "[OK] 7z detected (optional)"
else
  echo "[MISSING] 7z not found (optional — needed for .7z/.rar archives)"
  missing_optional+=("p7zip")
fi

# --- Optional: ffmpeg ---
if command -v ffmpeg &>/dev/null; then
  echo "[OK] ffmpeg detected (optional)"
else
  echo "[MISSING] ffmpeg not found (optional — useful for audio format conversion)"
  missing_optional+=("ffmpeg")
fi

# --- Optional: jq ---
if command -v jq &>/dev/null; then
  echo "[OK] jq detected (optional)"
else
  echo "[MISSING] jq not found (optional — makes 3.x config.json inspection easier)"
  missing_optional+=("jq")
fi

# --- Machine-readable summary ---
echo
if [[ ${#missing_required[@]} -gt 0 ]]; then
  for dep in "${missing_required[@]}"; do
    echo "INSTALL_REQUIRED:$dep"
  done
fi
if [[ ${#missing_optional[@]} -gt 0 ]]; then
  for dep in "${missing_optional[@]}"; do
    echo "INSTALL_OPTIONAL:$dep"
  done
fi

echo
if (( errors > 0 )); then
  echo "*** ${#missing_required[@]} required dependency/ies missing. ***"
  echo "Run install-dep.sh <name> to install, or see references/setup-guide.md."
  exit 1
fi

if [[ ${#missing_optional[@]} -gt 0 ]]; then
  echo "Required dependencies OK. ${#missing_optional[@]} optional dependency/ies missing."
  echo "Run install-dep.sh <name> to install optional tools."
else
  echo "All dependencies are installed. Ready to reverse."
fi
exit 0
