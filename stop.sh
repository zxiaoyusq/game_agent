#!/usr/bin/env bash
# 一键停止本项目进程。
#
# 用法：
#   ./stop.sh local        # 停止本地模式进程
#   ./stop.sh domain       # 停止域名模式进程及旧的 80 端口临时服务
#   ./stop.sh all          # 停止两种模式及旧版本脚本残留进程（默认）

set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$ROOT_DIR/logs"
STOP_MODE="${1:-all}"

case "$STOP_MODE" in
  local|domain|all) ;;
  *)
    echo "用法: $0 [local|domain|all]" >&2
    exit 2
    ;;
esac

c_green()  { printf "\033[32m%s\033[0m" "$*"; }
c_yellow() { printf "\033[33m%s\033[0m" "$*"; }
c_blue()   { printf "\033[34m%s\033[0m" "$*"; }
info() { echo "$(c_blue "[stop]") $*"; }
warn() { echo "$(c_yellow "[stop]") $*"; }

pid_alive() {
  local pid="$1"
  [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null
}

stop_pid() {
  local name="$1"
  local pid_file="$2"
  local pid pgid

  [[ -f "$pid_file" ]] || return 0
  pid="$(tr -d '[:space:]' < "$pid_file")"
  if ! pid_alive "$pid"; then
    rm -f "$pid_file"
    return 0
  fi

  info "停止 $name (pid=$pid)"
  pgid="$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' ')"
  if [[ -n "$pgid" ]]; then
    kill -- "-$pgid" 2>/dev/null || kill "$pid" 2>/dev/null || true
  else
    kill "$pid" 2>/dev/null || true
  fi

  for _ in $(seq 1 20); do
    pid_alive "$pid" || break
    sleep 0.2
  done
  if pid_alive "$pid"; then
    warn "$name 未正常退出，强制停止"
    [[ -n "$pgid" ]] && kill -9 -- "-$pgid" 2>/dev/null || kill -9 "$pid" 2>/dev/null || true
  fi
  rm -f "$pid_file"
}

stop_mode() {
  local mode="$1"

  stop_pid "$mode 模式日志进程" "$LOG_DIR/tail-$mode.pid"
  stop_pid "$mode 模式看门狗" "$LOG_DIR/watch-$mode.pid"
  stop_pid "$mode 模式前端" "$LOG_DIR/frontend-$mode.pid"
  stop_pid "$mode 模式后端" "$LOG_DIR/backend-$mode.pid"
}

stop_legacy_domain_service() {
  command -v systemctl >/dev/null 2>&1 || return 0
  if systemctl is-active --quiet game-agent-frontend-80.service 2>/dev/null; then
    info "停止旧的域名前端服务 game-agent-frontend-80.service"
    systemctl stop game-agent-frontend-80.service || warn "停止 systemd 服务失败，可能需要 sudo/root 权限"
  fi
}

stop_legacy_pid_files() {
  stop_pid "旧版日志进程" "$LOG_DIR/tail.pid"
  stop_pid "旧版看门狗" "$LOG_DIR/watch.pid"
  stop_pid "旧版 Cloudflare 隧道" "$LOG_DIR/cloudflared.pid"
  stop_pid "旧版前端" "$LOG_DIR/frontend.pid"
  stop_pid "旧版前端 80" "$LOG_DIR/frontend-80.pid"
  stop_pid "旧版后端" "$LOG_DIR/backend.pid"
}

mkdir -p "$LOG_DIR"
case "$STOP_MODE" in
  local)
    stop_mode local
    ;;
  domain)
    stop_legacy_domain_service
    stop_mode domain
    ;;
  all)
    stop_legacy_domain_service
    stop_mode local
    stop_mode domain
    stop_legacy_pid_files
    ;;
esac

info "$(c_green "停止完成")"
