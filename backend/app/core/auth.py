import base64
import hashlib
import hmac
import secrets
import struct
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Generator, Optional, Tuple, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    plan: Mapped[str] = mapped_column(String(20), default="free")
    totp_secret: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    pending_totp_secret: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verification_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    password_reset_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    password_reset_expires: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    trial_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_requests_used: Mapped[int] = mapped_column(Integer, default=0)
    trial_requests_limit: Mapped[int] = mapped_column(Integer, default=lambda: settings.TRIAL_REQUESTS_LIMIT)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class LoginOtp(Base):
    __tablename__ = "login_otps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    code_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used: Mapped[bool] = mapped_column(Boolean, default=False)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class DailyUsage(Base):
    __tablename__ = "daily_usage"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    usage_date: Mapped[date] = mapped_column(Date, index=True)
    request_count: Mapped[int] = mapped_column(Integer, default=0)


class GuestSession(Base):
    __tablename__ = "guest_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    requests_used: Mapped[int] = mapped_column(Integer, default=0)
    requests_limit: Mapped[int] = mapped_column(Integer, default=5)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


engine_options = {"connect_args": {"check_same_thread": False}} if settings.AUTH_DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.AUTH_DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
password_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)
PLAN_DAILY_LIMITS = {"free": 10, "plus": 100, "pro": None, "trial": 100}


def init_auth_database() -> None:
    # Ensure all tables are created, including new ones like GuestSession
    Base.metadata.create_all(bind=engine)
    print("Auth database initialized with tables:", list(Base.metadata.tables.keys()))


def get_db() -> Generator[Session, None, None]:
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_access_token(user: User, token_type: str = "access") -> str:
    expiry_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES if token_type == "access" else settings.OTP_LOGIN_TOKEN_EXPIRE_MINUTES
    payload = {
        "sub": user.id,
        "type": token_type,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def get_user_from_token(token: str, database: Session, token_type: str = "access") -> User:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != token_type or not payload.get("sub"):
            raise JWTError("Invalid token type")
    except JWTError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from error

    user = database.get(User, payload["sub"])
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    database: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return get_user_from_token(credentials.credentials, database)


def create_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def totp_code(secret: str, for_time: Optional[datetime] = None) -> str:
    timestamp = int((for_time or datetime.now(timezone.utc)).timestamp())
    counter = struct.pack(">Q", timestamp // 30)
    padded_secret = secret + "=" * (-len(secret) % 8)
    digest = hmac.new(base64.b32decode(padded_secret), counter, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{value:06d}"


def verify_totp(secret: str, code: str) -> bool:
    now = datetime.now(timezone.utc)
    return any(hmac.compare_digest(totp_code(secret, now + timedelta(seconds=offset)), code) for offset in (-30, 0, 30))


def issue_login_otp(user: User, database: Session) -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"
    database.add(LoginOtp(
        user_id=user.id,
        code_hash=hashlib.sha256(code.encode()).hexdigest(),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
    ))
    database.commit()
    return code


def verify_login_otp(user: User, code: str, database: Session) -> bool:
    record = database.query(LoginOtp).filter(
        LoginOtp.user_id == user.id, LoginOtp.used.is_(False)
    ).order_by(LoginOtp.expires_at.desc()).first()
    if record is None or record.expires_at < datetime.now(timezone.utc):
        return False
    if not hmac.compare_digest(record.code_hash, hashlib.sha256(code.encode()).hexdigest()):
        return False
    record.used = True
    database.commit()
    return True


def consume_voice_request(user: User, database: Session) -> None:
    # Handle trial users - trial is total requests, not daily
    if user.trial_enabled:
        if user.trial_requests_used >= user.trial_requests_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Your trial has expired. You've used {user.trial_requests_used} of {user.trial_requests_limit} trial requests. Please upgrade to continue."
            )
        user.trial_requests_used += 1
        database.commit()
        return

    # Handle regular plans with daily limits
    limit = PLAN_DAILY_LIMITS.get(user.plan, PLAN_DAILY_LIMITS["free"])
    if limit is None:
        return
    today = datetime.now(timezone.utc).date()
    usage = database.query(DailyUsage).filter(
        DailyUsage.user_id == user.id, DailyUsage.usage_date == today
    ).first()
    if usage is None:
        usage = DailyUsage(user_id=user.id, usage_date=today, request_count=0)
        database.add(usage)
    if usage.request_count >= limit:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"Your {user.plan} plan allows {limit} voice requests per day")
    usage.request_count += 1
    database.commit()


def usage_summary(user: User, database: Session) -> dict:
    if user.trial_enabled:
        return {
            "plan": user.plan,
            "trial_enabled": True,
            "trial_requests_used": user.trial_requests_used,
            "trial_requests_limit": user.trial_requests_limit,
            "trial_remaining": user.trial_requests_limit - user.trial_requests_used,
            "trial_start_date": user.trial_start_date.isoformat() if user.trial_start_date else None,
        }

    limit = PLAN_DAILY_LIMITS.get(user.plan, PLAN_DAILY_LIMITS["free"])
    usage = database.query(DailyUsage).filter(
        DailyUsage.user_id == user.id,
        DailyUsage.usage_date == datetime.now(timezone.utc).date(),
    ).first()
    return {
        "plan": user.plan,
        "trial_enabled": False,
        "daily_limit": limit,
        "used_today": usage.request_count if usage else 0
    }


def create_refresh_token(user: User, database: Session) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    database.add(RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    ))
    database.commit()
    return token


