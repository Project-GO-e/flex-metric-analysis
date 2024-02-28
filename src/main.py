from pathlib import Path
from typing import Dict, List, NamedTuple

import numpy as np
from dataclass_binder import Binder
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.flex_metrics_dao import FlexMetricsDao
from db.non_flex_devices_dao import NonFlexDevicesDao
from experiment_description import DeviceType
from flex_metric_config import Config

DB_FILE="flex-metrics.db"
CONFIG_FILE="config.toml"


class FlexAssetProfiles(NamedTuple):
    ev: List[float]
    hp: Dict[str,List[float]]


class NonFlexAssetProfiles(NamedTuple):
    pv: List[float]
    sjv: Dict[str,List[float]]


class FlexPower():

    def __init__(self, config_file: Path) -> None:
        self.conf: Config = Binder(Config).parse_toml(config_file)
        if not self.conf.is_valid():
            print("Exiting...")
            exit(1)
        self.engine = create_engine(f"sqlite:///{DB_FILE}", echo=False)


    def fetch_flex_metrics(self) -> FlexAssetProfiles:
        with Session(self.engine) as session:
            dao = FlexMetricsDao(session)
            ev_fm = dao.get_flex_metrics(DeviceType.EV, self.conf.congestion_start, self.conf.congestion_duration, self.conf.ev.pc4, self.conf.ev.typical_day)
            hp_fm : Dict[str, List[float]] = {}
            for hp in self.conf.hp.house_type:
                hp_fm[hp.name] = dao.get_flex_metrics(DeviceType.HP, self.conf.congestion_start, self.conf.congestion_duration, hp.name, self.conf.hp.typical_day)
        return FlexAssetProfiles(ev_fm, hp_fm)

    
    def fetch_flex_asset_baselines(self) -> FlexAssetProfiles:
        with Session(self.engine) as session:
            dao = FlexMetricsDao(session)
            ev = dao.get_baseline(DeviceType.EV, self.conf.congestion_start, self.conf.congestion_duration, self.conf.ev.pc4, self.conf.ev.typical_day)
            hp_baselines : Dict[str, List[float]] = {}
            for hp in self.conf.hp.house_type:
                hp_baselines[hp.name] = dao.get_baseline(DeviceType.HP, self.conf.congestion_start, self.conf.congestion_duration, hp.name, self.conf.hp.typical_day)
        return FlexAssetProfiles(ev, hp_baselines)


    def fetch_non_flex_asset_baselines(self) -> NonFlexAssetProfiles:
        with Session(self.engine) as session:
            dao = NonFlexDevicesDao(session)
            pv = dao.get_baseline('PV', self.conf.congestion_start, self.conf.congestion_duration, self.conf.pv.typical_day)
            sjv_baselines : Dict[str, List[float]] = {}
            for sjv in self.conf.non_flexible_load.sjv:
                sjv_baselines[sjv.name] = dao.get_baseline(sjv.name, self.conf.congestion_start, self.conf.congestion_duration, self.conf.non_flexible_load.typical_day)
        return NonFlexAssetProfiles(pv, sjv_baselines)


    def determine_flex_power(self) -> np.array:
        flex_metrics = self.fetch_flex_metrics()
        if self.conf.all_baselines_available():
            ev_baseline = np.array(self.conf.ev.baseline_total_W)
            hp_baselines = {hp.name:np.array(hp.baseline_total_W) for hp in self.conf.hp.house_type}
        else:
            profiles = self.fetch_flex_asset_baselines()
            ev_baseline = np.array(profiles.ev) * self.conf.ev.amount
            hp_baselines = {}
            for hp_type in self.conf.hp.house_type:
                hp_baselines[hp_type.name] = np.array(profiles.hp[hp_type.name]) * hp_type.amount

            non_flex_profiles = self.fetch_non_flex_asset_baselines()
            # TODO: the pv profile seems to be in kW. Change database content to W.
            pv_baseline = np.array(non_flex_profiles.pv) * self.conf.pv.peak_power_W / 1000
            sjv_baseline = 0
            for sjv_type in self.conf.non_flexible_load.sjv:
                # TODO: the baseline seems to be in kW. Change database content to W.
                sjv_baseline += np.array(non_flex_profiles.sjv[sjv_type.name]) * sjv_type.amount * 1000
        

        ev_flex = np.array(flex_metrics.ev) * ev_baseline
        hp_flex = np.zeros(len(flex_metrics.ev))
        hp_baseline_total = np.zeros(len(flex_metrics.ev))
        for hp in hp_baselines:
            hp_flex += np.array(flex_metrics.hp[hp]) * hp_baselines[hp]
            hp_baseline_total += hp_baselines[hp]
        
        print("EV flex" + str(ev_flex))
        print("HP flex" + str(hp_flex))

        if self.conf.all_baselines_available():
            print("Baseline Power: " + str(np.array(self.conf.baseline_total_W)))
            print("Flexible load: " + str(ev_flex + hp_flex))
            print("Power after application of flex: " + str(np.array(self.conf.baseline_total_W) - ev_flex - hp_flex))
            return ev_flex + hp_flex
        else:
            print("Baseline Power: " + str(self.conf.baseline_total_W))
            print("Flexible load: " + str(ev_flex + hp_flex))
            print("Power after application of flex: " + str(np.array(self.conf.baseline_total_W) - ev_flex - hp_flex))
            return ev_flex + hp_flex / (ev_baseline + hp_baseline_total + pv_baseline + sjv_baseline) * np.array(self.conf.baseline_total_W)
            

def test_toml():
    config_file = Path("config.toml")
    config = Binder(Config).parse_toml(config_file)
    print(config.congestion_start)


def write_toml_template():
    with open("config.toml.template", "w") as out:
        for line in Binder(Config).format_toml():
            print(line, file=out)


if __name__ == "__main__":
    float_formatter = "{:.0f}".format
    np.set_printoptions(formatter={'float_kind':float_formatter})
    FlexPower(Path(CONFIG_FILE)).determine_flex_power()
    
    
    # write_toml_template()
    # test_toml()
    print("Done. Bye!")