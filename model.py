from dataclasses import dataclass
from typing import List, Dict
import psutil

@dataclass
class Memory_info:
    total_gb:float
    used_gb:float
    available_gb:float
    usage_percent:float

    @classmethod
    def from_psutil(cls):
        mem=psutil.virtual_memory()
        return cls(
            total_gb=mem.total,
            used_gb=mem.used,
            available_gb=mem.available,
            usage_percent=mem.percent
        )
    
class ProcessAnalyzer:
    def __init__(self, max_processses:int =10):
        self.max_processes=max_processses

    def get_top_consumers(self) -> List[Dict]:
        pass