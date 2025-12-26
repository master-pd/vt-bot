"""
Database CRUD Operations
Advanced database operations with SQLAlchemy
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_

from utils.logger import setup_logger
from database.models import (
    User, Test, TikTokAccount, Proxy, SystemLog,
    engine, SessionLocal
)

logger = setup_logger(__name__)

# ==================== USER OPERATIONS ====================

def create_user(
    db: Session,
    telegram_id: str = None,
    username: str = None,
    email: str = None,
    is_admin: bool = False
) -> User:
    """Create a new user"""
    try:
        user = User(
            telegram_id=telegram_id,
            username=username,
            email=email,
            is_admin=is_admin
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created user: {user.id}")
        return user
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise

def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_telegram_id(db: Session, telegram_id: str) -> Optional[User]:
    """Get user by Telegram ID"""
    return db.query(User).filter(User.telegram_id == telegram_id).first()

def update_user(
    db: Session,
    user_id: int,
    **kwargs
) -> Optional[User]:
    """Update user information"""
    try:
        user = get_user(db, user_id)
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user {user_id}: {e}")
        return None

def delete_user(db: Session, user_id: int) -> bool:
    """Delete user"""
    try:
        user = get_user(db, user_id)
        if user:
            db.delete(user)
            db.commit()
            logger.info(f"Deleted user: {user_id}")
            return True
        return False
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user {user_id}: {e}")
        return False

# ==================== TEST OPERATIONS ====================

def create_test(
    db: Session,
    user_id: int,
    task_id: str,
    video_url: str,
    view_count: int
) -> Test:
    """Create a new test"""
    try:
        test = Test(
            user_id=user_id,
            task_id=task_id,
            video_url=video_url,
            view_count=view_count
        )
        db.add(test)
        db.commit()
        db.refresh(test)
        logger.info(f"Created test: {task_id}")
        return test
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating test: {e}")
        raise

def get_test(db: Session, test_id: int) -> Optional[Test]:
    """Get test by ID"""
    return db.query(Test).filter(Test.id == test_id).first()

def get_test_by_task_id(db: Session, task_id: str) -> Optional[Test]:
    """Get test by task ID"""
    return db.query(Test).filter(Test.task_id == task_id).first()

def update_test(
    db: Session,
    test_id: int,
    **kwargs
) -> Optional[Test]:
    """Update test information"""
    try:
        test = get_test(db, test_id)
        if not test:
            return None
        
        for key, value in kwargs.items():
            if hasattr(test, key):
                setattr(test, key, value)
        
        db.commit()
        db.refresh(test)
        return test
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating test {test_id}: {e}")
        return None

def update_test_by_task_id(
    db: Session,
    task_id: str,
    views_sent: int = None,
    views_failed: int = None,
    status: str = None
) -> Optional[Test]:
    """Update test by task ID"""
    try:
        test = get_test_by_task_id(db, task_id)
        if not test:
            return None
        
        if views_sent is not None:
            test.views_sent = views_sent
        
        if views_failed is not None:
            test.views_failed = views_failed
        
        if status is not None:
            test.status = status
            if status == 'completed':
                test.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(test)
        return test
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating test {task_id}: {e}")
        return None

def get_user_tests(
    db: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[Test]:
    """Get tests for a user"""
    return db.query(Test)\
        .filter(Test.user_id == user_id)\
        .order_by(desc(Test.created_at))\
        .offset(offset)\
        .limit(limit)\
        .all()

def get_recent_tests(
    db: Session,
    hours: int = 24,
    limit: int = 100
) -> List[Test]:
    """Get recent tests"""
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    
    return db.query(Test)\
        .filter(Test.created_at >= time_threshold)\
        .order_by(desc(Test.created_at))\
        .limit(limit)\
        .all()

def get_test_statistics(
    db: Session,
    user_id: int = None
) -> Dict[str, Any]:
    """Get test statistics"""
    query = db.query(Test)
    
    if user_id:
        query = query.filter(Test.user_id == user_id)
    
    total_tests = query.count()
    total_views = db.query(func.sum(Test.view_count)).scalar() or 0
    total_sent = db.query(func.sum(Test.views_sent)).scalar() or 0
    total_failed = db.query(func.sum(Test.views_failed)).scalar() or 0
    
    # Get today's tests
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    
    today_tests = query.filter(Test.created_at >= today_start).count()
    today_views = db.query(func.sum(Test.view_count))\
        .filter(Test.created_at >= today_start)\
        .scalar() or 0
    
    # Calculate success rate
    success_rate = (total_sent / total_views * 100) if total_views > 0 else 0
    
    return {
        "total_tests": total_tests,
        "total_views": total_views,
        "total_sent": total_sent,
        "total_failed": total_failed,
        "success_rate": success_rate,
        "today_tests": today_tests,
        "today_views": today_views
    }

# ==================== ACCOUNT OPERATIONS ====================

def create_account(
    db: Session,
    username: str,
    password: str,
    email: str = None,
    phone: str = None,
    notes: str = None
) -> TikTokAccount:
    """Create a new TikTok account"""
    try:
        account = TikTokAccount(
            username=username,
            password=password,
            email=email,
            phone=phone,
            notes=notes
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        logger.info(f"Created account: {username}")
        return account
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating account: {e}")
        raise

def get_account(db: Session, account_id: int) -> Optional[TikTokAccount]:
    """Get account by ID"""
    return db.query(TikTokAccount).filter(TikTokAccount.id == account_id).first()

def get_account_by_username(db: Session, username: str) -> Optional[TikTokAccount]:
    """Get account by username"""
    return db.query(TikTokAccount).filter(TikTokAccount.username == username).first()

def update_account(
    db: Session,
    account_id: int,
    **kwargs
) -> Optional[TikTokAccount]:
    """Update account information"""
    try:
        account = get_account(db, account_id)
        if not account:
            return None
        
        for key, value in kwargs.items():
            if hasattr(account, key):
                setattr(account, key, value)
        
        db.commit()
        db.refresh(account)
        return account
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating account {account_id}: {e}")
        return None

def update_account_status(
    db: Session,
    account_id: int,
    status: str,
    notes: str = None
) -> Optional[TikTokAccount]:
    """Update account status"""
    try:
        account = get_account(db, account_id)
        if not account:
            return None
        
        account.status = status
        account.last_used = datetime.utcnow()
        
        if notes:
            account.notes = notes
        
        db.commit()
        db.refresh(account)
        return account
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating account status {account_id}: {e}")
        return None

def increment_account_views(
    db: Session,
    account_id: int,
    success: bool = True
) -> Optional[TikTokAccount]:
    """Increment account view count and update success rate"""
    try:
        account = get_account(db, account_id)
        if not account:
            return None
        
        account.view_count += 1
        
        # Update success rate
        if success:
            # Simplified success rate calculation
            account.success_rate = (account.success_rate * (account.view_count - 1) + 1) / account.view_count
        else:
            account.success_rate = (account.success_rate * (account.view_count - 1)) / account.view_count
        
        account.last_used = datetime.utcnow()
        db.commit()
        db.refresh(account)
        return account
    except Exception as e:
        db.rollback()
        logger.error(f"Error incrementing account views {account_id}: {e}")
        return None

def get_active_accounts(db: Session, limit: int = 100) -> List[TikTokAccount]:
    """Get active accounts"""
    return db.query(TikTokAccount)\
        .filter(TikTokAccount.status == 'active')\
        .order_by(TikTokAccount.last_used)\
        .limit(limit)\
        .all()

def get_banned_accounts(db: Session) -> List[TikTokAccount]:
    """Get banned accounts"""
    return db.query(TikTokAccount)\
        .filter(TikTokAccount.status == 'banned')\
        .all()

def get_account_statistics(db: Session) -> Dict[str, Any]:
    """Get account statistics"""
    total_accounts = db.query(TikTokAccount).count()
    active_accounts = db.query(TikTokAccount)\
        .filter(TikTokAccount.status == 'active')\
        .count()
    
    banned_accounts = db.query(TikTokAccount)\
        .filter(TikTokAccount.status == 'banned')\
        .count()
    
    total_views = db.query(func.sum(TikTokAccount.view_count)).scalar() or 0
    
    # Average success rate
    avg_success_rate = db.query(func.avg(TikTokAccount.success_rate)).scalar() or 0
    
    return {
        "total_accounts": total_accounts,
        "active_accounts": active_accounts,
        "banned_accounts": banned_accounts,
        "total_views": total_views,
        "average_success_rate": avg_success_rate
    }

# ==================== PROXY OPERATIONS ====================

def create_proxy(
    db: Session,
    proxy_url: str,
    proxy_type: str = "http",
    country: str = None,
    speed: float = None
) -> Proxy:
    """Create a new proxy"""
    try:
        proxy = Proxy(
            proxy_url=proxy_url,
            proxy_type=proxy_type,
            country=country,
            speed=speed
        )
        db.add(proxy)
        db.commit()
        db.refresh(proxy)
        logger.info(f"Created proxy: {proxy_url[:50]}...")
        return proxy
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating proxy: {e}")
        raise

def get_proxy(db: Session, proxy_id: int) -> Optional[Proxy]:
    """Get proxy by ID"""
    return db.query(Proxy).filter(Proxy.id == proxy_id).first()

def get_active_proxies(db: Session, limit: int = 100) -> List[Proxy]:
    """Get active proxies"""
    return db.query(Proxy)\
        .filter(Proxy.is_active == True)\
        .order_by(Proxy.speed)\
        .limit(limit)\
        .all()

def update_proxy(
    db: Session,
    proxy_id: int,
    **kwargs
) -> Optional[Proxy]:
    """Update proxy information"""
    try:
        proxy = get_proxy(db, proxy_id)
        if not proxy:
            return None
        
        for key, value in kwargs.items():
            if hasattr(proxy, key):
                setattr(proxy, key, value)
        
        proxy.last_tested = datetime.utcnow()
        db.commit()
        db.refresh(proxy)
        return proxy
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating proxy {proxy_id}: {e}")
        return None

def update_proxy_success_rate(
    db: Session,
    proxy_id: int,
    success: bool = True
) -> Optional[Proxy]:
    """Update proxy success rate"""
    try:
        proxy = get_proxy(db, proxy_id)
        if not proxy:
            return None
        
        # Simplified success rate update
        proxy.success_rate = (proxy.success_rate * 9 + (1 if success else 0)) / 10
        proxy.last_used = datetime.utcnow()
        
        db.commit()
        db.refresh(proxy)
        return proxy
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating proxy success rate {proxy_id}: {e}")
        return None

def get_proxy_statistics(db: Session) -> Dict[str, Any]:
    """Get proxy statistics"""
    total_proxies = db.query(Proxy).count()
    active_proxies = db.query(Proxy)\
        .filter(Proxy.is_active == True)\
        .count()
    
    avg_speed = db.query(func.avg(Proxy.speed)).scalar() or 0
    avg_success_rate = db.query(func.avg(Proxy.success_rate)).scalar() or 0
    
    # Count by type
    http_count = db.query(Proxy)\
        .filter(Proxy.proxy_type == 'http')\
        .count()
    
    https_count = db.query(Proxy)\
        .filter(Proxy.proxy_type == 'https')\
        .count()
    
    socks_count = db.query(Proxy)\
        .filter(Proxy.proxy_type.like('socks%'))\
        .count()
    
    return {
        "total_proxies": total_proxies,
        "active_proxies": active_proxies,
        "average_speed": avg_speed,
        "average_success_rate": avg_success_rate,
        "http_proxies": http_count,
        "https_proxies": https_count,
        "socks_proxies": socks_count
    }

# ==================== LOG OPERATIONS ====================

def create_log(
    db: Session,
    level: str,
    module: str,
    message: str
) -> SystemLog:
    """Create a system log"""
    try:
        log = SystemLog(
            level=level,
            module=module,
            message=message
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating log: {e}")
        raise

def get_recent_logs(
    db: Session,
    level: str = None,
    module: str = None,
    limit: int = 100
) -> List[SystemLog]:
    """Get recent logs with optional filtering"""
    query = db.query(SystemLog)
    
    if level:
        query = query.filter(SystemLog.level == level)
    
    if module:
        query = query.filter(SystemLog.module == module)
    
    return query\
        .order_by(desc(SystemLog.created_at))\
        .limit(limit)\
        .all()

def get_error_logs(
    db: Session,
    hours: int = 24,
    limit: int = 50
) -> List[SystemLog]:
    """Get error logs from specified hours"""
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    
    return db.query(SystemLog)\
        .filter(SystemLog.level == 'error')\
        .filter(SystemLog.created_at >= time_threshold)\
        .order_by(desc(SystemLog.created_at))\
        .limit(limit)\
        .all()

# ==================== BULK OPERATIONS ====================

def bulk_create_accounts(
    db: Session,
    accounts: List[Dict[str, str]]
) -> int:
    """Bulk create accounts"""
    created = 0
    try:
        for account_data in accounts:
            account = TikTokAccount(**account_data)
            db.add(account)
            created += 1
        
        db.commit()
        logger.info(f"Bulk created {created} accounts")
        return created
    except Exception as e:
        db.rollback()
        logger.error(f"Error bulk creating accounts: {e}")
        return 0

def bulk_create_proxies(
    db: Session,
    proxies: List[Dict[str, Any]]
) -> int:
    """Bulk create proxies"""
    created = 0
    try:
        for proxy_data in proxies:
            proxy = Proxy(**proxy_data)
            db.add(proxy)
            created += 1
        
        db.commit()
        logger.info(f"Bulk created {created} proxies")
        return created
    except Exception as e:
        db.rollback()
        logger.error(f"Error bulk creating proxies: {e}")
        return 0

def cleanup_old_data(
    db: Session,
    days: int = 30
) -> Dict[str, int]:
    """Cleanup old data"""
    try:
        time_threshold = datetime.utcnow() - timedelta(days=days)
        
        # Delete old logs
        old_logs = db.query(SystemLog)\
            .filter(SystemLog.created_at < time_threshold)\
            .delete()
        
        # Delete old completed tests
        old_tests = db.query(Test)\
            .filter(Test.status == 'completed')\
            .filter(Test.completed_at < time_threshold)\
            .delete()
        
        db.commit()
        
        return {
            "old_logs_deleted": old_logs,
            "old_tests_deleted": old_tests
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error cleaning up old data: {e}")
        return {"old_logs_deleted": 0, "old_tests_deleted": 0}

# ==================== DATABASE UTILITIES ====================

def get_database_stats(db: Session) -> Dict[str, Any]:
    """Get database statistics"""
    try:
        # Table counts
        users_count = db.query(User).count()
        tests_count = db.query(Test).count()
        accounts_count = db.query(TikTokAccount).count()
        proxies_count = db.query(Proxy).count()
        logs_count = db.query(SystemLog).count()
        
        # Database size (approximate)
        import os
        from config import DATABASE_PATH
        
        db_size = os.path.getsize(DATABASE_PATH) if os.path.exists(DATABASE_PATH) else 0
        
        return {
            "users": users_count,
            "tests": tests_count,
            "accounts": accounts_count,
            "proxies": proxies_count,
            "logs": logs_count,
            "total_records": users_count + tests_count + accounts_count + proxies_count + logs_count,
            "database_size_bytes": db_size,
            "database_size_mb": db_size / (1024 * 1024)
        }
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {}