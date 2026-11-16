"""网站登录、当前身份与退出接口。"""

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.services.auth import COOKIE_NAME, SESSION_SECONDS, InvalidCredentials, LoginThrottled

router = APIRouter(prefix="/auth", tags=["用户登录"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=512)


@router.post("/login")
def login(body: LoginRequest, request: Request, response: Response):
    source = request.client.host if request.client else "unknown"
    try:
        user, token = request.app.state.auth_store.login(body.username.strip(), body.password, source,
                                                       request.cookies.get(COOKIE_NAME, ""))
    except InvalidCredentials as error:
        raise HTTPException(401, str(error)) from error
    except LoginThrottled as error:
        raise HTTPException(429, str(error), headers={"Retry-After": "60"}) from error
    response.set_cookie(COOKIE_NAME, token, max_age=SESSION_SECONDS, httponly=True,
                        secure=request.url.scheme == "https", samesite="lax", path="/")
    response.headers["Cache-Control"] = "no-store"
    return {"user": user}


@router.get("/session")
def session(request: Request, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return {"user": request.state.user}


@router.post("/logout")
def logout(request: Request, response: Response):
    request.app.state.auth_store.logout(request.cookies.get(COOKIE_NAME, ""))
    response.delete_cookie(COOKIE_NAME, path="/", httponly=True,
                           secure=request.url.scheme == "https", samesite="lax")
    response.headers["Cache-Control"] = "no-store"
    return {"success": True, "data": {"logged_out": True}}
