
from __future__ import annotations

import re
from datetime import datetime, timedelta
from enum import Enum

from dateutil import parser


class DeviceType(Enum):
    EV = 1
    HEAT_PUMP = 2
    
    @classmethod
    def from_string(cls, device_type: str) -> DeviceType:
        return cls[device_type.upper()]


class ExperimentDescription():

    v1_regex ="pc4\d{4}_flexwindowduration\d*_congestionstart[^_]*_congestionduration\d*$"
    v2_regex = "pc4\d{4}_flexwindowstart\d{4}-\d{2}-\d{2}T\d{4}_flexwindowduration\d*_congestionstart[^_]*_congestionduration\d*$"
    #E.g., pc41077_flexwindowstart2020-06-03T0100_flexwindowduration96_congestionstart2020-06-03T0700_congestionduration4

    @staticmethod
    def validate_name(exp_name: str) -> bool:
        v1_pattern = re.fullmatch(ExperimentDescription.v1_regex, exp_name)
        v2_pattern = re.fullmatch(ExperimentDescription.v2_regex, exp_name)
        return v1_pattern or v2_pattern


    def __init__(self, expirement_name: str, device_type: DeviceType) -> None:
        if not ExperimentDescription.validate_name(expirement_name):
            raise AssertionError(f"Invalid experiment (file) name '{expirement_name}'")
        self.name = expirement_name
        self.device_type = device_type
        self.parse_experiment_name(expirement_name)


    def parse_experiment_name(self, experiment_name: str):
        self.area: str = re.findall("pc4\d{4}", experiment_name)[0].removeprefix('pc4')
        self.flexwindow_duration: int = int(re.findall("flexwindowduration\d*", experiment_name)[0].removeprefix("flexwindowduration"))
        self.congestion_start: datetime = parser.parse(re.findall("congestionstart\d{4}-\d{2}-\d{2}T\d{4}", experiment_name)[0].removeprefix("congestionstart"))
        self.congestion_duration = int(re.findall("congestionduration\d*", experiment_name)[0].removeprefix("congestionduration"))
        if re.fullmatch(ExperimentDescription.v1_regex, experiment_name):
            self.flexwindow_start = self.congestion_start - timedelta(hours=6)
        elif re.fullmatch(ExperimentDescription.v2_regex, experiment_name):
            self.flexwindow_start: datetime = parser.parse(re.findall("flexwindowstart\d{4}-\d{2}-\d{2}T\d{4}", experiment_name)[0].removeprefix("flexwindowstart"))


    def get_area(self) -> str:
        return self.area


    def get_flexwindow_duration(self) -> datetime:
        return self.flexwindow_duration


    def get_congestion_start(self) -> datetime:
        return self.congestion_start


    def get_congestion_duration(self) -> int:
        return self.congestion_duration
    
    
    def get_device_type(self) -> DeviceType:
        return self.device_type
