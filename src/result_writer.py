
from typing import List
from experiment.device_type import DeviceType
from flex_metrics_results import Results


class DirectoryResultWriter():

    def __init__(self, results: Results, reduce_group: List[DeviceType]) -> None:
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

        results.round(1).to_csv('out.csv', sep=';')