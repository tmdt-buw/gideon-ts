import time
from uuid import UUID

import numpy as np
import numpy.typing as npt
from fastapi import HTTPException
from sklearn.cluster import DBSCAN
from sqlalchemy.orm import Session
from tslearn.utils import to_sklearn_dataset

from src.controllers import label_class_controller, project_controller, dtw_controller
from src.controllers.cache_controller import cache
from src.db.timescale_db.tsdb_connector import TimescaleDBConnector
from src.models.models.label import Severity
from src.models.models.prediction import Prediction, PredictionWindow, SamplePrediction, PredictionRequest, \
    PredictionAlgorithm


def predict(project_uuid: UUID, prediction: PredictionRequest, db: Session,
            connector: TimescaleDBConnector) -> Prediction:
    x = time.time()
    samples = cache.read_from_cache(project_uuid)
    project = project_controller.project.get(db=db, uuid=project_uuid)
    if not samples:
        samples = cache.db_to_cache(project, connector)
    print(f"sample retrieval time {time.time() - x}")
    if prediction.algorithm == PredictionAlgorithm.DBSCAN:
        window = round(prediction.params['window'])
        x = time.time()
        windows = __split_into_windows(samples, window)
        print(f"window time {time.time() - x}")
        x = time.time()
        algorithm = DBSCAN(eps=prediction.params['eps'])
        predictions = __perform_prediction(windows, algorithm)
        label_classes = label_class_controller.labelClass.get_all(db=db, project_id=project_uuid)
        normal = next((normal for normal in label_classes if normal.severity == Severity.okay), None)
        error = next((err for err in label_classes if err.severity == Severity.error), None)
        result = Prediction(model=prediction.algorithm, params=prediction.params)
        for idx, sample in enumerate(samples):
            sample_pred = SamplePrediction(sample=sample['id'])
            result.sample_predictions.append(sample_pred)
            first_sample = sample['sample'][0]
            for pindx, prediction in enumerate(predictions):
                val = prediction[idx]
                if val == 0:
                    lbl_class = normal
                else:
                    lbl_class = error
                start = first_sample['timestamps'][pindx * window]
                try:
                    end = first_sample['timestamps'][pindx * window + window - 1]
                except IndexError:
                    end = first_sample['timestamps'][-1]
                pred = PredictionWindow(start=start, end=end, labelClass=lbl_class)
                label_pred = dtw_controller.DTW_Controller(project=project).classify_label_for_new_sample(window=pred, sample_id=sample["id"])
                pred.labelClass = label_pred
                sample_pred.prediction.append(pred)
        runtime = time.time() - x
        print(f"Prediction Runtime {runtime}")
        return result
    else:
        raise HTTPException(status_code=400, detail="Unsupported algorithm.")


def __split_into_windows(sample_list: list[dict], window_size: int) -> list[npt.ArrayLike]:
    """
    Returns a list of datasets, one for each sample window
    """
    sample_list_with_windows = []
    window_dict = {}
    window_datasets = []
    for tsSample in sample_list:
        data = list(map(lambda x: x['data'], tsSample['sample']))
        dimensions_chunked = [[np.array(el[i:i + window_size]) for i in range(0, len(el), window_size)] for el in data]
        sample_list_with_windows.append(dimensions_chunked)
        n_windows = len(dimensions_chunked[0])
    for window_idx in range(n_windows):
        window_dict[f"window_{window_idx}"] = {}
        for sample_idx, sample in enumerate(sample_list_with_windows):
            window_dict[f"window_{window_idx}"][f"sample_{sample_idx}"] = []
            for dimension in sample:
                window_dict[f"window_{window_idx}"][f"sample_{sample_idx}"].append(dimension[window_idx])
    for window in window_dict.keys():
        window_datasets.append(to_sklearn_dataset(list(map(lambda x: np.array(x), window_dict[window].values()))))

    return window_datasets


def __perform_prediction(windows: list[npt.ArrayLike], algorithm) -> list[list[int]]:
    result = []
    for idx, window in enumerate(windows):
        clustering = algorithm.fit(window)
        result.append(list(clustering.labels_))
    return result
