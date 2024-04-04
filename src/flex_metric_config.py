
from dataclasses import dataclass
from datetime import time
from typing import List


@dataclass
class EvConfig:
    typical_day: str
    '''The typical EV day [work/weekend]'''
    pc4: str
    '''The PC4 area for which EV data used'''
    amount: int = None
    '''The amount of EVs in the scenario. This cannot be used in combination with baseline_total'''
    baseline_total_W: List[float] = None
    '''The baseline in Watt of all EVs in the scenario. This cannot be used in combination with amount'''


@dataclass
class HouseTypeConfig:
    name: str
    '''Name of this house type, formatted as [RVO-type]+[construction-year]+[inhabitants], e.g. tussen+2012+family'''
    amount: int = None
    '''The amount of heat pumps of this type. This cannot be used in combination with baseline_total'''
    baseline_total_W: List[float] = None
    '''The baseline in Watt of all heat pumps of this type. This cannot be used in combination with amount'''


@dataclass
class HpConfig:
    typical_day: str
    '''Use a typical day in month'''
    house_type: List[HouseTypeConfig]


@dataclass
class SjvConfig:
    name: str
    '''Name of the sjv catogery, formatted as svj[amount-kWh], e.g. svj500. Possible values for amount-kWh are: 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 6000, 7000, 8000, 9000, 10000, 15000'''
    amount: int
    '''Amount of househould in this sjv catogery'''


@dataclass
class BaseloadConfig:
    typical_day: str
    '''Use a typical work/weekend day in month'''
    sjv: List[SjvConfig]


@dataclass
class PvConfig:
    typical_day: str
    '''Use a typical work/weekend day in month'''
    peak_power_W: float
    '''Peak power in Watt of all PV'''

@dataclass
class Config:
    congestion_start: time
    '''Start time of the congestion'''
    congestion_duration: int
    '''Duration of the congestion in amount of PTU (15min)'''
    ev: EvConfig
    hp: HpConfig
    pv: PvConfig = None
    non_flexible_load: BaseloadConfig = None
    baseline_total_W: List[float] = None
    '''The summed baseline in Watt of all devices in the scenario. This will only be used if individual asset type profiles are not provided'''


    def all_baselines_available(self) -> bool:
        baseline_available = True
        for hp in self.hp.house_type:
            if hp.baseline_total_W is None:
                baseline_available = False
                print(f"No heatpump baseline for {hp.name}")
        
        if self.ev.baseline_total_W is None:
            print("No EV baseline provided")
            baseline_available = False
        return baseline_available


    def all_asset_amounts_available(self) -> bool:
        amounts_available = True
        for hp in self.hp.house_type:
            if hp.amount is None:
                amounts_available = False
                print(f"No heatpump amount provided for {hp.name}")
        
        if self.ev.amount is None:
            print("No EV amount provided")
            amounts_available = False
        return amounts_available
    

    def is_valid(self) -> bool:
        valid = True
        if not self.all_baselines_available() and not self.all_asset_amounts_available():
            print("Invalid configuration. Not for all flexible assets baselines have been provided. The alternative is to provide amounts of flexible devices for all flexible device types but not all flexible devices have amounts.")
            valid = False
        # TODO: check if all requested data is in the database
        return valid
