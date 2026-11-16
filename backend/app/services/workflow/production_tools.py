"""生产工具：显式安装网页验收依赖、调用服务器图片服务，不借模型身份访问宿主工具。"""

import asyncio
import hashlib
import io
import json
import os
from pathlib import Path

from langchain_core.tools import tool
from pydantic import StrictInt

from app.services.workflow.codex_model import stop_process
from app.services.workflow.model_runtime import safe_error
from app.services.workflow.workspace import checked_child


def validation_environment() -> dict:
    """只传递操作系统和区域环境，避免遗漏非标准命名的服务凭据。"""
    allowed = {"PATH", "HOME", "USER", "LOGNAME", "SHELL", "LANG", "LANGUAGE", "TZ",
               "TERM", "COLORTERM", "TMPDIR", "TMP", "TEMP", "SYSTEMROOT", "COMSPEC", "PATHEXT",
               "LC_ALL", "LC_CTYPE", "LC_NUMERIC", "LC_TIME", "LC_COLLATE", "LC_MONETARY", "LC_MESSAGES"}
    return {key: value for key, value in os.environ.items() if key.upper() in allowed}


def _workspace_path(workspace: Path, relative: str) -> Path:
    """只接受明确的工作区相对路径，拒绝隐藏路径、目录穿越和所有符号链接。"""
    if (not isinstance(relative, str) or not relative or len(relative) > 1024 or "\\" in relative
            or any(ord(char) < 32 for char in relative)
            or any(not part or part.startswith(".") or ":" in part for part in relative.split("/"))):
        raise ValueError("路径必须是工作区内非隐藏的普通相对路径")
    raw = Path(relative)
    if raw.is_absolute() or not raw.parts or any(part.startswith(".") for part in raw.parts):
        raise ValueError("路径必须是工作区内非隐藏的相对路径，不能包含目录穿越")
    if workspace.is_symlink():
        raise ValueError("生产工作区不能使用符号链接")
    cursor = workspace
    for part in raw.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError("生产文件路径不能使用符号链接")
    return checked_child(workspace, relative)


