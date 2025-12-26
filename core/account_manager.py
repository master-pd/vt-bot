"""
Advanced Account Manager
Professional TikTok account management with encryption
"""

import asyncio
import json
import hashlib
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

from utils.logger import setup_logger
from utils.file_handler import FileHandler
from database.crud import (
    create_account, get_account_by_username, update_account,
    get_active_accounts, get_banned_accounts, update_account_status,
    increment_account_views, bulk_create_accounts
)
from database.models import SessionLocal
from config import ACCOUNTS_DIR, Colors

logger = setup_logger(__name__)

@dataclass
class AccountInfo:
    """Account information container"""
    username: str
    password: str
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str = "active"  # active, banned, limited, inactive
    view_count: int = 0
    success_rate: float = 0.0
    last_used: Optional[datetime] = None
    created_at: datetime = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "username": self.username,
            "password": self.password,
            "email": self.email,
            "phone": self.phone,
            "status": self.status,
            "view_count": self.view_count,
            "success_rate": self.success_rate,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AccountInfo':
        """Create from dictionary"""
        return cls(
            username=data.get("username", ""),
            password=data.get("password", ""),
            email=data.get("email"),
            phone=data.get("phone"),
            status=data.get("status", "active"),
            view_count=data.get("view_count", 0),
            success_rate=data.get("success_rate", 0.0),
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            notes=data.get("notes")
        )

class AccountEncryption:
    """Account data encryption handler"""
    
    def __init__(self, key_file: Path = ACCOUNTS_DIR / ".encryption_key"):
        self.key_file = key_file
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)
    
    def _load_or_generate_key(self) -> bytes:
        """Load existing key or generate new one"""
        if self.key_file.exists():
            try:
                with open(self.key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error loading encryption key: {e}")
        
        # Generate new key
        key = Fernet.generate_key()
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.key_file, 'wb') as f:
            f.write(key)
        
        logger.info("Generated new encryption key")
        return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt data"""
        encrypted = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data"""
        encrypted = base64.urlsafe_b64decode(encrypted_data.encode())
        return self.cipher.decrypt(encrypted).decode()
    
    def encrypt_account(self, account: AccountInfo) -> Dict[str, Any]:
        """Encrypt sensitive account data"""
        encrypted_data = {
            "username": account.username,  # Keep username unencrypted for searching
            "password": self.encrypt(account.password),
            "email": self.encrypt(account.email) if account.email else None,
            "phone": self.encrypt(account.phone) if account.phone else None,
            "status": account.status,
            "view_count": account.view_count,
            "success_rate": account.success_rate,
            "last_used": account.last_used.isoformat() if account.last_used else None,
            "created_at": account.created_at.isoformat() if account.created_at else None,
            "notes": account.notes
        }
        return encrypted_data
    
    def decrypt_account(self, encrypted_data: Dict[str, Any]) -> AccountInfo:
        """Decrypt account data"""
        return AccountInfo(
            username=encrypted_data["username"],
            password=self.decrypt(encrypted_data["password"]),
            email=self.decrypt(encrypted_data["email"]) if encrypted_data.get("email") else None,
            phone=self.decrypt(encrypted_data["phone"]) if encrypted_data.get("phone") else None,
            status=encrypted_data.get("status", "active"),
            view_count=encrypted_data.get("view_count", 0),
            success_rate=encrypted_data.get("success_rate", 0.0),
            last_used=datetime.fromisoformat(encrypted_data["last_used"]) if encrypted_data.get("last_used") else None,
            created_at=datetime.fromisoformat(encrypted_data["created_at"]) if encrypted_data.get("created_at") else datetime.now(),
            notes=encrypted_data.get("notes")
        )

