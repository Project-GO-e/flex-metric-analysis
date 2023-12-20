from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from db.flex_metrics import Base, FlexMetrics
from experiment_filter import ExperimentFilter
from experiment_loader import FileLoader

BASE_DIR='data/all_pc4/'

BASELINES_DIR=BASE_DIR + 'ev/baselines/'
SHIFTED_DIR=BASE_DIR + 'ev/shifted/'

DAY = datetime(2020,6,6)

load_filter = ExperimentFilter()
all_experiments = FileLoader(baselines_dir=Path(BASELINES_DIR), shifted_dir=Path(SHIFTED_DIR)).load_experiments(load_filter)

engine = create_engine("sqlite:///test.db", echo=True)

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)


with Session(engine) as session:
    
    for e in all_experiments.exp.values():
        session.add(e.to_db_object())
    session.commit()

