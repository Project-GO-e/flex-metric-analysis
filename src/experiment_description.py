
from __future__ import annotations

import re
from datetime import datetime
from enum import Enum

from dateutil import parser


class DeviceType(Enum):
    EV = 1
    HEAT_PUMP = 2
    
    @classmethod
    def from_string(cls, device_type: str) -> DeviceType:
        return cls[device_type.upper()]


class ExperimentDescription():

    @staticmethod
    def __validate_name(exp_name: str):
        if not re.fullmatch("pc\d{5}_flexwindowduration\d*_congestionstart[^_]*_congestionduration\d*$", exp_name):
            raise AssertionError(f"Invalid experiment (file) name '{exp_name}'")


    def __init__(self, expirement_name: str, device_type: DeviceType) -> None:
        ExperimentDescription.__validate_name(expirement_name)
        self.name = expirement_name
        self.device_type = device_type


    def get_area(self) -> str:
        return self.name.split("_")[0].removeprefix("pc")


    def get_flexwindow_duration(self) -> datetime:
        return int(self.name.split("_")[1].removeprefix("flexwindowduration"))


    def get_congestion_start(self) -> datetime:
        return parser.parse(self.name.split("_")[2].removeprefix("congestionstart"))


    def get_congestion_duration(self) -> int:
        return int(self.name.split("_")[3].removeprefix("congestionduration"))
    
    
    def get_device_type(self) -> DeviceType:
        return self.device_type
