from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from db.flex_metrics import Base, FlexMetrics
from experiment_description import DeviceType, ExperimentDescription
from experiment_filter import ExperimentFilter
from experiment_loader import FileLoader

BASE_DIR='data/all_pc4/'

BASELINES_DIR=BASE_DIR + 'ev/baselines/'
SHIFTED_DIR=BASE_DIR + 'ev/shifted/'

DAY = datetime(2020,6,6)

engine = create_engine("sqlite:///test.db", echo=True)

FlexMetrics.metadata.drop_all(engine)
FlexMetrics.metadata.create_all(engine)

areas = set(map(lambda e: ExperimentDescription(e.stem, DeviceType.EV).get_area(), Path(BASELINES_DIR).iterdir()))

print(areas)

for area in areas:

    load_filter = ExperimentFilter().with_area(area)
    all_experiments = FileLoader(baselines_dir=Path(BASELINES_DIR), shifted_dir=Path(SHIFTED_DIR)).load_experiments(load_filter)

    with Session(engine) as session:
        for e in all_experiments.exp.values():
            session.add(e.to_db_object())
        session.commit()

