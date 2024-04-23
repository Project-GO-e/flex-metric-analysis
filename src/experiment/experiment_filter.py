from __future__ import annotations

from datetime import datetime
from typing import List

from .experiment_description import ExperimentDescription


class ExperimentFilter():

    def __init__(self) -> None:
        self.groups = []
        self.flex_window_durations = []
        self.cong_starts = []
        self.cong_durations = []
    
    def with_group(self, group: str ) -> ExperimentFilter:
        self.groups.append(group)
        return self

    def with_groups(self, groups: List[str] ) -> ExperimentFilter:
        if type(groups) is not list:
            raise AssertionError("Only use this method with list argument")
        self.groups.extend(groups)
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

    def with_cong_starts(self, cong_starts: List[datetime] ) -> ExperimentFilter:
        self.cong_starts.extend(cong_starts)
        return self

    def with_cong_duration(self, cong_duration: int )-> ExperimentFilter:
        self.cong_durations.append(cong_duration)
        return self

    def with_cong_durations(self, cong_duration: List[int] ) -> ExperimentFilter:
        self.cong_durations.extend(cong_duration)
        return self
    
    def pass_filter(self, description: ExperimentDescription) -> bool:
        return (description.group in self.groups or len(self.groups) == 0) and \
                (description.flexwindow_duration in self.flex_window_durations or len(self.flex_window_durations) == 0 ) and \
                (description.congestion_start in self.cong_starts or len(self.cong_starts) == 0 ) and \
                (description.congestion_duration in self.cong_durations or len(self.cong_durations) ==0)