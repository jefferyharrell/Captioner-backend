from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.models import Photo


class PhotoDAO:
    """Data Access Object for Photo."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, photo_id: int) -> Photo | None:
        return self.db.get(Photo, photo_id)

    def list(self, limit: int = 100, offset: int = 0) -> Sequence[Photo]:
        return (
            self.db.query(Photo)
            .order_by(Photo.id)
            .offset(offset)
            .limit(limit)
            .all()
        )

    def create(self, object_key: str, caption: str | None = None) -> Photo:
        photo = Photo(object_key=object_key, caption=caption)
        self.db.add(photo)
        self.db.commit()
        self.db.refresh(photo)
        return photo

    def update_caption(self, photo_id: int, caption: str) -> Photo | None:
        photo = self.get(photo_id)
        if photo is None:
            return None
        photo.caption = caption
        self.db.commit()
        self.db.refresh(photo)
        return photo

    def delete(self, photo_id: int) -> bool:
        photo = self.get(photo_id)
        if photo is None:
            return False
        self.db.delete(photo)
        self.db.commit()
        return True
