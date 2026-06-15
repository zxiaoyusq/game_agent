#!/usr/bin/env bash
# 一键同时启动 后端 (FastAPI) + 前端 (Vite) 的开发脚本。
#
# 使用方式：
#   ./dev.sh                # 同时启动前后端，Ctrl+C 一起退出
#   ./dev.sh backend        # 只起后端
#   ./dev.sh frontend       # 只起前端
#   BACKEND_PORT=8001 ./dev.sh   # 自定义后端端口（前端 vite 的 proxy 也会同步指过去）
#
# 默认端口：后端 8000，前端 由 vite 自行选择 (5173+)
# 日志文件：./logs/backend.log、./logs/frontend.log

set -u  # 未定义变量直接报错；不开 -e，因为我们要自己处理子进程退出

# ---- 路径常量 -------------------------------------------------------------

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"

BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

BACKEND_PORT="${BACKEND_PORT:-8000}"
CONDA_ENV="${CONDA_ENV:-base}"

# ---- 工具函数 -------------------------------------------------------------

c_red()    { printf "\033[31m%s\033[0m" "$*"; }
c_green()  { printf "\033[32m%s\033[0m" "$*"; }
c_yellow() { printf "\033[33m%s\033[0m" "$*"; }
c_blue()   { printf "\033[34m%s\033[0m" "$*"; }
c_dim()    { printf "\033[2m%s\033[0m" "$*"; }

info()  { echo "$(c_blue "[dev]") $*"; }
warn()  { echo "$(c_yellow "[dev]") $*"; }
error() { echo "$(c_red   "[dev]") $*" >&2; }

# 端口是否被占用
port_in_use() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

# 加载 conda（让 `conda activate` 在脚本里可用）
load_conda() {
  # 优先用 CONDA_EXE 推断；fallback 走 PATH
  local base
  if [[ -n "${CONDA_EXE:-}" ]]; then
    base="$(dirname "$(dirname "$CONDA_EXE")")"
  else
    base="$(conda info --base 2>/dev/null || true)"
  fi
  if [[ -z "$base" || ! -f "$base/etc/profile.d/conda.sh" ]]; then
    error "找不到 conda（CONDA_EXE 未设置且 \`conda info --base\` 无输出）"
    error "请确认已安装 miniconda/anaconda，或手动 source 后再执行此脚本"
    return 1
  fi
  # shellcheck disable=SC1091
  source "$base/etc/profile.d/conda.sh"
}

# ---- 启动函数 -------------------------------------------------------------

start_backend() {
  if port_in_use "$BACKEND_PORT"; then
    error "后端端口 $BACKEND_PORT 已被占用，请先释放或设置 BACKEND_PORT=其它端口"
    error "查看占用：lsof -nP -iTCP:$BACKEND_PORT -sTCP:LISTEN"
    return 1
  fi
  if [[ ! -f "$BACKEND_DIR/app/main.py" ]]; then
    error "未找到 $BACKEND_DIR/app/main.py，目录结构是否正确？"
    return 1
  fi

  load_conda || return 1
  info "激活 conda env: $(c_green "$CONDA_ENV")"
  conda activate "$CONDA_ENV" || { error "conda activate $CONDA_ENV 失败"; return 1; }

  info "启动后端 uvicorn @ $(c_green "127.0.0.1:$BACKEND_PORT")，日志：$(c_dim "$BACKEND_LOG")"
  # cd 到 backend 目录，让 app.main 的相对路径 / 数据目录都正确
  (
    cd "$BACKEND_DIR" &&
    exec uvicorn app.main:app --reload --port "$BACKEND_PORT"
  ) >"$BACKEND_LOG" 2>&1 &
  BACKEND_PID=$!
  echo "$BACKEND_PID" > "$LOG_DIR/backend.pid"
}

start_frontend() {
  if [[ ! -f "$FRONTEND_DIR/package.json" ]]; then
    error "未找到 $FRONTEND_DIR/package.json"
    return 1
  fi
  if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
    warn "未发现 node_modules，先执行 npm install（首次启动）"
    (cd "$FRONTEND_DIR" && npm install) || { error "npm install 失败"; return 1; }
  fi

  info "启动前端 vite，日志：$(c_dim "$FRONTEND_LOG")"
  (
    cd "$FRONTEND_DIR" &&
    exec npm run dev
  ) >"$FRONTEND_LOG" 2>&1 &
  FRONTEND_PID=$!
  echo "$FRONTEND_PID" > "$LOG_DIR/frontend.pid"
}

# ---- 清理：脚本退出时同步 kill 子进程 -------------------------------------

cleanup() {
  # 防止 EXIT + INT 同时触发导致重复进入
  trap '' EXIT INT TERM
  echo
  info "正在停止子进程…"
  # tail / watch：必须先杀，否则会变成孤儿继续追写日志，
  # 下次再启动 dev.sh 就会出现"同一条 log 被打印多遍"的现象
  for pid in "${TAIL_PID:-}" "${WATCH_PID:-}" "${BACKEND_PID:-}" "${FRONTEND_PID:-}"; do
    [[ -z "$pid" ]] && continue
    if kill -0 "$pid" 2>/dev/null; then
      # 先 SIGTERM；若 vite/uvicorn 启动了子进程，用 pkill -P 一并收掉子进程
      kill "$pid" 2>/dev/null || true
      pkill -P "$pid" 2>/dev/null || true
    fi
  done
  rm -f "$LOG_DIR/backend.pid" "$LOG_DIR/frontend.pid"
  info "已退出。"
}
trap cleanup EXIT INT TERM

# ---- 主流程 ---------------------------------------------------------------

mode="${1:-all}"
BACKEND_PID=""
FRONTEND_PID=""

case "$mode" in
  backend)
    start_backend || exit 1
    ;;
  frontend)
    start_frontend || exit 1
    ;;
  all|"")
    start_backend  || exit 1
    start_frontend || exit 1
    ;;
  *)
    error "未知参数：$mode"
    echo "用法：$0 [backend|frontend|all]"
    exit 2
    ;;
esac

info "$(c_green "全部启动完成")。"
echo
echo "   后端: http://127.0.0.1:$BACKEND_PORT/docs"
echo "   前端: 见上方 vite 输出的 Local 地址（默认 http://localhost:5173/）"
echo
info "实时日志（Ctrl+C 退出）："
echo

# 同时跟随两份日志；--pid 让某一边 crash 时自动结束 tail，从而触发 cleanup
TAIL_TARGETS=()
[[ -n "$BACKEND_PID"  ]] && TAIL_TARGETS+=("$BACKEND_LOG")
[[ -n "$FRONTEND_PID" ]] && TAIL_TARGETS+=("$FRONTEND_LOG")

# wait 在收到 SIGINT 时会立刻返回并触发 trap
tail -n 0 -F "${TAIL_TARGETS[@]}" &
TAIL_PID=$!

# 任意一个子进程退出，tail 也跟着结束
( while true; do
    [[ -n "$BACKEND_PID"  ]] && ! kill -0 "$BACKEND_PID"  2>/dev/null && break
    [[ -n "$FRONTEND_PID" ]] && ! kill -0 "$FRONTEND_PID" 2>/dev/null && break
    sleep 1
  done
  kill "$TAIL_PID" 2>/dev/null || true
) &
WATCH_PID=$!

wait "$TAIL_PID" 2>/dev/null || true
kill "$WATCH_PID" 2>/dev/null || true
