"""图片服务协议回归：只替代HTTP出口，校验生成、编辑、认证和错误脱敏。"""

import base64
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from app.services import art_image


class ImageProviderTests(unittest.IsolatedAsyncioTestCase):
    def response(self):
        return httpx.Response(200, json={"data": [{"b64_json": base64.b64encode(b"image-fixture").decode()}]})

    async def test_openai_generation_and_edit_share_explicit_model_and_bearer(self):
        """两个操作都使用同一个已选网关，参考图必须真实进入multipart。"""
        with patch.multiple(art_image, IMAGE_PROVIDER="openai", IMAGE_API_BASE_URL="https://image.invalid/v1",
                            IMAGE_API_KEY="image-test-credential", IMAGE_MODEL="gpt-image-2"), \
             patch.object(art_image, "_post_with_retry", AsyncMock(return_value=self.response())) as post:
            result = await art_image.generate(prompt="原创商路背景", size="1536x1024", quality="high")
            self.assertEqual(result, b"image-fixture")
            args, kwargs = post.call_args
            self.assertEqual(args, ("https://image.invalid/v1/images/generations",))
            self.assertEqual(kwargs["headers"]["Authorization"], "Bearer image-test-credential")
            self.assertEqual(kwargs["json"]["model"], "gpt-image-2")
            reference = art_image.ReferenceImage("reference.png", b"reference-fixture", "image/png")
            await art_image.edit(prompt="保留构图", size="1024x1024", quality="medium", references=[reference])
            args, kwargs = post.call_args
            self.assertEqual(args, ("https://image.invalid/v1/images/edits",))
            self.assertEqual(kwargs["data"]["model"], "gpt-image-2")
            self.assertEqual(kwargs["files"], [("image[]", ("reference.png", b"reference-fixture", "image/png"))])

    async def test_azure_contract_is_preserved(self):
        with patch.multiple(art_image, IMAGE_PROVIDER="azure", AZURE_IMAGE_ENDPOINT="https://azure.invalid",
                            AZURE_IMAGE_API_KEY="azure-test-credential", AZURE_IMAGE_DEPLOYMENT="art-deployment",
                            AZURE_IMAGE_API_VERSION="test-version"), \
             patch.object(art_image, "_post_with_retry", AsyncMock(return_value=self.response())) as post:
            await art_image.generate(prompt="原创背景", size="1024x1024", quality="medium")
            args, kwargs = post.call_args
            self.assertEqual(args[0], "https://azure.invalid/openai/deployments/art-deployment/images/generations?api-version=test-version")
            self.assertEqual(kwargs["headers"]["api-key"], "azure-test-credential")
            self.assertNotIn("model", kwargs["json"])

    def test_upstream_credentials_are_removed_before_truncation_and_error_display(self):
        key = "private-fixture-" * 20
        response = httpx.Response(401, json={"error": {"message": f"认证失败：{key}"}})
        with patch.object(art_image, "IMAGE_API_KEY", key):
            self.assertNotIn("private-fixture", art_image._short_error_text(response))
            with self.assertRaises(art_image.ArtImageAPIError) as raised:
                art_image._parse_image_response(response)
            self.assertNotIn(key, str(raised.exception))
            self.assertIn("[凭据已隐藏]", str(raised.exception))