def verify_refresh_token(token: str, database: Session) -> Optional[User]:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    refresh_token = database.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.expires_at > datetime.now(timezone.utc)
    ).first()
    if refresh_token is None:
        return None
    return database.get(User, refresh_token.user_id)


def revoke_refresh_token(token: str, database: Session) -> bool:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    refresh_token = database.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()
    if refresh_token:
        database.delete(refresh_token)
        database.commit()
        return True
    return False


def create_email_verification_token(user: User, database: Session) -> str:
    token = secrets.token_urlsafe(32)
    user.email_verification_token = token
    database.commit()
    return token


def verify_email_token(token: str, database: Session) -> Optional[User]:
    user = database.query(User).filter(User.email_verification_token == token).first()
    if user:
        user.email_verified = True
        user.email_verification_token = None
        database.commit()
    return user


def create_password_reset_token(user: User, database: Session) -> str:
    token = secrets.token_urlsafe(32)
    user.password_reset_token = token
    user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    database.commit()
    return token


def verify_password_reset_token(token: str, database: Session) -> Optional[User]:
    user = database.query(User).filter(
        User.password_reset_token == token,
        User.password_reset_expires > datetime.now(timezone.utc)
    ).first()
    return user


def require_plan(required_plan: str = "free"):
    def decorator(user: User = Depends(get_current_user)):
        plan_hierarchy = {"free": 0, "plus": 1, "pro": 2}
        user_level = plan_hierarchy.get(user.plan, 0)
        required_level = plan_hierarchy.get(required_plan, 0)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires a {required_plan} plan or higher"
            )
        return user
    return decorator


def require_email_verification(user: User = Depends(get_current_user)):
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please verify your email address."
        )
    return user


def create_guest_session(database: Session) -> tuple[str, str]:
    """Create a guest session and return (session_id, session_token)"""
    session_id = str(uuid.uuid4())
    session_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(session_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    guest_session = GuestSession(
        session_token=token_hash,
        requests_limit=settings.GUEST_REQUESTS_LIMIT,
        expires_at=expires_at,
    )
    database.add(guest_session)
    database.commit()
    database.refresh(guest_session)

    return session_id, session_token


def verify_guest_session(session_token: str, database: Session) -> Optional[GuestSession]:
    """Verify guest session token and return session if valid"""
    token_hash = hashlib.sha256(session_token.encode()).hexdigest()
    guest_session = database.query(GuestSession).filter(
        GuestSession.session_token == token_hash,
        GuestSession.expires_at > datetime.now(timezone.utc)
    ).first()
    return guest_session


def consume_guest_request(guest_session: GuestSession, database: Session) -> None:
    """Consume a guest request and check limits"""
    if guest_session.requests_used >= guest_session.requests_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Guest session limit reached. You've used {guest_session.requests_used} of {guest_session.requests_limit} free requests. Please sign up for more."
        )
    guest_session.requests_used += 1
    database.commit()


def get_guest_session_from_token(
    credentials: Optional[HTTPAuthorizationCredentials],
    database: Session,
) -> GuestSession:
    """Dependency to get guest session from token"""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    guest_session = verify_guest_session(credentials.credentials, database)
    if guest_session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired guest session")
    return guest_session


def get_current_user_or_guest(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    database: Session = Depends(get_db),
) -> Tuple[Union[User, GuestSession], bool]:
    """
    Get either a regular user or guest session from token.
    Returns (user_or_guest, is_guest) tuple.
    """
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    # Try to get regular user first
    try:
        user = get_user_from_token(credentials.credentials, database)
        return user, False
    except HTTPException:
        # If not a user, try guest session
        guest_session = verify_guest_session(credentials.credentials, database)
        if guest_session is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
        return guest_session, True


def get_current_user_or_guest_dep(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    database: Session = Depends(get_db),
) -> Tuple[Union[User, GuestSession], bool]:
    """
    Dependency function for FastAPI - same as get_current_user_or_guest but without default params
    """
    return get_current_user_or_guest(credentials, database)
