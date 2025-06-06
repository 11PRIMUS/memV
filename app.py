# models.py
from dataclasses import dataclass
from typing import List, Dict
import psutil

@dataclass
class SystemMemoryInfo:
    """Custom class for memory information"""
    total_gb: float
    used_gb: float
    available_gb: float
    usage_percent: float
    
    @classmethod
    def from_psutil(cls):
        mem = psutil.virtual_memory()
        return cls(
            total_gb=mem.total / (1024**3),
            used_gb=mem.used / (1024**3),
            available_gb=mem.available / (1024**3),
            usage_percent=mem.percent
        )

class ProcessAnalyzer:
    """Custom process analysis class"""
    
    def __init__(self, max_processes: int = 10):
        self.max_processes = max_processes
    
    def get_top_consumers(self) -> List[Dict]:
        # Your custom implementation
        pass