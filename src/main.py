from pathlib import Path
from typing import Dict, List, NamedTuple

import numpy as np
from dataclass_binder import Binder
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.flex_metrics_dao import FlexMetricsDao
from experiment_description import DeviceType
from flex_metric_config import Config

DB_FILE="ev-hp-flex-metrics.db"
CONFIG_FILE="config.toml"


class DatabaseProfiles(NamedTuple):
    ev: List[float]
    hp: Dict[str,List[float]]


class FlexPower():

    def __init__(self, config_file: Path) -> None:
        self.conf: Config = Binder(Config).parse_toml(config_file)
        if not self.conf.is_valid():
            print("Exiting...")
            exit(1)
        self.engine = create_engine(f"sqlite:///{DB_FILE}", echo=False)


    def fetch_flex_metrics(self) -> DatabaseProfiles:
        with Session(self.engine) as session:
            doa = FlexMetricsDao(session)
            ev_fm = doa.get_flex_metrics(DeviceType.EV, self.conf.congestion_start, self.conf.congestion_duration, self.conf.ev.pc4, self.conf.ev.typical_day)
            hp_fm : Dict[str, List[float]] = {}
            for hp in self.conf.hp.house_type:
                hp_fm[hp.name] = doa.get_flex_metrics(DeviceType.HP, self.conf.congestion_start, self.conf.congestion_duration, hp.name, self.conf.hp.typical_day)
        return DatabaseProfiles(ev_fm, hp_fm)

    
    def fetch_flex_asset_baselines(self) -> DatabaseProfiles:
        with Session(self.engine) as session:
            doa = FlexMetricsDao(session)
            ev = doa.get_baseline(DeviceType.EV, self.conf.congestion_start, self.conf.congestion_duration, self.conf.ev.pc4, self.conf.ev.typical_day)
            hp_baselines : Dict[str, List[float]] = {}
            for hp in self.conf.hp.house_type:
                hp_baselines[hp.name] = doa.get_baseline(DeviceType.HP, self.conf.congestion_start, self.conf.congestion_duration, hp.name, self.conf.hp.typical_day)
        return DatabaseProfiles(ev, hp_baselines)


    def determine_flex_power(self) -> np.array:
        flex_metrics = self.fetch_flex_metrics()
        if self.conf.all_baselines_available():
            ev_baseline = np.array(self.conf.ev.baseline_total)
            hp_baselines = {hp.name:np.array(hp.baseline_total) for hp in self.conf.hp.house_type}
        else:
            profiles = self.fetch_flex_asset_baselines()
            ev_baseline = np.array(profiles.ev) * self.conf.ev.amount
            hp_baselines = {}
            for hp_type in self.conf.hp.house_type:
                hp_baselines[hp_type.name] = np.array(profiles.hp[hp_type.name]) * hp_type.amount
        
        ev_flex = np.array(flex_metrics.ev) * ev_baseline
        hp_flex = 0
        for hp in hp_baselines:
            hp_flex += np.array(flex_metrics.hp[hp]) * hp_baselines[hp]
        
        print("EV flex" + str(ev_flex))
        print("HP flex" + str(hp_flex))
        print("Flex Power: " + str(ev_flex + hp_flex))
        return ev_flex + hp_flex
            


def test_toml():
    config_file = Path("config.toml")
    config = Binder(Config).parse_toml(config_file)
    print(config.congestion_start)


def write_toml_template():
    with open("config.toml.template", "w") as out:
        for line in Binder(Config).format_toml():
            print(line, file=out)

if __name__ == "__main__":

    FlexPower(Path(CONFIG_FILE)).determine_flex_power()

    # write_toml_template()
    # test_toml()
    print("Done. Bye!")