from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.flex_devices_dao import FlexDevicesDao
from db.models import FlexDevices, NonFlexDevices
from db.non_flex_devices_dao import NonFlexDevicesDao
from experiment.experiment_description import DeviceType, ExperimentDescription
from experiment.experiment_filter import ExperimentFilter
from experiment.experiment_loader import FileLoader
from util.conflex import (get_daily_pv_expectation_values,
                          get_daily_sjv_expectation_values, readGM)

BASE_PATH=Path('data/test')

EV_BASELINES=BASE_PATH / 'ev/baseline/'
EV_SHIFTED=BASE_PATH / 'ev/shifted/'

HP_BASELINES=BASE_PATH / 'hp/baseline/'
HP_SHIFTED=BASE_PATH / 'hp/shifted/'

SJV_PV_GM_DIR=BASE_PATH / 'SJV-PV-GM-input'

engine = create_engine("sqlite:///test.db", echo=False)


def drop_database_tables():
    FlexDevices.metadata.drop_all(engine)
    NonFlexDevices.metadata.drop_all(engine)


def create_database_tables():
    FlexDevices.metadata.create_all(engine)
    NonFlexDevices.metadata.create_all(engine)


def ev_from_file_to_db():
    areas = set(map(lambda e: ExperimentDescription(e.stem, DeviceType.EV).get_group(), EV_BASELINES.iterdir()))
    print(list(areas)[:10])

    for area in areas:
        load_filter = ExperimentFilter().with_group(area)
        all_experiments = FileLoader(baselines_dir=EV_BASELINES, shifted_dir=EV_SHIFTED).load_experiments(load_filter)

        with Session(engine) as session:
            doa = FlexDevicesDao(session)
            doa.save_container(all_experiments)


def hp_from_file_to_db():
    hp_experiments = FileLoader(baselines_dir=HP_BASELINES, shifted_dir=HP_SHIFTED).load_experiments()

    with Session(engine) as session:
        doa = FlexDevicesDao(session)
        doa.save_container(hp_experiments)


def gm_types():
    gm_df = readGM(SJV_PV_GM_DIR / 'GM-types GO-e.xlsx')
    
    gm_types = ["sjv500", "sjv1000", "sjv1500", "sjv2000", "sjv2500", "sjv3000", "sjv3500", "sjv4000", "sjv4500", "sjv5000", "sjv6000", "sjv7000", "sjv8000", "sjv9000", "sjv10000", "sjv15000", "PV"]
    day_types = ["Workday", "Weekend"]

    for day_type in day_types:
        for month_idx in range(1, 13):
            for t in gm_types:
                if t.startswith('sjv'):
                    expectation_value = get_daily_sjv_expectation_values(t, gm_df, day_type, month_idx)
                    print(t + " - Expectation value: " + str(expectation_value))
                elif t.startswith('PV'):
                    expectation_value = get_daily_pv_expectation_values(t, gm_df, day_type, month_idx)
                    print(t + " - Expectation value: " + str(expectation_value))
                month = datetime(2020,month_idx,1).strftime('%B')
                with Session(engine) as session:
                    doa = NonFlexDevicesDao(session)
                    doa.save(asset_type=t, typical_day=f"{month}_{day_type}", mean_power=expectation_value)

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

    if args.all or 'ev' in args.asset_type:
        ev_from_file_to_db()
    if args.all or 'hp' in args.asset_type:
        hp_from_file_to_db()
    if args.all or 'sjv-pv' in args.asset_type:
        gm_types()


if __name__ == "__main__":
    main()
