
from dataclasses import dataclass
from typing import List


@dataclass
class Pdfs():
    metadata_start: float
    metadata_step: float
    pdfs: List[List]

    @property
    def metadata_stop(self) -> float:
        return self.metadata_start + (len(self.pdfs[0]) - 1) * self.metadata_step