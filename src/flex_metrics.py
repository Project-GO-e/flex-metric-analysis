

from datetime import date, datetime, timedelta
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

    def fetch_flex_metrics(self) -> FlexAssetProfiles:
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
        return FlexAssetProfiles(ev_fm, hp_fm, hhp_fm)
    
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
                baselines['pv'] = np.array(dao.get_baseline_mean(DeviceType.PV, self.conf.pv.typical_day, 'pv')) * self.conf.pv.peak_power_W
            if self.conf.non_flexible_load:
                #TODO: get rid of hardcode length
                baselines['sjv'] = 96 * [0]
                for sjv in self.conf.non_flexible_load.sjv:
                    baselines['sjv'] += np.array(dao.get_baseline_mean(DeviceType.SJV, self.conf.non_flexible_load.typical_day, sjv.name)) * sjv.amount
        return baselines
    

    def determine_flex_power(self, reduce_to_device_type: bool) -> pd.DataFrame:
        flex_metrics = self.fetch_flex_metrics()
        cong_start_idx = int((datetime.combine(date(2020,1,1), self.conf.congestion_start) - datetime(2020,1,1)) / timedelta(minutes=15))
        baselines_db = self.fetch_baselines()[cong_start_idx:cong_start_idx + self.conf.congestion_duration]
        baselines = pd.DataFrame(index=pd.RangeIndex(self.conf.congestion_duration))
        results = pd.DataFrame(index=pd.RangeIndex(self.conf.congestion_duration))
        
        if self.conf.ev:
            for e in self.conf.ev:
                baselines[f'ev-{e.pc4}'] = np.array(e.baseline_total_W) if e.baseline_total_W else baselines_db[f'ev-{e.pc4}'].values
                results[f"flex_ev_{e.pc4}"] = np.array(flex_metrics.ev[e.pc4]) * baselines[f'ev-{e.pc4}']
        
        if self.conf.pv:
            baselines['pv'] = baselines_db['pv'].values

        if self.conf.non_flexible_load:
            baselines['sjv'] = baselines_db['sjv'].values

        if self.conf.hp:
            for hp in self.conf.hp.house_type:
                baselines[hp.name] = np.array(hp.baseline_total_W) if hp.baseline_total_W  else baselines_db['hp-' + hp.name].values
                results["flex_hp_" + hp.name] = np.array(flex_metrics.hp[hp.name]) * baselines[hp.name]
        
        if self.conf.hhp:
            for hhp in self.conf.hhp.house_type:
                baselines[hhp.name] = np.array(hhp.baseline_total_W) if hhp.baseline_total_W else baselines_db['hhp-' + hhp.name].values
                results["flex_hhp_" + hp.name] = np.array(flex_metrics.hhp[hhp.name]) * baselines[hhp.name]
        
        ev_baseline = results.filter(regex="flex_ev_")
        if reduce_to_device_type and len(ev_baseline.columns) > 0:
            results.drop(list(ev_baseline), axis=1, inplace=True)
            results["flex_ev"] = ev_baseline.sum(axis=1)

        hp_baseline = results.filter(regex="flex_hp_")
        if reduce_to_device_type and len(hp_baseline.columns) > 0:
            results.drop(list(hp_baseline), axis=1, inplace=True)
            results["flex_hp"] = hp_baseline.sum(axis=1)

        hhp_baseline = results.filter(regex="flex_hhp_")
        if reduce_to_device_type and len(hhp_baseline.columns) > 0:
            results.drop(list(hhp_baseline), axis=1, inplace=True)
            results["flex_hhp"] = hhp_baseline.sum(axis=1)

        results['baseline'] = baselines.sum(axis=1)
        return results