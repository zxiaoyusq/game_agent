#!/usr/bin/env bash
# 一键启动：可选择本地开发或固定域名部署。
#
# 用法：
#   ./start.sh local       # 本地模式：前端 http://127.0.0.1:15173/
#   ./start.sh domain      # 域名模式：监听 24681，由 http://pagent.ahagamecenter.com/ 转发访问
#   ./start.sh             # 默认域名模式，保持原有部署习惯
#
# 可选环境变量：
#   CONDA_ENV=base BACKEND_PORT=8003 FRONTEND_PORT=15173 ./start.sh local
#   CONDA_ENV=base BACKEND_PORT=8003 FRONTEND_PORT=24681 ./start.sh domain

set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_DIR="$ROOT_DIR/logs"
FRONTEND_DOMAIN="${FRONTEND_DOMAIN:-pagent.ahagamecenter.com}"
BACKEND_PORT="${BACKEND_PORT:-8003}"
CONDA_ENV="${CONDA_ENV:-base}"

DEPLOY_MODE="${1:-domain}"
case "$DEPLOY_MODE" in
  local)
    FRONTEND_PORT="${FRONTEND_PORT:-15173}"
    FRONTEND_HOST="127.0.0.1"
    FRONTEND_URL="http://127.0.0.1:$FRONTEND_PORT/"
    ;;
  domain)
    FRONTEND_PORT="${FRONTEND_PORT:-24681}"
    FRONTEND_HOST="0.0.0.0"
    FRONTEND_URL="http://$FRONTEND_DOMAIN/"
    ;;
  *)
    echo "用法: $0 [local|domain]" >&2
    exit 2
    ;;
esac

mkdir -p "$LOG_DIR"
BACKEND_LOG="$LOG_DIR/backend-$DEPLOY_MODE.log"
FRONTEND_LOG="$LOG_DIR/frontend-$DEPLOY_MODE.log"
BACKEND_PID_FILE="$LOG_DIR/backend-$DEPLOY_MODE.pid"
FRONTEND_PID_FILE="$LOG_DIR/frontend-$DEPLOY_MODE.pid"
TAIL_PID_FILE="$LOG_DIR/tail-$DEPLOY_MODE.pid"
WATCH_PID_FILE="$LOG_DIR/watch-$DEPLOY_MODE.pid"

c_red()    { printf "\033[31m%s\033[0m" "$*"; }
c_green()  { printf "\033[32m%s\033[0m" "$*"; }
c_yellow() { printf "\033[33m%s\033[0m" "$*"; }
c_blue()   { printf "\033[34m%s\033[0m" "$*"; }
c_dim()    { printf "\033[2m%s\033[0m" "$*"; }
info()  { echo "$(c_blue "[start]") $*"; }
warn()  { echo "$(c_yellow "[start]") $*"; }
error() { echo "$(c_red "[start]") $*" >&2; }

port_in_use() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

load_conda() {
  local conda_base
  if [[ -n "${CONDA_EXE:-}" ]]; then
    conda_base="$(dirname "$(dirname "$CONDA_EXE")")"
  else
    conda_base="$(conda info --base 2>/dev/null || true)"
  fi

  if [[ -z "$conda_base" || ! -f "$conda_base/etc/profile.d/conda.sh" ]]; then
    error "找不到 conda（CONDA_EXE 未设置且 conda info --base 无输出）"
    return 1
  fi

  # shellcheck disable=SC1091
  source "$conda_base/etc/profile.d/conda.sh"
}

kill_pg_or_pid() {
  local pid="$1"
  local pgid

  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null || return 0
  pgid="$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' ')"
  if [[ -n "$pgid" ]]; then
    kill -- "-$pgid" 2>/dev/null || kill "$pid" 2>/dev/null || true
  else
    kill "$pid" 2>/dev/null || true
  fi
}

remove_own_pid_file() {
  local pid_file="$1"
  local pid="$2"

  [[ -n "$pid" && -f "$pid_file" ]] || return 0
  [[ "$(tr -d '[:space:]' < "$pid_file")" == "$pid" ]] && rm -f "$pid_file"
}

