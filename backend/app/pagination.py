import math
from typing import Generic, List, TypeVar

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy.orm import Query as SAQuery

from .config import get_settings

settings = get_settings()

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


def pagination_params(
    page: int = Query(default=1, ge=1, description="Номер страницы (с 1)"),
    page_size: int = Query(
        default=settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description="Размер страницы",
    ),
):
    return {"page": page, "page_size": page_size}


def paginate(query: SAQuery, page: int, page_size: int):
    total = query.count()
    pages = max(1, math.ceil(total / page_size)) if page_size else 1
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total, pages
