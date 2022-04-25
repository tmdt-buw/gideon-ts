from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from src.controllers import project_controller
from src.controllers.base_controller import ControllerBase
from src.models.models.label import CreateLabelClass
from src.models.schemas.label import LabelClass


class LabelClassController(ControllerBase[LabelClass, CreateLabelClass, LabelClass]):

    def get_all(self, db: Session, project_id: UUID, skip: int = 0, limit: int = 100) -> list[LabelClass]:
        project = project_controller.project.get_or_error(db=db, uuid=project_id)
        return project.labelClasses

    def get_by_project_and_name(self, db: Session, project: UUID, name: str) -> LabelClass:
        return db.query(self.model).filter(self.model.project == project, self.model.name == name).first()

    def create(self, db: Session, project_id: UUID, create: CreateLabelClass) -> LabelClass:
        create_obj = jsonable_encoder(create)
        db_obj = self.model(**create_obj)  # type: ignore
        project = project_controller.project.get_or_error(db=db, uuid=project_id)
        db_obj.priority = len(project.labelClasses)
        project.labelClasses.append(db_obj)
        db.add(project)
        db.commit()
        db.refresh(db_obj)
        return db_obj


labelClass = LabelClassController(LabelClass)
