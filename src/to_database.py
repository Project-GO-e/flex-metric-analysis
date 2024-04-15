from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path

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
HP_SHIFTED=BASE_PATH / 'hp/shifted-1/'

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


def ev_from_file_to_db():
    areas = set(map(lambda e: ExperimentDescription(e.stem, DeviceType.EV).get_group(), EV_BASELINES.iterdir()))
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
    hh_types = set(map(lambda x : x.get_group(), descriptions))
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
                    expectation_value = get_daily_sjv_expectation_values(t, gm_df, day_type, month_idx)
                    group = t
                    device_type = DeviceType.SJV
                    print(f"{t} - {month} - {day_type}")
                elif t.startswith('PV'):
                    expectation_value = get_daily_pv_expectation_values(t, gm_df, day_type, month_idx)
                    group = 'pv'
                    device_type = DeviceType.PV
                    print(t + " - Expectation value: " + str(expectation_value))

                with Session(engine) as session:
                    doa = BaselineDao(session)
                    doa.save(device_type=device_type, typical_day=f"{month}_{day_type}", group=group, mean_power=expectation_value)

def main() :
    parser = ArgumentParser(prog="FlexMetricDatabaseWriter", description="Helper program to fill the data base for flex metrics lookup" )
    parser.add_argument('-d', '--drop', action='store_true', help="drop the database tables before write")
    parser.add_argument('-a', '--all', action="store_true", help="write data for all asset types")
    parser.add_argument('-t', '--asset_type', choices=['ev', 'hp', 'sjv-pv'], nargs="+", help="select for which asset type data to write")
    parser.add_argument('-p', '--path', nargs="+", help="provide the path where the input files reside")

    args = parser.parse_args()

    if args.drop:
        drop_database_tables()

    create_database_tables()

    hp_from_file_to_db()
    if args.all or (args.asset_type and 'ev' in args.asset_type):
        ev_from_file_to_db()
    if args.all or (args.asset_type and 'hp' in args.asset_type):
        hp_from_file_to_db()
    if args.all or (args.asset_type and 'sjv-pv' in args.asset_type):
        gm_types()


if __name__ == "__main__":
    main()
