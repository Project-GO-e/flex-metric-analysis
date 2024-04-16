

from pathlib import Path
from sys import exit
from typing import Dict, List, NamedTuple

import numpy as np
import pandas as pd
from dataclass_binder import Binder
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.baselines_dao import BaselineDao
from db.flex_devices_dao import FlexDevicesDao
from experiment.experiment_description import DeviceType
from flex_metric_config import Config


class FlexAssetProfiles(NamedTuple):
    ev: List[float]
    hp: Dict[str,List[float]]


class FlexMetrics():

    def __init__(self, config_file: Path, db_file: Path) -> None:
        if not db_file.exists():
            print("Database file is missing. Cannot run the flex metrics tool.\nExiting...")
            exit(1)
        else:
            self.engine = create_engine(f"sqlite:///{db_file}", echo=False)
        try:
            self.conf: Config = Binder(Config).parse_toml(config_file)
        except ValueError as e:
            print("Configuration invalid. " + str(e) +"\nExiting...")
            exit(1)
        except FileNotFoundError:
            print(f"Configuration file '{config_file}' not found." + "\nExiting...")
            exit(1)
        if not self.conf.is_valid():
            print("Configuration invalid. Exiting...")
            exit(1)

    def fetch_flex_metrics(self) -> FlexAssetProfiles:
        with Session(self.engine) as session:
            dao = FlexDevicesDao(session)
            ev_fm = dao.get_flex_metrics(DeviceType.EV, self.conf.congestion_start, self.conf.congestion_duration, self.conf.ev.pc4, self.conf.ev.typical_day)
            hp_fm : Dict[str, List[float]] = {}
            for hp in self.conf.hp.house_type:
                hp_fm[hp.name] = dao.get_flex_metrics(DeviceType.HP, self.conf.congestion_start, self.conf.congestion_duration, hp.name, self.conf.hp.typical_day)
        return FlexAssetProfiles(ev_fm, hp_fm)
    
    def fetch_baselines(self) -> pd.DataFrame:
        with Session(self.engine) as session:
            baselines: pd.DataFrame = pd.DataFrame(index=range(0,96))
            dao = BaselineDao(session)
            baselines['ev'] = dao.get_baseline_mean(DeviceType.EV, self.conf.ev.typical_day, self.conf.ev.pc4).values * self.conf.ev.amount
            baselines['hp'] = 96 * [0]
            for hp in self.conf.hp.house_type:
                baselines['hp'] += dao.get_baseline_mean(DeviceType.HP, self.conf.hp.typical_day, hp.name).values * hp.amount
            baselines['pv'] = np.array(dao.get_baseline_mean(DeviceType.PV, self.conf.pv.typical_day, 'pv')) * self.conf.pv.peak_power_W
            baselines['sjv'] = 96 * [0]
            for sjv in self.conf.non_flexible_load.sjv:
                # TODO: the baseline seems to be in kW. Change database content to W.
                baselines['sjv'] += np.array(dao.get_baseline_mean(DeviceType.SJV, self.conf.non_flexible_load.typical_day, sjv.name)) * sjv.amount * 1000
        return baselines.round(1)

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

            non_flex_profiles = self.fetch_baselines()
            pv_baseline = np.array(non_flex_profiles.pv) * self.conf.pv.peak_power_W
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
        
        res = {}
        res["baseline"] = np.array(self.conf.baseline_total_W)
        res["flex_ev"] = ev_flex
        res["flex_hp"] = hp_flex
        print("Baseline Power: " + str(np.array(self.conf.baseline_total_W)))
        if self.conf.all_baselines_available():
            print("Flexible load: " + str(ev_flex + hp_flex))
            print("Power after application of flex: " + str(np.array(self.conf.baseline_total_W) - ev_flex - hp_flex))
            res["flex_total"] = ev_flex + hp_flex
        else:
            print("Baseline Power: " + str(np.array(self.conf.baseline_total_W)))
            print("Flexible load: " + str(ev_flex + hp_flex))
            print("Power after application of flex: " + str(np.array(self.conf.baseline_total_W) - ev_flex - hp_flex))
            res["flex_total"] = ev_flex + hp_flex / (ev_baseline + hp_baseline_total + pv_baseline + sjv_baseline) * np.array(self.conf.baseline_total_W)
        
        pd.DataFrame(res).round(2).to_excel("out.xlsx")
        return res["flex_total"]