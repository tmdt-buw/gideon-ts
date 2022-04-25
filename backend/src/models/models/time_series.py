from typing import List, Optional

from pydantic import BaseModel


class TimeSeries(BaseModel):
    """ TimeSeries - a model defined in OpenAPI

        id: The id of this TimeSeries [Optional].
        data: The data of this TimeSeries [Optional].
        timestamps: The timestamps of this TimeSeries [Optional].
    """
    id: Optional[int] = None
    data: Optional[List[float]] = None
    data_max: Optional[List[float]] = None
    data_min: Optional[List[float]] = None
    timestamps: Optional[List[float]] = None

    class Config:
        orm_mode = True


class TimeSeriesSample(BaseModel):
    """ TimeSeriesSample - a time series sample containing one or more time series
        id: The id of this TimeSeriesSample [Optional].
        sample: The sample of this TimeSeriesSample [Optional].
        sample_agg : The aggregated sample of this TimeSeriesSample [Optional].
    """
    id: Optional[int] = None
    sample: Optional[List[TimeSeries]] = None

    class Config:
        orm_mode = True


class TimeSeriesProject(BaseModel):
    """ TimeSeriesProject - a time series project
        samples: The samples of this TimeSeriesProject [Optional].
    """
    samples: Optional[List[TimeSeriesSample]] = None

    class Config:
        orm_mode = True
