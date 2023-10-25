
from dateutil import parser
from datetime import datetime
import re

class ExperimentDescription():

    @staticmethod
    def __validate_name(exp_name: str):
        if not re.fullmatch("pc\d{5}_flexwindowduration\d*_congestionstart[^_]*_congestionduration\d*$", exp_name):
            raise AssertionError(f"Invalid experiment (file) name '{exp_name}'")


    def __init__(self, expirement_name: str) -> None:
        ExperimentDescription.__validate_name(expirement_name)
        self.name = expirement_name


    def get_congestion_zipcode(self) -> str:
        return self.name.split("_")[0].removeprefix("pc")


    def get_flexwindow_duration(self) -> datetime:
        return int(self.name.split("_")[1].removeprefix("flexwindowduration"))


    def get_congestion_start(self) -> datetime:
        return parser.parse(self.name.split("_")[2].removeprefix("congestionstart"))


    def get_congestion_duration(self) -> int:
        return int(self.name.split("_")[3].removeprefix("congestionduration"))
    
    
