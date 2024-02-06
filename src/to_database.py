from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.flex_metrics import FlexMetrics
from db.flex_metrics_dao import FlexMetricsDao
from experiment_description import DeviceType, ExperimentDescription
from experiment_filter import ExperimentFilter
from experiment_loader import FileLoader

BASE_DIR=Path('data')

BASELINES_DIR=BASE_DIR / Path('all_pc4/ev/baselines/')
SHIFTED_DIR=BASE_DIR / Path('all_pc4/ev/shifted/')

HP_BASELINES_DIR=BASE_DIR / Path('hp/baseline/')
HP_SHIFTED_DIR=BASE_DIR / Path('hp/shifted/')

engine = create_engine("sqlite:///ev-hp-flex-metrics.db", echo=False)

FlexMetrics.metadata.drop_all(engine)
FlexMetrics.metadata.create_all(engine)

areas = set(map(lambda e: ExperimentDescription(e.stem, DeviceType.EV).get_group(), Path(BASELINES_DIR).iterdir()))
print(list(areas)[:10])

for area in areas:
    load_filter = ExperimentFilter().with_group(area)
    all_experiments = FileLoader(baselines_dir=Path(BASELINES_DIR), shifted_dir=Path(SHIFTED_DIR)).load_experiments(load_filter)

    with Session(engine) as session:
        doa = FlexMetricsDao(session)
        doa.save_container(all_experiments)
       

hp_experiments = FileLoader(baselines_dir=HP_BASELINES_DIR, shifted_dir=HP_SHIFTED_DIR).load_experiments()

with Session(engine) as session:
    doa = FlexMetricsDao(session)
    doa.save_container(hp_experiments)
