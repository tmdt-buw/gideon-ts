from uuid import uuid4, UUID

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from src.apis.connectors import get_db, get_connector
from src.controllers import project_controller
from src.controllers.util.file_util import gen_temp_file
from src.db.timescale_db.tsdb_connector_pool import TimescaleDBConnectorPool
from src.models.models.project import Project, CreateProject

router = APIRouter(prefix="/projects", tags=["projects"])

"""
    APIs
"""


@router.post("", response_model=Project)
async def create_project(project: CreateProject, background_tasks: BackgroundTasks, db: Session = Depends(get_db), connector: TimescaleDBConnectorPool = Depends(get_connector)) -> Project:
    """Create a project"""
    db_project = project_controller.project.get_by_name(db=db, name=project.name)
    if db_project:
        raise HTTPException(status_code=400, detail="Project with this name already exists.")
    project, values = project_controller.project.create(db=db, connector=connector, create=project)
    background_tasks.add_task(project_controller.project.integrate_project, db, connector, project, values)
    return project


@router.get("/{uuid}", response_model=Project)
async def get_project(uuid: UUID, db: Session = Depends(get_db)) -> Project:
    """Return a project"""
    return project_controller.project.get_or_error(db=db, uuid=uuid)


@router.get("", response_model=list[Project])
async def get_projects(db: Session = Depends(get_db)) -> list[Project]:
    """Returns a list of projects"""
    return project_controller.project.get_all(db=db)


@router.delete("/{uuid}")
def delete_project(uuid: UUID, db: Session = Depends(get_db), connector: TimescaleDBConnectorPool = Depends(get_connector)) -> Project:
    """Deletes given project"""
    return project_controller.project.remove(db=db, connector=connector, uuid=uuid)


@router.post("/files")
async def upload_file(file: UploadFile = File(None, description="")) -> UUID:
    """Upload a file for a project"""
    uuid = uuid4()
    temp_dir = gen_temp_file(uuid, file.filename)
    with open(temp_dir, "wb") as f:
        f.write(file.file.read())
    return uuid
