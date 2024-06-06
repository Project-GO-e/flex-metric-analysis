

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.baselines_dao import BaselinePdfDao
from experiment.device_type import DeviceType


engine = create_engine(f"sqlite:///flex-metrics-pdf.db", echo=False)

with Session(engine) as s:
    pdf = BaselinePdfDao(session=s).get_baseline_pdf(DeviceType.PV, "january", "pv")

    print(pdf.pdfs[0])