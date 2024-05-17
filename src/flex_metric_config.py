
from dataclasses import dataclass
from datetime import time
from typing import List, Optional, Tuple


@dataclass
class EvConfig:
    typical_day: str
    '''The typical EV day [work/weekend]'''
    pc4: str
    '''The PC4 area for which EV data used'''
    amount: Optional[int] = None
    '''The amount of EVs in the scenario. This cannot be used in combination with baseline_total'''
    baseline_total_W: Optional[List[float]] = None
    '''The baseline in Watt of all EVs in the scenario. This cannot be used in combination with amount'''


@dataclass
class HouseTypeConfig:
    name: str
    '''Name of this house type, formatted as [RVO-type]+[construction-year]+[inhabitants], e.g. tussen+2012+family'''
    amount: Optional[int] = None
    '''The amount of heat pumps of this type. This cannot be used in combination with baseline_total'''
    baseline_total_W: Optional[List[float]] = None
    '''The baseline in Watt of all heat pumps of this type. This cannot be used in combination with amount'''


@dataclass
class HpConfig:
    typical_day: str
    '''Use a typical day in month'''
    house_type: List[HouseTypeConfig]


@dataclass
class HhpConfig:
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
    ev: Optional[List[EvConfig]] = None
    hp: Optional[HpConfig] = None
    hhp: Optional[HhpConfig] = None
    pv: Optional[PvConfig] = None
    non_flexible_load: Optional[BaseloadConfig] = None
    baseline_total_W: Optional[List[float]] = None
    '''The summed baseline in Watt of all devices in the scenario. This will only be used if individual asset type profiles are not provided'''

    # def all_baselines_available(self) -> bool:
    #     baseline_available = True
    #     for hp in self.hp.house_type:
    #         if hp.baseline_total_W is None:
    #             baseline_available = False
    #     for hhp in self.hhp.house_type:
    #         if hhp.baseline_total_W is None:
    #             baseline_available = False
    #     if self.ev.baseline_total_W is None:
    #         baseline_available = False
    #     return baseline_available

    # def all_asset_amounts_available(self) -> bool:
    #     amounts_available = True
    #     for hp in self.hp.house_type:
    #         if hp.amount is None:
    #             amounts_available = False
    #     for hhp in self.hp.house_type:
    #         if hhp.amount is None:
    #             amounts_available = False
    #     if self.ev.amount is None:
    #         amounts_available = False
    #     return amounts_available

    def validate_profile_lengths(self) -> Tuple[bool, str]:
        all_lengths_valid = True
        non_valid_device_baselines = []
        if self.hp:
            for hp in self.hp.house_type:
                if hp.baseline_total_W and len(hp.baseline_total_W) is not self.congestion_duration:
                    all_lengths_valid = False
                    non_valid_device_baselines.append("HP: " + hp.name)

        if self.hhp:
            for hhp in self.hhp.house_type:
                if hhp.baseline_total_W and len(hhp.baseline_total_W) is not self.congestion_duration:
                    all_lengths_valid = False
                    non_valid_device_baselines.append("HHP" + hhp.name)
        
        if self.ev:
            for e in self.ev:
                if e.baseline_total_W and len(e.baseline_total_W) is not self.congestion_duration:
                    all_lengths_valid = False
                    non_valid_device_baselines.append("EV")
        
        if not all_lengths_valid:
            msg = "The following device types have a different profile length than the congestion duration: " + ", ".join(non_valid_device_baselines)
        else: 
            msg = ""
        return (all_lengths_valid, msg)
    
    def is_valid(self) -> bool:
        profile_length_validation = self.validate_profile_lengths()
        if not profile_length_validation[0]:
            raise AssertionError("Validation error: " + profile_length_validation[1])
        return profile_length_validation[0]
