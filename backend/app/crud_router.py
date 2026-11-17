from typing import Callable, List, Optional, Type

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import auth
from .database import get_db
from .pagination import Page, pagination_params, paginate


def _empty_filters():
    return {}


def apply_filters(query, model, filters: dict, search_fields: Optional[List[str]] = None):
    for key, value in filters.items():
        if value is None or value == "":
            continue
        if key == "search":
            if search_fields:
                conditions = [getattr(model, f).ilike(f"%{value}%") for f in search_fields]
                query = query.filter(or_(*conditions))
            continue
        if key.endswith("_min"):
            field = key[: -len("_min")]
            query = query.filter(getattr(model, field) >= value)
        elif key.endswith("_max"):
            field = key[: -len("_max")]
            query = query.filter(getattr(model, field) <= value)
        else:
            query = query.filter(getattr(model, key) == value)
    return query


def build_crud_router(
    *,
    model: Type,
    id_field: str,
    create_schema: Type,
    update_schema: Type,
    response_schema: Type,
    prefix: str,
    tags: List[str],
    entity_name: str,
    filter_dependency: Optional[Callable] = None,
    search_fields: Optional[List[str]] = None,
    on_create: Optional[Callable] = None,
    on_update: Optional[Callable] = None,
    before_update: Optional[Callable] = None,
    before_delete: Optional[Callable] = None,
    conflict_detail: str = "Нарушено ограничение целостности данных",
    read_dependency: Optional[Callable] = None,
    write_dependency: Optional[Callable] = None,
    delete_dependency: Optional[Callable] = None,
):
    router = APIRouter(prefix=prefix, tags=tags)
    filter_dep = filter_dependency or _empty_filters
    read_dep = read_dependency or auth.get_current_user
    write_dep = write_dependency or auth.get_current_user
    delete_dep = delete_dependency or write_dep

    def get_or_404(db: Session, item_id: int):
        item = db.query(model).filter(getattr(model, id_field) == item_id).first()
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_name} с id={item_id} не найден(а)",
            )
        return item

    def _list_items(
        pagination: dict = Depends(pagination_params),
        filters: dict = Depends(filter_dep),
        db: Session = Depends(get_db),
        current_user=Depends(read_dep),
    ):
        query = db.query(model)
        query = apply_filters(query, model, filters, search_fields=search_fields)
        query = query.order_by(getattr(model, id_field).desc())
        items, total, pages = paginate(query, pagination["page"], pagination["page_size"])
        return Page(
            items=items,
            total=total,
            page=pagination["page"],
            page_size=pagination["page_size"],
            pages=pages,
        )

    router.add_api_route("", _list_items, methods=["GET"], response_model=Page[response_schema])

    def _get_item(item_id: int, db: Session = Depends(get_db), current_user=Depends(read_dep)):
        return get_or_404(db, item_id)

    router.add_api_route(
        "/{item_id}", _get_item, methods=["GET"], response_model=response_schema
    )

    def _create_item(payload: create_schema, db: Session = Depends(get_db), current_user=Depends(write_dep)):
        data = payload.model_dump()
        if on_create:
            data = on_create(data, current_user)
        item = model(**data)
        db.add(item)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflict_detail)
        db.refresh(item)
        return item

    router.add_api_route(
        "", _create_item, methods=["POST"], response_model=response_schema, status_code=status.HTTP_201_CREATED
    )

    def _update_item(
        item_id: int,
        payload: update_schema,
        db: Session = Depends(get_db),
        current_user=Depends(write_dep),
    ):
        item = get_or_404(db, item_id)
        data = payload.model_dump(exclude_unset=True)
        if before_update:
            before_update(item, data, db)
        if on_update:
            data = on_update(data, current_user)
        for key, value in data.items():
            setattr(item, key, value)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflict_detail)
        db.refresh(item)
        return item

    router.add_api_route(
        "/{item_id}", _update_item, methods=["PUT"], response_model=response_schema
    )

    def _delete_item(item_id: int, db: Session = Depends(get_db), current_user=Depends(delete_dep)):
        item = get_or_404(db, item_id)
        if before_delete:
            before_delete(item, db)
        db.delete(item)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{entity_name} используется в других записях и не может быть удалён(а)",
            )
        return None

    router.add_api_route(
        "/{item_id}", _delete_item, methods=["DELETE"], status_code=status.HTTP_204_NO_CONTENT
    )

    return router
