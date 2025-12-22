from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
)

from app.libs.database import Base


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    code = Column(String(255), nullable=False, index=True, unique=True)
    name = Column(String(255), nullable=True, index=True, unique=True)
    description = Column(String(500), nullable=True)
    is_enabled = Column(Boolean, nullable=False, default=True, index=True)
