import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Response, Request, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)
from core.validators import validate_email, validate_password
from core.errors import ok, err, ErrorCode
from core.limiter import limiter, LIMIT_AUTH_LOGIN, LIMIT_AUTH_SIGNUP
from db.supabase_client import supabase, supabase_admin
from config import get_settings

settings = get_settings()
logger = logging.getLogger("dialecta.auth")
router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "dialecta_refresh"
COOKIE_OPTS = dict(
    httponly=True,
    secure=settings.is_production,
    samesite="lax",
    max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    path="/auth/refresh",
)


# ── Request models ────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: str
    password: str
    display_name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    pass


# ── Signup ────────────────────────────────────────────────────────────────────

@router.post("/signup")
@limiter.limit(LIMIT_AUTH_SIGNUP)
async def signup(request: Request, body: SignupRequest, response: Response):
    email = validate_email(body.email)
    password = validate_password(body.password)

    try:
        result = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {"display_name": body.display_name or email.split("@")[0]}
            },
        })
    except Exception as e:
        logger.warning("Signup error: %s", e)
        # Never reveal if email already exists
        return JSONResponse(
            status_code=200,
            content=ok(message="If this email is new, a verification link has been sent"),
        )

    if result.user:
        logger.info("New signup: %s", email)

    return JSONResponse(
        status_code=200,
        content=ok(message="Check your email for a verification link"),
    )


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login")
@limiter.limit(LIMIT_AUTH_LOGIN)
async def login(request: Request, body: LoginRequest, response: Response):
    email = validate_email(body.email)

    try:
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": body.password,
        })
    except Exception as e:
        logger.warning("Login failed for %s: %s", email, e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not result.user or not result.session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not result.user.email_confirmed_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your email before logging in",
        )

    user_id = str(result.user.id)
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)

    # Update last_active
    try:
        supabase_admin.table("users").update({
            "last_active": datetime.now(timezone.utc).isoformat()
        }).eq("user_id", user_id).execute()
    except Exception:
        pass

    resp = JSONResponse(content=ok(
        data={"access_token": access_token, "user_id": user_id, "email": email},
        message="Login successful",
    ))
    resp.set_cookie(REFRESH_COOKIE, refresh_token, **COOKIE_OPTS)
    logger.info("Login successful: %s", email)
    return resp


# ── Refresh ───────────────────────────────────────────────────────────────────

@router.post("/refresh")
async def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get(REFRESH_COOKIE)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )

    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Wrong token type")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload["sub"]

    # Get user email from DB
    try:
        result = supabase_admin.table("users").select("email").eq("user_id", user_id).single().execute()
        email = result.data["email"]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    new_access_token = create_access_token(user_id, email)
    new_refresh_token = create_refresh_token(user_id)

    resp = JSONResponse(content=ok(
        data={"access_token": new_access_token},
        message="Token refreshed",
    ))
    # Rotate refresh token — old one is replaced
    resp.set_cookie(REFRESH_COOKIE, new_refresh_token, **COOKIE_OPTS)
    return resp


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout")
async def logout(request: Request, current_user: dict = Depends(get_current_user)):
    resp = JSONResponse(content=ok(message="Logged out"))
    resp.delete_cookie(REFRESH_COOKIE, path="/auth/refresh")
    logger.info("Logout: %s", current_user.get("email"))
    return resp


# ── Me ────────────────────────────────────────────────────────────────────────

@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    user_id = current_user["sub"]
    try:
        result = supabase_admin.table("users").select(
            "user_id, email, display_name, created_at, debate_count, last_active"
        ).eq("user_id", user_id).single().execute()
        return JSONResponse(content=ok(data=result.data))
    except Exception:
        raise HTTPException(status_code=404, detail="User not found")


# ── Resend verification ───────────────────────────────────────────────────────

@router.post("/resend-verification")
@limiter.limit("3/hour")
async def resend_verification(request: Request, body: SignupRequest):
    email = validate_email(body.email)
    try:
        supabase.auth.resend({"type": "signup", "email": email})
    except Exception:
        pass
    # Always return same message — never reveal if email exists
    return JSONResponse(content=ok(message="If this email is registered, a verification link has been sent"))

# ── Update Password ───────────────────────────────────────────────────────────

class UpdatePasswordRequest(BaseModel):
    password: str


@router.post("/update-password")
async def update_password(request: Request, body: UpdatePasswordRequest, current_user: dict = Depends(get_current_user)):
    password = validate_password(body.password)
    user_id = current_user["sub"]

    try:
        supabase_admin.auth.admin.update_user_by_id(user_id, {"password": password})
    except Exception as e:
        logger.warning("Password update failed for %s: %s", user_id, e)
        raise HTTPException(status_code=400, detail="Failed to update password")

    logger.info("Password updated for user: %s", user_id)
    return JSONResponse(content=ok(message="Password updated successfully"))