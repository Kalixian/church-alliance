"""CRUD operations for articles."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.db.article.models import Article
from app.db.article.schemas import ArticleCreate, ArticleUpdate, _default_summary


def create_article(db: Session, article: ArticleCreate, creator_id: UUID) -> Article:
    db_article = Article(
        title=article.title,
        content=article.content,
        summary=article.summary or _default_summary(article.content),
        creator_id=creator_id,
    )
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article


def get_article_by_id(db: Session, article_id: UUID) -> Article | None:
    return db.query(Article).filter(Article.id == article_id).first()


def get_all_articles(db: Session, skip: int = 0, limit: int = 100) -> list[Article]:
    return (
        db.query(Article)
        .order_by(Article.created_at.desc(), Article.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_article(db: Session, article_id: UUID, article_update: ArticleUpdate) -> Article | None:
    db_article = get_article_by_id(db, article_id)
    if not db_article:
        return None

    update_data = article_update.model_dump(exclude_unset=True)
    if "title" in update_data:
        db_article.title = update_data["title"]
    if "content" in update_data:
        db_article.content = update_data["content"]
    if "summary" in update_data and update_data["summary"]:
        db_article.summary = update_data["summary"]
    elif "content" in update_data or "summary" in update_data:
        db_article.summary = _default_summary(db_article.content)

    db.commit()
    db.refresh(db_article)
    return db_article


def delete_article(db: Session, article_id: UUID) -> bool:
    db_article = get_article_by_id(db, article_id)
    if not db_article:
        return False

    db.delete(db_article)
    db.commit()
    return True
