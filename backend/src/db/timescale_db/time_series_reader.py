from typing import List, Union

from src.config.settings import get_settings
from src.db.timescale_db.tsdb_connector_pool import TimescaleDBConnectorPool
from src.models.models.project import ProjectDB,Project
from src.models.models.time_series import TimeSeries, TimeSeriesProject, TimeSeriesSample


def query_time_series_sample(project: Union[Project,ProjectDB], sample: int, connector: TimescaleDBConnectorPool) -> dict:
    """
    Queries a sample for a project.
    """
    cursor = connector.get_conn().cursor()
    sample_idx = sample - 1
    cursor.execute(f"""
                    SELECT json_agg(
                        json_build_object(
                            'id', id,
                            'data', data,
                            'timestamps', timestamps
                        )
                    )
                    FROM (
                        SELECT timeseries_id + 1 as id, array_agg(value ORDER BY ts) as data, array_agg(EXTRACT(EPOCH FROM ts)::float * 1000 ORDER BY ts) as timestamps
                        FROM "{project.id}"
                        WHERE sample_id = {sample_idx} 
                        GROUP BY timeseries_id
                        ORDER BY timeseries_id
                    ) as agg           
                    """)
    data = cursor.fetchall()[0][0]
    cursor.close()
    return {
        'id': sample,
        'sample': data
    }


def query_time_series_sample_dimension(project: ProjectDB, sample: int, dimension: int, connector: TimescaleDBConnectorPool) -> TimeSeries:
    """
    Queries the timescale database for a single dimension of a timeseries
    """
    cursor = connector.get_conn().cursor()
    sample_idx = sample - 1
    dimension_index = dimension - 1
    if sample == 0:
        where = f""" WHERE timeseries_id = {dimension_index} """
    else:
        where = f""" WHERE timeseries_id = {dimension_index} AND sample_id = {sample_idx} """
    cursor.execute(f"""
                    SELECT value, EXTRACT(EPOCH FROM ts)::float * 1000
                    FROM "{project.id}"
                    {where}
                    ORDER BY ts 
                    """)
    data = cursor.fetchall()
    return TimeSeries(id=dimension + 1,
                      data=[x[0] for x in data] if project.hasTimestamps else list(data),
                      timestamps=[x[1] for x in data] if project.hasTimestamps else list(range(len(data[0]))))


def query_time_series_dimension(project: ProjectDB, dimension: int, connector: TimescaleDBConnectorPool) -> TimeSeries:
    """
    Queries the timescale database for a single dimension of a timeseries
    """
    return query_time_series_sample_dimension(project, 0, dimension, connector)


def query_time_series_samples(project: ProjectDB, connector: TimescaleDBConnectorPool) -> List[dict]:
    n_values = project.samples * project.sampleLength * project.dimensions
    modifier = str(project.id) + "_lttb" if n_values > get_settings().MAX_DATA_POINTS else str(project.id)
    data = []
    cursor = connector.get_conn().cursor()
    cursor.execute(f"""
                        SELECT json_agg(
                            json_build_object(
                                'id', sample,
                                'sample', sample_data
                            )
                        )
                        FROM(
                            SELECT sample, json_agg(
                                    json_build_object(
                                        'id', series,
                                        'data', data,
                                        'timestamps', timestamps
                                    )
                            ) as sample_data
                            FROM (
                                SELECT sample_id + 1 as sample, timeseries_id + 1 as series, array_agg(value ORDER BY ts) as data, array_agg(EXTRACT(EPOCH FROM ts)::float * 1000 ORDER BY ts) as timestamps
                                FROM "{modifier}"
                                GROUP BY sample_id, timeseries_id
                                ORDER BY sample_id, timeseries_id
                            ) as agg
                            GROUP BY sample
                            ORDER BY sample
                        ) as samples
                        """)
    data.extend(cursor.fetchall()[0][0])
    cursor.close()
    return data


def query_time_series(project: ProjectDB, connector: TimescaleDBConnectorPool) -> TimeSeriesProject:
    """
    Queries the TimescaleDB to create TimeSeriesProject Object
    """
    cursor = connector.get_conn().cursor()
    cursor.execute(f"""
                        SELECT json_agg(
                                json_build_object(
                                    'id', series,
                                    'data', data,
                                    'timestamps', timestamps
                                )
                        )
                        FROM (
                            SELECT timeseries_id + 1 as series, array_agg(value ORDER BY ts) as data, array_agg(EXTRACT(EPOCH FROM ts)::float * 1000 ORDER BY ts) as timestamps
                            FROM "{project.id}"
                            GROUP BY timeseries_id
                            ORDER BY timeseries_id
                        ) as agg   
                    """)
    data = cursor.fetchall()[0][0]
    cursor.close()
    return TimeSeriesProject(samples=[TimeSeriesSample(id=0, sample=data)])
