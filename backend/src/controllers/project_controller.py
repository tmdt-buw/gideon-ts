import json
import shutil
from typing import Type
from uuid import UUID

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from src.config.settings import get_settings
from src.controllers import label_class_controller
from src.controllers.base_controller import ControllerBase
from src.controllers.cache_controller import cache
from src.controllers.util.file_processor import JsonFileProcessor, FileProcessor
from src.controllers.util.file_util import get_temp_file
from src.controllers.util.redis import redis_instance
from src.db.timescale_db.time_series_writer import TimeSeriesWriter
from src.db.timescale_db.tsdb_connector_pool import TimescaleDBConnectorPool
from src.models.models.label import default_type
from src.models.models.project import CreateProject, IntegrationStatus, ProjectStatusUpdate
from src.models.schemas import Project
from src.models.shared.file_type import FileType


class ProjectController(ControllerBase[Project, CreateProject, Project]):

    def create(self, db: Session, connector: TimescaleDBConnectorPool, create: CreateProject) -> (Project, dict):

        # check if file exists
        file = get_temp_file(create.file)
        if not file.exists() or not file.is_file():
            raise HTTPException(status_code=400, detail="Invalid file id.")

        # write ts data to db
        file_type = file.suffix
        processor_type: Type[FileProcessor]
        if file_type == FileType.json:
            processor_type = JsonFileProcessor
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type.")
        processor = processor_type(file=file, project=create)
        project_obj = processor.process()
        project_obj.status = IntegrationStatus.integrating
        # delete temp folder to clean up
        shutil.rmtree(file.parent)

        # save meta data
        db.add(project_obj)
        db.commit()
        db.refresh(project_obj)

        label_class_controller.labelClass.create(db=db, project_id=project_obj.id, create=default_type)
        db.refresh(project_obj)
        return project_obj, processor.values

    async def integrate_project(self, db: Session, connector: TimescaleDBConnectorPool, project_obj: Project, values: dict):

        def send_progress_update_from_writer(id: UUID, writer: TimeSeriesWriter, increase: float):
            p = writer.progress
            writer.progress += increase
            update = ProjectStatusUpdate(id=id, progress=round(p, 2), status=IntegrationStatus.integrating)
            redis_instance.publish(get_settings().INTEGRATION_PROGRESS_CHANNEL, json.dumps(jsonable_encoder(update)))

        def send_progress_update(id: UUID, progress: int, status: IntegrationStatus):
            update = ProjectStatusUpdate(id=id, progress=progress, status=status)
            redis_instance.publish(get_settings().INTEGRATION_PROGRESS_CHANNEL, json.dumps(jsonable_encoder(update)))

        # write ts data
        try:
            writer = TimeSeriesWriter(connector=connector, project=project_obj)
            increase = get_settings().DATA_PER_SECOND / writer.n_values
            scheduler = BackgroundScheduler()
            job = scheduler.add_job(send_progress_update_from_writer, 'interval', args=[project_obj.id, writer, increase], seconds=1)
            scheduler.start()
            writer.write(values)
            job.remove()
            send_progress_update(project_obj.id, 100, IntegrationStatus.finished)
            project_obj.status = IntegrationStatus.finished
            db.add(project_obj)
            db.commit()
        except:
            # clean up in case of error
            send_progress_update(project_obj.id, 100, IntegrationStatus.error)
            project_obj.status = IntegrationStatus.error
            db.add(project_obj)
            db.commit()

    def get_by_name(self, db: Session, name: str) -> Project:
        return db.query(self.model).filter(self.model.name == name).first()

    def remove(self, db: Session, connector: TimescaleDBConnectorPool, uuid: UUID) -> Project:
        TimeSeriesWriter(connector=connector).remove(uuid)
        cache.delete_cache(uuid)
        return super().remove(db=db, uuid=uuid)


project = ProjectController(Project)
