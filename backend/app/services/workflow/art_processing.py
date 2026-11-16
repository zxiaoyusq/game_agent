"""美术资源的确定性裁切和等比装配，不生成内容、不推测透明背景。"""

import hashlib
import io

from PIL import Image

MAX_IMAGE_BYTES = 10_000_000
MAX_IMAGE_EDGE = 8192
MAX_IMAGE_PIXELS = 16_777_216
IMAGE_FORMATS = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".webp": "WEBP"}
FORMAT_SUFFIXES = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}


def _dimensions(values: list[int], name: str) -> tuple[int, int]:
    """在分配画布前限制两边与总像素数，不能靠压缩文件大小判断内存规模。"""
    if len(values) != 2 or any(type(value) is not int or value <= 0 for value in values):
        raise ValueError(f"{name}必须是两个正整数 [宽, 高]")
    width, height = values
    if max(values) > MAX_IMAGE_EDGE or width * height > MAX_IMAGE_PIXELS:
        raise ValueError(f"{name}超过8192边长或16777216像素限制")
    return width, height


def _alpha_summary(image: Image.Image) -> dict:
    """按最终解码像素统计透明信息；不把存在alpha通道误报为已有透明背景。"""
    alpha = image.getchannel("A")
    histogram = alpha.histogram()
    return {"transparent_pixels": histogram[0], "opaque_pixels": histogram[255],
            "semitransparent_pixels": sum(histogram[1:255]), "extrema": list(alpha.getextrema()),
            "sha256": hashlib.sha256(alpha.tobytes()).hexdigest()}


def decode_art_image(content: bytes) -> tuple[Image.Image, str]:
    """按真实编码校验图片，兼容Cocos中使用.png名称的WebP，不接受其他格式或多帧。"""
    if len(content) > MAX_IMAGE_BYTES:
        raise ValueError("输入图片超过10MB限制")
    try:
        with Image.open(io.BytesIO(content)) as source:
            actual_format = source.format
            if actual_format not in FORMAT_SUFFIXES:
                raise ValueError("输入图片的真实编码只支持PNG/JPEG/WebP")
            _dimensions(list(source.size), "输入图片尺寸")
            if getattr(source, "n_frames", 1) != 1:
                raise ValueError("不能静默处理多帧图片，请明确提取所需动画帧")
            source.verify()
        # verify检查容器结构后必须重新打开；完整解码可再拦截损坏的像素数据。
        with Image.open(io.BytesIO(content)) as source:
            source.load()
            image = source.convert("RGBA")
    except (OSError, SyntaxError, Image.DecompressionBombError) as error:
        raise ValueError("输入文件不是完整、可安全解码的PNG/JPEG/WebP图片") from error
    return image, actual_format


def process_image_bytes(content: bytes, *, output_format: str,
                        crop: list[int] | None = None, target_size: list[int] | None = None) -> tuple[bytes, dict]:
    """只接受明确矩形和目标尺寸；缩放始终等比居中，空余区域透明，不裁掉主体。"""
    if output_format not in {"PNG", "WEBP"}:
        raise ValueError("输出只支持PNG/WebP")
    canvas_size = _dimensions(target_size, "目标尺寸") if target_size is not None else None
    image, actual_format = decode_art_image(content)
    source_size = image.size

    # 裁切只认调用方给出的像素矩形；越界直接报错，不补黑、不裁掉错误坐标。
    rectangle = crop if crop is not None else [0, 0, *source_size]
    if (len(rectangle) != 4 or any(type(value) is not int for value in rectangle)
            or rectangle[0] < 0 or rectangle[1] < 0 or rectangle[2] <= 0 or rectangle[3] <= 0):
        raise ValueError("裁切参数必须是非负起点及正尺寸 [x, y, 宽, 高]")
    x, y, width, height = rectangle
    if x + width > source_size[0] or y + height > source_size[1]:
        raise ValueError("裁切矩形超出原图范围")
    image = image.crop((x, y, x + width, y + height))
    resized_size = image.size
    offset = (0, 0)
    if canvas_size is not None:
        # 先等比缩放内容，再原样贴到透明画布；不把alpha当蒙版重复相乘。
        scale = min(canvas_size[0] / width, canvas_size[1] / height)
        resized_size = (max(1, min(canvas_size[0], round(width * scale))),
                        max(1, min(canvas_size[1], round(height * scale))))
        if resized_size != image.size:
            image = image.resize(resized_size, Image.Resampling.LANCZOS)
        offset = ((canvas_size[0] - resized_size[0]) // 2, (canvas_size[1] - resized_size[1]) // 2)
        canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        canvas.paste(image, offset)
        image = canvas

    # 无损编码避免把裁切和纹理处理混在一起；WebP显式保留全透明像素的RGB。
    output = io.BytesIO()
    if output_format == "WEBP":
        image.save(output, "WEBP", lossless=True, exact=True, method=6)
    else:
        image.save(output, "PNG")
    result = output.getvalue()
    if len(result) > MAX_IMAGE_BYTES:
        raise ValueError("处理后图片超过10MB限制，请减少实际交付范围")
    return result, {"input_format": actual_format, "input_width": source_size[0], "input_height": source_size[1],
                    "width": image.width, "height": image.height, "crop": list(rectangle),
                    "target_size": list(canvas_size) if canvas_size else None,
                    "resize_mode": "contain" if canvas_size else "none", "content_size": list(resized_size),
                    "offset": list(offset), "alpha": _alpha_summary(image), "output_format": output_format}