def create_production_tools(workspace: Path, run: dict, emit):
    @tool
    async def prepare_web_runtime() -> str:
        """仅代码或测试阶段可用：为本项目安装锁定的Playwright1.63.0浏览器测试依赖；保留package.json脚本，禁用安装生命周期。之后自行编写真实浏览器测试并运行npm run check。"""
        if run.get("stage") not in {"code", "test"}:
            raise ValueError("网页测试依赖只在代码或测试阶段准备")
        package = _workspace_path(workspace, "package.json")
        if not package.is_file():
            raise ValueError("请先写入本项目package.json，再准备浏览器测试依赖")
        if not isinstance(json.loads(package.read_text(encoding="utf-8")), dict):
            raise ValueError("package.json必须是JSON对象")
        # npm会写入锁文件和依赖目录，因此这些入口也不能指向工作区外。
        for name in ("package-lock.json", "npm-shrinkwrap.json", "node_modules"):
            _workspace_path(workspace, name)
        process = await asyncio.create_subprocess_exec(
            "npm", "install", "--ignore-scripts", "--no-audit", "--no-fund", "--save-dev", "--save-exact", "playwright@1.63.0",
            cwd=workspace, env=validation_environment(), stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT, start_new_session=True,
        )
        try:
            output, _ = await asyncio.wait_for(process.communicate(), 180)
        finally:
            await stop_process(process)
        result = {"exit_code": process.returncode, "output": output.decode(errors="replace")[-10000:],
                  "dependency": "playwright@1.63.0", "browser": "使用本机已安装的Chromium；npm run check仍须实际启动验证"}
        emit("runtime_prepared", "网页测试依赖准备完成" if process.returncode == 0 else "网页测试依赖安装失败", result)
        return json.dumps(result, ensure_ascii=False)

    @tool
    async def generate_art_image(prompt: str, destination: str, size: str = "1536x1024",
                                 quality: str = "high", reference_paths: list[str] | None = None) -> str:
        """调用工程配置的图片API生成或参考图编辑，保存WebP/PNG到public/assets或assets。可传当前工作区内参考图片路径；返回真实文件SHA256，可交接资源清单。"""
        from PIL import Image
        from app.services import art_image
        from app.services.workflow.art_processing import IMAGE_FORMATS, FORMAT_SUFFIXES, MAX_IMAGE_BYTES, decode_art_image

        if run.get("stage") != "art":
            raise ValueError("AI图片生产属于美术阶段；修改已确认美术须重跑对应阶段")
        raw = Path(destination)
        if not (raw.parts[:2] == ("public", "assets") or raw.parts[:1] == ("assets",)):
            raise ValueError("生成图片仅能写入public/assets或assets目录")
        target = _workspace_path(workspace, destination)
        if target.suffix.lower() not in {".webp", ".png"}:
            raise ValueError("输出格式仅支持WebP或PNG")
        if target.exists():
            raise ValueError("目标已存在，请用新的版本文件名保留之前的候选")
        reference_names = reference_paths or []
        if len(reference_names) > 4:
            raise ValueError("一次最多使用4张参考图")
        references = []
        reference_details = []
        for name in reference_names:
            source = _workspace_path(workspace, name)
            suffix = source.suffix.lower()
            if not source.is_file() or suffix not in IMAGE_FORMATS or source.stat().st_size > MAX_IMAGE_BYTES:
                raise ValueError("参考图须为不超过10MB的PNG/JPEG/WebP文件")
            data = source.read_bytes()
            # 原包可能使用.png名保存WebP；按真实编码上传，不改原始文件或像素。
            decoded, actual_format = decode_art_image(data)
            content_type = f"image/{actual_format.lower()}"
            upload_name = source.stem + FORMAT_SUFFIXES[actual_format]
            references.append(art_image.ReferenceImage(upload_name, data, content_type))
            reference_details.append({"path": name, "sha256": hashlib.sha256(data).hexdigest(),
                                      "size": len(data), "width": decoded.width, "height": decoded.height,
                                      "format": actual_format, "content_type": content_type, "upload_filename": upload_name})
            decoded.close()
        emit("image_generation_started", "开始通过工程图片API生产美术", {
            "destination": destination, "size": size, "quality": quality, "prompt": prompt,
            "references": reference_paths or [], "reference_images": reference_details, **art_image.provider_info(),
        })
        try:
            if references:
                raw_image = await art_image.edit(prompt=prompt, size=size, quality=quality, references=references)
            else:
                raw_image = await art_image.generate(prompt=prompt, size=size, quality=quality)
        except Exception as error:
            raise RuntimeError(safe_error(error)) from None
        # 先完成解码和编码再创建文件；API错误或损坏图片不留下伪成功产物。
        with Image.open(io.BytesIO(raw_image)) as image:
            image.load()
            output = io.BytesIO()
            if target.suffix.lower() == ".webp":
                image.save(output, "WEBP", quality=88, method=6)
            else:
                image.save(output, "PNG")
            width, height = image.size
        content = output.getvalue()
        # 远程生成期间目标可能已被其他工具创建；独占写入不能覆盖这些结果。
        target = _workspace_path(workspace, destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        _workspace_path(workspace, destination)
        with target.open("xb") as destination_file:
            destination_file.write(content)
        result = {"path": target.relative_to(workspace).as_posix(), "size": len(content),
                  "width": width, "height": height,
                  "sha256": hashlib.sha256(content).hexdigest(), "source": "工程图片API真实生成",
                  "reference_images": reference_details, **art_image.provider_info()}
        emit("image_generated", "图片API已生成并保存真实资源", result)
        return json.dumps(result, ensure_ascii=False)

    @tool
    def process_art_image(source_path: str, destination: str, crop: list[StrictInt] | None = None,
                          target_size: list[StrictInt] | None = None) -> str:
        """美术阶段确定性处理工作区PNG/JPEG/WebP：crop=[x,y,宽,高]精确裁切；可选target_size=[宽,高]等比居中到透明画布。无损PNG/WebP写入public/assets，不覆盖、不拉伸、不自动抠底。"""
        from app.services.workflow.art_processing import IMAGE_FORMATS, MAX_IMAGE_BYTES, process_image_bytes

        if run.get("stage") != "art":
            raise ValueError("图片裁切与尺寸装配只允许在美术阶段执行")
        source = _workspace_path(workspace, source_path)
        target = _workspace_path(workspace, destination)
        if Path(destination).parts[:2] != ("public", "assets") or target.suffix.lower() not in {".png", ".webp"}:
            raise ValueError("处理图片仅能写入public/assets内的PNG/WebP文件")
        if target.exists():
            raise ValueError("目标已存在，请使用新的候选文件名，不能覆盖已有美术")
        if not source.is_file() or source.suffix.lower() not in IMAGE_FORMATS or source.stat().st_size > MAX_IMAGE_BYTES:
            raise ValueError("输入须为工作区内不超过10MB的PNG/JPEG/WebP文件")
        content = source.read_bytes()
        processed, details = process_image_bytes(content, output_format=IMAGE_FORMATS[target.suffix.lower()],
                                                  crop=crop, target_size=target_size)
        # 解码、参数校验和编码全部成功后才写文件；独占创建并重查路径防止覆盖其他候选。
        target = _workspace_path(workspace, destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        _workspace_path(workspace, destination)
        with target.open("xb") as output:
            output.write(processed)
        result = {"path": target.relative_to(workspace).as_posix(), "size": len(processed),
                  "sha256": hashlib.sha256(processed).hexdigest(), "source_path": source_path,
                  "source_sha256": hashlib.sha256(content).hexdigest(), "source_bytes": len(content),
                  "source": "工作区图片确定性裁切与等比装配", "provenance": "deterministic_image_processing", **details}
        emit("image_processed", "图片已按明确矩形和尺寸处理并保存", result)
        return json.dumps(result, ensure_ascii=False)

    return [prepare_web_runtime, generate_art_image, process_art_image]
