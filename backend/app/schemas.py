import re
from datetime import date, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

PHONE_PATTERN = re.compile(r"^\+?[\d\s\-()]+$")


def validate_phone_number(value: str) -> str:
    value = value.strip()
    if not PHONE_PATTERN.match(value):
        raise ValueError("Телефон может содержать только цифры, пробелы, +, - и скобки")
    digit_count = sum(ch.isdigit() for ch in value)
    if not (10 <= digit_count <= 15):
        raise ValueError("Номер телефона должен содержать от 10 до 15 цифр")
    return value


def validate_password_strength(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Пароль должен содержать минимум 8 символов")
    if not re.search(r"[a-z]", value):
        raise ValueError("Пароль должен содержать хотя бы одну строчную латинскую букву")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Пароль должен содержать хотя бы одну заглавную латинскую букву")
    if not re.search(r"\d", value):
        raise ValueError("Пароль должен содержать хотя бы одну цифру")
    return value

class StaffBase(BaseModel):
    surname: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=30)
    patronymic: Optional[str] = Field(default=None, max_length=30)
    position: str = Field(min_length=1, max_length=100)
    phonenum: str = Field(min_length=1, max_length=20)
    email: EmailStr
    role: str = Field(default="user", max_length=50)
    two_factor_enabled: bool = Field(default=True)

    @field_validator("phonenum")
    @classmethod
    def _validate_phonenum(cls, value: str) -> str:
        return validate_phone_number(value)


class StaffCreate(StaffBase):
    login: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def _validate_password(cls, value: str) -> str:
        return validate_password_strength(value)


class StaffUpdate(BaseModel):
    surname: Optional[str] = Field(default=None, max_length=30)
    name: Optional[str] = Field(default=None, max_length=30)
    patronymic: Optional[str] = Field(default=None, max_length=30)
    position: Optional[str] = Field(default=None, max_length=100)
    phonenum: Optional[str] = Field(default=None, max_length=20)
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(default=None, max_length=50)
    two_factor_enabled: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)

    @field_validator("phonenum")
    @classmethod
    def _validate_phonenum(cls, value: Optional[str]) -> Optional[str]:
        return validate_phone_number(value) if value is not None else value

    @field_validator("password")
    @classmethod
    def _validate_password(cls, value: Optional[str]) -> Optional[str]:
        return validate_password_strength(value) if value is not None else value


class StaffResponse(StaffBase):
    model_config = ConfigDict(from_attributes=True)

    id_s: int
    login: str

class ObjectBase(BaseModel):
    obj_name: str = Field(min_length=1, max_length=100)
    obj_type: str = Field(min_length=1, max_length=50)
    location: Optional[str] = Field(default=None, max_length=150)


class ObjectCreate(ObjectBase):
    pass


class ObjectUpdate(BaseModel):
    obj_name: Optional[str] = Field(default=None, max_length=100)
    obj_type: Optional[str] = Field(default=None, max_length=50)
    location: Optional[str] = Field(default=None, max_length=150)


class ObjectResponse(ObjectBase):
    model_config = ConfigDict(from_attributes=True)
    id_obj: int

class VulnerabilityTypeBase(BaseModel):
    type_name: str = Field(min_length=1, max_length=150)


class VulnerabilityTypeCreate(VulnerabilityTypeBase):
    pass


class VulnerabilityTypeUpdate(BaseModel):
    type_name: Optional[str] = Field(default=None, max_length=150)


class VulnerabilityTypeResponse(VulnerabilityTypeBase):
    model_config = ConfigDict(from_attributes=True)
    id_vultype: int

class ResponseMeasureBase(BaseModel):
    meas_name: str = Field(min_length=1, max_length=150)
    time_reg: Optional[int] = Field(default=None, ge=0)


class ResponseMeasureCreate(ResponseMeasureBase):
    pass


class ResponseMeasureUpdate(BaseModel):
    meas_name: Optional[str] = Field(default=None, max_length=150)
    time_reg: Optional[int] = Field(default=None, ge=0)


class ResponseMeasureResponse(ResponseMeasureBase):
    model_config = ConfigDict(from_attributes=True)
    id_meas: int

class IncidentBase(BaseModel):
    id_obj: int
    id_s: int
    inc_type: str = Field(min_length=1, max_length=100)
    inc_date: date
    inc_time: time
    threat_lvl: int = Field(ge=1, le=10)
    state: str = Field(min_length=1, max_length=100)


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(BaseModel):
    id_obj: Optional[int] = None
    id_s: Optional[int] = None
    inc_type: Optional[str] = Field(default=None, max_length=100)
    inc_date: Optional[date] = None
    inc_time: Optional[time] = None
    threat_lvl: Optional[int] = Field(default=None, ge=1, le=10)
    state: Optional[str] = Field(default=None, max_length=100)


class IncidentResponse(IncidentBase):
    model_config = ConfigDict(from_attributes=True)
    id_inc: int


class IncidentDetailResponse(IncidentResponse):
    model_config = ConfigDict(from_attributes=True)
    related_object: Optional[ObjectResponse] = None
    responsible: Optional[StaffResponse] = None


class VulnerabilityBase(BaseModel):
    id_s: int
    id_vultype: int
    sw_ver: Optional[str] = Field(default=None, max_length=50)
    fix_status: str = Field(min_length=1, max_length=50)


class VulnerabilityCreate(VulnerabilityBase):
    pass


class VulnerabilityUpdate(BaseModel):
    id_s: Optional[int] = None
    id_vultype: Optional[int] = None
    sw_ver: Optional[str] = Field(default=None, max_length=50)
    fix_status: Optional[str] = Field(default=None, max_length=50)


class VulnerabilityResponse(VulnerabilityBase):
    model_config = ConfigDict(from_attributes=True)
    id_vul: int
    
class ResponseLogBase(BaseModel):
    id_inc: int
    id_meas: int
    id_s: int
    date_exec: date
    time_exec: time
    result: Optional[str] = None


class ResponseLogCreate(ResponseLogBase):
    pass


class ResponseLogUpdate(BaseModel):
    id_inc: Optional[int] = None
    id_meas: Optional[int] = None
    id_s: Optional[int] = None
    date_exec: Optional[date] = None
    time_exec: Optional[time] = None
    result: Optional[str] = None


class ResponseLogResponse(ResponseLogBase):
    model_config = ConfigDict(from_attributes=True)
    id_log: int

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    role: Optional[str] = None
    type: str
    exp: int


class LoginResponse(BaseModel):
    requires_otp: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    pending_token: Optional[str] = None
    expires_in: Optional[int] = Field(default=None, description="Секунд до истечения OTP-кода")
    masked_email: Optional[str] = None


class VerifyOtpRequest(BaseModel):
    pending_token: str
    code: str = Field(min_length=4, max_length=10)


class ResendOtpRequest(BaseModel):
    pending_token: str


class ResendOtpResponse(BaseModel):
    sent: bool
    expires_in: int
    masked_email: str

class PageMeta(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
