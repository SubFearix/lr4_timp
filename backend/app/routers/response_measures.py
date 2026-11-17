from typing import Optional

from fastapi import Query

from .. import models, permissions, schemas
from ..crud_router import build_crud_router


def measure_filters(
    search: Optional[str] = Query(default=None, description="Поиск по названию меры реагирования"),
):
    return {"search": search}


router = build_crud_router(
    model=models.ResponseMeasure,
    id_field="id_meas",
    create_schema=schemas.ResponseMeasureCreate,
    update_schema=schemas.ResponseMeasureUpdate,
    response_schema=schemas.ResponseMeasureResponse,
    prefix="/response-measures",
    tags=["response-measures"],
    entity_name="Мера реагирования",
    filter_dependency=measure_filters,
    search_fields=["meas_name"],
    write_dependency=permissions.require_admin,
)
