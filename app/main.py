from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from app.storage import get_storage_backend

load_dotenv()

app = FastAPI()

HTTP_200_OK = 200
HTTP_500_INTERNAL_SERVER_ERROR = 500

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

# Expose get_storage_backend for test monkeypatching
