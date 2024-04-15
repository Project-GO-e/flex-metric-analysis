from __future__ import annotations

from enum import Enum


class DeviceType(Enum):
    EV = 1
    HP = 2
    PV = 3
    SJV = 4
    
    @classmethod
    def from_string(cls, device_type: str) -> DeviceType:
        return cls[device_type.upper()]

    def __str__(self) -> str:
        return self.name