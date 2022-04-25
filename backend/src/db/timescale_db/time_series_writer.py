import logging
import math
from datetime import datetime
from itertools import chain
from typing import Dict
from uuid import UUID

import lttb
import numpy as np
from fastapi import HTTPException
from joblib import Parallel, delayed
from pgcopy import CopyManager
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT, ISOLATION_LEVEL_DEFAULT

from src.controllers.cache_controller import cache
from .tsdb_connector_pool import TimescaleDBConnectorPool
from ...config.settings import get_settings
from ...controllers.util.time_util import current_time
from ...models.models.project import ProjectDB


class TimeSeriesWriter:
    columns = ['ts', 'sample_id', 'timeseries_id', 'value']

    def __init__(self, connector: TimescaleDBConnectorPool, project: ProjectDB = None):
        self.project = project
        self.connector = connector
        if project is not None:
            self.n_values = project.samples * project.sampleLength * project.dimensions
            self.no_lttb = self.n_values > get_settings().MAX_DATA_POINTS
        self.progress = 0

    def write(self, values: Dict):
        if self.project is None:
            raise HTTPException(status_code=400, detail="Invalid project.")
        logger = logging.getLogger("gideon")
        logger.debug(f"{current_time()} create tables")
        self.__create_tables()
        self.progress = 5
        logger.debug(f"{current_time()} lttb subsample")
        self.__lttb_subsample(values)
        self.progress = 50
        logger.debug(f"{current_time()} insert vales")
        self.__insert_data(values)
        self.progress = 80
        logger.debug(f"{current_time()} create aggregated view")
        self.__create_aggregated_view()
        self.progress = 95
        logger.debug(f"{current_time()} update cache")
        if self.no_lttb:
            cache.db_to_cache(project=self.project, connector=self.connector)
        logger.debug(f"{current_time()} all done")

    def remove(self, project: UUID):
        connection = self.connector.get_conn()
        cursor = connection.cursor()
        cursor.execute(f'DROP TABLE IF EXISTS "{project}" CASCADE;')
        cursor.execute(f'DROP TABLE IF EXISTS "{project}_lttb" CASCADE;')
        connection.commit()
        cursor.close()

    def __create_tables(self):
        """
        Adds the given project to the database
        """
        queries = [f"""DROP TABLE IF EXISTS "{self.project.id}";
                       CREATE TABLE "{self.project.id}"(
                            ts {"TIMESTAMP NOT NULL" if self.project.hasTimestamps else "INTEGER"},
                            sample_id INTEGER ,
                            timeseries_id INTEGER,
                            value DOUBLE PRECISION
                       );
                       CREATE INDEX ON "{self.project.id}" (sample_id, ts DESC);
                       CREATE INDEX ON "{self.project.id}" (timeseries_id, ts DESC);
                       SELECT create_hypertable('{self.project.id}', 'ts');
                    """]
        if self.no_lttb:
            queries.append(f"""                 
                       DROP TABLE IF EXISTS "{self.project.id}_lttb";
                       CREATE TABLE "{self.project.id}_lttb"(
                            ts {"TIMESTAMP NOT NULL" if self.project.hasTimestamps else "INTEGER"},
                            sample_id INTEGER ,
                            timeseries_id INTEGER,
                            value DOUBLE PRECISION
                       );
                       CREATE INDEX ON "{self.project.id}_lttb" (sample_id, ts DESC);
                       CREATE INDEX ON "{self.project.id}_lttb" (timeseries_id, ts DESC);
                       """)
        connection = self.connector.get_conn()
        cursor = connection.cursor()
        [cursor.execute(query) for query in queries]
        connection.commit()
        cursor.close()

    def __lttb_subsample(self, values: Dict):
        """
        Sample time series using lttb sampling
        """

        def downsample_func(sample, dimension):
            sample_results = []
            for key, values in dimension.items():
                timeseries = []
                timeseries.append(list(map(lambda dimension_values: dimension_values[0].timestamp(), values)))
                timeseries.append(list(map(lambda dimension_values: dimension_values[3], values)))
                timeseries = lttb.downsample(data=np.array(timeseries).T, n_out=math.ceil(factor * len(values)))
                sample_results.append([[ts, sample, key, value] for ts, value in zip(timeseries.T[0], timeseries.T[1])])
            return list(chain.from_iterable(sample_results))

        self.n_values = self.project.samples * self.project.sampleLength * self.project.dimensions
        connection = self.connector.get_conn()
        if self.n_values > get_settings().MAX_DATA_POINTS:
            factor = get_settings().MAX_DATA_POINTS / self.n_values
            export = list(chain.from_iterable(Parallel(n_jobs=-1)(delayed(downsample_func)(sample, dimension) for sample, dimension in values.items())))
            mgr = CopyManager(connection, str(self.project.id) + "_lttb", self.columns)
            export = list(map(lambda x: [datetime.fromtimestamp(x[0]), x[1], x[2], x[3]], export))
            mgr.threading_copy(export)
            connection.commit()
            cache.cache_project_init(export, self.project)
            self.no_lttb = False

    def __insert_data(self, values: Dict):
        """
        Inserts data into previously create time series table
        """
        values = list(chain.from_iterable([value for sample_id, dimension in values.items() for key, value in dimension.items()]))
        connection = self.connector.get_conn()
        cursor = connection.cursor()
        mgr = CopyManager(connection, str(self.project.id), self.columns)
        mgr.threading_copy(values)
        connection.commit()
        cursor.close()

    def __create_aggregated_view(self):
        """
        Creates materialized aggregated view for time series
        """
        connection = self.connector.get_conn()
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = connection.cursor()
        cursor.execute(
            f"""CREATE MATERIALIZED VIEW "aggregated_{self.project.id}" WITH (timescaledb.continuous, timescaledb.create_group_indexes, timescaledb.materialized_only = true)
                    AS SELECT 
                        sample_id, 
                        timeseries_id,
                        time_bucket('{self.__calc_agg_interval()} seconds', ts) as timestamp,
                        avg(value) as avg_value,
                        (max(value) - min(value)) as max_value,
                        min(value) as min_value
                        FROM "{self.project.id}"
                        GROUP BY sample_id, timeseries_id, timestamp;        
            """
        )
        connection.commit()
        connection.set_isolation_level(ISOLATION_LEVEL_DEFAULT)
        cursor.close()

    def __calc_agg_interval(self):
        """
        Calculates aggregation interval
        """
        data_points = self.project.sampleLength * self.project.dimensions * self.project.samples
        coeff = data_points / (get_settings().MAX_SAMPLES / 100)
        time_delta = self.project.sampleTime / self.project.sampleLength
        return coeff * time_delta
