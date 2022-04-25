from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.apis.connectors import get_db, get_connector
from src.controllers import label_class_controller, label_controller
from src.controllers.prediction_controller import predict
from src.db.timescale_db.tsdb_connector import TimescaleDBConnector
from src.models.models.label import Label, LabelClass, CreateLabel, CreateLabelClass
from src.models.models.prediction import Prediction, PredictionRequest

router = APIRouter(prefix="/labels", tags=["labels"])


@router.get("/classes", response_model=List[LabelClass])
def get_label_classes(project: UUID, db: Session = Depends(get_db)) -> List[LabelClass]:
    return label_class_controller.labelClass.get_all(db=db, project_id=project)


@router.post("/classes", response_model=LabelClass)
def create_label_class(project: UUID, label_type: CreateLabelClass, db: Session = Depends(get_db)) -> LabelClass:
    db_label_type = label_class_controller.labelClass.get_by_project_and_name(db=db, project=project, name=label_type.name)
    if db_label_type:
        raise HTTPException(status_code=400, detail="Label type with this name already exists.")
    return label_class_controller.labelClass.create(db=db, project_id=project, create=label_type)


@router.get("", response_model=List[Label])
def get_labels(project: UUID, db: Session = Depends(get_db)) -> List[Label]:
    return label_controller.label.get_all(db=db, project_id=project)


@router.put("", response_model=Label)
def update_label(label: Label, db: Session = Depends(get_db)) -> Label:
    update = {key: label.dict()[key] for key in ["label_class", "start", "end"]}
    db_label = label_controller.label.get(db=db, uuid=label.id)
    return label_controller.label.update(db=db, db_obj=db_label, update_obj=update)


@router.post("", response_model=List[Label])
def set_labels(project: UUID, labels: List[CreateLabel], db: Session = Depends(get_db)) -> List[Label]:
    return label_controller.label.create(db=db, project_id=project, create=labels)


@router.delete("/{uuid}", response_model=Label)
def delete_label(uuid: UUID, db: Session = Depends(get_db)) -> Label:
    return label_controller.label.remove(db=db, uuid=uuid)


@router.delete("")
def delete_labels_by_sample(project: UUID, sample: int, db: Session = Depends(get_db)) -> Label:
    return label_controller.label.delete_by_sample(db=db, sample=sample, project_id=project)


@router.post("/predictions", response_model=Prediction)
async def predict_labels(project: UUID, prediction: PredictionRequest, db: Session = Depends(get_db), connector: TimescaleDBConnector = Depends(get_connector)) -> Prediction:
    return predict(project_uuid=project, prediction=prediction, db=db, connector=connector)


@router.get("/export")
async def export_labels(project: UUID, db: Session = Depends(get_db)):
    return label_controller.label.export_labels(db=db, project_id=project)
