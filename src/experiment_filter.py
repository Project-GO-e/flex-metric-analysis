from __future__ import annotations

from datetime import datetime
from typing import List

from experiment_description import ExperimentDescription


class ExperimentFilter():

    def __init__(self) -> None:
        self.area_ids = []
        self.flex_window_durations = []
        self.cong_starts = []
        self.cong_durations = []
    
    def with_area(self, area_id: str ) -> ExperimentFilter:
        self.area_ids.append(area_id)
        return self

    def with_areas(self, aread_ids: List[str] ) -> ExperimentFilter:
        if type(aread_ids) is not list:
            raise AssertionError("Only use this method with list argument")
        self.area_ids.extend(aread_ids)
        return self

    def with_flex_window_duration(self, flex_window_duration: int ) -> ExperimentFilter:
        self.flex_window_durations.append(flex_window_duration)
        return self

    def with_flex_window_durations(self, flex_window_durations: List[int] ) -> ExperimentFilter:
        self.flex_window_durations.extend(flex_window_durations)
        return self

    def with_cong_start(self, cong_start: datetime ) -> ExperimentFilter:
        self.cong_starts.append(cong_start)
        return self

    def with_cong_starts(self, cong_starts: List[str] ) -> ExperimentFilter:
        self.cong_starts.extend(cong_starts)
        return self

    def with_cong_duration(self, cong_duration: int )-> ExperimentFilter:
        self.cong_durations.append(cong_duration)
        return self

    def with_cong_durations(self, cong_duration: List[str] ) -> ExperimentFilter:
        self.cong_durations.extend(cong_duration)
        return self
    
    def passFilter(self, description: ExperimentDescription) -> bool:
        return (description.get_area() in self.area_ids or len(self.area_ids) == 0) and \
                (description.get_flexwindow_duration() in self.flex_window_durations or len(self.flex_window_durations) == 0 ) and \
                (description.get_congestion_start() in self.cong_starts or len(self.cong_starts) == 0 ) and \
                (description.get_congestion_duration() in self.cong_durations or len(self.cong_durations) ==0)