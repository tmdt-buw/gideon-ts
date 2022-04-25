import json
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from starlette.responses import Response

from src.controllers import project_controller, label_class_controller
from src.controllers.base_controller import ControllerBase
from src.models.models.label import CreateLabel
from src.models.schemas import Label


class LabelController(ControllerBase[Label, CreateLabel, Label]):

    def get_all(self, db: Session, project_id: UUID, skip: int = 0, limit: int = 10000) -> list[Label]:
        project = project_controller.project.get_or_error(db=db, uuid=project_id)
        return project.labels

    def create(self, db: Session, project_id: UUID, create: list[CreateLabel]) -> list[Label]:
        res = []
        for createLabel in create:
            create_obj = jsonable_encoder(createLabel)
            db_obj = self.model(**create_obj)  # type: ignore
            project = project_controller.project.get_or_error(db=db, uuid=project_id)
            label_type = label_class_controller.labelClass.get(db=db, uuid=createLabel.label_class)
            db_obj.label_type = label_type
            project.labels.append(db_obj)
            db.add(project)
            res.append(db_obj)
        db.commit()
        for res_obj in res:
            db.refresh(res_obj)
        return res

    def delete_by_sample(self, db: Session, project_id: UUID, sample: int):
        project = project_controller.project.get_or_error(db=db, uuid=project_id)
        db.query(Label).filter(Label.sample == sample, Label.project == project.id).delete()
        db.commit()

    def export_labels(self, db: Session, project_id: UUID):
        label_dict = {}
        project = project_controller.project.get_or_error(db=db, uuid=project_id)
        for sampleIt in range(project.samples):
            sample = sampleIt + 1
            label_dict[sample] = {}
            all_labels_for_sample = db.query(Label).filter(Label.sample == sample, Label.project == project.id)
            for dimensionIt in range(project.dimensions):
                dimension = dimensionIt + 1
                label_dict[sample][dimension] = []
                for single_label_for_sample in all_labels_for_sample:
                    if dimension in single_label_for_sample.dimensions:
                        label_class = label_class_controller.labelClass.get(db=db, uuid=single_label_for_sample.label_class)
                        label_description_dimension = {
                            "name": label_class.name,
                            "severity": label_class.severity.value,
                            "start": single_label_for_sample.start,
                            "end": single_label_for_sample.end,
                            "priority": label_class.priority,
                            "created": single_label_for_sample.created
                        }
                        label_dict[sample][dimension].append(label_description_dimension)
        bytes = json.dumps(label_dict, indent=4, default=str)
        return Response(content=bytes, media_type="application/json")


label = LabelController(Label)
