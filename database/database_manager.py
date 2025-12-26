"""
Database Manager - SQLite database operations
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import threading

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "database/tiktok_bot.db"):
        self.db_path = db_path
        self.connection = None
        self.lock = threading.Lock()
        self.initialize()
    
    def initialize(self):
        """Initialize database with required tables"""
        with self.lock:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Tasks table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE,
                video_url TEXT,
                requested_views INTEGER,
                completed_views INTEGER,
                failed_views INTEGER,
                method_used TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                success_rate REAL,
                details TEXT
            )
            ''')
            
            # Views table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                view_number INTEGER,
                status TEXT,
                method TEXT,
                proxy_used TEXT,
                account_used TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response_time REAL,
                error_message TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks (task_id)
            )
            ''')
            
            # Proxies table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS proxies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proxy TEXT UNIQUE,
                proxy_type TEXT,
                country TEXT,
                response_time REAL,
                success_count INTEGER DEFAULT 0,
                fail_count INTEGER DEFAULT 0,
                last_used TIMESTAMP,
                last_checked TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Accounts table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT UNIQUE,
                username TEXT,
                email TEXT,
                cookies TEXT,
                user_agent TEXT,
                device_info TEXT,
                total_views INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0,
                last_used TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Statistics table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE UNIQUE,
                total_views INTEGER DEFAULT 0,
                successful_views INTEGER DEFAULT 0,
                failed_views INTEGER DEFAULT 0,
                total_tasks INTEGER DEFAULT 0,
                methods_used TEXT,
                avg_success_rate REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def get_connection(self):
        """Get database connection"""
        if self.connection is None:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def save_task(self, task_data: Dict) -> bool:
        """Save a new task to database"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO tasks 
                (task_id, video_url, requested_views, method_used, status)
                VALUES (?, ?, ?, ?, ?)
                ''', (
                    task_data['task_id'],
                    task_data['video_url'],
                    task_data['requested_views'],
                    task_data.get('method', 'auto'),
                    'pending'
                ))
                
                conn.commit()
                logger.debug(f"Task saved: {task_data['task_id']}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving task: {e}")
            return False
    
    def update_task(self, task_id: str, update_data: Dict) -> bool:
        """Update task status"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                # Build update query
                set_clause = []
                values = []
                
                for key, value in update_data.items():
                    set_clause.append(f"{key} = ?")
                    values.append(value)
                
                values.append(task_id)
                
                query = f'''
                UPDATE tasks 
                SET {', '.join(set_clause)}
                WHERE task_id = ?
                '''
                
                cursor.execute(query, values)
                conn.commit()
                logger.debug(f"Task updated: {task_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return False
    
    def save_view_result(self, view_data: Dict) -> bool:
        """Save individual view result"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO views 
                (task_id, view_number, status, method, proxy_used, 
                 account_used, response_time, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    view_data['task_id'],
                    view_data['view_number'],
                    view_data['status'],
                    view_data.get('method', 'unknown'),
                    view_data.get('proxy_used'),
                    view_data.get('account_used'),
                    view_data.get('response_time'),
                    view_data.get('error_message')
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving view result: {e}")
            return False
    
    def save_proxy(self, proxy_data: Dict) -> bool:
        """Save proxy information"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT OR REPLACE INTO proxies 
                (proxy, proxy_type, country, response_time, 
                 success_count, fail_count, last_checked, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    proxy_data['proxy'],
                    proxy_data.get('type', 'http'),
                    proxy_data.get('country', 'unknown'),
                    proxy_data.get('response_time', 0),
                    proxy_data.get('success_count', 0),
                    proxy_data.get('fail_count', 0),
                    datetime.now().isoformat(),
                    proxy_data.get('is_active', 1)
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving proxy: {e}")
            return False
    
    def save_account(self, account_data: Dict) -> bool:
        """Save account information"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                # Convert cookies to JSON string
                cookies_json = json.dumps(account_data.get('cookies', {}))
                device_json = json.dumps(account_data.get('device_info', {}))
                
                cursor.execute('''
                INSERT OR REPLACE INTO accounts 
                (account_id, username, email, cookies, user_agent, 
                 device_info, total_views, success_rate, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    account_data['account_id'],
                    account_data.get('username'),
                    account_data.get('email'),
                    cookies_json,
                    account_data.get('user_agent'),
                    device_json,
                    account_data.get('total_views', 0),
                    account_data.get('success_rate', 0),
                    account_data.get('is_active', 1)
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving account: {e}")
            return False
    
    def get_active_proxies(self, limit: int = 100) -> List[Dict]:
        """Get active proxies from database"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT * FROM proxies 
                WHERE is_active = 1 
                ORDER BY response_time ASC 
                LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting proxies: {e}")
            return []
    
    def get_active_accounts(self, limit: int = 50) -> List[Dict]:
        """Get active accounts from database"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT * FROM accounts 
                WHERE is_active = 1 
                ORDER BY success_rate DESC 
                LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                
                accounts = []
                for row in rows:
                    account = dict(row)
                    # Parse JSON fields
                    if account.get('cookies'):
                        account['cookies'] = json.loads(account['cookies'])
                    if account.get('device_info'):
                        account['device_info'] = json.loads(account['device_info'])
                    accounts.append(account)
                
                return accounts
                
        except Exception as e:
            logger.error(f"Error getting accounts: {e}")
            return []
    
    def update_proxy_stats(self, proxy: str, success: bool):
        """Update proxy statistics"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                if success:
                    cursor.execute('''
                    UPDATE proxies 
                    SET success_count = success_count + 1,
                        last_used = ?
                    WHERE proxy = ?
                    ''', (datetime.now().isoformat(), proxy))
                else:
                    cursor.execute('''
                    UPDATE proxies 
                    SET fail_count = fail_count + 1
                    WHERE proxy = ?
                    ''', (proxy,))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating proxy stats: {e}")
    
    def update_account_stats(self, account_id: str, success: bool):
        """Update account statistics"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                # Get current stats
                cursor.execute('''
                SELECT total_views, success_rate FROM accounts 
                WHERE account_id = ?
                ''', (account_id,))
                
                row = cursor.fetchone()
                if row:
                    total_views = row['total_views'] + 1
                    
                    if success:
                        # Update success rate (weighted average)
                        old_success_rate = row['success_rate']
                        new_success_rate = ((old_success_rate * row['total_views']) + 1) / total_views
                        
                        cursor.execute('''
                        UPDATE accounts 
                        SET total_views = ?,
                            success_rate = ?,
                            last_used = ?
                        WHERE account_id = ?
                        ''', (
                            total_views,
                            new_success_rate,
                            datetime.now().isoformat(),
                            account_id
                        ))
                    else:
                        # Only update total views for failure
                        cursor.execute('''
                        UPDATE accounts 
                        SET total_views = ?,
                            last_used = ?
                        WHERE account_id = ?
                        ''', (
                            total_views,
                            datetime.now().isoformat(),
                            account_id
                        ))
                    
                    conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating account stats: {e}")
    
    def get_task_stats(self, task_id: str) -> Dict:
        """Get statistics for a specific task"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                # Get task info
                cursor.execute('''
                SELECT * FROM tasks WHERE task_id = ?
                ''', (task_id,))
                
                task_row = cursor.fetchone()
                if not task_row:
                    return {}
                
                task_info = dict(task_row)
                
                # Get view stats
                cursor.execute('''
                SELECT 
                    COUNT(*) as total_views,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_views,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_views,
                    AVG(response_time) as avg_response_time
                FROM views 
                WHERE task_id = ?
                ''', (task_id,))
                
                stats_row = cursor.fetchone()
                if stats_row:
                    task_info.update(dict(stats_row))
                
                # Get method distribution
                cursor.execute('''
                SELECT method, COUNT(*) as count
                FROM views 
                WHERE task_id = ?
                GROUP BY method
                ''', (task_id,))
                
                methods = cursor.fetchall()
                task_info['method_distribution'] = [
                    dict(row) for row in methods
                ]
                
                return task_info
                
        except Exception as e:
            logger.error(f"Error getting task stats: {e}")
            return {}
    
    def get_daily_stats(self, date: str = None) -> Dict:
        """Get daily statistics"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                # Get or create daily stats
                cursor.execute('''
                SELECT * FROM statistics WHERE date = ?
                ''', (date,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                
                # Calculate stats for the day
                cursor.execute('''
                SELECT 
                    COUNT(*) as total_tasks,
                    SUM(requested_views) as total_views_requested,
                    SUM(completed_views) as total_views_completed,
                    AVG(success_rate) as avg_success_rate
                FROM tasks 
                WHERE DATE(created_at) = ?
                ''', (date,))
                
                stats = cursor.fetchone()
                
                if stats:
                    daily_stats = dict(stats)
                    daily_stats['date'] = date
                    
                    # Insert into statistics table
                    cursor.execute('''
                    INSERT INTO statistics 
                    (date, total_tasks, total_views, successful_views, avg_success_rate)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (
                        date,
                        daily_stats.get('total_tasks', 0),
                        daily_stats.get('total_views_requested', 0),
                        daily_stats.get('total_views_completed', 0),
                        daily_stats.get('avg_success_rate', 0)
                    ))
                    
                    conn.commit()
                    
                    return daily_stats
                
                return {}
                
        except Exception as e:
            logger.error(f"Error getting daily stats: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30):
        """Cleanup old data from database"""
        try:
            with self.lock:
                conn = self.get_connection()
                cursor = conn.cursor()
                
                cutoff_date = datetime.now().replace(
                    day=datetime.now().day - days
                ).strftime('%Y-%m-%d')
                
                # Delete old tasks
                cursor.execute('''
                DELETE FROM tasks 
                WHERE DATE(created_at) < ?
                ''', (cutoff_date,))
                
                # Delete old views
                cursor.execute('''
                DELETE FROM views 
                WHERE DATE(timestamp) < ?
                ''', (cutoff_date,))
                
                conn.commit()
                logger.info(f"Cleaned up data older than {days} days")
                
        except Exception as e:
            logger.error(f"Error cleaning up data: {e}")
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")
    
    def backup(self, backup_path: str):
        """Create database backup"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False