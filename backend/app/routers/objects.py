from typing import Optional

from fastapi import Query

from .. import models, permissions, schemas
from ..crud_router import build_crud_router


def object_filters(
    obj_type: Optional[str] = Query(default=None, description="Фильтр по типу объекта"),
    search: Optional[str] = Query(default=None, description="Поиск по названию объекта"),
):
    return {"obj_type": obj_type, "search": search}


router = build_crud_router(
    model=models.Object,
    id_field="id_obj",
    create_schema=schemas.ObjectCreate,
    update_schema=schemas.ObjectUpdate,
    response_schema=schemas.ObjectResponse,
    prefix="/objects",
    tags=["objects"],
    entity_name="Объект",
    filter_dependency=object_filters,
    search_fields=["obj_name"],
    conflict_detail="Не удалось сохранить объект: нарушено ограничение целостности данных",
    # Объекты — инфраструктурный справочник: просматривать может любой
    # авторизованный, изменять — только администратор.
    write_dependency=permissions.require_admin,
)
