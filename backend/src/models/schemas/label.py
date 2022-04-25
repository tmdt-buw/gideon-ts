import uuid

from sqlalchemy import BigInteger, ARRAY, Column, String, Enum, Integer, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.db.sqlalchemy.database import Base
from src.models.models.label import Severity


class Label(Base):
    __tablename__ = "labels"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project = Column(UUID(as_uuid=True), ForeignKey('projects.id'))
    label_class = Column(UUID(as_uuid=True), ForeignKey('label_classes.id'))
    start = Column(BigInteger)
    end = Column(BigInteger)
    sample = Column(Integer)
    dimensions = Column(ARRAY(Integer))
    created = Column(DateTime(timezone=True), server_default=func.now())


class LabelClass(Base):
    __tablename__ = "label_classes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    color = Column(String)
    severity = Column(Enum(Severity))
    priority = Column(Integer)
    project = Column(UUID(as_uuid=True), ForeignKey('projects.id'))
    labels = relationship(
        "Label",
        cascade="all, delete"
    )
