

import pickle

from sqlalchemy.orm import Session

from db.models import NonFlexDevices


class NonFlexDevicesDao():

    def __init__(self, session: Session) -> None:
        self.session = session

    
    def save(self, asset_type: str, typical_day: str, mean_power) -> None:
        power = pickle.dumps(mean_power)
        self.session.add(NonFlexDevices(asset_type, typical_day, power))
        self.session.commit()