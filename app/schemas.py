from pydantic import BaseModel


class RescanResponse(BaseModel):
    status: str
    num_new_photos: int


class PhotoListResponse(BaseModel):
    photo_ids: list[int]


class PhotoResponse(BaseModel):
    id: int
    object_key: str
    caption: str | None
    tags: str = ""


class CaptionUpdateRequest(BaseModel):
    caption: str
