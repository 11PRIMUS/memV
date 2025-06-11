from contextlib import asynccontextmanager
from model import memory_snap, memory_stats, history_record, process_info, DatabaseStats
from typing import Optional, List, Dict
import sqlite3
import json
import asyncio
import logging
from datetime import datetime, timedelta

logger=logging.getLogger(__name__)

class db_manager:
    def __init__(self, db_path:str="memory_monitor.db"):
        self.db_path=db_path
        self.connection_pool=[]
        self.max_connections=5

    async def init(self): #db with required tables
        try:
            await self._create_tables()
            await self._create_indexes()
            logger.info("Db init successful")
        except Exception as e:
            logger.error(f"db failed{e}")
            raise
    
    async def create_tables(self):
        conn=sqlite3.connect(self.db_path)
        cursor=conn.cursor()
        
        #main memory snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                total_memory INTEGER NOT NULL,
                available_memory INTEGER NOT NULL,
                used_memory INTEGER NOT NULL,
                memory_percent REAL NOT NULL,
                swap_total INTEGER NOT NULL,
                swap_used INTEGER NOT NULL,
                swap_percent REAL NOT NULL,
                process_count INTEGER NOT NULL,
                top_processes TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'good',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_info (
                id INTEGER PRIMARY KEY,
                hostname TEXT,
                platform TEXT,
                cpu_count INTEGER,
                total_memory INTEGER,
                boot_time TEXT,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')    
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                memory_percent REAL NOT NULL,
                acknowledged BOOLEAN DEFAULT FALSE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    @asynccontextmanager
    async def get_connection(self):
        conn=None
        try:
            conn=sqlite3.connect(self.db_path,timeout=30.0)
            conn.row_factory = sqlite3.Row  #column access by row
            yield conn
        except Exception as e:
            logger.error(f"db error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    async def save_snap(self, snapshot:memory_snap) -> bool:
        try:
            async with self.get_connection() as conn:
                cursor=conn.cursor()
                cursor.execute('''
                    INSERT INTO memory_snapshots 
                    (timestamp, total_memory, available_memory, used_memory, memory_percent,
                     swap_total, swap_used, swap_percent, process_count, top_processes, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    snapshot.timestamp,
                    snapshot.total_memory,
                    snapshot.available_memory,
                    snapshot.used_memory,
                    snapshot.memory_percent,
                    snapshot.swap_total,
                    snapshot.swap_used,
                    snapshot.swap_percent,
                    snapshot.process_count,
                    json.dumps([p.dict() for p in snapshot.top_processes]),
                    snapshot.status.value
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"failed to save:{e}")
            return False
        
    async def get_history(self,hours:int=24) -> List[Dict]: #historical data
        try:
            start_time=(datetime.now()-timedelta(hours=hours)).isoformat()
            
            async with self.get_connection() as conn:
                cursor=conn.cursor()
                cursor.execute('''
                    SELECT timestamp, memory_percent, swap_percent, used_memory, 
                           available_memory, top_processes, status
                    FROM memory_snapshots 
                    WHERE timestamp >= ? 
                    ORDER BY timestamp ASC
                ''', (start_time,))
                
                rows=cursor.fetchall()
                
                history=[]
                for row in rows:
                    try:
                        top_processes=json.loads(row['top_processes']) if row['top_processes'] else []
                    except json.JSONDecodeError:
                        top_processes=[]
                    
                    history.append({
                        'timestamp':row['timestamp'],
                        'memory_percent':row['memory_percent'],
                        'swap_percent':row['swap_percent'],
                        'used_memory':row['used_memory'],
                        'available_memory': row['availble_memory'],
                        'top_processes':top_processes,
                        'status': row['status']
                    })
                
                return history
        except Exception as e:
            logger.error(f"failed to get history: {e}")
            return []
    
    async def get_stats(self,hours:int=24)-> memory_stats:  # memory usage stats
        try:
            start_time=(datetime.now()-timedelta(hours=hours)).isoformat()
            
            async with self.get_connection() as conn:
                cursor=conn.cursor()
                cursor.execute('''
                    SELECT memory_percent, timestamp
                    FROM memory_snapshots 
                    WHERE timestamp >= ? 
                    ORDER BY timestamp ASC
                ''', (start_time,))
                
                rows=cursor.fetchall()
                
                if not rows:
                    return memory_stats(
                        avg_usage=0,max_usage=0,min_usage=0,
                        peak_time="",low_time="",
                        usage_trend="stable",stability_score=100.0,
                        efficiency_grade="A"
                    )
                
                usage_values=[row['memory_percent'] for row in rows]
                max_usage= max(usage_values)
                min_usage= min(usage_values)
                avg_usage=sum(usage_values)/len(usage_values)
                
                peak_time=next(row['timestamp'] for row in rows if row['memory_percent']==max_usage)
                low_time=next(row['timestamp'] for row in rows if row['memory_percent']==min_usage)
                
                trend =self._calculate_trend(usage_values)
                stability = self._calculate_stability(usage_values)
                grade=self._calculate_efficiency_grade(avg_usage,stability)
                
                return memory_stats(
                    avg_usage=round(avg_usage,2),
                    max_usage=max_usage,
                    min_usage=min_usage,
                    peak_time=peak_time,
                    low_time=low_time,
                    usage_trend=trend,
                    stability_score=stability,
                    efficiency_grade=grade
                )
        except Exception as e:
            logger.error(f"stats failed: {e}")
            return memory_stats(
                avg_usage=0,max_usage=0, min_usage=0,
                peak_time="",low_time=""
            )
    
    def calculate_trend(self,values: List[float]) ->str:
        if len(values) < 5:
            return "stable"
        
        recent=values[-5:]
        earlier=values[-10:-5] if len(values) >= 10 else values[:-5]
        
        recent_avg=sum(recent)/len(recent)
        earlier_avg=sum(earlier)/len(earlier)
        
        diff=recent_avg-earlier_avg
        
        if diff > 5:
            return "increasing"
        elif diff < -5:
            return "decreasing"
        else:
            return "stable"
