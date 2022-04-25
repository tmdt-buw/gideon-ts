from typing import List, Dict, Union
from uuid import UUID

from sqlalchemy.orm import Session

from src.config.settings import get_settings
from src.controllers import project_controller
from src.db.timescale_db.time_series_reader import query_time_series, query_time_series_sample, query_time_series_sample_dimension, query_time_series_samples
from src.db.timescale_db.time_series_reader_aggregator import query_time_series_agg, query_time_series_sample_agg, query_time_series_sample_dimension_agg
from src.db.timescale_db.tsdb_connector_pool import TimescaleDBConnectorPool
from src.models.models.time_series import TimeSeries, TimeSeriesProject, TimeSeriesSample


class TimeSeriesController:

    @staticmethod
    def query_time_series(uuid: UUID, db: Session, connector: TimescaleDBConnectorPool) -> TimeSeriesProject:
        """
        Queries the TimescaleDB to create TimeSeriesProject Object
        """
        project = project_controller.project.get_or_error(db=db, uuid=uuid)
        if (project.sampleLength * project.dimensions * project.samples) > get_settings().MAX_SAMPLES:
            return query_time_series_agg(project=project, connector=connector)
        return query_time_series(project=project, connector=connector)

    @staticmethod
    def query_time_series_samples(uuid: UUID, db: Session, connector: TimescaleDBConnectorPool) -> List[dict]:
        """
        Query all samples for a project
        """
        project = project_controller.project.get_or_error(db=db, uuid=uuid)
        return query_time_series_samples(project=project, connector=connector)

    @staticmethod
    def query_time_series_sample(uuid: UUID, sample: int, db: Session, connector: TimescaleDBConnectorPool) -> Union[Dict, TimeSeriesSample]:
        """
           Queries a sample for a project.
        """
        project = project_controller.project.get_or_error(db=db, uuid=uuid)
        if (project.sampleLength * project.dimensions) > get_settings().MAX_SAMPLES:
            return query_time_series_sample_agg(project=project, sample=sample, connector=connector, max_samples=get_settings().MAX_SAMPLES)
        return query_time_series_sample(project=project, sample=sample, connector=connector)

    @staticmethod
    def query_time_series_sample_dimension(uuid: UUID, sample: int, dimension: int, db: Session, connector: TimescaleDBConnectorPool) -> TimeSeries:
        """
        Queries the timescale database for a single dimension of a timeseries
        """
        project = project_controller.project.get_or_error(db=db, uuid=uuid)
        if project.sampleLength > get_settings().MAX_SAMPLES:
            query_time_series_sample_dimension_agg(project=project, sample=sample, dimension=dimension, connector=connector, max_samples=get_settings().MAX_SAMPLES)
        return query_time_series_sample_dimension(project=project, sample=sample, dimension=dimension, connector=connector)
