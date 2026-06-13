# Game Agent Backend

游戏 AI Agent 系统后端，FastAPI + Python 3.13。

## 启动

```bash
# 切换到 conda 313 环境
conda activate 313

# 安装依赖（首次）
cd backend
pip install -r requirements.txt

# 启动开发服务器（默认 8000 端口）
uvicorn app.main:app --reload --port 8000
```

启动后访问：
- `http://localhost:8000/` — 根路径，返回服务信息
- `http://localhost:8000/api/health` — 健康检查
- `http://localhost:8000/docs` — Swagger 自动文档

## 目录结构

```
backend/
├── app/
│   ├── main.py              FastAPI 入口
│   ├── config.py            配置（路径、CORS、API key）
│   ├── api/routes/          各模块 HTTP 路由
│   ├── models/              Pydantic schemas
│   ├── services/            业务逻辑
│   └── providers/           外部服务适配（LLM 等）
├── data/                    运行时本地状态（gitignore）
└── tests/
```

## 路由约定

所有业务路由都挂在 `/api` 前缀下：

- `/api/health`        健康检查
- `/api/planning/*`    策划 Agent
- `/api/art/*`         美术 Agent
- `/api/knowledge/*`   知识库
- `/api/tasks/*`       任务管理
- `/api/chat/*`        通用对话
