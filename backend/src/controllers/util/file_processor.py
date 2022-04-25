import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from src.models.models.project import CreateProject
from src.models.schemas import Project


class FileProcessor(ABC):

    def __init__(self, file: Path, project: CreateProject):
        self.file = file
        self.values = dict()
        self.project = project

    @abstractmethod
    def get_data_from_file(self) -> Project:
        pass

    def process(self) -> Project:
        project_obj = self.get_data_from_file()
        return project_obj


class JsonFileProcessor(FileProcessor):
    def get_data_from_file(self) -> Project:
        f = open(self.file)
        file = json.load(f)
        first_sample = next(iter(file[0]))
        sample_length = len(file[0][first_sample])
        samples = len(file)
        # -1 because we do not count the time dimension
        dimensions = len(file[0]) - 1
        for sample_idx, sample in enumerate(file):
            self.values[sample_idx] = {}
            for dimension_idx, dimension in enumerate(filter(lambda x: x != 'time', list(sample.keys()))):
                self.values[sample_idx][dimension_idx] = []
                for ts_idx, value in enumerate(sample[dimension]):
                    self.values[sample_idx][dimension_idx].append(
                        (datetime.fromisoformat(sample["time"][ts_idx]), sample_idx, dimension_idx, value))
        sample_time = datetime.fromisoformat(file[-1]["time"][-1]) - datetime.fromisoformat(file[-1]["time"][0])
        return Project(name=self.project.name, samples=samples, dimensions=dimensions, hasTimestamps=True, sampleLength=sample_length, sampleTime=sample_time.total_seconds())
