from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import auth, models, otp, schemas
from ..config import get_settings
from ..database import get_db

router = APIRouter(tags=["auth"])
settings = get_settings()


def _issue_tokens(user: models.Staff) -> schemas.LoginResponse:
    return schemas.LoginResponse(
        requires_otp=False,
        access_token=auth.create_access_token(user.login, user.role),
        refresh_token=auth.create_refresh_token(user.login, user.role),
    )


def _start_otp_challenge(db: Session, user: models.Staff) -> schemas.LoginResponse:
    db.query(models.LoginOTP).filter(
        models.LoginOTP.staff_id == user.id_s,
        models.LoginOTP.consumed.is_(False),
    ).update({"consumed": True})

    code = otp.generate_otp_code()
    now = datetime.now(timezone.utc)
    entry = models.LoginOTP(
        staff_id=user.id_s,
        code_hash=otp.hash_otp_code(code),
        created_at=now,
        expires_at=now + timedelta(minutes=settings.otp_expire_minutes),
        attempts=0,
        consumed=False,
    )
    db.add(entry)
    db.commit()

    full_name = f"{user.name} {user.surname}"
    otp.send_otp_email(user.email, full_name, code)

    return schemas.LoginResponse(
        requires_otp=True,
        pending_token=auth.create_pending_token(user.login),
        expires_in=settings.otp_expire_minutes * 60,
        masked_email=otp.mask_email(user.email),
    )


@router.post("/register", response_model=schemas.StaffResponse, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.StaffCreate, db: Session = Depends(get_db)):
    is_first_ever_staff = db.query(models.Staff).count() == 0
    if is_first_ever_staff:
        role = "admin"
    else:
        if payload.role == "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Регистрация с ролью администратора закрыта. "
                    "Роль администратора может выдать только текущий администратор."
                ),
            )
        role = payload.role or "user"

    staff = models.Staff(
        surname=payload.surname,
        name=payload.name,
        patronymic=payload.patronymic,
        position=payload.position,
        phonenum=payload.phonenum,
        login=payload.login,
        password_hash=auth.get_password_hash(payload.password),
        email=payload.email,
        role=role,
        two_factor_enabled=payload.two_factor_enabled if payload.two_factor_enabled is not None else True,
    )
    db.add(staff)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Сотрудник с таким логином или email уже зарегистрирован",
        )
    db.refresh(staff)
    return staff


@router.post("/login", response_model=schemas.LoginResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.Staff).filter(models.Staff.login == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.two_factor_enabled:
        return _start_otp_challenge(db, user)
    return _issue_tokens(user)


@router.post("/login/verify-otp", response_model=schemas.LoginResponse)
def verify_otp(payload: schemas.VerifyOtpRequest, db: Session = Depends(get_db)):
    token_payload = auth.decode_pending_token(payload.pending_token)
    login_value = token_payload.get("sub")
    user = db.query(models.Staff).filter(models.Staff.login == login_value).first()
    if user is None:
        raise auth.CREDENTIALS_EXCEPTION

    entry = (
        db.query(models.LoginOTP)
        .filter(models.LoginOTP.staff_id == user.id_s, models.LoginOTP.consumed.is_(False))
        .order_by(models.LoginOTP.created_at.desc())
        .first()
    )
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Код не запрошен или уже использован. Войдите заново.",
        )

    now = datetime.now(timezone.utc)
    expires_at = entry.expires_at if entry.expires_at.tzinfo else entry.expires_at.replace(tzinfo=timezone.utc)
    if now > expires_at:
        entry.consumed = True
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Срок действия кода истёк. Запросите новый.")

    if entry.attempts >= settings.otp_max_attempts:
        entry.consumed = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Превышено число попыток ввода кода. Запросите новый код.",
        )

    if not otp.verify_otp_code(payload.code, entry.code_hash):
        entry.attempts += 1
        db.commit()
        remaining = settings.otp_max_attempts - entry.attempts
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Неверный код. Осталось попыток: {max(remaining, 0)}",
        )

    entry.consumed = True
    db.commit()
    return _issue_tokens(user)


@router.post("/login/resend-otp", response_model=schemas.ResendOtpResponse)
def resend_otp(payload: schemas.ResendOtpRequest, db: Session = Depends(get_db)):
    token_payload = auth.decode_pending_token(payload.pending_token)
    login_value = token_payload.get("sub")
    user = db.query(models.Staff).filter(models.Staff.login == login_value).first()
    if user is None:
        raise auth.CREDENTIALS_EXCEPTION

    last_entry = (
        db.query(models.LoginOTP)
        .filter(models.LoginOTP.staff_id == user.id_s)
        .order_by(models.LoginOTP.created_at.desc())
        .first()
    )
    if last_entry is not None:
        created_at = last_entry.created_at if last_entry.created_at.tzinfo else last_entry.created_at.replace(tzinfo=timezone.utc)
        seconds_since = (datetime.now(timezone.utc) - created_at).total_seconds()
        if seconds_since < settings.otp_resend_cooldown_seconds:
            wait = int(settings.otp_resend_cooldown_seconds - seconds_since)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Подождите {wait} сек. перед повторной отправкой кода",
            )

    challenge = _start_otp_challenge(db, user)
    return schemas.ResendOtpResponse(
        sent=True,
        expires_in=challenge.expires_in,
        masked_email=challenge.masked_email,
    )


@router.post("/refresh", response_model=schemas.AccessToken)
def refresh(payload: dict, db: Session = Depends(get_db)):
    """Принимает {"refresh_token": "..."} и выдаёт новый access-токен."""
    refresh_token = payload.get("refresh_token") if isinstance(payload, dict) else None
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Отсутствует refresh_token")

    token_payload = auth.decode_refresh_token(refresh_token)
    login_value = token_payload.get("sub")
    user = db.query(models.Staff).filter(models.Staff.login == login_value).first()
    if user is None:
        raise auth.CREDENTIALS_EXCEPTION

    return schemas.AccessToken(access_token=auth.create_access_token(user.login, user.role))


@router.get("/profile", response_model=schemas.StaffResponse)
def profile(current_user: models.Staff = Depends(auth.get_current_user)):
    return current_user
