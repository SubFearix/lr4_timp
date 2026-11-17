from typing import Optional

from fastapi import Query

from .. import models, permissions, schemas
from ..crud_router import build_crud_router


def response_log_filters(
    id_inc: Optional[int] = Query(default=None, description="Фильтр по инциденту"),
    id_meas: Optional[int] = Query(default=None, description="Фильтр по мере реагирования"),
    id_s: Optional[int] = Query(default=None, description="Фильтр по исполнителю"),
):
    return {"id_inc": id_inc, "id_meas": id_meas, "id_s": id_s}


router = build_crud_router(
    model=models.ResponseLog,
    id_field="id_log",
    create_schema=schemas.ResponseLogCreate,
    update_schema=schemas.ResponseLogUpdate,
    response_schema=schemas.ResponseLogResponse,
    prefix="/response-logs",
    tags=["response-logs"],
    entity_name="Запись журнала реагирования",
    filter_dependency=response_log_filters,
    conflict_detail="Не удалось сохранить запись: проверьте ссылки на инцидент, меру и исполнителя",
    write_dependency=permissions.require_operational_write,
    delete_dependency=permissions.require_admin,
)
