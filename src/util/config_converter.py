
from pathlib import Path

import pandas as pd
from flex_metric_config import BaseloadConfig, Config, EvConfig, HhpConfig, HouseTypeConfig, HpConfig, PvConfig


class ExcelConverter():
    '''
    Helper class to read an Excel file with the scenario configuration and convert it to a Config object
    '''
    
    def __init__(self, config_file: Path) -> None:
        self.config_file = config_file        
        self.assets_df = pd.read_excel(self.config_file, sheet_name="assets", index_col=0)
        self.cong_df = pd.read_excel(self.config_file, sheet_name="congestion", index_col=0, header=None)
        self.validate()

    def validate(self) -> None:
        # assert len(assets_df.query('type=="ev"')) == 1, "Only one ev row allowed"
        if not self.assets_df.query('type=="pv"').empty:
            assert len(self.assets_df.query('type=="pv"')) == 1, "Only one pv row allowed"
        if not self.assets_df.query('type=="hp"').empty:
            assert len(self.assets_df.query('type=="hp"')['typical_day'].unique()) == 1, "Use the same typical day for all heat pump configurations"
        if not self.assets_df.query('type=="baseload"').empty:
            assert len(self.assets_df.query('type=="baseload"')['typical_day'].unique()) == 1, "Use the same typical day for all baseload configurations"
        
    def convert(self) -> Config:
        cong_start = self.cong_df.loc['start'].iloc[0]
        cong_dur = self.cong_df.loc['duration'].iloc[0]
        ev_conf = None
        hp_conf = None
        pv_conf = None
        sjv_conf = None
        hhp_conf = None
        for i,r in self.assets_df.iterrows():
            if r['type'] == 'ev':
                #TODO: check if baseline provided, then load and add instead of amount
                ev_conf = [] if ev_conf is None else ev_conf
                ev_conf.append(EvConfig(typical_day=r['typical_day'], pc4=r['group'], amount=r['amount']))
            elif r['type'] == 'hp':
                if hp_conf is None:
                    hp_conf = HpConfig(typical_day=r['typical_day'], house_type=[])
                #TODO: check if baseline provided, then load and add instead of amount
                hp_conf.house_type.append(HouseTypeConfig(name=r['group'], amount=r['amount']))
            elif r['type'] == 'hhp':
                if hhp_conf is None:
                    hhp_conf = HhpConfig(typical_day=r['typical_day'], house_type=[])
                #TODO: check if baseline provided, then load and add instead of amount
                hhp_conf.house_type.append(HouseTypeConfig(name=r['group'], amount=r['amount']))
            elif r['type'] == 'baseload':
                if sjv_conf is None:
                    sjv_conf = BaseloadConfig(typical_day=r['typical_day'], sjv=[])
                #TODO: check if baseline provided, then load and add instead of amount
                sjv_conf.sjv.append(HouseTypeConfig(name=r['group'], amount=r['amount']))
            elif r['type'] == 'pv':
                #TODO: check if baseline provided, then load and add instead of amount
                pv_conf = PvConfig(typical_day=r['typical_day'], peak_power_W=r['amount'])

        return Config(congestion_start=cong_start, congestion_duration=cong_dur, ev=ev_conf, hp=hp_conf, pv=pv_conf, non_flexible_load=sjv_conf, hhp=hhp_conf)


if __name__ == "__main__":
    ExcelConverter(Path("example-config.xlsx")).convert()
