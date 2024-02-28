
from __future__ import annotations

import re
from datetime import datetime, timedelta
from enum import Enum

from dateutil import parser


class DeviceType(Enum):
    EV = 1
    HP = 2
    
    @classmethod
    def from_string(cls, device_type: str) -> DeviceType:
        return cls[device_type.upper()]

    def __str__(self) -> str:
        return self.name

class ExperimentDescription():

    ev_regex_v1 ="pc4\d{4}_flexwindowduration\d*_congestionstart[^_]*_congestionduration\d*$"
    ev_regex_v2 = "pc4\d{4}_flexwindowstart\d{4}-\d{2}-\d{2}T\d{4}_flexwindowduration\d*_congestionstart[^_]*_congestionduration\d*$"
    hp_regex = ".*_flexwindowstart\d{4}-\d{2}-\d{2}T\d{4}_flexwindowduration\d*_congestionstart[^_]*_congestionduration\d*$"

    @staticmethod
    def validate_name(exp_name: str) -> bool:
        v1_match = re.fullmatch(ExperimentDescription.ev_regex_v1, exp_name)
        v2_match = re.fullmatch(ExperimentDescription.ev_regex_v2, exp_name)
        hp_match = re.fullmatch(ExperimentDescription.hp_regex, exp_name)
        return v1_match or v2_match or hp_match


    def determine_typical_day(self):
        match self.device_type:
            case DeviceType.EV:
                return "workday" if self.congestion_start.weekday() < 5 else "weekendday"
            case DeviceType.HP:
                return self.congestion_start.strftime('%B')
            case other:
                return ""
    

    def __init__(self, expirement_name: str, device_type: DeviceType) -> None:
        if not ExperimentDescription.validate_name(expirement_name):
            raise AssertionError(f"Invalid experiment (file) name '{expirement_name}'")
        self.name = expirement_name
        self.device_type = device_type
        self.parse_experiment_name(expirement_name)
        self.typical_day = self.determine_typical_day()


    def parse_experiment_name(self, experiment_name: str):
        self.flexwindow_duration: int = int(re.findall("flexwindowduration\d*", experiment_name)[0].removeprefix("flexwindowduration"))
        self.congestion_start: datetime = parser.parse(re.findall("congestionstart\d{4}-\d{2}-\d{2}T\d{4}", experiment_name)[0].removeprefix("congestionstart"))
        self.congestion_duration = int(re.findall("congestionduration\d*", experiment_name)[0].removeprefix("congestionduration"))
        if re.fullmatch(ExperimentDescription.ev_regex_v1, experiment_name):
            self.group: str = re.findall("pc4\d{4}", experiment_name)[0].removeprefix('pc4')
            self.flexwindow_start = self.congestion_start - timedelta(hours=6)
        elif re.fullmatch(ExperimentDescription.ev_regex_v2, experiment_name):
            self.group: str = re.findall("pc4\d{4}", experiment_name)[0].removeprefix('pc4')
            self.flexwindow_start: datetime = parser.parse(re.findall("flexwindowstart\d{4}-\d{2}-\d{2}T\d{4}", experiment_name)[0].removeprefix("flexwindowstart"))
        elif re.fullmatch(ExperimentDescription.hp_regex, experiment_name):
            self.group : str = re.findall(".*_flexwindowstart", experiment_name)[0].removesuffix('_flexwindowstart')


    def get_group(self) -> str:
        return self.group


    def get_flexwindow_duration(self) -> datetime:
        return self.flexwindow_duration


    def get_congestion_start(self) -> datetime:
        return self.congestion_start


    def get_congestion_duration(self) -> int:
        return self.congestion_duration
    
    
    def get_device_type(self) -> DeviceType:
        return self.device_type
