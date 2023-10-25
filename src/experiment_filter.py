

from datetime import datetime
from typing import List

from experiment_description import ExperimentDescription


class ExperimentFilter():

    def __init__(self) -> None:
        self.zipcodes = []
        self.flex_window_durations = []
        self.cong_starts = []
        self.cong_durations = []
    
    def with_zipcode(self, zipcode: str ):
        self.zipcodes.append(zipcode)
        return self

    def with_zipcodes(self, zipcode: List[str] ):
        self.zipcodes.extend(zipcode)
        return self

    def with_flex_window_duration(self, flex_window_duration: int ):
        self.flex_window_durations.append(flex_window_duration)
        return self

    def with_flex_window_durations(self, flex_window_durations: List[int] ):
        self.flex_window_durations.extend(flex_window_durations)
        return self

    def with_cong_start(self, cong_start: datetime ):
        self.cong_starts.append(cong_start)
        return self

    def with_cong_starts(self, cong_starts: List[str] ):
        self.cong_starts.extend(cong_starts)
        return self

    def with_cong_duration(self, cong_duration: int ):
        self.cong_durations.append(cong_duration)
        return self

    def with_cong_durations(self, cong_duration: List[str] ):
        self.cong_durations.extend(cong_duration)
        return self
    
    def passFilter(self, description: ExperimentDescription) -> bool:
        return (description.get_congestion_zipcode() in self.zipcodes or len(self.zipcodes) == 0) and \
                (description.get_flexwindow_duration() in self.flex_window_durations or len(self.flex_window_durations) == 0 ) and \
                (description.get_congestion_start() in self.cong_starts or len(self.cong_starts) == 0 ) and \
                (description.get_congestion_duration() in self.cong_durations or len(self.cong_durations) ==0)