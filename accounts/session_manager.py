"""
Session Manager - Manage TikTok sessions and cookies
"""

import json
import time
import logging
import pickle
from typing import Dict, List, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self, session_dir: str = "temp/sessions"):
        self.session_dir = session_dir
        self.sessions = {}
        self.ensure_directory()
        self.load_sessions()
    
    def ensure_directory(self):
        """Ensure session directory exists"""
        os.makedirs(self.session_dir, exist_ok=True)
    
    def load_sessions(self):
        """Load all saved sessions"""
        try:
            session_files = [f for f in os.listdir(self.session_dir) 
                           if f.endswith('.json') or f.endswith('.pkl')]
            
            for filename in session_files:
                session_id = filename.split('.')[0]
                filepath = os.path.join(self.session_dir, filename)
                
                try:
                    if filename.endswith('.json'):
                        with open(filepath, 'r') as f:
                            session_data = json.load(f)
                    else:  # .pkl
                        with open(filepath, 'rb') as f:
                            session_data = pickle.load(f)
                    
                    self.sessions[session_id] = session_data
                    logger.debug(f"Loaded session: {session_id}")
                    
                except Exception as e:
                    logger.error(f"Error loading session {filename}: {e}")
            
            logger.info(f"Loaded {len(self.sessions)} sessions")
            
        except Exception as e:
            logger.error(f"Error loading sessions: {e}")
            self.sessions = {}
    
    def save_session(self, session_id: str, session_data: Dict, format: str = "json"):
        """Save session to file"""
        try:
            filepath = os.path.join(self.session_dir, f"{session_id}.{format}")
            
            if format == "json":
                with open(filepath, 'w') as f:
                    json.dump(session_data, f, indent=2, default=str)
            else:  # pickle
                with open(filepath, 'wb') as f:
                    pickle.dump(session_data, f)
            
            self.sessions[session_id] = session_data
            logger.debug(f"Saved session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving session {session_id}: {e}")
            return False
    
    def create_session(self, account_data: Dict) -> str:
        """Create new session from account data"""
        session_id = f"session_{int(time.time())}_{account_data.get('username', 'unknown')}"
        
        session_data = {
            'session_id': session_id,
            'account_id': account_data.get('account_id', ''),
            'username': account_data.get('username', ''),
            'cookies': account_data.get('cookies', {}),
            'user_agent': account_data.get('user_agent', ''),
            'created_at': datetime.now().isoformat(),
            'last_used': datetime.now().isoformat(),
            'usage_count': 0,
            'success_count': 0,
            'fail_count': 0,
            'is_active': True
        }
        
        if self.save_session(session_id, session_data):
            return session_id
        
        return ""
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        if session_id in self.sessions:
            # Update last used
            self.sessions[session_id]['last_used'] = datetime.now().isoformat()
            self.save_session(session_id, self.sessions[session_id])
            
            return self.sessions[session_id]
        
        return None
    
    def get_active_sessions(self) -> List[Dict]:
        """Get all active sessions"""
        active_sessions = []
        
        for session_id, session_data in self.sessions.items():
            if session_data.get('is_active', True):
                # Check if session is expired
                last_used = datetime.fromisoformat(session_data['last_used'])
                hours_since_use = (datetime.now() - last_used).total_seconds() / 3600
                
                if hours_since_use < 24:  # Sessions expire after 24 hours
                    active_sessions.append(session_data)
                else:
                    # Mark as inactive
                    session_data['is_active'] = False
                    self.save_session(session_id, session_data)
        
        return active_sessions
    
    def update_session_stats(self, session_id: str, success: bool):
        """Update session statistics"""
        if session_id in self.sessions:
            session_data = self.sessions[session_id]
            
            session_data['usage_count'] += 1
            session_data['last_used'] = datetime.now().isoformat()
            
            if success:
                session_data['success_count'] += 1
            else:
                session_data['fail_count'] += 1
            
            # Calculate success rate
            total = session_data['success_count'] + session_data['fail_count']
            if total > 0:
                session_data['success_rate'] = (session_data['success_count'] / total) * 100
            
            # Mark as inactive if too many failures
            if session_data['fail_count'] > 10 and session_data['success_rate'] < 20:
                session_data['is_active'] = False
                logger.warning(f"Session {session_id} marked as inactive due to failures")
            
            self.save_session(session_id, session_data)
    
    def rotate_session(self, current_session_id: str = "") -> Optional[Dict]:
        """Rotate to next available session"""
        active_sessions = self.get_active_sessions()
        
        if not active_sessions:
            logger.warning("No active sessions available")
            return None
        
        # Sort by usage count (use less used sessions first)
        active_sessions.sort(key=lambda x: x.get('usage_count', 0))
        
        # Don't return the same session if specified
        if current_session_id:
            for session in active_sessions:
                if session['session_id'] != current_session_id:
                    return session
        
        return active_sessions[0] if active_sessions else None
    
    def cleanup_old_sessions(self, max_age_hours: int = 48):
        """Cleanup old session files"""
        try:
            current_time = time.time()
            deleted_count = 0
            
            for filename in os.listdir(self.session_dir):
                filepath = os.path.join(self.session_dir, filename)
                
                # Get file age
                file_age = current_time - os.path.getmtime(filepath)
                
                # Delete if older than threshold
                if file_age > (max_age_hours * 3600):
                    os.remove(filepath)
                    
                    # Remove from memory
                    session_id = filename.split('.')[0]
                    if session_id in self.sessions:
                        del self.sessions[session_id]
                    
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old sessions")
                
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
    
    def export_sessions(self, output_file: str = "sessions_export.json"):
        """Export all sessions to file"""
        try:
            with open(output_file, 'w') as f:
                json.dump(self.sessions, f, indent=2, default=str)
            
            logger.info(f"Exported {len(self.sessions)} sessions to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error exporting sessions: {e}")
            return False
    
    def import_sessions(self, import_file: str):
        """Import sessions from file"""
        try:
            with open(import_file, 'r') as f:
                imported_sessions = json.load(f)
            
            # Merge with existing sessions
            for session_id, session_data in imported_sessions.items():
                self.sessions[session_id] = session_data
                self.save_session(session_id, session_data)
            
            logger.info(f"Imported {len(imported_sessions)} sessions from {import_file}")
            return True
        except Exception as e:
            logger.error(f"Error importing sessions: {e}")
            return False
    
    def get_session_stats(self) -> Dict:
        """Get session statistics"""
        total_sessions = len(self.sessions)
        active_sessions = len(self.get_active_sessions())
        
        total_usage = sum(s.get('usage_count', 0) for s in self.sessions.values())
        total_success = sum(s.get('success_count', 0) for s in self.sessions.values())
        
        avg_success_rate = 0
        if total_usage > 0:
            avg_success_rate = (total_success / total_usage) * 100
        
        return {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'inactive_sessions': total_sessions - active_sessions,
            'total_usage': total_usage,
            'total_success': total_success,
            'average_success_rate': avg_success_rate
        }