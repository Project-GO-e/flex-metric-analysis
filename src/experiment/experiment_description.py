from dataclasses import dataclass
import re

from datetime import datetime, timedelta
from dateutil import parser

from experiment.device_type import DeviceType

@dataclass(init=False)
class ExperimentDescription():
    name: str
    group: str 
    typical_day: str
    device_type: DeviceType
    flexwindow_duration: int
    congestion_start: datetime
    congestion_duration: int
    
    __ev_regex_v1 ="pc4\d{4}_flexwindowduration\d*_congestionstart[^_]*_congestionduration\d*$"
    __ev_regex_v2 = "pc4\d{4}_flexwindowstart\d{4}-\d{2}-\d{2}T\d{4}_flexwindowduration\d*_congestionstart[^_]*_congestionduration\d*$"
    __hp_regex = ".*_flexwindowstart\d{4}-\d{2}-\d{2}T\d{4}_flexwindowduration\d*_congestionstart[^_]*_congestionduration\d*$"

    @staticmethod
    def validate_name(exp_name: str) -> bool:
        v1_match = bool(re.fullmatch(ExperimentDescription.__ev_regex_v1, exp_name))
        v2_match = bool(re.fullmatch(ExperimentDescription.__ev_regex_v2, exp_name))
        hp_match = bool(re.fullmatch(ExperimentDescription.__hp_regex, exp_name))
        return v1_match or v2_match or hp_match

    def __init__(self, experiment_name: str, device_type: DeviceType) -> None:
        if not ExperimentDescription.validate_name(experiment_name):
            raise AssertionError(f"Invalid experiment (file) name '{experiment_name}'")
        self.name = experiment_name
        self.device_type = device_type
        self.flexwindow_duration = int(re.findall("flexwindowduration\d*", experiment_name)[0].removeprefix("flexwindowduration"))
        self.congestion_start = parser.parse(re.findall("congestionstart\d{4}-\d{2}-\d{2}T\d{4}", experiment_name)[0].removeprefix("congestionstart"))
        self.congestion_duration = int(re.findall("congestionduration\d*", experiment_name)[0].removeprefix("congestionduration"))
        if re.fullmatch(ExperimentDescription.__ev_regex_v1, experiment_name):
            self.group = re.findall("pc4\d{4}", experiment_name)[0].removeprefix('pc4')
            self.flexwindow_start = self.congestion_start - timedelta(hours=6)
        elif re.fullmatch(ExperimentDescription.__ev_regex_v2, experiment_name):
            self.group = re.findall("pc4\d{4}", experiment_name)[0].removeprefix('pc4')
            self.flexwindow_start: datetime = parser.parse(re.findall("flexwindowstart\d{4}-\d{2}-\d{2}T\d{4}", experiment_name)[0].removeprefix("flexwindowstart"))
        elif re.fullmatch(ExperimentDescription.__hp_regex, experiment_name):
            self.group = re.findall(".*_flexwindowstart", experiment_name)[0].removesuffix('_flexwindowstart')
        self.typical_day = self.determine_typical_day()

    def determine_typical_day(self) -> str:
        match self.device_type:
            case DeviceType.EV:
                return "workday" if self.congestion_start.weekday() < 5 else "weekendday"
            case DeviceType.HP:
                return self.congestion_start.strftime('%B').lower()
        return ""

    def get_flex_file_name(self) -> str:
        dt_fmt = "%Y-%m%dT%H%M"
        if self.device_type is DeviceType.EV:
            return f"pc4{self.group}_flexwindowstart{self.flexwindow_start.strftime(dt_fmt)}_flexwindowduration{self.flexwindow_start}_congestionstart{self.congestion_start.strftime(dt_fmt)}_congestionduration{self.congestion_duration}"        
        elif self.device_type is DeviceType.HP:
            return f"flex_profiles+{self.group}+start{28}+dur{self.congestion_duration}month{self.flexwindow_start.month}"

    def get_baseline_file_name(self) -> str:
        dt_fmt = "%Y-%m-%dT%H%M"
        if self.device_type is DeviceType.EV:
            return f"pc4{self.group}_flexwindowstart{self.flexwindow_start.strftime(dt_fmt)}_flexwindowduration{self.flexwindow_duration}_congestionstart{self.congestion_start.strftime(dt_fmt)}_congestionduration{self.congestion_duration}"        
        elif self.device_type is DeviceType.HP:
            return f"baselines+{self.group}"
