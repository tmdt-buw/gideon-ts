from typing import Generic, List, Optional, Type, TypeVar, Union, Dict, Any
from uuid import UUID

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.db.sqlalchemy.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateModelType = TypeVar("CreateModelType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class ControllerBase(Generic[ModelType, CreateModelType, UpdateSchemaType]):

    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        """
        self.model = model

    def get(self, db: Session, uuid: UUID) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == uuid).first()

    def get_all(self, db: Session, skip: int = 0, limit: int = 1000) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, create: CreateModelType) -> ModelType:
        create_obj = jsonable_encoder(create)
        db_obj = self.model(**create_obj)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: ModelType, update_obj: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(update_obj, dict):
            update_data = update_obj
        else:
            update_data = update_obj.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, uuid: UUID) -> ModelType:
        obj = self.get_or_error(db=db, uuid=uuid)
        db.delete(obj)
        db.commit()
        return obj

    def get_or_error(self, db: Session, uuid: UUID) -> ModelType:
        obj = self.get(db=db, uuid=uuid)
        if not obj:
            raise HTTPException(status_code=404, detail="Not found.")
        return obj
