from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.v1.auth.dependencies import (
    ensure_owner_or_role,
    get_current_user,
    is_manager,
    require_confirmed,
    require_manager,
)
from app.db.database import get_db
from app.db.gallery.crud import (
    create_gallery,
    count_pictures,
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
    PictureResponse,
    PictureUpdate,
    PictureUploadConfirm,
    UploadSignatureResponse,
)
from app.db.user import UserResponse
from app.services.pictures import DuplicateUploadError, confirm_upload, remove_gallery, remove_picture
from app.storage import ImageStorage, StorageUnavailableError, UploadVerificationError, get_image_storage

router = APIRouter(prefix="/galleries", tags=["galleries"])
pictures_router = APIRouter(prefix="/pictures", tags=["pictures"])

gallery_managers = require_manager("Only coordinators and administrators can manage galleries")


@router.post("", response_model=GalleryResponse)
def create_gallery_route(
    gallery: GalleryCreate,
    current_user: Annotated[UserResponse, Depends(gallery_managers)],
    db: Session = Depends(get_db),
):
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
    current_user: Annotated[UserResponse, Depends(gallery_managers)],
    db: Session = Depends(get_db),
):
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
    current_user: Annotated[UserResponse, Depends(gallery_managers)],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    storage: ImageStorage = Depends(get_image_storage),
):
    try:
        gallery_uuid = UUID(gallery_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid gallery ID")

    if not remove_gallery(db, storage, background_tasks, gallery_uuid):
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
    current_user: Annotated[
        UserResponse,
        Depends(require_manager("Only coordinators and administrators can move galleries")),
    ],
    db: Session = Depends(get_db),
):
    try:
        source_uuid = UUID(source_gallery_id)
        target_uuid = UUID(target_gallery_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid gallery ID")

    moved_pictures = move_pictures_between_galleries(db, source_uuid, target_uuid)
    if moved_pictures is None:
        raise HTTPException(status_code=404, detail="Gallery not found")
    return moved_pictures


@pictures_router.post("/upload-signature", response_model=UploadSignatureResponse)
def create_upload_signature_route(
    current_user: Annotated[UserResponse, Depends(require_confirmed("Only confirmed users can add pictures"))],
    storage: ImageStorage = Depends(get_image_storage),
):
    """Sign a direct browser-to-Cloudinary upload. Confirm it afterwards with POST /pictures."""
    try:
        signature = storage.create_upload_signature()
    except StorageUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return UploadSignatureResponse(upload_url=signature.upload_url, fields=signature.fields)


@pictures_router.post("", response_model=PictureResponse)
def create_picture_route(
    upload: PictureUploadConfirm,
    current_user: Annotated[UserResponse, Depends(require_confirmed("Only confirmed users can add pictures"))],
    db: Session = Depends(get_db),
    storage: ImageStorage = Depends(get_image_storage),
):
    """Save a picture for a completed direct upload, using Cloudinary's signed upload response."""
    try:
        picture = confirm_upload(
            db,
            storage,
            public_id=upload.public_id,
            version=upload.version,
            signature=upload.signature,
            caption=upload.caption,
            gallery_id=upload.gallery_id,
            uploaded_by_id=current_user.id,
        )
    except UploadVerificationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DuplicateUploadError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except StorageUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not picture:
        raise HTTPException(status_code=404, detail="Gallery not found")
    return picture


@pictures_router.get("", response_model=list[PictureResponse])
def list_pictures(
    response: Response,
    skip: int = Query(0, ge=0),
    limit: int = Query(24, ge=1, le=100),
    search: str | None = Query(None, alias="q"),
    gallery_id: str | None = Query(None),
    db: Session = Depends(get_db),
):
    resolved_gallery_id = None
    if gallery_id:
        try:
            resolved_gallery_id = UUID(gallery_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid gallery ID")

    response.headers["X-Total-Count"] = str(count_pictures(db, search=search, gallery_id=resolved_gallery_id))
    return get_all_pictures(db, skip=skip, limit=limit, search=search, gallery_id=resolved_gallery_id)


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

    if picture_update.gallery_id is not None and not is_manager(current_user):
        raise HTTPException(status_code=403, detail="Only coordinators and administrators can change a picture's gallery")

    ensure_owner_or_role(current_user, picture.uploaded_by_id, "You can only update your own pictures")

    updated_picture = update_picture(
        db,
        picture_uuid,
        caption=picture_update.caption,
        gallery_id=picture_update.gallery_id,
    )
    if not updated_picture:
        raise HTTPException(status_code=404, detail="Picture not found")
    return updated_picture


@pictures_router.delete("/{picture_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_picture_route(
    picture_id: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    storage: ImageStorage = Depends(get_image_storage),
):
    try:
        picture_uuid = UUID(picture_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid picture ID")

    picture = get_picture_by_id(db, picture_uuid)
    if not picture:
        raise HTTPException(status_code=404, detail="Picture not found")

    ensure_owner_or_role(current_user, picture.uploaded_by_id, "You can only delete pictures you uploaded")

    if not remove_picture(db, storage, background_tasks, picture_uuid):
        raise HTTPException(status_code=404, detail="Picture not found")
    return None

