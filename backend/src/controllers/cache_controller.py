import os
import pickle
import shutil
from pathlib import Path

from src.controllers.util.time_util import time_string_to_js_timestamp
from src.db.timescale_db.time_series_reader import query_time_series_samples
from src.db.timescale_db.tsdb_connector_pool import TimescaleDBConnectorPool
from src.models.models.project import ProjectDB


class CacheController:
    src_path = Path(__file__).parents[1].absolute()

    def _get_cachepath(self) -> Path:
        cachepath = self.src_path.joinpath("cache")
        if not cachepath.exists():
            cachepath.mkdir()
        return cachepath

    def read_from_cache(self, uuid):
        if self._get_cachepath().joinpath(f'{uuid}.pkl').is_file():
            with open(self._get_cachepath().joinpath(f'{uuid}.pkl'), 'rb') as pickle_file:
                return pickle.load(pickle_file)
        else:
            return False

    def db_to_cache(self, project: ProjectDB, connector: TimescaleDBConnectorPool):
        samples = query_time_series_samples(project, connector)
        with open(self._get_cachepath().joinpath(f'{project.id}.pkl'), 'wb') as pickle_file:
            pickle.dump(samples, pickle_file)
        return samples

    def delete_cache(self, uuid):
        try:
            os.remove(self._get_cachepath().joinpath(f'{uuid}.pkl'))
        except:
            print("cache could not be removed")

    def clear_cache(self):
        shutil.rmtree(self._get_cachepath())

    # Hier in der remove funktion des Project controllers aufrufen und die file im Ordner löschen

    def cache_project_init(self, data, project):
        sample_list = []
        if not (self._get_cachepath().joinpath(f'{project.id}.pkl').is_file()):
            for sample in range(project.samples):
                sample_list.append({"id": sample + 1, 'sample': [{'id': dimension_idx + 1,
                                                                  'data': [],
                                                                  'timestamps': []} for dimension_idx in
                                                                 range(project.dimensions)]})
            for el in data:
                sample_list[el[1]]["sample"][el[2]]["data"].append(el[3])
                sample_list[el[1]]["sample"][el[2]]["timestamps"].append(time_string_to_js_timestamp(el[0]))
            with open(self._get_cachepath().joinpath(f'{project.id}.pkl'), 'wb') as pickle_file:
                pickle.dump(sample_list, pickle_file)


cache = CacheController()
