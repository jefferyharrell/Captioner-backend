from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.dao import PhotoDAO
from app.deps import get_db
from app.schemas import RescanResponse

router = APIRouter()


@router.post("/rescan", response_model=RescanResponse)
def rescan(
    db: Annotated[Session, Depends(get_db)],
) -> RescanResponse | JSONResponse:
    """
    Discover any new photos in storage and report count.
    """
    # Late import to allow test override of get_storage_backend
    from app.main import get_storage_backend

    try:
        backend = get_storage_backend()
        photos = backend.list_photos()
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(status_code=500, content={"detail": str(exc)})

    # Ensure DB tables exist for in-memory SQLite used in tests
    from app.database import Base

    try:
        engine = db.get_bind()
        Base.metadata.create_all(bind=engine)
    except Exception:  # noqa: BLE001, S110
        # If we can't get the engine or create tables, continue anyway
        # This is mostly for test scenarios and should be silent
        pass

    # Process DB entries; dependency handles session cleanup
    dao = PhotoDAO(db)
    existing = dao.list(limit=len(photos), offset=0)
    existing_keys = {p.object_key for p in existing}
    new_keys = [k for k in photos if k not in existing_keys]
    for key in new_keys:
        dao.create(key)
    num_new = len(new_keys)
    return RescanResponse(status="ok", num_new_photos=num_new)
