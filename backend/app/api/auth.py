"""网站接口的会话检查，使用原生 ASGI 保留流式响应与 MCP 生命周期。"""

from starlette.requests import Request
from starlette.responses import JSONResponse

from app.services.auth import COOKIE_NAME


class LoginRequiredMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request = Request(scope)
        path = request.url.path
        protected = path == "/api" or path.startswith("/api/") or path in {"/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"}
        if not protected or request.method == "OPTIONS" or path == "/api/health":
            return await self.app(scope, receive, send)
        if path != "/api/auth/login":
            user = scope["app"].state.auth_store.session_user(request.cookies.get(COOKIE_NAME, ""))
            if user is None:
                return await JSONResponse({"detail": "请先登录"}, status_code=401,
                                          headers={"Cache-Control": "no-store"})(scope, receive, send)
            scope.setdefault("state", {})["user"] = user
        # 写操作只接受网页主动添加的自定义头，跨站表单无法携带该头。
        if request.method not in {"GET", "HEAD"} and request.headers.get("x-requested-with") != "GameAgent":
            return await JSONResponse({"detail": "请求校验失败，请刷新页面后重试"}, status_code=403)(scope, receive, send)
        return await self.app(scope, receive, send)
