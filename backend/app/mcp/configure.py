"""生成内部 MCP 客户端配置；明文令牌只写入权限为 0600 的本机文件。"""

import argparse
import hashlib
import json
import os
import secrets
import shlex
import tempfile
from pathlib import Path

from app.config import DATA_DIR
from app.mcp.auth import MCPClient, MCPSettings, load_settings


def add_client(directory: Path, client_id: str, project_ids: list[str], can_create: bool,
               public_url: str) -> tuple[Path, Path]:
    """增添新身份，保留已有客户端；重复标识或现有凭据文件均拒绝覆盖。"""
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    config_path = directory / "server.json"
    previous = load_settings(config_path) if config_path.exists() else None
    if previous and previous.public_url.rstrip("/") != public_url.rstrip("/"):
        raise ValueError("已有配置的 public_url 不同，请显式编辑配置后重试")
    token = secrets.token_urlsafe(32)
    client = MCPClient(client_id=client_id, token_sha256=hashlib.sha256(token.encode()).hexdigest(),
                       project_ids=project_ids, can_create_projects=can_create)
    settings = MCPSettings(public_url=public_url, clients=[*(previous.clients if previous else []), client])
    # 先校验身份，再把它用作文件名，避免配置命令写到目标目录之外。
    credential_path = directory / f"{client.client_id}.env"
    descriptor = os.open(credential_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as target:
        target.write(f"GAME_AGENT_MCP_TOKEN={shlex.quote(token)}\nGAME_AGENT_MCP_URL={shlex.quote(public_url.rstrip('/') + '/')}\n")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory, delete=False) as target:
            temporary = Path(target.name)
            json.dump(settings.model_dump(), target, ensure_ascii=False, indent=2)
            target.write("\n")
        temporary.replace(config_path)
    except Exception:
        # 配置未成功提交时移除本次创建的凭据，避免留下不可用的半份配置。
        credential_path.unlink(missing_ok=True)
        raise
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)
    return config_path, credential_path


def main() -> None:
    """命令只显示文件位置，不在终端、日志或命令参数中回显令牌。"""
    parser = argparse.ArgumentParser(description="为可信内部客户端生成 MCP 访问配置")
    parser.add_argument("--directory", type=Path, default=DATA_DIR / "mcp", help="配置目录，默认 backend/data/mcp")
    parser.add_argument("--client-id", required=True, help="客户端标识，仅限小写字母、数字、下划线或短横线")
    parser.add_argument("--project-id", action="append", required=True, help="可重复指定项目；全部项目使用 '*'，请保留引号")
    parser.add_argument("--allow-create", action="store_true", help="允许创建项目，需要同时授权全部项目")
    parser.add_argument("--public-url", default="http://127.0.0.1:8003/mcp", help="外部 MCP 地址；远程访问必须为 HTTPS")
    args = parser.parse_args()
    try:
        config_path, credential_path = add_client(
            args.directory, args.client_id, args.project_id, args.allow_create, args.public_url,
        )
    except (OSError, ValueError):
        parser.exit(1, "配置生成失败：请检查项目权限、URL、重复身份和文件写入权限；已有配置不会被覆盖。\n")
    print(f"服务端配置：{config_path.resolve()}")
    print(f"客户端凭据：{credential_path.resolve()}（仅文件所有者可读写）")
    print("将服务端配置路径填入 GAME_MCP_CONFIG 后启动后端；客户端凭据仅交给对应调用方。")


if __name__ == "__main__":
    main()
