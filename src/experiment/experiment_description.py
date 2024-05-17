from dataclasses import dataclass
from enum import Enum
import re

from datetime import datetime, timedelta
from dateutil import parser

from experiment.device_type import DeviceType


class DataSource(Enum):
    GO_E=0
    ELAAD_ALL=1
    ELAAD_AGG=2


@dataclass(init=False)
class ExperimentDescription():
    name: str
    group: str
    typical_day: str
    device_type: DeviceType
    flexwindow_duration: int
    congestion_start: datetime
    congestion_duration: int
    __data_source: DataSource

    __ev_regex_v1 =r"pc4\d{4}_flexwindowduration\d*_congestionstart[^_]*_congestionduration\d*$"
    __ev_regex_v2 = r"pc4\d{4}_flexwindowstart\d{4}-\d{2}-\d{2}T\d{4}_flexwindowduration\d*_congestionstart[^_]*_congestionduration\d*$"
    __ev_regex_elaad = r".*-\d{1,2}-\d{4}-\d{1,2}-\d-\d{1,2}(_\d{1,2})?-(none|st-\d{1,2}-\d{4}-\d{4})-\d*-(week|wknd)"
    __hp_regex = r".*_flexwindowstart\d{4}-\d{2}-\d{2}T\d{4}_flexwindowduration\d*_congestionstart[^_]*_congestionduration\d*$"

    @staticmethod
    def validate_name(exp_name: str) -> bool:
        v1_match = bool(re.fullmatch(ExperimentDescription.__ev_regex_v1, exp_name))
        v2_match = bool(re.fullmatch(ExperimentDescription.__ev_regex_v2, exp_name))
        hp_match = bool(re.fullmatch(ExperimentDescription.__hp_regex, exp_name))
        elaad_match = bool(re.fullmatch(ExperimentDescription.__ev_regex_elaad, exp_name))
        return v1_match or v2_match or hp_match or elaad_match

    def __init__(self, experiment_name: str, device_type: DeviceType) -> None:
        if not ExperimentDescription.validate_name(experiment_name):
            raise AssertionError(f"Invalid experiment (file) name '{experiment_name}'")
        self.name = experiment_name
        self.device_type = device_type
        if re.fullmatch(ExperimentDescription.__ev_regex_elaad, experiment_name):
            self.flexwindow_duration = None
            self.flexwindow_start = None
            # public-med-50-2030-11-2-17_25-st-4-1600-1700-20-week.csv
            self.congestion_start = datetime.strptime(experiment_name.split('-')[9], "%H%M")
            cong_end = datetime.strptime(experiment_name.split('-')[10], "%H%M")
            # TODO: get rid of hardcoded 15 minutes
            self.congestion_duration = int((cong_end - self.congestion_start) / timedelta(minutes=15))
            self.group = re.match(r"^\w+-\w+", experiment_name).group() + f"-{experiment_name.split('-')[3]}"
            # TODO: how to differentiate for other Elaad data?
            self.__data_source = DataSource.ELAAD_AGG
        else:
            self.__data_source = DataSource.GO_E
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
        if self.device_type == DeviceType.EV and self.__data_source == DataSource.GO_E:
            return "workday" if self.congestion_start.weekday() < 5 else "weekendday"
        elif self.device_type == DeviceType.EV and self.__data_source == DataSource.ELAAD_AGG:
            return "weekend" if self.name.endswith("wknd") else "workday"
        elif self.device_type == DeviceType.HP:
            return self.congestion_start.strftime('%B').lower()
        else:
            return ""

    def get_flex_file_name(self) -> str:
        # dt_fmt = "%Y-%m%dT%H%M"
        # if self.__data_source == DataSource.GO_E and self.device_type == DeviceType.EV:
        #     return f"pc4{self.group}_flexwindowstart{self.flexwindow_start.strftime(dt_fmt)}_flexwindowduration{self.flexwindow_start}_congestionstart{self.congestion_start.strftime(dt_fmt)}_congestionduration{self.congestion_duration}"        
        # elif self.__data_source == DataSource.GO_E and self.device_type == DeviceType.HP:
        #     return f"flex_profiles+{self.group}+start{28}+dur{self.congestion_duration}month{self.flexwindow_start.month}"
        # elif self.__data_source == DataSource.ELAAD_AGG:
        return self.name

    def get_baseline_file_name(self) -> str:
        dt_fmt = "%Y-%m-%dT%H%M"
        if self.__data_source == DataSource.GO_E and self.device_type == DeviceType.EV:
            return f"pc4{self.group}_flexwindowstart{self.flexwindow_start.strftime(dt_fmt)}_flexwindowduration{self.flexwindow_duration}_congestionstart{self.congestion_start.strftime(dt_fmt)}_congestionduration{self.congestion_duration}"        
        elif self.__data_source == DataSource.GO_E and self.device_type == DeviceType.HP:
            return f"baselines+{self.group}"
        elif self.__data_source is DataSource.ELAAD_AGG:
            return re.sub(r'st-\d{1,2}-\d{4}-\d{4}', 'none', self.name)