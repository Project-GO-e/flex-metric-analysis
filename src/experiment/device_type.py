from __future__ import annotations

from enum import Enum


class DeviceType(Enum):
    EV = 1
    HP = 2
    HHP = 3
    PV = 4
    SJV = 5
    
    @classmethod
    def from_string(cls, device_type: str) -> DeviceType:
        return cls[device_type.upper()]

    def __str__(self) -> str:
        return self.name