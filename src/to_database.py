from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
import re
from typing import List

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.baselines_dao import BaselineDao
from db.flex_devices_dao import FlexDevicesDao
from db.models import Baseline, FlexMetric
from experiment.experiment_container import ExperimentContainer
from experiment.experiment_description import DeviceType, ExperimentDescription
from experiment.experiment_filter import ExperimentFilter
from experiment.experiment_loader import FileLoader
from util.conflex import (get_daily_pv_expectation_values,
                          get_daily_sjv_expectation_values, readGM)

BASE_PATH=Path('data')

EV_BASELINES=BASE_PATH / 'ev/baselines/'
EV_SHIFTED=BASE_PATH / 'ev/shifted/'

HP_BASELINES=BASE_PATH / 'hp/baselines/'
HP_SHIFTED=BASE_PATH / 'hp/shifted-12/'

HHP_BASELINES=BASE_PATH / 'hhp/baselines/'


SJV_PV_GM_DIR=BASE_PATH / 'SJV-PV-GM-input'

engine = create_engine("sqlite:///flex-metrics.db", echo=False)


def drop_database_tables():
    FlexMetric.metadata.drop_all(engine)
    Baseline.metadata.drop_all(engine)

def create_database_tables():
    FlexMetric.metadata.create_all(engine)
    Baseline.metadata.create_all(engine)

def delete_device_type(device_type: DeviceType):
    with Session(engine) as session:
        doa = FlexDevicesDao(session)
        doa.delete_device_type(device_type)
        baseline_dao = BaselineDao(session)
        baseline_dao.delete_device_type(device_type)

def ev_from_file_to_db():
    areas = set(map(lambda e: ExperimentDescription(e.stem, DeviceType.EV).group, EV_BASELINES.iterdir()))
    print(f"Writing EV flex metrics to database. Amount of PC4 areas: {len(areas)}")

    for i, area in enumerate(areas):
        load_filter = ExperimentFilter().with_group(area)
        all_experiments: ExperimentContainer = FileLoader(baselines_dir=EV_BASELINES, shifted_dir=EV_SHIFTED).load_experiments(load_filter)

        with Session(engine) as session:
            doa = FlexDevicesDao(session)
            doa.save_container(all_experiments)
            baseline_dao = BaselineDao(session)
            for e in all_experiments.exp.values():
                baseline_dao.save_experiment(e)
        print(f"Written {i + 1} / {len(areas)} pc4 areas to database.")

def hp_from_file_to_db():
    descriptions = list(map(lambda e: ExperimentDescription(e.stem, DeviceType.HP), HP_SHIFTED.iterdir()))
    hh_types = set(map(lambda x : x.group, descriptions))
    print(f"Writing HP flex metrics to database. Amount of household types: {len(hh_types)}")
    
    for i, hh_type in enumerate(hh_types):
        load_filter = ExperimentFilter().with_group(hh_type)
        
        hp_experiments = FileLoader(baselines_dir=HP_BASELINES, shifted_dir=HP_SHIFTED).load_experiments(load_filter)
        with Session(engine) as session:
            doa = FlexDevicesDao(session)
            baseline_dao = BaselineDao(session)
            doa.save_container(hp_experiments)
            for e in hp_experiments.exp.values():
                baseline_dao.save_experiment(e)
        print(f"Written {i + 1} / {len(hh_types)} household_types to database.")

def hhp_from_file_to_db():
    for f in HHP_BASELINES.iterdir():
        print(f)
        if f.suffix == '.csv':
            df_baseline = pd.read_csv(f, sep=';', decimal=',', index_col=0, parse_dates=True)
        else:
            print(f"Warning: cannot load file: {f}")
        
        for month_idx in range(1,13):            
            df_month: pd.DataFrame = df_baseline.loc[df_baseline.index.month == month_idx]
            df_month_w_tod: pd.DataFrame = df_month.copy()
            df_month_w_tod['Time'] = df_month_w_tod.index.time
            df_month_avg: pd.DataFrame = df_month_w_tod.groupby('Time').mean()
            month = datetime(2020, month_idx, 1).strftime('%B')
            group_elements: List[str] = f.stem.removeprefix("baselines+").split('+')
            group = f"{group_elements[0]}+{group_elements[1]}+{group_elements[2].removeprefix('status')}".replace(' ', '_').lower()
            with Session(engine) as session:
                doa = BaselineDao(session)
                doa.save(device_type=DeviceType.HHP, typical_day=f"{month}_avg".lower(), group=group, mean_power=df_month_avg.mean(axis=1).round(2))
                doa.save(device_type=DeviceType.HHP, typical_day=f"{month}_15th".lower(), group=group, mean_power=df_month.loc[df_month.index.day == 15].mean(axis=1))
        
    
def gm_types():
    gm_df = readGM(SJV_PV_GM_DIR / 'GM-types GO-e.xlsx')
    
    gm_types = ["sjv500", "sjv1000", "sjv1500", "sjv2000", "sjv2500", "sjv3000", "sjv3500", "sjv4000", "sjv4500", "sjv5000", "sjv6000", "sjv7000", "sjv8000", "sjv9000", "sjv10000", "sjv15000", "PV"]
    day_types = ["Workday", "Weekend"]

    for day_type in day_types:
        for month_idx in range(1, 13):
            for t in gm_types:
                group: str
                month = datetime(2020, month_idx, 1).strftime('%B')
                if t.startswith('sjv'):
                    # Convert expectation values from kW to W
                    expectation_value = np.array(get_daily_sjv_expectation_values(t, gm_df, day_type, month_idx)) * 1000
                    group = t
                    device_type = DeviceType.SJV
                elif t.startswith('PV'):
                    # It seems that the profiles are normalized to 1, so no need to scale
                    expectation_value = get_daily_pv_expectation_values(t, gm_df, day_type, month_idx)
                    group = 'pv'
                    device_type = DeviceType.PV
                print(f"{t} - {month} - {day_type}")

                with Session(engine) as session:
                    doa = BaselineDao(session)
                    doa.save(device_type=device_type, typical_day=f"{month}_{day_type}".lower(), group=group.lower(), mean_power=expectation_value)

def main() :
    parser = ArgumentParser(prog="FlexMetricDatabaseWriter", description="Helper program to fill the data base for flex metrics lookup" )
    parser.add_argument('-d', '--drop', action='store_true', help="delete data before write. if combined with --all, all data is dropped from the database. if combined with --asset_type, only data for those assets is deleted")
    parser.add_argument('-a', '--all', action="store_true", help="write data for all asset types")
    parser.add_argument('-t', '--asset_type', choices=['ev', 'hp', 'sjv-pv', 'hhp'], nargs="+", help="select for which asset type data to write")
    parser.add_argument('-p', '--path', nargs="+", help="provide the path where the input files reside")

    args = parser.parse_args()

    create_database_tables()

    if args.all or (args.asset_type and 'ev' in args.asset_type):
        if args.drop:
            delete_device_type(DeviceType.EV)
        ev_from_file_to_db()
    if args.all or (args.asset_type and 'hp' in args.asset_type):
        if args.drop:
            delete_device_type(DeviceType.HP)
        hp_from_file_to_db()
    if args.all or (args.asset_type and 'sjv-pv' in args.asset_type):
        if args.drop:
            delete_device_type(DeviceType.PV)
            delete_device_type(DeviceType.SJV)
        gm_types()
    if args.all or (args.asset_type and 'hhp' in args.asset_type):
        if args.drop:
            delete_device_type(DeviceType.HHP)
        hhp_from_file_to_db()


if __name__ == "__main__":
    main()
