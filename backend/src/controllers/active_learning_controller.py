import sktime.datasets
from modAL.models import ActiveLearner
from modAL.uncertainty import uncertainty_sampling

from sqlalchemy.orm import Session

from src.models.models.project import Project
from src.db.timescale_db.tsdb_connector import TimescaleDBConnector
from src.db.sqlalchemy.database import SessionLocal
from src.controllers.label_controller import label
from src.controllers.label_class_controller import labelClass
from src.controllers.cache_controller import cache

from typing import Union
import numpy as np
import pandas as pd
from pandas import DataFrame

import uuid
from sktime.classification.distance_based import ProximityForest


class ActiveLearningController:
    # connector: TimescaleDBConnector, session: Session
    def __init__(self, project: Project, window_size):
        self.session = SessionLocal()
        self.samples = cache.read_from_cache(project.id)
        self.project = project
        self.window_size = window_size
        self.__generate_active_learner()
        self.labeled_y = None
        self.labeled_X = None

    def __create_active_learner(self) -> None:
        """ generates the active learning model """
        # Hier das Modell ohne Active learning testen
        # vorher noch die series zu sliding umbauen
        #
        ProximityForest()

    def __generate_active_learner(self) -> None:
        """
        Creates a dataset & active learner that is the basis for this modul
        """
        self.update_dataset()
        self.__create_active_learner()

    def __get_labels(self)-> list:
        """ Get all labels that were labeled"""
        all_project_labels = label.get_all(db=self.session, project_id=self.project.id, skip=0)
        label_list = [[el.sample, el.label_class, el.start, el.end] for el in all_project_labels]
        label_classes = labelClass.get_all(db=self.session, project_id=self.project.id)
        labels = label_list[:]
        for idx, l in enumerate(label_list):
            for cl in label_classes:
                if l[1] == cl.id:
                    labels[idx][1] = cl.name
                    if cl.name != "Normal":
                        labels[idx].append(0)
                    else:
                        labels[idx].append(1)
        return labels

    def update_dataset(self) -> None:
        """ updates all datasets for active learning"""
        df = None
        for idx, tsSample in enumerate(self.samples):
            data = list(map(lambda x: x['data'], tsSample['sample']))
            timestamps = list(map(lambda x: x['timestamps'], tsSample['sample']))
            sample_dimensions_chunked = [[np.array(el[i:i + self.window_size]) for i in range(0, len(el), self.window_size)] for
                                         el in data]
            sample_timestamps_chunked = [[np.array(el[i:i + self.window_size]) for i in range(0, len(el), self.window_size)] for
                                         el in timestamps]
            n_windows = len(sample_dimensions_chunked[0])
            single_window_df = DataFrame()
            for n in range(n_windows):
                combined_row = {}
                combined_row["sample"] = tsSample["id"]
                combined_row["sample"] = combined_row["sample"]
                # hier bei series 250 elemente gucken das es sliding windows gibt
                for i, (dimension, window_ts) in enumerate(zip(sample_dimensions_chunked, sample_timestamps_chunked)):
                    combined_row["ts-interval"] = [min(window_ts[n]), max(window_ts[n])]
                    combined_row[f"dimension {i + 1}"] = pd.Series(dimension[n])
                single_window_df = single_window_df.append(combined_row, ignore_index=True)
            if df is None:
                df = single_window_df
            else:
                df = df.append(single_window_df, ignore_index=True)
        df = df.reset_index(drop=True)
        df['targets'] = None
        df['labeled'] = False
        label_list = self.__get_labels()
        for el in label_list:
            df['targets'] = df.apply(lambda row: el[-1] if (
                    (row["ts-interval"][0] <= el[2] <= row["ts-interval"][1]) or (
                    row["ts-interval"][0] <= el[3] <= row["ts-interval"][1])
            ) else row['targets'], axis=1)
            df['labeled'] = df.apply(lambda row: True if (
                    (row["ts-interval"][0] <= el[2] <= row["ts-interval"][1]) or (
                    row["ts-interval"][0] <= el[3] <= row["ts-interval"][1])
            ) else row['labeled'], axis=1)
        self.complete_dataset = df
        labeled_dataset = df[df["labeled"] == True].reset_index(drop=True)
        X_test,y_test = sktime.datasets.load_UCR_UEA_dataset(name = "SpokenArabicDigits", return_X_y=True)
        self.labeled_X = labeled_dataset.drop(columns=["targets", "labeled", "ts-interval", "sample"], axis=1)
        self.labeled_X = X_test
        self.labeled_y = labeled_dataset["targets"]
        self.labeled_y = y_test

    def get_label_suggestions(self):
        """ Suggest new data points that are supposed to be labeled """
        unlabeled_df = self.complete_dataset[self.complete_dataset["labeled"] != True]
        X = unlabeled_df.drop(columns=["targets", "labeled", "ts-interval"], axis=1)
        return self.AL.query(X)


    def teach(self):
        """Adds new datapoints to the training of the predictor"""
        self.AL.teach(self.labeled_X, self.labeled_y)

    def predict(self, sample_id):
        """ Return predictions for samples"""
        # Hier sollte eine sample id reinkommen oder eine liste von denen
        unlabeled_df = self.complete_dataset[self.complete_dataset["labeled"] == True]
        X = unlabeled_df.drop(columns=["targets", "labeled", "ts-interval"], axis=1).reset_index(drop=True)
        return self.AL.predict(X)

# https://tslearn.readthedocs.io/en/stable/gen_modules/tslearn.utils.html#module-tslearn.utils

if __name__ == "__main__":
    project = Project(id=uuid.UUID("1f8f134e-877b-4313-8878-ef5dac721dc0").hex)
    active_leaner = ActiveLearningController(window_size=500, project=project)
    pass