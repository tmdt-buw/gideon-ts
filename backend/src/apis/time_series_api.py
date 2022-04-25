from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.apis.connectors import get_connector, get_db
from src.controllers.time_series_controller import TimeSeriesController
from src.db.timescale_db.tsdb_connector_pool import TimescaleDBConnectorPool
from src.models.models.time_series import TimeSeries, TimeSeriesProject, TimeSeriesSample

router = APIRouter(prefix="/ts", tags=["time-series"])


@router.get("/{uuid}", responses={200: {"model": TimeSeriesProject, "description": "A list of time series."}})
async def get_time_series(uuid: UUID, db: Session = Depends(get_db), connector: TimescaleDBConnectorPool = Depends(get_connector)) -> TimeSeriesProject:
    """Returns all time series from file"""
    return TimeSeriesController.query_time_series(uuid=uuid, db=db, connector=connector)


@router.get("/{uuid}/samples", responses={200: {"model": List[TimeSeriesSample], "description": "A list of time series."}})
async def get_time_series_samples(uuid: UUID, db: Session = Depends(get_db), connector: TimescaleDBConnectorPool = Depends(get_connector)) -> List[dict]:
    """Returns all time series samples"""
    """ We could do typecasting with
        from pydantic import parse_obj_as 
        parse_obj_as(List[TimeSeriesSample], samples)
        but it takes a lot of time
    """
    return TimeSeriesController.query_time_series_samples(uuid=uuid, db=db, connector=connector)


@router.get("/{uuid}/{sample}", responses={200: {"model": TimeSeriesSample, "description": "A sample time series"}})
async def get_time_series_sample(uuid: UUID, sample: int, db: Session = Depends(get_db), connector: TimescaleDBConnectorPool = Depends(get_connector)) -> TimeSeriesSample:
    """Returns time series sample from file"""
    return TimeSeriesController.query_time_series_sample(uuid=uuid, sample=sample, db=db, connector=connector)


@router.get("/{uuid}/{sample}/{dimension}", responses={200: {"model": TimeSeriesSample, "description": "A sample time series dimension."}})
async def get_time_series_sample_dimension(uuid: UUID, sample: int, dimension: int, db: Session = Depends(get_db), connector: TimescaleDBConnectorPool = Depends(get_connector)) -> TimeSeries:
    """Returns time series sample dimension from file"""
    return TimeSeriesController.query_time_series_sample_dimension(uuid=uuid, sample=sample, dimension=dimension, db=db, connector=connector)
