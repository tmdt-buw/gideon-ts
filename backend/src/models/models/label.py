from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel


class Severity(Enum):
    okay = 'okay'
    warning = 'warning'
    error = 'error'


class LabelClassBase(BaseModel):
    """
    Label Object which includes start end and id

    name: name of the Label
    color: color of the Label
    range: range of the Label
    """
    name: Optional[str] = None
    color: Optional[str] = None
    severity: Optional[Severity] = None


class LabelClass(LabelClassBase):
    id: UUID
    priority: int

    class Config:
        orm_mode = True


class CreateLabelClass(LabelClassBase):
    pass


default_type = CreateLabelClass(name="Normal", color="#2b821d", severity=Severity.okay)


class LabelBase(BaseModel):
    """ Label - Shared properties
    """
    label_class: Optional[UUID]
    start: Optional[int]
    end: Optional[int]
    sample: Optional[int]
    dimensions: Optional[List[int]]


class LabelDB(LabelBase):
    """ Project - DB Model
    """
    id: UUID
    label_class: LabelClass

    class Config:
        orm_mode = True


class CreateLabel(LabelBase):
    """ Project - Create request object
        name: The name of this InlineObject1 [Optional].
        file: The file of this InlineObject1 [Optional].
    """
    pass


class Label(LabelBase):
    """ Project - Model to pass to frontend
    """
    id: UUID

    class Config:
        orm_mode = True

