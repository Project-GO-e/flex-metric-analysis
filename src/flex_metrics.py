

from datetime import date, datetime, timedelta
from pathlib import Path
from sys import exit
from typing import Dict, List, NamedTuple

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.baselines_dao import BaselineDao
from db.flex_devices_dao import FlexDevicesDao
from experiment.experiment_description import DeviceType
from flex_metric_config import Config
from flex_metrics_results import DeviceResults, Results


class FlexMetricProfiles(NamedTuple):
    ev: Dict[str, List[float]]
    hp: Dict[str, List[float]]
    hhp: Dict[str, List[float]]


class FlexMetrics():

    def __init__(self, config: Config, db_file: Path) -> None:
        if not db_file.exists():
            print("Database file is missing. Cannot run the flex metrics tool.\nExiting...")
            exit(1)
        else:
            self.engine = create_engine(f"sqlite:///{db_file}", echo=False)
        self.conf = config

    def fetch_flex_metrics(self) -> FlexMetricProfiles:
        with Session(self.engine) as session:
            dao = FlexDevicesDao(session)
            ev_fm: Dict[str, List[float]] = {}
            hp_fm: Dict[str, List[float]] = {}
            hhp_fm: Dict[str, List[float]] = {}
            if self.conf.ev:
                for e in self.conf.ev:
                    ev_fm[e.pc4] = dao.get_flex_metrics(DeviceType.EV, self.conf.congestion_start, self.conf.congestion_duration, e.pc4, e.typical_day)
            if self.conf.hp:
                for hp in self.conf.hp.house_type:
                    hp_fm[hp.name] = dao.get_flex_metrics(DeviceType.HP, self.conf.congestion_start, self.conf.congestion_duration, hp.name, self.conf.hp.typical_day)
            if self.conf.hhp:
                for hhp in self.conf.hhp.house_type:
                    hhp_fm[hhp.name] = self.conf.congestion_duration * [1]
        return FlexMetricProfiles(ev_fm, hp_fm, hhp_fm)
    
    def fetch_baselines(self) -> pd.DataFrame:
        with Session(self.engine) as session:
            #TODO: get rid of hardcode length
            baselines: pd.DataFrame = pd.DataFrame(index=range(0,96))
            dao = BaselineDao(session)
            if self.conf.ev:
                for e in self.conf.ev:
                    # TODO: this is wrong! The baselines are accidentially stored as DataFrame in de database therefore we can now multiply the array!
                    baselines[f'ev-{e.pc4}'] = dao.get_baseline_mean(DeviceType.EV, e.typical_day, e.pc4).values * e.amount
            if self.conf.hp:
                for hp in self.conf.hp.house_type:
                    baselines['hp-' + hp.name] = dao.get_baseline_mean(DeviceType.HP, self.conf.hp.typical_day, hp.name).values * hp.amount
            if self.conf.hhp:
                for hhp in self.conf.hhp.house_type:
                    baselines['hhp-' + hhp.name] = dao.get_baseline_mean(DeviceType.HHP, self.conf.hhp.typical_day, hhp.name).values * hhp.amount
            if self.conf.pv:
                b = dao.get_baseline_mean(DeviceType.PV, self.conf.pv.typical_day, self.conf.pv.profile_type).values
                baselines['pv']= b * self.conf.pv.peak_power_W
            if self.conf.non_flexible_load:
                #TODO: get rid of hardcode length
                baselines['sjv'] = 96 * [0]
                for sjv in self.conf.non_flexible_load.sjv:
                    baselines['sjv'] += np.array(dao.get_baseline_mean(DeviceType.SJV, self.conf.non_flexible_load.typical_day, sjv.name)) * sjv.amount
        return baselines
    

    def determine_flex_power(self) -> Results:
        flex_metrics = self.fetch_flex_metrics()
        cong_start_idx = int((datetime.combine(date(2020,1,1), self.conf.congestion_start) - datetime(2020,1,1)) / timedelta(minutes=15))
        baselines_db = self.fetch_baselines()[cong_start_idx:cong_start_idx + self.conf.congestion_duration].reset_index()
        device_results: List[DeviceResults] = []
        
        if self.conf.ev:
            ev_baselines = pd.DataFrame(index=pd.RangeIndex(self.conf.congestion_duration))
            ev_flex_profiles = pd.DataFrame(index=pd.RangeIndex(self.conf.congestion_duration))
            for e in self.conf.ev:
                #TODO: array from baseline_total_W should be dataframe
                ev_baselines[e.pc4] = np.array(e.baseline_total_W) if e.baseline_total_W else baselines_db[f'ev-{e.pc4}']
                ev_flex_profiles[e.pc4] = np.array(flex_metrics.ev[e.pc4]) * ev_baselines[e.pc4]
            device_results.append(DeviceResults(DeviceType.EV, ev_baselines, ev_flex_profiles))
        
        if self.conf.pv:
            pv_baselines = pd.DataFrame(index=pd.RangeIndex(self.conf.congestion_duration))
            pv_baselines['pv'] = baselines_db['pv']
            device_results.append(DeviceResults(DeviceType.PV, pv_baselines))

        if self.conf.non_flexible_load:
            non_flex_baselines = pd.DataFrame(index=pd.RangeIndex(self.conf.congestion_duration))
            non_flex_baselines['non_flex'] = baselines_db['sjv']
            device_results.append(DeviceResults(DeviceType.SJV, non_flex_baselines))

        if self.conf.hp:
            hp_baselines = pd.DataFrame(index=pd.RangeIndex(self.conf.congestion_duration))
            hp_flex_profiles = pd.DataFrame(index=pd.RangeIndex(self.conf.congestion_duration))
            for hp in self.conf.hp.house_type:
                #TODO: array from baseline_total_W should be dataframe
                hp_baselines[hp.name] = np.array(hp.baseline_total_W) if hp.baseline_total_W  else baselines_db['hp-' + hp.name]
                hp_flex_profiles[hp.name] = np.array(flex_metrics.hp[hp.name]) * hp_baselines[hp.name]
            device_results.append(DeviceResults(DeviceType.HP, hp_baselines, hp_flex_profiles))
        
        if self.conf.hhp:
            hhp_baselines = pd.DataFrame(index=pd.RangeIndex(self.conf.congestion_duration))
            hhp_flex_profiles = pd.DataFrame(index=pd.RangeIndex(self.conf.congestion_duration))
            for hhp in self.conf.hhp.house_type:
                #TODO: array from baseline_total_W should be dataframe
                hhp_baselines[hhp.name] = np.array(hhp.baseline_total_W) if hhp.baseline_total_W else baselines_db['hhp-' + hhp.name]
                hhp_flex_profiles[hhp.name] = np.array(flex_metrics.hhp[hhp.name]) * hhp_baselines[hhp.name]
            device_results.append(DeviceResults(DeviceType.HHP, hhp_baselines, hhp_flex_profiles))
        
        return Results(cong_start=self.conf.congestion_start, cong_duration=self.conf.congestion_duration, results=device_results)