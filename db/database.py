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
