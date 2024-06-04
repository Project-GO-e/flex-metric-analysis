
import datetime
from pathlib import Path
from typing import List
from experiment.device_type import DeviceType
from flex_metrics_results import Results


class DirectoryResultWriter():
    base_dir: Path = Path("results")

    def __init__(self, results: Results, reduce_group: List[DeviceType]) -> None:
        if not DirectoryResultWriter.base_dir.exists():
            DirectoryResultWriter.base_dir.mkdir()
        self.reduce_group = reduce_group
        self.results = results

    def write(self) -> None:
        results = self.results.flex_profiles()
        for device_type in self.reduce_group:
            columns_to_reduce = results.filter(regex="flex_" + str(device_type).lower() + "_")
            if len(columns_to_reduce.columns) > 0:
                results.drop(list(columns_to_reduce), axis=1, inplace=True)
                results["flex_" + str(device_type).lower()] = columns_to_reduce.sum(axis=1)
        results['baseline'] = self.results.baselines().sum(axis=1)
        res_file_name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        results.round(1).to_csv(DirectoryResultWriter.base_dir / (res_file_name + '.csv'), sep=';')