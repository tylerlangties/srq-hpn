from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.category import Category
from app.schemas.events import CategoryOut

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
) -> list[CategoryOut]:
    categories = db.scalars(select(Category).order_by(Category.name.asc())).all()
    return [
        CategoryOut(
            id=category.id,
            name=category.name,
            slug=category.slug,
        )
        for category in categories
    ]
