from typing import Optional

from fastapi import Query

from .. import models, permissions, schemas
from ..crud_router import build_crud_router


def vulnerability_filters(
    fix_status: Optional[str] = Query(default=None, description="Фильтр по статусу исправления"),
    id_vultype: Optional[int] = Query(default=None, description="Фильтр по типу уязвимости"),
    id_s: Optional[int] = Query(default=None, description="Фильтр по сотруднику, нашедшему уязвимость"),
):
    return {"fix_status": fix_status, "id_vultype": id_vultype, "id_s": id_s}


router = build_crud_router(
    model=models.Vulnerability,
    id_field="id_vul",
    create_schema=schemas.VulnerabilityCreate,
    update_schema=schemas.VulnerabilityUpdate,
    response_schema=schemas.VulnerabilityResponse,
    prefix="/vulnerabilities",
    tags=["vulnerabilities"],
    entity_name="Уязвимость",
    filter_dependency=vulnerability_filters,
    conflict_detail="Не удалось сохранить уязвимость: проверьте ссылки на сотрудника и тип уязвимости",
    # Оперативные данные: создавать/редактировать могут admin и operator,
    # удалять — только admin.
    write_dependency=permissions.require_operational_write,
    delete_dependency=permissions.require_admin,
)
