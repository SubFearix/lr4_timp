from typing import Optional

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import auth, models, permissions, schemas
from ..crud_router import build_crud_router
from ..database import get_db


def incident_filters(
    state: Optional[str] = Query(default=None, description="Фильтр по состоянию инцидента"),
    inc_type: Optional[str] = Query(default=None, description="Фильтр по типу инцидента"),
    id_obj: Optional[int] = Query(default=None, description="Фильтр по объекту"),
    id_s: Optional[int] = Query(default=None, description="Фильтр по ответственному сотруднику"),
    threat_lvl_min: Optional[int] = Query(default=None, ge=1, le=10, description="Мин. уровень угрозы"),
    threat_lvl_max: Optional[int] = Query(default=None, ge=1, le=10, description="Макс. уровень угрозы"),
):
    return {
        "state": state,
        "inc_type": inc_type,
        "id_obj": id_obj,
        "id_s": id_s,
        "threat_lvl_min": threat_lvl_min,
        "threat_lvl_max": threat_lvl_max,
    }


router = build_crud_router(
    model=models.Incident,
    id_field="id_inc",
    create_schema=schemas.IncidentCreate,
    update_schema=schemas.IncidentUpdate,
    response_schema=schemas.IncidentResponse,
    prefix="/incidents",
    tags=["incidents"],
    entity_name="Инцидент",
    filter_dependency=incident_filters,
    conflict_detail="Не удалось сохранить инцидент: проверьте ссылки на объект и сотрудника",
    write_dependency=permissions.require_operational_write,
    delete_dependency=permissions.require_admin,
)


# Дополнительный эндпоинт "Подробнее" — возвращает инцидент вместе с
# развёрнутыми связанными сущностями (объект, ответственный сотрудник),
# чтобы фронтенду не пришлось делать три отдельных запроса.
@router.get("/{item_id}/detail", response_model=schemas.IncidentDetailResponse)
def get_incident_detail(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: models.Staff = Depends(auth.get_current_user),
):
    incident = db.query(models.Incident).filter(models.Incident.id_inc == item_id).first()
    if incident is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Инцидент с id={item_id} не найден")
    return incident
