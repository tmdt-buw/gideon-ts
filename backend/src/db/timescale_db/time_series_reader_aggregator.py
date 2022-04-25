from src.db.timescale_db.tsdb_connector_pool import TimescaleDBConnectorPool
from src.models.models.project import Project, ProjectDB
from src.models.models.time_series import TimeSeries, TimeSeriesProject, TimeSeriesSample


def query_time_series_sample_agg(project: ProjectDB, sample: int, connector: TimescaleDBConnectorPool, max_samples: int) -> TimeSeriesSample:
    data = []
    cursor = connector.get_conn().cursor()
    sample_idx = sample - 1
    data_points = project.sampleLength * project.dimensions * project.samples
    coeff = data_points / (max_samples / 100)
    time_delta = project.sampleTime / project.sampleLength
    interval = coeff * time_delta
    if interval == 0:
        interval = project.sampleTime / (data_points / max_samples)
    for dimension in range(project.dimensions):
        if sample == 0:
            where = f""" "timeseries_id" = {dimension} """
        else:
            where = f""" "timeseries_id" = {dimension} and "sample_id" = {sample_idx} """
        cursor.execute(f"""
                        SELECT time_bucket('{interval} seconds', ts) as data,
                                    avg(value),
                                    max(value),
                                    min(value)
                                FROM "{project.id}"
                                WHERE {where}
                                GROUP BY "sample_id",data
                                ORDER BY "sample_id", data
                           ;""")
        data.append(cursor.fetchall())
    cursor.close()
    return TimeSeriesSample(id=0, sample=[(TimeSeries(id=idx + 1,
                                                      data_min=list(map(lambda x: x[3], d)),
                                                      data_max=list(map(lambda x: x[2] - x[3], d)),
                                                      data=list(map(lambda x: x[1], d)),
                                                      timestamps=list(map(lambda x: str(x[0]), d))))
                                          for idx, d in enumerate(data)])


def query_time_series_agg(project: Project, connector: TimescaleDBConnectorPool) -> TimeSeriesProject:
    """
    Queries the TimescaleDB to create TimeSeriesProject Object
    """
    cursor = connector.get_conn().cursor()
    cursor.execute(f"""
                        SELECT json_agg(
                                json_build_object(
                                    'id', series,
                                    'data', data,
                                    'data_min', data_min,
                                    'data_max', data_max,
                                    'timestamps', timestamps
                                )
                        )
                        FROM (
                            SELECT timeseries_id + 1 as series, array_agg(EXTRACT(EPOCH FROM timestamp)::float * 1000 ORDER BY timestamp) as timestamps, array_agg(avg_value ORDER BY timestamp) as data, array_agg(max_value ORDER BY timestamp) as data_max, array_agg(min_value ORDER BY timestamp) as data_min
                            FROM "aggregated_{project.id}"
                            GROUP BY timeseries_id
                            ORDER BY timeseries_id
                        ) as agg   
                    """)
    data = cursor.fetchall()[0][0]
    cursor.close()
    res = TimeSeriesProject(samples=[TimeSeriesSample(id=0, sample=data)])
    return res


def query_time_series_sample_dimension_agg(project: ProjectDB, sample: int, dimension: int, connector: TimescaleDBConnectorPool, max_samples) -> TimeSeries:
    cursor = connector.get_conn().cursor()
    sample_idx = sample - 1
    dimension_index = dimension - 1
    interval = round(project.sampleTime / (project.sampleLength / max_samples), 0)
    if sample == 0:
        where = f""" "timeseries_id" = {dimension_index} """
    else:
        where = f""" "timeseries_id" = {dimension_index} and "sample_id" = {sample_idx} """
    cursor.execute(f"""
                        SELECT EXTRACT(EPOCH FROM time_bucket('{interval} seconds', ts))::float * 1000 as data,
                                    avg(value),
                                    max(value),
                                    min(value)
                                FROM "{project.id}"
                                WHERE {where}
                                GROUP BY "sample_id",data
                                ORDER BY "sample_id", data
                           ;""")
    data = cursor.fetchall()
    cursor.close()
    return TimeSeries(id=dimension,
                      data_min=list(map(lambda x: x[3], data)),
                      data_max=list(map(lambda x: x[2] - x[3], data)),
                      data=list(map(lambda x: x[1], data)),
                      timestamps=list(map(lambda x: x[0], data)))
