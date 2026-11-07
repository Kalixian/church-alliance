from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.auth.dependencies import (
    ARTICLE_AUTHOR_ROLES,
    allow_roles,
    ensure_can_manage_article,
    get_current_user,
)
from app.db.article import (
    ArticleCreate,
    ArticleResponse,
    ArticleUpdate,
    create_article,
    get_all_articles,
    get_article_by_id,
    update_article,
)
from app.db.database import get_db
from app.db.gallery import GalleryResponse, get_or_create_article_gallery
from app.db.user import UserResponse
from app.services.pictures import remove_article
from app.storage import ImageStorage, get_image_storage

router = APIRouter(prefix="/articles", tags=["articles"])


def _parse_article_id(article_id: str) -> UUID:
    try:
        return UUID(article_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid article ID") from exc


@router.post("", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
def create_article_route(
    article: ArticleCreate,
    current_user: Annotated[UserResponse, Depends(allow_roles(*ARTICLE_AUTHOR_ROLES, detail="Only coordinators and administrators can create articles"))],
    db: Session = Depends(get_db),
):
    return create_article(db, article, current_user.id)


@router.get("", response_model=list[ArticleResponse])
def list_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return get_all_articles(db, skip=skip, limit=limit)


@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(article_id: str, db: Session = Depends(get_db)):
    article = get_article_by_id(db, _parse_article_id(article_id))
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.patch("/{article_id}", response_model=ArticleResponse)
def update_article_route(
    article_id: str,
    article_update: ArticleUpdate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    parsed_id = _parse_article_id(article_id)
    article = get_article_by_id(db, parsed_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    ensure_can_manage_article(current_user, article.creator_id, "You can only update your own articles")
    return update_article(db, parsed_id, article_update)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article_route(
    article_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    storage: ImageStorage = Depends(get_image_storage),
):
    parsed_id = _parse_article_id(article_id)
    article = get_article_by_id(db, parsed_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    ensure_can_manage_article(current_user, article.creator_id, "You can only delete your own articles")
    remove_article(db, storage, background_tasks, parsed_id)
    return None


@router.put("/{article_id}/gallery", response_model=GalleryResponse)
def ensure_article_gallery_route(
    article_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Return the article's photo gallery, creating it if needed. Upload into it with POST /pictures."""
    parsed_id = _parse_article_id(article_id)
    article = get_article_by_id(db, parsed_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    ensure_can_manage_article(current_user, article.creator_id, "You can only add photos to your own articles")
    return get_or_create_article_gallery(db, parsed_id)
