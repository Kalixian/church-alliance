from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.auth.dependencies import get_current_user
from app.db.article import (
    ArticleCreate,
    ArticleResponse,
    ArticleUpdate,
    create_article,
    delete_article,
    get_all_articles,
    get_article_by_id,
    update_article,
)
from app.db.database import get_db
from app.db.user import UserResponse, UserRole

router = APIRouter(prefix="/articles", tags=["articles"])


def _parse_article_id(article_id: str) -> UUID:
    try:
        return UUID(article_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid article ID") from exc


def _can_manage_article(article, current_user: UserResponse) -> bool:
    return current_user.role in {UserRole.ADMINISTRATOR, UserRole.COORDINATOR} or article.creator_id == current_user.id


@router.post("", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
def create_article_route(
    article: ArticleCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.APPLICANT:
        raise HTTPException(status_code=403, detail="Applicants cannot create articles")
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
    if not _can_manage_article(article, current_user):
        raise HTTPException(status_code=403, detail="You can only update your own articles")
    return update_article(db, parsed_id, article_update)


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_article_route(
    article_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    parsed_id = _parse_article_id(article_id)
    article = get_article_by_id(db, parsed_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if not _can_manage_article(article, current_user):
        raise HTTPException(status_code=403, detail="You can only delete your own articles")
    delete_article(db, parsed_id)
    return None
