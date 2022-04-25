from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from src.models.models.label import Label, LabelClass


class IntegrationStatus(Enum):
    integrating = "integrating"
    error = "error"
    finished = "finished"


class ProjectBase(BaseModel):
    """ Project - Shared properties

        name: The name of this Project [Optional].
        samples: The samples of this Project [Optional].
        dimensions: The dimensions of this Project [Optional].
    """
    name: Optional[str] = None
    samples: Optional[int] = None
    dimensions: Optional[int] = None
    hasTimestamps: Optional[bool] = None
    status: Optional[IntegrationStatus] = None


class ProjectDB(ProjectBase):
    """ Project - DB Model
    """
    id: Optional[UUID]
    name: Optional[str]
    labelTypes: list[LabelClass] = []
    labels: list[Label] = []
    sampleLength: Optional[int] = None
    sampleTime: Optional[float] = None

    class Config:
        orm_mode = True


class CreateProject(BaseModel):
    """ Project - Create request object
        name: The name of this InlineObject1 [Optional].
        file: The file of this InlineObject1 [Optional].
    """
    name: str
    file: UUID


class Project(ProjectBase):
    """ Project - Model to pass to frontend
    """
    id: UUID

    class Config:
        orm_mode = True


class ProjectStatusUpdate(BaseModel):
    id: UUID
    progress: float
    status: IntegrationStatus
