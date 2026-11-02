#!/usr/bin/env bash
# install-dep.sh — Install a single dependency for Cocos Creator reverse engineering.
# Usage: install-dep.sh <dep>
# Dependencies: node, npm, cc-reverse, unzip, p7zip, ffmpeg, jq
#
# Exit codes:
#   0 — installed successfully
#   1 — installation failed
#   2 — requires manual action (sudo needed but unavailable or declined)
set -euo pipefail

usage() {
  cat <<EOF
Usage: install-dep.sh <dependency>

Install a dependency required for Cocos Creator reverse engineering.

Available dependencies:
  node        Node.js runtime (v16+)
  npm         Node Package Manager (usually bundled with node)
  cc-reverse  The cc-reverse CLI (npm install -g cc-reverse)
  unzip       For extracting .zip archives
  p7zip       For extracting .7z/.rar archives
  ffmpeg      For optional audio conversion
  jq          For 3.x config.json inspection

The script detects your OS and package manager, then:
  - Uses brew / apt / dnf / pacman when available
  - Prefers user-local installs (npm -g goes through node)
  - Prints manual instructions if a step needs sudo and none is available
EOF
  exit 0
}

if [[ $# -lt 1 || "$1" == "-h" || "$1" == "--help" ]]; then
  usage
fi

DEP="$1"

# --- Detect environment ---
OS="unknown"
PKG_MANAGER="none"
HAS_SUDO=false

case "$(uname -s)" in
  Linux)  OS="linux" ;;
  Darwin) OS="macos" ;;
esac

if [[ "$OS" == "macos" ]]; then
  if command -v brew &>/dev/null; then PKG_MANAGER="brew"; fi
elif [[ "$OS" == "linux" ]]; then
  if   command -v apt-get &>/dev/null; then PKG_MANAGER="apt"
  elif command -v dnf     &>/dev/null; then PKG_MANAGER="dnf"
  elif command -v pacman  &>/dev/null; then PKG_MANAGER="pacman"
  elif command -v brew    &>/dev/null; then PKG_MANAGER="brew"
  fi
fi

if command -v sudo &>/dev/null; then
  if sudo -n true 2>/dev/null; then HAS_SUDO=true; fi
fi

echo "OS: $OS | Package manager: $PKG_MANAGER | sudo: $HAS_SUDO"
echo

manual_instructions() {
  echo "[MANUAL] sudo is required but unavailable. Run these manually:"
  echo
  echo "$1"
  exit 2
}

# --- Install handlers ---
install_node() {
  case "$PKG_MANAGER" in
    brew)   brew install node ;;
    apt)
      if $HAS_SUDO; then sudo apt-get update && sudo apt-get install -y nodejs npm
      else manual_instructions "sudo apt-get update && sudo apt-get install -y nodejs npm"
      fi ;;
    dnf)
      if $HAS_SUDO; then sudo dnf install -y nodejs npm
      else manual_instructions "sudo dnf install -y nodejs npm"
      fi ;;
    pacman)
      if $HAS_SUDO; then sudo pacman -S --noconfirm nodejs npm
      else manual_instructions "sudo pacman -S --noconfirm nodejs npm"
      fi ;;
    *)
      echo "[MANUAL] Install Node.js from https://nodejs.org/ (v16 or newer)."
      exit 2 ;;
  esac
}

install_cc_reverse() {
  if ! command -v npm &>/dev/null; then
    echo "npm is required to install cc-reverse. Installing node first..."
    install_node
  fi

  # Prefer a user-global install (no sudo) via npm's prefix.
  local npm_prefix
  npm_prefix=$(npm config get prefix 2>/dev/null || echo "")
  if [[ -z "$npm_prefix" || "$npm_prefix" == "/usr" || "$npm_prefix" == "/usr/local" ]]; then
    echo "Configuring npm to install globals into ~/.npm-global (avoids sudo)..."
    mkdir -p "$HOME/.npm-global"
    npm config set prefix "$HOME/.npm-global"
    echo "Add this to your shell profile if not already there:"
    echo '  export PATH="$HOME/.npm-global/bin:$PATH"'
    export PATH="$HOME/.npm-global/bin:$PATH"
  fi

  npm install -g cc-reverse
  echo
  echo "cc-reverse installed. Run 'cc-reverse --help' to verify."
}

install_unzip() {
  case "$PKG_MANAGER" in
    brew)   brew install unzip ;;
    apt)
      if $HAS_SUDO; then sudo apt-get install -y unzip
      else manual_instructions "sudo apt-get install -y unzip"
      fi ;;
    dnf)
      if $HAS_SUDO; then sudo dnf install -y unzip
      else manual_instructions "sudo dnf install -y unzip"
      fi ;;
    pacman)
      if $HAS_SUDO; then sudo pacman -S --noconfirm unzip
      else manual_instructions "sudo pacman -S --noconfirm unzip"
      fi ;;
    *) echo "[MANUAL] Install 'unzip' via your package manager."; exit 2 ;;
  esac
}

install_p7zip() {
  case "$PKG_MANAGER" in
    brew)   brew install p7zip ;;
    apt)
      if $HAS_SUDO; then sudo apt-get install -y p7zip-full
      else manual_instructions "sudo apt-get install -y p7zip-full"
      fi ;;
    dnf)
      if $HAS_SUDO; then sudo dnf install -y p7zip
      else manual_instructions "sudo dnf install -y p7zip"
      fi ;;
    pacman)
      if $HAS_SUDO; then sudo pacman -S --noconfirm p7zip
      else manual_instructions "sudo pacman -S --noconfirm p7zip"
      fi ;;
    *) echo "[MANUAL] Install 'p7zip' via your package manager."; exit 2 ;;
  esac
}

install_ffmpeg() {
  case "$PKG_MANAGER" in
    brew) brew install ffmpeg ;;
    apt)
      if $HAS_SUDO; then sudo apt-get install -y ffmpeg
      else manual_instructions "sudo apt-get install -y ffmpeg"
      fi ;;
    dnf)
      if $HAS_SUDO; then sudo dnf install -y ffmpeg
      else manual_instructions "sudo dnf install -y ffmpeg"
      fi ;;
    pacman)
      if $HAS_SUDO; then sudo pacman -S --noconfirm ffmpeg
      else manual_instructions "sudo pacman -S --noconfirm ffmpeg"
      fi ;;
    *) echo "[MANUAL] Install ffmpeg via your package manager."; exit 2 ;;
  esac
}

install_jq() {
  case "$PKG_MANAGER" in
    brew) brew install jq ;;
    apt)
      if $HAS_SUDO; then sudo apt-get install -y jq
      else manual_instructions "sudo apt-get install -y jq"
      fi ;;
    dnf)
      if $HAS_SUDO; then sudo dnf install -y jq
      else manual_instructions "sudo dnf install -y jq"
      fi ;;
    pacman)
      if $HAS_SUDO; then sudo pacman -S --noconfirm jq
      else manual_instructions "sudo pacman -S --noconfirm jq"
      fi ;;
    *) echo "[MANUAL] Install jq via your package manager."; exit 2 ;;
  esac
}

case "$DEP" in
  node|npm)     install_node ;;
  cc-reverse)   install_cc_reverse ;;
  unzip)        install_unzip ;;
  p7zip|7z)     install_p7zip ;;
  ffmpeg)       install_ffmpeg ;;
  jq)           install_jq ;;
  *)
    echo "Error: unknown dependency '$DEP'" >&2
    usage ;;
esac

echo
echo "Done. Re-run check-deps.sh to confirm."

