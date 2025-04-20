from contextlib import suppress
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.exc import OperationalError

from app.dao import PhotoDAO
from app.database import Base, SessionLocal, engine
from app.storage import get_storage_backend

load_dotenv()

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI()

HTTP_200_OK = 200
HTTP_500_INTERNAL_SERVER_ERROR = 500

class RescanResponse(BaseModel):
    status: str
    num_new_photos: int

class PhotoListResponse(BaseModel):
    photo_ids: list[int]

class PhotoResponse(BaseModel):
    id: int
    object_key: str
    caption: str | None

@app.get("/photos", response_model=PhotoListResponse)
def get_photos(
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> JSONResponse | PhotoListResponse:
    """
    List photo IDs with pagination.
    Returns: {"photo_ids": [...]}
    """
    try:
        db = SessionLocal()
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc)},
        )
    try:
        dao = PhotoDAO(db)
        try:
            photos = dao.list(limit=limit, offset=offset)
        except OperationalError:
            photo_ids = []
        else:
            photo_ids = [photo.id for photo in photos]
    finally:
        with suppress(Exception):
            db.close()
    return PhotoListResponse(photo_ids=photo_ids)

@app.get("/photos/{photo_id}", response_model=PhotoResponse)
def get_photo(photo_id: int) -> JSONResponse | PhotoResponse:
    """
    Retrieve photo metadata by ID.
    Returns: {"id": int, "object_key": str, "caption": str | None}
    """
    db = None
    try:
        db = SessionLocal()
        dao = PhotoDAO(db)
        photo = dao.get(photo_id)
    except OperationalError:
        return JSONResponse(
            status_code=404,
            content={"detail": "Photo not found"},
        )
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc)},
        )
    finally:
        with suppress(Exception):
            if db is not None:
                db.close()

    if photo is None:
        return JSONResponse(
            status_code=404,
            content={"detail": "Photo not found"},
        )

    return PhotoResponse(
        id=photo.id,
        object_key=photo.object_key,
        caption=photo.caption,
    )

@app.post("/rescan", response_model=RescanResponse)
def rescan() -> RescanResponse | JSONResponse:
    """
    Discover any new photos in storage and report count.
    """
    try:
        backend = get_storage_backend()
        photos = backend.list_photos()
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc)},
        )
    else:
        # Sync storage with DB: insert any missing records
        db = SessionLocal()
        # ensure tables exist for in-memory DB
        try:
            bind_engine = db.get_bind()
        except AttributeError:
            bind_engine = getattr(db, "bind", None)
        if bind_engine is not None:
            Base.metadata.create_all(bind=bind_engine)
        try:
            dao = PhotoDAO(db)
            # get existing records (limit equal to total storage count)
            existing = dao.list(limit=len(photos), offset=0)
            existing_keys = {photo.object_key for photo in existing}
            new_keys = [key for key in photos if key not in existing_keys]
            for key in new_keys:
                dao.create(key)
            num_new = len(new_keys)
        finally:
            with suppress(Exception):
                db.close()
        return RescanResponse(status="ok", num_new_photos=num_new)

# Expose get_storage_backend for test monkeypatching
