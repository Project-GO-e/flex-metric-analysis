
from dataclasses import dataclass
from datetime import time
from typing import List

import pandas as pd

from experiment.device_type import DeviceType


@dataclass
class DeviceResults():
    device_type: DeviceType
    baselines: pd.DataFrame
    flex_profiles: pd.DataFrame = None


@dataclass
class Results():
    cong_start: time
    cong_duration: int
    results: List[DeviceResults]

    def flex_profiles(self) -> pd.DataFrame:
        flex_profile = []
        for r in self.results:
            if not r.flex_profiles is None:
                flex_profile.append(r.flex_profiles.add_prefix('flex_' + str(r.device_type).lower() + '_'))
    
        return pd.concat(flex_profile, axis=1)
    
    def baselines(self) -> pd.DataFrame:
        baselines = []
        for r in self.results:
            baselines.append(r.baselines.add_prefix(str(r.device_type).lower() + '_'))
        return pd.concat(baselines, axis=1)

    

