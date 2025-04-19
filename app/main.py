from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

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

@app.get("/photos")
def get_photos(
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, list[str]]:
    """
    List photo IDs with pagination.
    Returns: {"photo_ids": [...]}
    """
    try:
        backend = get_storage_backend()
        photo_ids = backend.list_photos()
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc)},
        )  # type: ignore[return-value]
    else:
        paged = photo_ids[offset : offset + limit]
        return {"photo_ids": paged}

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
        )  # type: ignore[return-value]
    else:
        # Sync storage with DB: insert any missing records
        db = SessionLocal()
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
            db.close()
        return RescanResponse(status="ok", num_new_photos=num_new)

# Expose get_storage_backend for test monkeypatching
