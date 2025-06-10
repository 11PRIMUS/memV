from dataclasses import dataclass
from typing import List, Dict ,Optional
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

class memory_stats(BaseModel):
    avg_usage:float =Field(..., description="avg memory usage %")
    max_usage:float=Field(..., description="max_memory usage 5")
    min_usage:float=Field(..., description="min memory usage%")
    peak_time:str =Field(..., description="time of peek")
    low_time:str =Field(..., description="time of lowest use")
    # add ons
    # usage_trend: Optional[str] = Field(None, description="usage trend: increasing/stable/decreasing")
    # stability_score: Optional[float] = Field(None, ge=0, le=100, description="stability score")
    # efficiency_grade: Optional[str] = Field(None, description="grade")

class alert_config(BaseModel):
    warning_threshold:float =Field(75.0, ge=0, le=100, description="warning ")
    critical_threshold:float=Field(90.0, ge=0, le=100, description="critical threshold %")
    notification_interval:int=Field(300, ge=60, description="min sec b/w notifaction")
    
    def get_status_for_usage(self, usage_percent: float) -> system_status
        if usage_percent>= self.critical_threshold:
            return system_status.CRITICAL
        elif usage_percent>= self.warning_threshold:
            return system_status.WARNING
        elif usage_percent>=60:
            return system_status.GOOD
        else:
            return system_status.OPTIMAL

class history_record(BaseModel):
    timestamp:str
    memory_percent:float
    swap_percent:float
    used_memory:int
    available_memory:int
    top_processes:List[process_info]
    
    class Config:
        #custom filed from db
        populate_by_name = True

class system_info(BaseModel):
    hostname:Optional[str] =None
    platform:Optional[str] =None
    cpu_count:Optional[int] =None
    boot_time:Optional[str] =None
    uptime_seconds:Optional[int]=None
    
    @property
    def uptime_formatted(self) -> str:
        if not self.uptime_seconds:
            return "unknown"
        
        days=self.uptime_seconds // 86400
        hours=(self.uptime_seconds % 86400) // 3600
        minutes=(self.uptime_seconds % 3600) // 60
        
        return f"{days}d {hours}h {minutes}m"

class DatabaseStats(BaseModel):
    total_records:int
    oldest_record:Optional[str]=None
    newest_record:Optional[str]=None
    database_size_mb: float
    
class monitor_config(BaseModel):
    collection_interval:int = Field(60, ge=10, description="collection interval")
    retention_days:int=Field(7, ge=1, description="data retention period(days)")
    max_processes:int=Field(10, ge=5, description="max process to track")
    
    alerts:alert_config=Field(default_factory=alert_config) #alert setting
    
    auto_refresh_interval:int = Field(30, ge=10, description="dash auto refresh(sec)")
    chart_animation: bool=Field(True, description="chart animation")
    
    class Config:
        env_prefix="MEMORY_MONITOR_"
        case_sensitive=False
