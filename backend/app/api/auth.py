from typing import Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import (
    User, create_access_token, create_totp_secret, get_current_user,
    get_db, get_user_from_token, hash_password, issue_login_otp,
    usage_summary, verify_login_otp, verify_password, verify_totp,
    create_refresh_token, verify_refresh_token, revoke_refresh_token,
    create_email_verification_token, verify_email_token,
    create_password_reset_token, verify_password_reset_token,
    require_plan, require_email_verification,
    create_guest_session, GuestSession, verify_guest_session,
)
from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)

router = APIRouter()


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)


class TwoFactorCode(BaseModel):
    login_token: str
    code: str = Field(pattern=r"^\d{6}$")


class OtpRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class OtpVerification(BaseModel):
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    code: str = Field(pattern=r"^\d{6}$")
    totp_code: Optional[str] = Field(default=None, pattern=r"^\d{6}$")


class TotpVerification(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")


class PlanUpdate(BaseModel):
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    plan: str = Field(pattern=r"^(free|plus|pro)$")


class EmailVerificationRequest(BaseModel):
    token: str


class PasswordResetRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


def user_payload(user: User, database: Session) -> dict:
    return {"id": user.id, "email": user.email, "two_factor_enabled": user.totp_enabled, **usage_summary(user, database)}


def authenticated_response(user: User, database: Session) -> dict:
    return {
        "access_token": create_access_token(user),
        "refresh_token": create_refresh_token(user, database),
        "token_type": "bearer",
        "user": user_payload(user, database)
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(credentials: Credentials, database: Session = Depends(get_db)):
    email = str(credentials.email).lower()
    if database.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account already exists for this email")
    user = User(email=email, password_hash=hash_password(credentials.password), plan="free")
    database.add(user)
    database.commit()
    database.refresh(user)

    verification_token = create_email_verification_token(user, database)
    response = authenticated_response(user, database)
    response["email_verification_required"] = True
    if settings.OTP_EXPOSE_IN_RESPONSE:
        response["verification_token"] = verification_token
    return response


@router.post("/login")
def login(credentials: Credentials, database: Session = Depends(get_db)):
    user = database.query(User).filter(User.email == str(credentials.email).lower()).first()
    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if user.totp_enabled:
        return {"requires_two_factor": True, "login_token": create_access_token(user, "pending_2fa")}
    if not user.email_verified:
        return {"requires_email_verification": True, "login_token": create_access_token(user, "pending_verification")}
    return authenticated_response(user, database)


@router.post("/login/2fa")
def login_two_factor(request: TwoFactorCode, database: Session = Depends(get_db)):
    user = get_user_from_token(request.login_token, database, "pending_2fa")
    if not user.totp_secret or not verify_totp(user.totp_secret, request.code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid two-factor code")
    if not user.email_verified:
        return {"requires_email_verification": True, "login_token": create_access_token(user, "pending_verification")}
    return authenticated_response(user, database)


@router.post("/login/complete-verification")
def complete_login_verification(request: EmailVerificationRequest, database: Session = Depends(get_db)):
    user = get_user_from_token(request.token, database, "pending_verification")
    if not user.email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email must be verified first")
    return authenticated_response(user, database)


@router.post("/login/otp/request")
def request_otp(request: OtpRequest, database: Session = Depends(get_db)):
    user = database.query(User).filter(User.email == str(request.email).lower()).first()
    if user is None:
        return {"message": "If an account exists, a sign-in code has been sent"}
    code = issue_login_otp(user, database)
    response = {"message": "If an account exists, a sign-in code has been sent"}
    if settings.OTP_EXPOSE_IN_RESPONSE:
        response["development_otp"] = code
    return response


@router.post("/login/otp/verify")
def verify_otp(request: OtpVerification, database: Session = Depends(get_db)):
    user = database.query(User).filter(User.email == str(request.email).lower()).first()
    if user is None or not verify_login_otp(user, request.code, database):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired sign-in code")
    if user.totp_enabled and (not request.totp_code or not verify_totp(user.totp_secret or "", request.totp_code)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="A valid two-factor code is required")
    return authenticated_response(user, database)


@router.post("/2fa/setup")
def setup_two_factor(user: User = Depends(get_current_user), database: Session = Depends(get_db)):
    secret = create_totp_secret()
    user.pending_totp_secret = secret
    database.commit()
    return {"secret": secret, "otpauth_uri": f"otpauth://totp/VoiceGPT:{user.email}?secret={secret}&issuer=VoiceGPT"}


@router.post("/2fa/confirm")
def confirm_two_factor(request: TotpVerification, user: User = Depends(get_current_user), database: Session = Depends(get_db)):
    if not user.pending_totp_secret or not verify_totp(user.pending_totp_secret, request.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid two-factor code")
    user.totp_secret = user.pending_totp_secret
    user.pending_totp_secret = None
    user.totp_enabled = True
    database.commit()
    return {"two_factor_enabled": True}


@router.post("/2fa/disable")
def disable_two_factor(request: TotpVerification, user: User = Depends(get_current_user), database: Session = Depends(get_db)):
    if not user.totp_secret or not verify_totp(user.totp_secret, request.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid two-factor code")
    user.totp_secret = None
    user.pending_totp_secret = None
    user.totp_enabled = False
    database.commit()
    return {"two_factor_enabled": False}


@router.get("/me")
def current_user(user: User = Depends(get_current_user), database: Session = Depends(get_db)):
    return user_payload(user, database)


@router.post("/admin/plan")
def update_plan(request: PlanUpdate, admin: User = Depends(get_current_user), database: Session = Depends(get_db)):
    if admin.email not in settings.ADMIN_EMAILS:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required")
    user = database.query(User).filter(User.email == request.email.lower()).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.plan = request.plan
    database.commit()
    return user_payload(user, database)


@router.post("/verify-email")
def verify_email(request: EmailVerificationRequest, database: Session = Depends(get_db)):
    user = verify_email_token(request.token, database)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token")
    return {"message": "Email verified successfully", "email_verified": True}


@router.post("/resend-verification")
def resend_verification(user: User = Depends(get_current_user), database: Session = Depends(get_db)):
    if user.email_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified")
    token = create_email_verification_token(user, database)
    response = {"message": "Verification email sent"}
    if settings.OTP_EXPOSE_IN_RESPONSE:
        response["verification_token"] = token
    return response


@router.post("/password-reset/request")
def request_password_reset(request: PasswordResetRequest, database: Session = Depends(get_db)):
    user = database.query(User).filter(User.email == str(request.email).lower()).first()
    if user is None:
        return {"message": "If an account exists, a password reset link has been sent"}
    token = create_password_reset_token(user, database)
    response = {"message": "If an account exists, a password reset link has been sent"}
    if settings.OTP_EXPOSE_IN_RESPONSE:
        response["reset_token"] = token
    return response


@router.post("/password-reset/confirm")
def confirm_password_reset(request: PasswordResetConfirm, database: Session = Depends(get_db)):
    user = verify_password_reset_token(request.token, database)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    user.password_hash = hash_password(request.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    database.commit()
    return {"message": "Password reset successfully"}


@router.post("/refresh")
def refresh_token(request: RefreshTokenRequest, database: Session = Depends(get_db)):
    user = verify_refresh_token(request.refresh_token, database)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    return {
        "access_token": create_access_token(user),
        "token_type": "bearer"
    }


@router.post("/logout")
def logout(request: RefreshTokenRequest, database: Session = Depends(get_db)):
    revoke_refresh_token(request.refresh_token, database)
    return {"message": "Logged out successfully"}


@router.get("/protected/free")
def protected_free(user: User = Depends(require_plan("free"))):
    return {"message": "Free tier endpoint", "plan": user.plan}


@router.get("/protected/plus")
def protected_plus(user: User = Depends(require_plan("plus"))):
    return {"message": "Plus tier endpoint", "plan": user.plan}


@router.get("/protected/pro")
def protected_pro(user: User = Depends(require_plan("pro"))):
    return {"message": "Pro tier endpoint", "plan": user.plan}


@router.get("/protected/verified")
def protected_verified(user: User = Depends(require_email_verification)):
    return {"message": "Email verified endpoint", "email": user.email}


@router.post("/start-trial")
def start_trial(user: User = Depends(get_current_user), database: Session = Depends(get_db)):
    if user.trial_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trial already started")
    if user.plan != "free":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trial is only available for free plan users")
    user.trial_enabled = True
    user.trial_start_date = datetime.now(timezone.utc)
    user.trial_requests_used = 0
    user.trial_requests_limit = settings.TRIAL_REQUESTS_LIMIT
    database.commit()
    return {
        "message": "Trial started successfully",
        "trial_requests_limit": user.trial_requests_limit,
        "user": user_payload(user, database)
    }


@router.post("/guest/start", status_code=status.HTTP_201_CREATED)
def start_guest_session(database: Session = Depends(get_db)):
    """Start a guest session without requiring sign-in"""
    session_id, session_token = create_guest_session(database)
    return {
        "message": "Guest session started",
        "session_id": session_id,
        "access_token": session_token,
        "token_type": "bearer",
        "guest": True,
        "requests_limit": settings.GUEST_REQUESTS_LIMIT,
        "expires_in_hours": 24
    }


@router.get("/guest/status")
def guest_status(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    database: Session = Depends(get_db),
):
    """Get guest session status"""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    # Try to get user first
    try:
        user = get_user_from_token(credentials.credentials, database)
        return {
            "authenticated": True,
            "guest": False,
            "user": user_payload(user, database)
        }
    except HTTPException:
        # If not a user, try guest session
        guest_session = verify_guest_session(credentials.credentials, database)
        if guest_session is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")

        return {
            "authenticated": True,
            "guest": True,
            "session_id": guest_session.id,
            "requests_used": guest_session.requests_used,
            "requests_limit": guest_session.requests_limit,
            "requests_remaining": guest_session.requests_limit - guest_session.requests_used,
            "expires_at": guest_session.expires_at.isoformat()
        }
