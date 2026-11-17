from typing import Optional

from fastapi import HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import auth, models
from .. import permissions
from .. import schemas
from ..crud_router import build_crud_router


def staff_filters(
    role: Optional[str] = Query(default=None, description="Фильтр по роли"),
    search: Optional[str] = Query(default=None, description="Поиск по фамилии/имени/логину"),
):
    return {"role": role, "search": search}


def _hash_password_on_create(data: dict, current_user) -> dict:
    password = data.pop("password")
    data["password_hash"] = auth.get_password_hash(password)
    return data


def _hash_password_on_update(data: dict, current_user) -> dict:
    if "password" in data:
        password = data.pop("password")
        if password:
            data["password_hash"] = auth.get_password_hash(password)
    return data


def _remaining_admins(db: Session, exclude_id: int) -> int:
    return (
        db.query(models.Staff)
        .filter(models.Staff.role == permissions.ROLE_ADMIN, models.Staff.id_s != exclude_id)
        .count()
    )


def _guard_last_admin_on_update(item: models.Staff, data: dict, db: Session) -> None:
    """Не позволяет понизить в роли или отключить единственного
    оставшегося администратора — иначе управлять системой станет
    некому."""
    demoting_role = "role" in data and data["role"] != permissions.ROLE_ADMIN
    if item.role == permissions.ROLE_ADMIN and demoting_role:
        if _remaining_admins(db, item.id_s) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя понизить последнего администратора системы. "
                       "Сначала назначьте администратором другого сотрудника.",
            )


def _guard_last_admin_on_delete(item: models.Staff, db: Session) -> None:
    if item.role == permissions.ROLE_ADMIN:
        if _remaining_admins(db, item.id_s) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя удалить последнего администратора системы.",
            )


router = build_crud_router(
    model=models.Staff,
    id_field="id_s",
    create_schema=schemas.StaffCreate,
    update_schema=schemas.StaffUpdate,
    response_schema=schemas.StaffResponse,
    prefix="/staff",
    tags=["staff"],
    entity_name="Сотрудник",
    filter_dependency=staff_filters,
    search_fields=["surname", "name", "login"],
    on_create=_hash_password_on_create,
    on_update=_hash_password_on_update,
    before_update=_guard_last_admin_on_update,
    before_delete=_guard_last_admin_on_delete,
    conflict_detail="Сотрудник с таким логином или email уже существует",
    # Просматривать список сотрудников может любой авторизованный (нужно
    # для выпадающих списков "ответственный", "исполнитель" и т.п.), а вот
    # создавать/редактировать/удалять сотрудников — и тем более менять
    # роли — может только администратор.
    write_dependency=permissions.require_admin,
    delete_dependency=permissions.require_admin,
)