cleanup() {
  trap '' EXIT INT TERM
  echo
  info "正在停止 $DEPLOY_MODE 模式进程..."
  for pid in "${TAIL_PID:-}" "${WATCH_PID:-}" "${FRONTEND_PID:-}" "${BACKEND_PID:-}"; do
    kill_pg_or_pid "$pid"
  done
  remove_own_pid_file "$BACKEND_PID_FILE" "${BACKEND_PID:-}"
  remove_own_pid_file "$FRONTEND_PID_FILE" "${FRONTEND_PID:-}"
  remove_own_pid_file "$TAIL_PID_FILE" "${TAIL_PID:-}"
  remove_own_pid_file "$WATCH_PID_FILE" "${WATCH_PID:-}"
  info "已退出。"
}
trap cleanup EXIT INT TERM

start_backend() {
  if port_in_use "$BACKEND_PORT"; then
    error "后端端口 $BACKEND_PORT 已被占用。请先执行 ./stop.sh all，或设置 BACKEND_PORT。"
    return 1
  fi
  if [[ ! -f "$BACKEND_DIR/app/main.py" ]]; then
    error "未找到 $BACKEND_DIR/app/main.py"
    return 1
  fi

  load_conda || return 1
  info "激活 conda 环境: $(c_green "$CONDA_ENV")"
  conda activate "$CONDA_ENV" || { error "conda activate $CONDA_ENV 失败"; return 1; }

  info "启动后端 @ $(c_green "127.0.0.1:$BACKEND_PORT")，日志: $(c_dim "$BACKEND_LOG")"
  (
    cd "$BACKEND_DIR" &&
    exec setsid uvicorn app.main:app --host 127.0.0.1 --port "$BACKEND_PORT"
  ) >"$BACKEND_LOG" 2>&1 &
  BACKEND_PID=$!
  echo "$BACKEND_PID" > "$BACKEND_PID_FILE"
}

start_frontend() {
  if [[ ! -f "$FRONTEND_DIR/package.json" ]]; then
    error "未找到 $FRONTEND_DIR/package.json"
    return 1
  fi
  if port_in_use "$FRONTEND_PORT"; then
    error "前端端口 $FRONTEND_PORT 已被占用。请先执行 ./stop.sh $DEPLOY_MODE，或设置 FRONTEND_PORT。"
    return 1
  fi
  if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    warn "未发现 node_modules，正在执行 npm install..."
    (cd "$FRONTEND_DIR" && npm install) || { error "npm install 失败"; return 1; }
  fi

  info "启动前端 @ $(c_green "$FRONTEND_HOST:$FRONTEND_PORT")，日志: $(c_dim "$FRONTEND_LOG")"
  (
    cd "$FRONTEND_DIR" &&
    exec env BACKEND_PORT="$BACKEND_PORT" setsid npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" --strictPort
  ) >"$FRONTEND_LOG" 2>&1 &
  FRONTEND_PID=$!
  echo "$FRONTEND_PID" > "$FRONTEND_PID_FILE"
}

BACKEND_PID=""
FRONTEND_PID=""
TAIL_PID=""
WATCH_PID=""

info "启动模式: $(c_green "$DEPLOY_MODE")"
start_backend || exit 1
start_frontend || exit 1

info "$(c_green "全部启动完成")"
echo
echo "   后端 API:  http://127.0.0.1:$BACKEND_PORT/docs"
echo "   前端入口:  $FRONTEND_URL"
echo
info "实时日志（Ctrl+C 将停止当前模式）："
echo

tail -n 0 -F "$BACKEND_LOG" "$FRONTEND_LOG" &
TAIL_PID=$!
echo "$TAIL_PID" > "$TAIL_PID_FILE"

(
  while true; do
    ! kill -0 "$BACKEND_PID" 2>/dev/null && break
    ! kill -0 "$FRONTEND_PID" 2>/dev/null && break
    sleep 2
  done
  kill "$TAIL_PID" 2>/dev/null || true
) &
WATCH_PID=$!
echo "$WATCH_PID" > "$WATCH_PID_FILE"

wait "$TAIL_PID" 2>/dev/null || true
kill "$WATCH_PID" 2>/dev/null || true
