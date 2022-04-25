from enum import Enum
from typing import Optional, List, Dict

from pydantic import BaseModel

from src.models.models.label import LabelClass


class PredictionAlgorithm(Enum):
    DBSCAN = 'dbscan'


class PredictionRequest(BaseModel):
    algorithm: Optional[PredictionAlgorithm]
    params: Optional[dict]


class PredictionWindow(BaseModel):
    start: Optional[float]
    end: Optional[float]
    labelClass: Optional[LabelClass]


class SamplePrediction(BaseModel):
    sample: Optional[int]
    prediction: Optional[List[PredictionWindow]] = []


class Prediction(BaseModel):
    """
    Prediction Object
    """
    model: Optional[PredictionAlgorithm] = None
    params: Optional[Dict] = None
    sample_predictions: Optional[List[SamplePrediction]] = []
