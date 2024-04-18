

from datetime import date, datetime, timedelta
from functools import reduce
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

    def __init__(self, config: Config, db_file: Path) -> None:
        if not db_file.exists():
            print("Database file is missing. Cannot run the flex metrics tool.\nExiting...")
            exit(1)
        else:
            self.engine = create_engine(f"sqlite:///{db_file}", echo=False)
        self.conf = config

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
            for hp in self.conf.hp.house_type:
                baselines['hp-' + hp.name] = dao.get_baseline_mean(DeviceType.HP, self.conf.hp.typical_day, hp.name).values * hp.amount
            baselines['pv'] = np.array(dao.get_baseline_mean(DeviceType.PV, self.conf.pv.typical_day, 'pv')) * self.conf.pv.peak_power_W
            #TODO: get rid of hardcode length
            baselines['sjv'] = 96 * [0]
            for sjv in self.conf.non_flexible_load.sjv:
                baselines['sjv'] += np.array(dao.get_baseline_mean(DeviceType.SJV, self.conf.non_flexible_load.typical_day, sjv.name)) * sjv.amount
        return baselines.round(1)

    def determine_flex_power(self) -> np.array:
        flex_metrics = self.fetch_flex_metrics()
        if self.conf.all_baselines_available():
            ev_baseline = np.array(self.conf.ev.baseline_total_W)
            hp_baselines = {hp.name:np.array(hp.baseline_total_W) for hp in self.conf.hp.house_type}
        else:
            cong_start_idx = int((datetime.combine(date(2020,1,1), self.conf.congestion_start) - datetime(2020,1,1)) / timedelta(minutes=15))
            baseline_profiles = self.fetch_baselines()[cong_start_idx:cong_start_idx + self.conf.congestion_duration]
            ev_baseline = baseline_profiles['ev'].values
            hp_baselines: Dict[str: List[float]] = {}
            for hp in self.conf.hp.house_type:
                hp_baselines[hp.name] = baseline_profiles['hp-'+hp.name].values
            pv_baseline = baseline_profiles['pv'].values
            sjv_baseline = baseline_profiles['sjv'].values
            
        ev_flex = np.array(flex_metrics.ev) * ev_baseline
        hp_flex = np.zeros(len(flex_metrics.ev))
        hp_baseline_total = reduce(np.add, hp_baselines.values())
        for hp in hp_baselines:
            hp_flex += np.array(flex_metrics.hp[hp]) * hp_baselines[hp]
        res = {}
        if self.conf.baseline_total_W is None:
            baseline_total = ev_baseline + hp_baseline_total + pv_baseline + sjv_baseline
        
        res["baseline"] = np.array(baseline_total)
        res["flex_ev"] = ev_flex
        res["flex_hp"] = hp_flex
        print("Baseline Power: " + str(np.array(baseline_total)))
        if self.conf.all_baselines_available():
            print("Flexible load: " + str(ev_flex + hp_flex))
            print("Power after application of flex: " + str(np.array(baseline_total) - ev_flex - hp_flex))
            res["flex_total"] = ev_flex + hp_flex
        else:
            print("Baseline Power: " + str(np.array(baseline_total)))
            print("Flexible load: " + str(ev_flex + hp_flex))
            print("Power after application of flex: " + str(np.array(baseline_total) - ev_flex - hp_flex))
            res["flex_total"] = ev_flex + hp_flex / (ev_baseline + hp_baseline_total + pv_baseline + sjv_baseline) * np.array(baseline_total)
        
        pd.DataFrame(res).round(2).to_excel("out.xlsx")
        return res["flex_total"]