import uuid

from sqlalchemy import Column, String, Integer, Boolean, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.db.sqlalchemy.database import Base
from src.models.models.project import IntegrationStatus


class Project(Base):
    __tablename__ = "projects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, index=True)
    samples = Column(Integer)
    dimensions = Column(Integer)
    hasTimestamps = Column(Boolean)
    status = Column(Enum(IntegrationStatus))
    sampleLength = Column(Integer)
    sampleTime = Column(Float)
    labelClasses = relationship(
        "LabelClass",
        cascade="all, delete"
    )
    labels = relationship(
        "Label",
        cascade="all, delete"
    )
