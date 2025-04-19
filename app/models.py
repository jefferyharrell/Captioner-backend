from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    object_key: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
