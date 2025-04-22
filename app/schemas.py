from pydantic import BaseModel


class RescanResponse(BaseModel):
    status: str
    num_new_photos: int


class PhotoListResponse(BaseModel):
    photo_ids: list[int]


class PhotoResponse(BaseModel):
    id: int
    object_key: str
    description: str | None


class MetadataUpdateRequest(BaseModel):
    description: str
