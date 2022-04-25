import json
import time
from logging.config import dictConfig

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.routing import APIRoute

import src.models.schemas  # noqa: F401 - required for database init
from src.apis.health_api import router as HealthApiRouter
from src.apis.labeling_api import router as LabelingApiRouter
from src.apis.projects_api import router as ProjectsApiRouter
from src.apis.time_series_api import router as TimeSeriesApiRouter
from src.config.log_config import LogConfig
from src.config.settings import get_settings
from src.controllers.cache_controller import cache
from src.controllers.util.file_util import remove_temp
from src.controllers.util.redis import redis_instance
from src.db.sqlalchemy.database import init_db
from src.ws.websocket_manager import manager


def use_route_names_as_operation_ids(fast_app: FastAPI) -> None:
    """
    Simplify operation IDs so that generated API clients have simpler function
    names.

    Should be called only after all routes have been added.
    """
    for route in fast_app.routes:
        if isinstance(route, APIRoute):
            route.path = route.path.replace(get_settings().base_url, "")
            route.path_format = route.path.replace(get_settings().base_url, "")
            route.operation_id = route.name


app = FastAPI(
    title="Efficient Labeling of Time Series",
    description="No description provided",
    version="1.0",
    servers=[
        {"url": get_settings().base_url, "description": "Base Url"}
    ])

app.include_router(HealthApiRouter, prefix=get_settings().base_url)
app.include_router(ProjectsApiRouter, prefix=get_settings().base_url)
app.include_router(TimeSeriesApiRouter, prefix=get_settings().base_url)
app.include_router(LabelingApiRouter, prefix=get_settings().base_url)
use_route_names_as_operation_ids(app)
# init logging
dictConfig(LogConfig().dict())


@app.on_event("startup")
async def startup_event():
    init_db()


@app.on_event("shutdown")
def shutdown_event():
    # clean up
    cache.clear_cache()
    remove_temp()


@app.websocket("/socket")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        redis_pubsub = redis_instance.pubsub(ignore_subscribe_messages=True)
        redis_pubsub.subscribe(get_settings().INTEGRATION_PROGRESS_CHANNEL)
        while True:
            message = redis_pubsub.get_message()
            if message:
                update = json.loads(message['data'])
                await manager.send_project_update(update)
            time.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, workers=8)