class AccountManager:
    """Advanced account manager with encryption"""
    
    def __init__(self):
        self.encryption = AccountEncryption()
        self.file_handler = FileHandler(ACCOUNTS_DIR)
        self.accounts_file = ACCOUNTS_DIR / "accounts_encrypted.json"
        self.rotation_index = 0
        self.accounts_cache: List[AccountInfo] = []
        
    async def initialize(self):
        """Initialize account manager"""
        logger.info("Initializing Account Manager...")
        
        # Load accounts from file
        await self.load_accounts_from_file()
        
        # Sync with database
        await self.sync_with_database()
        
        logger.info(f"Account Manager initialized with {len(self.accounts_cache)} accounts")
    
    async def load_accounts_from_file(self):
        """Load accounts from encrypted file"""
        try:
            if await self.file_handler.file_exists(self.accounts_file):
                encrypted_data = await self.file_handler.read_json(self.accounts_file)
                
                self.accounts_cache = []
                for acc_data in encrypted_data:
                    try:
                        account = self.encryption.decrypt_account(acc_data)
                        self.accounts_cache.append(account)
                    except Exception as e:
                        logger.error(f"Error decrypting account: {e}")
                
                logger.info(f"Loaded {len(self.accounts_cache)} accounts from file")
            else:
                logger.info("No accounts file found, starting fresh")
                self.accounts_cache = []
                
        except Exception as e:
            logger.error(f"Error loading accounts from file: {e}")
            self.accounts_cache = []
    
    async def save_accounts_to_file(self):
        """Save accounts to encrypted file"""
        try:
            encrypted_data = []
            for account in self.accounts_cache:
                encrypted_acc = self.encryption.encrypt_account(account)
                encrypted_data.append(encrypted_acc)
            
            await self.file_handler.write_json(self.accounts_file, encrypted_data)
            logger.info(f"Saved {len(self.accounts_cache)} accounts to file")
            
        except Exception as e:
            logger.error(f"Error saving accounts to file: {e}")
    
    async def sync_with_database(self):
        """Sync accounts with database"""
        try:
            db = SessionLocal()
            
            # Add accounts from cache to database
            for account in self.accounts_cache:
                existing = get_account_by_username(db, account.username)
                
                if not existing:
                    create_account(
                        db,
                        username=account.username,
                        password=account.password,  # Store encrypted in real implementation
                        email=account.email,
                        phone=account.phone,
                        notes=account.notes
                    )
            
            db.commit()
            logger.info("Synced accounts with database")
            
        except Exception as e:
            logger.error(f"Error syncing with database: {e}")
        finally:
            db.close()
    
    async def add_account(
        self,
        username: str,
        password: str,
        email: str = None,
        phone: str = None,
        notes: str = None
    ) -> bool:
        """Add a new account"""
        try:
            # Check if account already exists
            existing = await self.get_account(username)
            if existing:
                logger.warning(f"Account {username} already exists")
                return False
            
            # Create new account
            account = AccountInfo(
                username=username,
                password=password,
                email=email,
                phone=phone,
                status="active",
                created_at=datetime.now(),
                notes=notes
            )
            
            # Add to cache
            self.accounts_cache.append(account)
            
            # Save to file
            await self.save_accounts_to_file()
            
            # Add to database
            db = SessionLocal()
            try:
                create_account(
                    db,
                    username=username,
                    password=password,
                    email=email,
                    phone=phone,
                    notes=notes
                )
                db.commit()
            except Exception as e:
                logger.error(f"Error adding account to database: {e}")
                db.rollback()
            finally:
                db.close()
            
            logger.info(f"Added account: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding account {username}: {e}")
            return False
    
    async def add_accounts_bulk(self, accounts_data: List[Dict[str, str]]) -> int:
        """Add multiple accounts at once"""
        added_count = 0
        
        for acc_data in accounts_data:
            success = await self.add_account(
                username=acc_data.get("username", ""),
                password=acc_data.get("password", ""),
                email=acc_data.get("email"),
                phone=acc_data.get("phone"),
                notes=acc_data.get("notes")
            )
            
            if success:
                added_count += 1
        
        logger.info(f"Added {added_count} accounts in bulk")
        return added_count
    
    async def get_account(self, username: str) -> Optional[AccountInfo]:
        """Get account by username"""
        for account in self.accounts_cache:
            if account.username == username:
                return account
        return None
    
    async def get_next_account(self) -> Optional[AccountInfo]:
        """Get next account for rotation (round-robin)"""
        if not self.accounts_cache:
            return None
        
        # Filter active accounts
        active_accounts = [
            acc for acc in self.accounts_cache 
            if acc.status == "active" and acc.view_count < 1000  # Limit per account
        ]
        
        if not active_accounts:
            logger.warning("No active accounts available")
            return None
        
        # Round-robin selection
        account = active_accounts[self.rotation_index % len(active_accounts)]
        self.rotation_index += 1
        
        # Update last used
        account.last_used = datetime.now()
        
        # Save changes
        await self.save_accounts_to_file()
        
        return account
    
    async def update_account_status(
        self,
        username: str,
        status: str,
        notes: str = None
    ) -> bool:
        """Update account status"""
        try:
            account = await self.get_account(username)
            if not account:
                return False
            
            account.status = status
            account.last_used = datetime.now()
            
            if notes:
                account.notes = notes
            
            # Update in database
            db = SessionLocal()
            try:
                update_account_status(db, self._get_account_id(username), status, notes)
                db.commit()
            except Exception as e:
                logger.error(f"Error updating account status in database: {e}")
                db.rollback()
            finally:
                db.close()
            
            await self.save_accounts_to_file()
            logger.info(f"Updated account {username} status to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating account status: {e}")
            return False
    
    async def increment_account_views(self, username: str, success: bool = True) -> bool:
        """Increment account view count"""
        try:
            account = await self.get_account(username)
            if not account:
                return False
            
            account.view_count += 1
            account.last_used = datetime.now()
            
            # Update success rate (simple moving average)
            if success:
                account.success_rate = (account.success_rate * (account.view_count - 1) + 1) / account.view_count
            else:
                account.success_rate = (account.success_rate * (account.view_count - 1)) / account.view_count
            
            # Update in database
            db = SessionLocal()
            try:
                account_id = self._get_account_id(username)
                if account_id:
                    from database.crud import increment_account_views as db_increment
                    db_increment(db, account_id, success)
                    db.commit()
            except Exception as e:
                logger.error(f"Error updating account views in database: {e}")
                db.rollback()
            finally:
                db.close()
            
            await self.save_accounts_to_file()
            return True
            
        except Exception as e:
            logger.error(f"Error incrementing account views: {e}")
            return False
    
    async def remove_account(self, username: str) -> bool:
        """Remove account"""
        try:
            account = await self.get_account(username)
            if not account:
                return False
            
            # Remove from cache
            self.accounts_cache = [acc for acc in self.accounts_cache if acc.username != username]
            
            # Save changes
            await self.save_accounts_to_file()
            
            logger.info(f"Removed account: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing account {username}: {e}")
            return False
    
    async def clean_banned_accounts(self) -> int:
        """Remove banned accounts"""
        try:
            banned_accounts = [acc for acc in self.accounts_cache if acc.status == "banned"]
            
            for account in banned_accounts:
                await self.remove_account(account.username)
            
            logger.info(f"Cleaned {len(banned_accounts)} banned accounts")
            return len(banned_accounts)
            
        except Exception as e:
            logger.error(f"Error cleaning banned accounts: {e}")
            return 0
    
    async def export_accounts(self, format: str = "json") -> str:
        """Export accounts to specified format"""
        try:
            if format == "json":
                data = [acc.to_dict() for acc in self.accounts_cache]
                return json.dumps(data, indent=2, default=str)
            
            elif format == "csv":
                import csv
                from io import StringIO
                
                output = StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow([
                    "username", "password", "email", "phone", 
                    "status", "view_count", "success_rate", 
                    "last_used", "created_at", "notes"
                ])
                
                # Write data
                for account in self.accounts_cache:
                    writer.writerow([
                        account.username,
                        account.password,
                        account.email or "",
                        account.phone or "",
                        account.status,
                        account.view_count,
                        f"{account.success_rate:.2f}",
                        account.last_used.isoformat() if account.last_used else "",
                        account.created_at.isoformat() if account.created_at else "",
                        account.notes or ""
                    ])
                
                return output.getvalue()
            
            elif format == "txt":
                lines = []
                for account in self.accounts_cache:
                    lines.append(f"Username: {account.username}")
                    lines.append(f"Password: {account.password}")
                    lines.append(f"Status: {account.status}")
                    lines.append(f"Views: {account.view_count}")
                    lines.append(f"Success Rate: {account.success_rate:.1f}%")
                    lines.append(f"Last Used: {account.last_used}" if account.last_used else "Never Used")
                    lines.append("-" * 40)
                
                return "\n".join(lines)
            
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting accounts: {e}")
            return ""
    
    async def import_accounts(self, file_path: Path, format: str = "json") -> int:
        """Import accounts from file"""
        try:
            if not await self.file_handler.file_exists(file_path):
                logger.error(f"File not found: {file_path}")
                return 0
            
            content = await self.file_handler.read_file(file_path)
            
            if format == "json":
                accounts_data = json.loads(content)
            elif format == "csv":
                import csv
                from io import StringIO
                
                reader = csv.DictReader(StringIO(content))
                accounts_data = list(reader)
            elif format == "txt":
                # Parse simple username:password format
                accounts_data = []
                for line in content.splitlines():
                    if ":" in line:
                        parts = line.strip().split(":", 1)
                        if len(parts) == 2:
                            accounts_data.append({
                                "username": parts[0].strip(),
                                "password": parts[1].strip()
                            })
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # Add accounts
            added = await self.add_accounts_bulk(accounts_data)
            logger.info(f"Imported {added} accounts from {file_path}")
            return added
            
        except Exception as e:
            logger.error(f"Error importing accounts: {e}")
            return 0
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get account statistics"""
        total = len(self.accounts_cache)
        
        status_counts = {}
        for account in self.accounts_cache:
            status_counts[account.status] = status_counts.get(account.status, 0) + 1
        
        total_views = sum(acc.view_count for acc in self.accounts_cache)
        
        active_accounts = [acc for acc in self.accounts_cache if acc.status == "active"]
        avg_success_rate = sum(acc.success_rate for acc in active_accounts) / len(active_accounts) if active_accounts else 0
        
        return {
            "total_accounts": total,
            "status_counts": status_counts,
            "active_accounts": len(active_accounts),
            "banned_accounts": status_counts.get("banned", 0),
            "total_views": total_views,
            "average_success_rate": avg_success_rate,
            "recently_used": len([acc for acc in self.accounts_cache 
                                 if acc.last_used and 
                                 (datetime.now() - acc.last_used).days < 1])
        }
    
    async def validate_account(self, username: str, password: str) -> bool:
        """Validate account credentials"""
        try:
            account = await self.get_account(username)
            if not account:
                return False
            
            return account.password == password
            
        except Exception as e:
            logger.error(f"Error validating account: {e}")
            return False
    
    async def search_accounts(self, query: str, field: str = "username") -> List[AccountInfo]:
        """Search accounts"""
        results = []
        
        for account in self.accounts_cache:
            value = getattr(account, field, "")
            if value and query.lower() in str(value).lower():
                results.append(account)
        
        return results
    
    def _get_account_id(self, username: str) -> Optional[int]:
        """Get database ID for account"""
        try:
            db = SessionLocal()
            account = get_account_by_username(db, username)
            return account.id if account else None
        except Exception:
            return None
        finally:
            db.close()
    
    async def backup_accounts(self) -> bool:
        """Create backup of accounts"""
        try:
            backup_file = ACCOUNTS_DIR / f"backup/accounts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            await self.file_handler.create_directory(backup_file.parent)
            
            encrypted_data = []
            for account in self.accounts_cache:
                encrypted_acc = self.encryption.encrypt_account(account)
                encrypted_data.append(encrypted_acc)
            
            await self.file_handler.write_json(backup_file, encrypted_data)
            logger.info(f"Created accounts backup: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False