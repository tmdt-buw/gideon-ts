import ast
import uuid
from dataclasses import dataclass
from typing import Any, Union, Optional
from uuid import UUID

import numpy as np
import pandas as pd
from dtwalign import dtw as dtw_func
from pydantic import BaseModel
from tslearn.metrics import dtw as dtw_measure

from src.controllers.cache_controller import cache
from src.controllers.label_class_controller import labelClass
from src.controllers.label_controller import label
from src.db.sqlalchemy.database import SessionLocal
from src.db.sqlalchemy.database import engine
from src.db.timescale_db.time_series_reader import query_time_series_sample
from src.db.timescale_db.tsdb_connector_pool import TimescaleDBConnectorPool
from src.models.models.label import Label
from src.models.models.prediction import PredictionWindow
from src.models.models.project import Project


@dataclass
class ProcessingLabel():
    sample_id: int
    start: int
    end: int
    label_name: str
    label_id: UUID


class LabelInDict(BaseModel):
    id: Optional[UUID]
    data: Any


class DTW_Controller:

    def __init__(self, project: Project):
        self.session = SessionLocal()
        self.samples = cache.read_from_cache(project.id)
        self.project = project

    @staticmethod
    def convert_db_column_string_to_tuple(result: Union[pd.Series, pd.DataFrame]):
        return [ast.literal_eval(el.replace("{", "").replace("}", "")) for el in result.tolist()]

    @staticmethod
    def match_label_to_timestamps_and_values(timestamps: list[int], data: list[float],
                                             label: Union[ProcessingLabel, PredictionWindow]) -> LabelInDict:
        start_idx = timestamps.index(label.start)
        end_idx = timestamps.index(label.end)
        label_timeseries = np.array(data[start_idx:end_idx])
        if type(label) is ProcessingLabel:
            return LabelInDict(id=label.label_id, data=label_timeseries)
        return LabelInDict(data=label_timeseries)

    def __transform_label(self, label: Label):
        label_classes = labelClass.get_all(db=self.session, project_id=self.project.id)
        for cl in label_classes:
            if label.label_class == cl.id:
                return ProcessingLabel(sample_id=label.sample, start=label.start, end=label.end, label_name=cl.name,
                                       label_id=label.id)
            else:
                return ValueError

    def __get_all_labels(self) -> list:
        """ Get all labels that were labeled"""
        all_project_labels = label.get_all(db=self.session, project_id=self.project.id, skip=0)
        label_list = [[el.sample, el.label_class, el.start, el.end, el.id] for el in all_project_labels]
        label_classes = labelClass.get_all(db=self.session, project_id=self.project.id)
        labels = list()
        for idx, l in enumerate(label_list):
            for cl in label_classes:
                if l[1] == cl.id:
                    labels.append(
                        ProcessingLabel(sample_id=l[0], start=l[2], end=l[3], label_name=cl.name, label_id=l[4]))
        return labels

    def align_all_labels(self) -> None:
        """ Updates all datasets for active learning"""

        labels = self.__get_all_labels()
        dtw_dict = {}
        references = {}
        aligned_labels = pd.DataFrame(columns=["data", "label_id", "dimension_idx", "label_name", "reference"])
        results = {}
        broken_labels = []

        # Create Dictionary with aligned numbers
        for label in labels:
            sample = next(filter(lambda x: x['id'] == label.sample_id, self.samples))

            # Add Entry for every label name/class in dict
            if label.label_name not in dtw_dict:
                dtw_dict[label.label_name] = {}

            # loop over sample and create timeseries for start and end of each label
            for dimension in sample["sample"]:
                if dimension['id'] not in dtw_dict[label.label_name]:
                    dtw_dict[label.label_name][dimension['id']] = []
                result = self.match_label_to_timestamps_and_values(timestamps=dimension["timestamps"],
                                                                   data=dimension["data"], label=label)
                dtw_dict[label.label_name][dimension["id"]].append(result)

        # Get The Longest Label for each Dimension and Label Class and declare them as reference label
        for label_name in dtw_dict.keys():
            references[label_name] = {}
            for dimension_id in dtw_dict[label_name].keys():
                references[label_name][dimension_id] = \
                    sorted(dtw_dict[label_name][dimension_id], key=lambda x: len(x.data), reverse=True)[0]

        # Align other labels with reference label
        for label_name in dtw_dict.keys():
            for dimension_id in dtw_dict[label_name]:
                for timeseries in filter(lambda ts: ts != references[label_name][dimension_id],
                                         dtw_dict[label_name][dimension_id]):
                    try:
                        res = dtw_func(x=timeseries.data, y=references[label_name][dimension_id].data,
                                       window_type="itakura")
                        warping_path = res.get_warping_path(target="query")
                        aligned_labels = aligned_labels.append(
                            {"data": timeseries.data[warping_path].tolist(), "dimension_idx": dimension_id,
                             "label_id": timeseries.id, "label_name": label_name, "reference": False},
                            ignore_index=True)
                    except ValueError:
                        print(
                            f"{timeseries.id} in dimension {dimension_id} for class {label_name} "
                            f"\n is not able to be matched with the reference")
                aligned_labels = aligned_labels.append(
                    {"data": references[label_name][dimension_id].data.tolist(), "dimension_idx": dimension_id,
                     "label_id": references[label_name][dimension_id].id, "label_name": label_name, "reference": True},
                    ignore_index=True)

        # Send Labels to Database
        aligned_labels.to_sql(name=f"{self.project.id}_aligned_labels", con=engine, if_exists='replace')

    def calculate_median_label(self):
        """ Get all aligned labels for all label names from the database and calculate the median label"""

        df = pd.read_sql(f""" SELECT * from "{self.project.id}_aligned_labels" """, con=engine)
        median_labels_df = pd.DataFrame(columns=["label_name", "dimension_idx", "data"])

        for label_name in set(df['label_name'].tolist()):
            for dimension_idx in set(df['dimension_idx'].tolist()):
                filtered_df = df[(df["dimension_idx"] == dimension_idx) & (df["label_name"] == label_name)]
                ts = self.convert_db_column_string_to_tuple(result=filtered_df['data'])
                array_ts = list(map(lambda x: np.array(x), ts))
                median = np.median(array_ts, axis=0).tolist()
                row = {"label_name": label_name, "dimension_idx": dimension_idx,
                       "data": median}
                median_labels_df = median_labels_df.append(row, ignore_index=True)

        median_labels_df.to_sql(name=f"{self.project.id}_median_labels", con=engine, if_exists='replace')

    def classify_label_for_new_sample(self, sample_id: int, window: PredictionWindow):
        """ Classify a potential label"""
        scores = []
        df = pd.read_sql(f""" SELECT * from "{self.project.id}_aligned_labels" """, con=engine)
        df["data"] = self.convert_db_column_string_to_tuple(df["data"])
        sample = query_time_series_sample(project=self.project, sample=sample_id, connector=TimescaleDBConnectorPool())
        for dimension in sample["sample"]:
            ts = self.match_label_to_timestamps_and_values(timestamps=dimension["timestamps"],
                                                           data=dimension["data"],
                                                           label=window)
            for label_id in set(df["label_id"].tolist()):
                dimension_median = df.loc[(df["label_id"] == label_id) & (
                        df["dimension_idx"] == dimension["id"]), "data"]
                scores.append((dtw_measure(dimension_median, ts.data), label_id))
        return min(scores, key=lambda x: x[0])[1]

    def update_label(self, label: Label):
        """ Update a previously existent label that was changed """
        sample = query_time_series_sample(project=self.project, sample=1,
                                          connector=TimescaleDBConnectorPool())
        df = pd.read_sql(f""" SELECT * from "{self.project.id}_aligned_labels" """, con=engine)
        for dimension in sample["sample"]:
            processing_label = self.__transform_label(label)
            matched_time_series = self.match_label_to_timestamps_and_values(timestamps=dimension["timestamps"],
                                                                            data=dimension["data"],
                                                                            label=processing_label)

            df["data"] = self.convert_db_column_string_to_tuple(df["data"])
            df.loc[(df["label_id"] == processing_label.label_id) & (
                    df["dimension_idx"] == dimension["id"]), "data"] = matched_time_series
        df.to_sql(name=f"{self.project.id}_aligned_labels", con=engine, if_exists='replace')
        self.calculate_median_label()

