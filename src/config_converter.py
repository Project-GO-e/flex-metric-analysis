
from datetime import datetime, time
from pathlib import Path

import pandas as pd
from flex_metric_config import BaseloadConfig, Config, EvConfig, HouseTypeConfig, HpConfig, PvConfig


class ExcelConverter():

    def __init__(self, config_file: Path, cong_start: time, cong_duration: int) -> None:
        self.config_file = config_file
        self.cong_start = cong_start
        self.cong_dur = cong_duration

    def convert(self) -> Config:
        assets_df = pd.read_excel(self.config_file, sheet_name="assets", index_col=0)
        ev_conf = None
        hp_conf = None
        pv_conf = None
        sjv_conf = None
        for i,r in assets_df.iterrows():
            if r['type'] == 'ev':
                #TODO: check if baseline provided, then laod and add instead of amount
                ev_conf = EvConfig(typical_day=r['typical-day'], pc4=r['group'], amount=r['amount'])
            elif r['type'] == 'hp':
                if hp_conf is None:
                    hp_conf = HpConfig(typical_day=r['typical-day'], house_type=[])
                #TODO: check if baseline provided, then laod and add instead of amount
                hp_conf.house_type.append(HouseTypeConfig(name=r['group'], amount=r['amount']))
            elif r['type'] == 'baseload':
                if sjv_conf is None:
                    sjv_conf = BaseloadConfig(typical_day=r['typical-day'], sjv=[])
                #TODO: check if baseline provided, then laod and add instead of amount
                sjv_conf.sjv.append(HouseTypeConfig(name=r['group'], amount=r['amount']))
            elif r['type'] == 'pv':
                #TODO: check if baseline provided, then laod and add instead of amount
                pv_conf = PvConfig(typical_day=r['typical-day'], peak_power_W=r['amount'])

        return Config(congestion_start=self.cong_start, congestion_duration=self.cong_dur, ev=ev_conf, hp=hp_conf, pv=pv_conf, non_flexible_load=sjv_conf)


if __name__ == "__main__":
    ExcelConverter(Path("example-config.xlsx"), time(8,0) ,4).convert()
