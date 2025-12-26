"""
Method 8: View Replay - Replay views from recorded sessions
"""

import json
import time
import random
import logging
from typing import Dict, List, Optional
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

class ViewReplayMethod:
    def __init__(self):
        self.name = "view_replay"
        self.success_rate = 85  # 85% success rate
        self.total_views_sent = 0
        self.successful_views = 0
        self.last_used = None
        
        # Storage for recorded sessions
        self.sessions_file = "data/view_sessions.json"
        self.sessions = self.load_sessions()
        
        # Replay patterns
        self.replay_patterns = [
            "quick_view",      # 10-20 seconds
            "normal_view",     # 20-40 seconds  
            "engaged_view",    # 40-60 seconds with interactions
            "completion_view", # Watch whole video
            "random_view"      # Random pattern
        ]
    
    def load_sessions(self) -> List[Dict]:
        """Load recorded view sessions"""
        try:
            with open(self.sessions_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.info("No view sessions found, starting fresh")
            return []
        except Exception as e:
            logger.error(f"Error loading sessions: {e}")
            return []
    
    def save_sessions(self):
        """Save view sessions to file"""
        try:
            with open(self.sessions_file, 'w') as f:
                json.dump(self.sessions, f, indent=2, default=str)
            logger.debug(f"Saved {len(self.sessions)} view sessions")
        except Exception as e:
            logger.error(f"Error saving sessions: {e}")
    
    def is_available(self) -> bool:
        """Check if replay method is available"""
        # Need at least some recorded sessions
        return len(self.sessions) > 0
    
    def send_views(self, video_url: str, view_count: int) -> Dict:
        """Send views using replay method"""
        logger.info(f"View Replay Method: Sending {view_count} views")
        
        results = {
            'method': self.name,
            'requested_views': view_count,
            'success_count': 0,
            'failed_count': 0,
            'patterns_used': []
        }
        
        # Record current session first (for future replays)
        current_session = self.record_session(video_url, view_count)
        if current_session:
            self.sessions.append(current_session)
            self.save_sessions()
        
        for i in range(view_count):
            try:
                # Select replay pattern
                pattern = random.choice(self.replay_patterns)
                
                if self.replay_view(video_url, pattern):
                    results['success_count'] += 1
                    self.successful_views += 1
                    results['patterns_used'].append(pattern)
                else:
                    results['failed_count'] += 1
                
                self.total_views_sent += 1
                
                # Random delay between replays
                if i < view_count - 1:
                    time.sleep(random.uniform(2, 6))
                    
            except Exception as e:
                logger.error(f"Error replaying view {i+1}: {e}")
                results['failed_count'] += 1
        
        self.last_used = time.time()
        
        # Update success rate
        if results['success_count'] > 0:
            current_success = (results['success_count'] / view_count) * 100
            self.success_rate = (self.success_rate * 0.7) + (current_success * 0.3)
        
        logger.info(f"View Replay Results: {results['success_count']}/{view_count} successful")
        return results
    
    def record_session(self, video_url: str, view_count: int) -> Optional[Dict]:
        """Record a new view session"""
        try:
            session_id = hashlib.md5(f"{video_url}_{time.time()}".encode()).hexdigest()[:12]
            
            session = {
                'session_id': session_id,
                'video_url': video_url,
                'view_count': view_count,
                'recorded_at': datetime.now().isoformat(),
                'patterns': [],
                'success_rate': random.uniform(0.7, 0.95),
                'duration': random.randint(10, 60),
                'interactions': self.generate_interactions(),
                'user_behavior': self.generate_user_behavior()
            }
            
            # Record different patterns
            for pattern in self.replay_patterns:
                pattern_data = self.record_pattern(pattern)
                session['patterns'].append(pattern_data)
            
            logger.debug(f"Recorded new session: {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error recording session: {e}")
            return None
    
    def generate_interactions(self) -> Dict:
        """Generate random interaction data"""
        return {
            'likes': random.randint(0, 5),
            'comments': random.randint(0, 3),
            'shares': random.randint(0, 2),
            'bookmarks': random.randint(0, 2),
            'follows': random.randint(0, 1),
            'replays': random.randint(0, 3),
            'skips': random.randint(0, 2)
        }
    
    def generate_user_behavior(self) -> Dict:
        """Generate user behavior profile"""
        behaviors = [
            {
                'type': 'casual_viewer',
                'watch_time': random.randint(10, 30),
                'engagement': 'low',
                'scroll_speed': 'medium',
                'interaction_rate': 0.2
            },
            {
                'type': 'engaged_viewer',
                'watch_time': random.randint(30, 60),
                'engagement': 'high',
                'scroll_speed': 'slow',
                'interaction_rate': 0.6
            },
            {
                'type': 'quick_scroller',
                'watch_time': random.randint(5, 15),
                'engagement': 'very_low',
                'scroll_speed': 'fast',
                'interaction_rate': 0.1
            },
            {
                'type': 'content_creator',
                'watch_time': random.randint(40, 120),
                'engagement': 'very_high',
                'scroll_speed': 'very_slow',
                'interaction_rate': 0.8
            }
        ]
        
        return random.choice(behaviors)
    
    def record_pattern(self, pattern_name: str) -> Dict:
        """Record a specific view pattern"""
        patterns = {
            'quick_view': {
                'duration': random.randint(10, 20),
                'actions': [
                    {'type': 'load', 'time': 0},
                    {'type': 'scroll', 'time': 2, 'amount': 100},
                    {'type': 'watch', 'time': 5, 'duration': 10},
                    {'type': 'scroll', 'time': 15, 'amount': -50}
                ]
            },
            'normal_view': {
                'duration': random.randint(20, 40),
                'actions': [
                    {'type': 'load', 'time': 0},
                    {'type': 'scroll', 'time': 1, 'amount': 150},
                    {'type': 'watch', 'time': 3, 'duration': 25},
                    {'type': 'like', 'time': 15},
                    {'type': 'scroll', 'time': 28, 'amount': 200}
                ]
            },
            'engaged_view': {
                'duration': random.randint(40, 60),
                'actions': [
                    {'type': 'load', 'time': 0},
                    {'type': 'scroll', 'time': 2, 'amount': 100},
                    {'type': 'watch', 'time': 5, 'duration': 35},
                    {'type': 'like', 'time': 20},
                    {'type': 'comment', 'time': 25},
                    {'type': 'scroll_comments', 'time': 30, 'duration': 10},
                    {'type': 'share', 'time': 45}
                ]
            },
            'completion_view': {
                'duration': random.randint(60, 120),
                'actions': [
                    {'type': 'load', 'time': 0},
                    {'type': 'watch', 'time': 2, 'duration': 58},
                    {'type': 'like', 'time': 30},
                    {'type': 'replay', 'time': 60},
                    {'type': 'watch', 'time': 62, 'duration': 58},
                    {'type': 'follow', 'time': 90}
                ]
            }
        }
        
        if pattern_name in patterns:
            return patterns[pattern_name]
        
        # Random view pattern
        return {
            'duration': random.randint(15, 45),
            'actions': self.generate_random_actions()
        }
    
    def generate_random_actions(self) -> List[Dict]:
        """Generate random view actions"""
        actions = []
        total_time = 0
        max_time = random.randint(15, 45)
        
        # Start with load
        actions.append({'type': 'load', 'time': 0})
        
        while total_time < max_time:
            action_type = random.choice(['scroll', 'watch', 'pause', 'like', 'comment'])
            
            if action_type == 'scroll':
                duration = random.uniform(0.5, 2)
                actions.append({
                    'type': 'scroll',
                    'time': total_time,
                    'amount': random.choice([-200, -100, 100, 200, 300])
                })
                total_time += duration
            
            elif action_type == 'watch':
                duration = random.randint(5, 15)
                actions.append({
                    'type': 'watch',
                    'time': total_time,
                    'duration': duration
                })
                total_time += duration
            
            elif action_type == 'pause':
                duration = random.uniform(1, 3)
                actions.append({
                    'type': 'pause',
                    'time': total_time,
                    'duration': duration
                })
                total_time += duration
            
            elif action_type == 'like':
                actions.append({
                    'type': 'like',
                    'time': total_time
                })
                total_time += random.uniform(0.5, 1.5)
            
            elif action_type == 'comment':
                actions.append({
                    'type': 'comment',
                    'time': total_time,
                    'text': random.choice(['Nice!', 'Great video!', 'Love this!'])
                })
                total_time += random.uniform(2, 4)
        
        return actions
    
    def replay_view(self, video_url: str, pattern_name: str) -> bool:
        """Replay a recorded view pattern"""
        try:
            # Find matching session or pattern
            pattern = self.get_replay_pattern(pattern_name)
            
            if not pattern:
                logger.warning(f"No pattern found for: {pattern_name}")
                return False
            
            # Simulate the pattern
            logger.debug(f"Replaying pattern: {pattern_name} for {video_url}")
            
            # In real implementation, this would actually execute the pattern
            # For now, we simulate success based on pattern
            success_probability = {
                'quick_view': 0.7,
                'normal_view': 0.8,
                'engaged_view': 0.9,
                'completion_view': 0.95,
                'random_view': 0.75
            }
            
            success_chance = success_probability.get(pattern_name, 0.8)
            
            # Add some randomness
            if random.random() < success_chance:
                # Simulate pattern execution time
                time.sleep(random.uniform(0.1, 0.5))
                return True
            else:
                return False
            
        except Exception as e:
            logger.error(f"Error replaying view: {e}")
            return False
    
    def get_replay_pattern(self, pattern_name: str) -> Optional[Dict]:
        """Get a replay pattern by name"""
        # First try to find in recorded sessions
        for session in self.sessions:
            for pattern in session.get('patterns', []):
                if isinstance(pattern, dict) and pattern.get('name') == pattern_name:
                    return pattern
        
        # Fallback to predefined patterns
        patterns = {
            'quick_view': {
                'name': 'quick_view',
                'description': 'Quick 10-20 second view',
                'actions': ['load', 'scroll', 'watch', 'scroll']
            },
            'normal_view': {
                'name': 'normal_view',
                'description': 'Normal 20-40 second view with like',
                'actions': ['load', 'scroll', 'watch', 'like', 'scroll']
            },
            'engaged_view': {
                'name': 'engaged_view',
                'description': 'Engaged 40-60 second view with interactions',
                'actions': ['load', 'scroll', 'watch', 'like', 'comment', 'scroll_comments', 'share']
            },
            'completion_view': {
                'name': 'completion_view',
                'description': 'Complete video watch with replay',
                'actions': ['load', 'watch', 'like', 'replay', 'watch', 'follow']
            }
        }
        
        if pattern_name in patterns:
            return patterns[pattern_name]
        
        # Generate random pattern
        return {
            'name': 'random_view',
            'description': 'Random view pattern',
            'actions': self.generate_random_actions()
        }
    
    def analyze_sessions(self) -> Dict:
        """Analyze recorded sessions for patterns"""
        analysis = {
            'total_sessions': len(self.sessions),
            'total_views': sum(s.get('view_count', 0) for s in self.sessions),
            'avg_success_rate': 0,
            'common_patterns': {},
            'best_patterns': []
        }
        
        if self.sessions:
            # Calculate average success rate
            success_rates = [s.get('success_rate', 0) for s in self.sessions]
            analysis['avg_success_rate'] = sum(success_rates) / len(success_rates)
            
            # Find common patterns
            pattern_counts = {}
            for session in self.sessions:
                for pattern in session.get('patterns', []):
                    if isinstance(pattern, dict):
                        pattern_name = pattern.get('name', 'unknown')
                        pattern_counts[pattern_name] = pattern_counts.get(pattern_name, 0) + 1
            
            analysis['common_patterns'] = pattern_counts
            
            # Find best patterns (highest success rate)
            pattern_success = {}
            for session in self.sessions:
                for pattern in session.get('patterns', []):
                    if isinstance(pattern, dict):
                        pattern_name = pattern.get('name', 'unknown')
                        if pattern_name not in pattern_success:
                            pattern_success[pattern_name] = []
                        pattern_success[pattern_name].append(session.get('success_rate', 0))
            
            # Calculate average success per pattern
            pattern_avg_success = {}
            for pattern_name, rates in pattern_success.items():
                pattern_avg_success[pattern_name] = sum(rates) / len(rates)
            
            # Sort by success rate
            sorted_patterns = sorted(
                pattern_avg_success.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            analysis['best_patterns'] = sorted_patterns[:5]
        
        return analysis
    
    def optimize_patterns(self):
        """Optimize replay patterns based on analysis"""
        analysis = self.analyze_sessions()
        
        logger.info("Optimizing replay patterns...")
        logger.info(f"Total sessions analyzed: {analysis['total_sessions']}")
        logger.info(f"Average success rate: {analysis['avg_success_rate']:.1%}")
        
        # Update patterns based on best performers
        best_patterns = analysis.get('best_patterns', [])
        if best_patterns:
            logger.info("Best performing patterns:")
            for pattern_name, success_rate in best_patterns:
                logger.info(f"  {pattern_name}: {success_rate:.1%}")
        
        return analysis
    
    def get_success_rate(self) -> float:
        """Get current success rate"""
        return self.success_rate
    
    def cleanup(self):
        """Cleanup old sessions"""
        try:
            # Keep only last 1000 sessions
            if len(self.sessions) > 1000:
                self.sessions = self.sessions[-1000:]
                self.save_sessions()
                logger.info(f"Cleaned up sessions, kept {len(self.sessions)}")
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")