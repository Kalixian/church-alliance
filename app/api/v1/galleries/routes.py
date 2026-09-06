from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.v1.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.gallery.crud import (
    create_gallery,
    create_picture,
    delete_gallery,
    delete_picture,
    get_all_galleries,
    get_all_pictures,
    get_gallery_by_id,
    get_picture_by_id,
    get_pictures_by_gallery,
    move_pictures_between_galleries,
    update_gallery,
    update_picture,
)
from app.db.gallery.schemas import (
    GalleryCreate,
    GalleryResponse,
    GalleryUpdate,
    PictureCreate,
    PictureResponse,
    PictureUpdate,
)
from app.db.user import UserResponse, UserRole

router = APIRouter(prefix="/galleries", tags=["galleries"])
pictures_router = APIRouter(prefix="/pictures", tags=["pictures"])


@router.post("", response_model=GalleryResponse)
def create_gallery_route(
    gallery: GalleryCreate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    if current_user.role not in {UserRole.ADMINISTRATOR, UserRole.ORGANIZER}:
        raise HTTPException(status_code=403, detail="Only organizers and administrators can manage galleries")

    existing = create_gallery(db, gallery.name)
    if existing is None:
        raise HTTPException(status_code=409, detail="Gallery already exists")
    return existing


@router.get("", response_model=list[GalleryResponse])
def list_galleries(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_all_galleries(db, skip=skip, limit=limit)


@router.get("/{gallery_id}", response_model=GalleryResponse)
def get_gallery(gallery_id: str, db: Session = Depends(get_db)):
    try:
        gallery_uuid = UUID(gallery_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid gallery ID")

    gallery = get_gallery_by_id(db, gallery_uuid)
    if not gallery:
        raise HTTPException(status_code=404, detail="Gallery not found")
    return gallery


@router.patch("/{gallery_id}", response_model=GalleryResponse)
def update_gallery_route(
    gallery_id: str,
    gallery_update: GalleryUpdate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    if current_user.role not in {UserRole.ADMINISTRATOR, UserRole.ORGANIZER}:
        raise HTTPException(status_code=403, detail="Only organizers and administrators can manage galleries")

    try:
        gallery_uuid = UUID(gallery_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid gallery ID")

    gallery = update_gallery(db, gallery_uuid, name=gallery_update.name)
    if not gallery:
        raise HTTPException(status_code=404, detail="Gallery not found")
    return gallery


@router.delete("/{gallery_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_gallery_route(
    gallery_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    if current_user.role not in {UserRole.ADMINISTRATOR, UserRole.ORGANIZER}:
        raise HTTPException(status_code=403, detail="Only organizers and administrators can manage galleries")

    try:
        gallery_uuid = UUID(gallery_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid gallery ID")

    success = delete_gallery(db, gallery_uuid)
    if not success:
        raise HTTPException(status_code=404, detail="Gallery not found")
    return None


@router.get("/{gallery_id}/pictures", response_model=list[PictureResponse])
def list_pictures_for_gallery(gallery_id: str, db: Session = Depends(get_db)):
    try:
        gallery_uuid = UUID(gallery_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid gallery ID")

    pictures = get_pictures_by_gallery(db, gallery_uuid)
    return pictures


@router.post("/{source_gallery_id}/move/{target_gallery_id}", response_model=list[PictureResponse])
def move_gallery_pictures_route(
    source_gallery_id: str,
    target_gallery_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    if current_user.role not in {UserRole.ADMINISTRATOR, UserRole.ORGANIZER}:
        raise HTTPException(status_code=403, detail="Only organizers and administrators can move galleries")

    try:
        source_uuid = UUID(source_gallery_id)
        target_uuid = UUID(target_gallery_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid gallery ID")

    moved_pictures = move_pictures_between_galleries(db, source_uuid, target_uuid)
    if moved_pictures is None:
        raise HTTPException(status_code=404, detail="Gallery not found")
    return moved_pictures


@pictures_router.post("", response_model=PictureResponse)
def create_picture_route(
    image: UploadFile = File(...),
    caption: str | None = Form(None),
    gallery_id: str | None = Form(None),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == UserRole.APPLICANT:
        raise HTTPException(status_code=403, detail="Only confirmed users can add pictures")

    resolved_gallery_id = None
    if gallery_id:
        try:
            resolved_gallery_id = UUID(gallery_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid gallery ID")

    image_bytes = image.file.read()
    db_picture = create_picture(
        db,
        caption=caption,
        gallery_id=resolved_gallery_id,
        uploaded_by_id=current_user.id,
        image_bytes=image_bytes,
        file_name=image.filename,
    )
    if not db_picture:
        raise HTTPException(status_code=404, detail="Gallery not found")
    return db_picture


@pictures_router.get("", response_model=list[PictureResponse])
def list_pictures(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_all_pictures(db, skip=skip, limit=limit)


@pictures_router.get("/{picture_id}", response_model=PictureResponse)
def get_picture(picture_id: str, db: Session = Depends(get_db)):
    try:
        picture_uuid = UUID(picture_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid picture ID")

    picture = get_picture_by_id(db, picture_uuid)
    if not picture:
        raise HTTPException(status_code=404, detail="Picture not found")
    return picture


@pictures_router.patch("/{picture_id}", response_model=PictureResponse)
def update_picture_route(
    picture_id: str,
    picture_update: PictureUpdate,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    try:
        picture_uuid = UUID(picture_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid picture ID")

    picture = get_picture_by_id(db, picture_uuid)
    if not picture:
        raise HTTPException(status_code=404, detail="Picture not found")

    if picture_update.gallery_id is not None and current_user.role not in {UserRole.ADMINISTRATOR, UserRole.ORGANIZER}:
        raise HTTPException(status_code=403, detail="Only organizers and administrators can change a picture's gallery")

    if current_user.role not in {UserRole.ADMINISTRATOR, UserRole.ORGANIZER} and picture.uploaded_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own pictures")

    updated_picture = update_picture(
        db,
        picture_uuid,
        caption=picture_update.caption,
        gallery_id=picture_update.gallery_id,
        url=picture_update.url,
    )
    if not updated_picture:
        raise HTTPException(status_code=404, detail="Picture not found")
    return updated_picture


@pictures_router.delete("/{picture_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_picture_route(
    picture_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    try:
        picture_uuid = UUID(picture_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid picture ID")

    picture = get_picture_by_id(db, picture_uuid)
    if not picture:
        raise HTTPException(status_code=404, detail="Picture not found")

    if current_user.role not in {UserRole.ADMINISTRATOR, UserRole.ORGANIZER} and picture.uploaded_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete pictures you uploaded")

    success = delete_picture(db, picture_uuid)
    if not success:
        raise HTTPException(status_code=404, detail="Picture not found")
    return None

