from dataclasses import dataclass
from typing import List, Dict
import psutil
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class process_info(BaseModel):
    pid: int =Field(..., description="Process Id")
    name:str =Field(..., description="Process name")
    memory_per:float=Field(..., ge=0, description="memory usage %")
    memory_mb:float=Field(..., ge=0, description="memory usage in mb")
    cpu_percent: Optional[float] =Field(None, description="cpu usage")

class system_status(str,Enum):
    OPTIMAL="optimal" #below 60%
    GOOD="good"       # bw 60-75%
    WARNIG="warning"  # bw 75-85%
    CRITICAL="critical"# above 85%

class memory_snap(BaseModel):
    timestamp:str =Field(..., description="snapshot timestamp")

    #memory info
    total_memory:int = Field(..., description="system memory in bytes")
    available_memory:int = Field(..., description="avialbale mmeory in bytes")
    used_memory:int = Field(..., description="Used memory ")
    memory_percent:float = Field(..., ge=0, le=100, description="memory usage %")

    #swap info
    swap_total:int = Field(..., description="total swap space")
    swap_used:int = Field(..., description="used swap space")
    swap_percent:float = Field(..., ge=0, le=100, description="swap usage %")
    
    #process info
    process_count:int=Field(..., description="total running process")
    top_processes:List[process_info]=Field(default=[], description="top memory consuming")
    
    # System status
    status:system_status=Field(..., description="overall system stats")


@property
def total_memory_gb(self) -> float:
    return round(self.total_memory/(1024**3),2)
@property
def available_memory_gb(self) -> float:
    return round(self.available_memory/(1024**3),2)

@property
def used_mmeory_gb(self) -> float:
    return round(self.used_mmeory/ (1024**3),2)

def get_status_color(self) -> str:
    status_colors={
        system_status.OPTIMAL: "#27ae60",  
        system_status.GOOD: "#2ecc71",      
        system_status.WARNIG: "#f39c12",   
        system_status.CRITICAL: "#e74c3c"    
        }
    return status_colors.get(self.status, "#95a5a6")
