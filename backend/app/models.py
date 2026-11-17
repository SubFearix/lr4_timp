from sqlalchemy import (
    Boolean, Column, DateTime, Integer, String, Text, Date, Time, ForeignKey, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base

# Примечание: в исходном отчёте (ЛР4) внешние ключи на staff были описаны
# как "NOT NULL ... ON DELETE SET NULL" — это взаимоисключающие условия
# (NOT NULL запрещает NULL, поэтому при удалении сотрудника такая операция
# упадёт с ошибкой). Здесь это исправлено на ON DELETE RESTRICT: пока на
# сотрудника ссылаются инциденты/уязвимости/записи журнала, удалить его
# нельзя — это и корректно работает, и не даёт потерять историю данных.


class Staff(Base):
    __tablename__ = "staff"

    id_s = Column(Integer, primary_key=True, index=True)
    surname = Column(String(30), nullable=False)
    name = Column(String(30), nullable=False)
    patronymic = Column(String(30), nullable=True)
    position = Column(String(100), nullable=False)
    phonenum = Column(String(20), nullable=False)
    login = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(String(50), nullable=False, default="user")
    two_factor_enabled = Column(Boolean, nullable=False, default=True, server_default="true")

    incidents = relationship("Incident", back_populates="responsible", passive_deletes=False)
    vulnerabilities_found = relationship("Vulnerability", back_populates="found_by", passive_deletes=False)
    response_logs = relationship("ResponseLog", back_populates="executor", passive_deletes=False)
    login_otps = relationship("LoginOTP", back_populates="staff", cascade="all, delete-orphan")


class Object(Base):
    __tablename__ = "object"

    id_obj = Column(Integer, primary_key=True, index=True)
    obj_name = Column(String(100), nullable=False)
    obj_type = Column(String(50), nullable=False)
    location = Column(String(150), nullable=True)

    incidents = relationship("Incident", back_populates="related_object", cascade="all, delete-orphan")


class VulnerabilityType(Base):
    __tablename__ = "vulnerability_type"

    id_vultype = Column(Integer, primary_key=True, index=True)
    type_name = Column(String(150), nullable=False)

    vulnerabilities = relationship("Vulnerability", back_populates="vul_type")


class ResponseMeasure(Base):
    __tablename__ = "response_measure"

    id_meas = Column(Integer, primary_key=True, index=True)
    meas_name = Column(String(150), nullable=False)
    time_reg = Column(Integer, nullable=True)

    response_logs = relationship("ResponseLog", back_populates="measure")


class Incident(Base):
    __tablename__ = "incident"

    id_inc = Column(Integer, primary_key=True, index=True)
    id_obj = Column(Integer, ForeignKey("object.id_obj", ondelete="CASCADE"), nullable=False)
    id_s = Column(Integer, ForeignKey("staff.id_s", ondelete="RESTRICT"), nullable=False)
    inc_type = Column(String(100), nullable=False)
    inc_date = Column(Date, nullable=False)
    inc_time = Column(Time, nullable=False)
    threat_lvl = Column(Integer, nullable=False)
    state = Column(String(100), nullable=False)

    __table_args__ = (
        CheckConstraint("threat_lvl BETWEEN 1 AND 10", name="ck_incident_threat_lvl"),
    )

    related_object = relationship("Object", back_populates="incidents")
    responsible = relationship("Staff", back_populates="incidents")
    response_logs = relationship("ResponseLog", back_populates="incident", cascade="all, delete-orphan")


class Vulnerability(Base):
    __tablename__ = "vulnerability"

    id_vul = Column(Integer, primary_key=True, index=True)
    id_s = Column(Integer, ForeignKey("staff.id_s", ondelete="RESTRICT"), nullable=False)
    id_vultype = Column(Integer, ForeignKey("vulnerability_type.id_vultype", ondelete="RESTRICT"), nullable=False)
    sw_ver = Column(String(50), nullable=True)
    fix_status = Column(String(50), nullable=False)

    found_by = relationship("Staff", back_populates="vulnerabilities_found")
    vul_type = relationship("VulnerabilityType", back_populates="vulnerabilities")


class ResponseLog(Base):
    __tablename__ = "response_log"

    id_log = Column(Integer, primary_key=True, index=True)
    id_inc = Column(Integer, ForeignKey("incident.id_inc", ondelete="CASCADE"), nullable=False)
    id_meas = Column(Integer, ForeignKey("response_measure.id_meas", ondelete="RESTRICT"), nullable=False)
    id_s = Column(Integer, ForeignKey("staff.id_s", ondelete="RESTRICT"), nullable=False)
    date_exec = Column(Date, nullable=False)
    time_exec = Column(Time, nullable=False)
    result = Column(Text, nullable=True)

    incident = relationship("Incident", back_populates="response_logs")
    measure = relationship("ResponseMeasure", back_populates="response_logs")
    executor = relationship("Staff", back_populates="response_logs")


class LoginOTP(Base):
    """Одноразовый код подтверждения входа (2FA), отправляемый на почту.

    Код хранится не в открытом виде, а в виде HMAC-хеша (см. app/otp.py),
    чтобы утечка базы данных не раскрывала действующие коды.
    """
    __tablename__ = "login_otp"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id_s", ondelete="CASCADE"), nullable=False, index=True)
    code_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    consumed = Column(Boolean, nullable=False, default=False)

    staff = relationship("Staff", back_populates="login_otps")
