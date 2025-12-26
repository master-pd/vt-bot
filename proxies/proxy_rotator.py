"""
Proxy Rotator - Intelligent proxy rotation system
"""

import time
import random
import logging
from typing import List, Dict, Optional, Tuple
from collections import deque, defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)

class ProxyRotator:
    def __init__(self, proxy_file: str = "proxies/proxies.txt"):
        self.proxy_file = proxy_file
        self.proxies = []
        self.proxy_stats = {}
        self.rotation_history = deque(maxlen=1000)
        
        # Rotation strategies
        self.strategies = {
            'random': self.random_rotation,
            'round_robin': self.round_robin_rotation,
            'weighted': self.weighted_rotation,
            'smart': self.smart_rotation,
            'sticky': self.sticky_rotation
        }
        
        # Current strategy
        self.current_strategy = 'smart'
        
        # Load proxies
        self.load_proxies()
    
    def load_proxies(self) -> int:
        """Load proxies from file"""
        try:
            with open(self.proxy_file, 'r') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
            
            # Initialize stats for new proxies
            for proxy in self.proxies:
                if proxy not in self.proxy_stats:
                    self.proxy_stats[proxy] = {
                        'total_uses': 0,
                        'successful_uses': 0,
                        'failed_uses': 0,
                        'total_response_time': 0,
                        'last_used': 0,
                        'last_success': 0,
                        'consecutive_failures': 0,
                        'is_active': True,
                        'weight': 1.0
                    }
            
            logger.info(f"Loaded {len(self.proxies)} proxies")
            return len(self.proxies)
            
        except FileNotFoundError:
            logger.warning(f"Proxy file not found: {self.proxy_file}")
            self.proxies = []
            return 0
        except Exception as e:
            logger.error(f"Error loading proxies: {e}")
            self.proxies = []
            return 0
    
    def save_proxies(self):
        """Save proxies to file"""
        try:
            with open(self.proxy_file, 'w') as f:
                for proxy in self.proxies:
                    f.write(f"{proxy}\n")
            
            logger.debug(f"Saved {len(self.proxies)} proxies to file")
        except Exception as e:
            logger.error(f"Error saving proxies: {e}")
    
    def get_proxy(self, strategy: str = None, exclude: List[str] = None) -> Optional[str]:
        """Get next proxy based on rotation strategy"""
        if not self.proxies:
            logger.warning("No proxies available")
            return None
        
        if exclude is None:
            exclude = []
        
        # Filter available proxies
        available_proxies = [
            p for p in self.proxies 
            if p not in exclude and self.proxy_stats.get(p, {}).get('is_active', True)
        ]
        
        if not available_proxies:
            logger.warning("No active proxies available")
            # Try including inactive ones
            available_proxies = [p for p in self.proxies if p not in exclude]
            
            if not available_proxies:
                return None
        
        # Select strategy
        if strategy is None:
            strategy = self.current_strategy
        
        rotation_func = self.strategies.get(strategy, self.smart_rotation)
        selected_proxy = rotation_func(available_proxies)
        
        if selected_proxy:
            # Update stats
            self.update_proxy_usage(selected_proxy)
            
            # Record rotation
            self.rotation_history.append({
                'proxy': selected_proxy,
                'timestamp': time.time(),
                'strategy': strategy
            })
        
        return selected_proxy
    
    def random_rotation(self, available_proxies: List[str]) -> str:
        """Random proxy selection"""
        return random.choice(available_proxies) if available_proxies else None
    
    def round_robin_rotation(self, available_proxies: List[str]) -> str:
        """Round-robin proxy selection"""
        if not hasattr(self, 'round_robin_index'):
            self.round_robin_index = 0
        
        if available_proxies:
            proxy = available_proxies[self.round_robin_index % len(available_proxies)]
            self.round_robin_index += 1
            return proxy
        
        return None
    
    def weighted_rotation(self, available_proxies: List[str]) -> str:
        """Weighted random selection based on success rate"""
        if not available_proxies:
            return None
        
        # Calculate weights
        weights = []
        for proxy in available_proxies:
            stats = self.proxy_stats.get(proxy, {})
            
            # Base weight from success rate
            total_uses = stats.get('total_uses', 0)
            if total_uses > 0:
                success_rate = stats.get('successful_uses', 0) / total_uses
            else:
                success_rate = 0.5  # Default for untested proxies
            
            # Adjust for recent failures
            consecutive_failures = stats.get('consecutive_failures', 0)
            failure_penalty = max(0.1, 1.0 - (consecutive_failures * 0.2))
            
            # Adjust for recency (prefer recently used successful proxies)
            last_success = stats.get('last_success', 0)
            recency_bonus = 1.0
            if last_success > 0:
                hours_since_success = (time.time() - last_success) / 3600
                if hours_since_success < 1:
                    recency_bonus = 1.2
                elif hours_since_success < 24:
                    recency_bonus = 1.1
            
            weight = success_rate * failure_penalty * recency_bonus
            weights.append(max(0.1, weight))  # Minimum weight
        
        # Weighted random selection
        return random.choices(available_proxies, weights=weights, k=1)[0]
    
    def smart_rotation(self, available_proxies: List[str]) -> str:
        """Smart rotation combining multiple factors"""
        if not available_proxies:
            return None
        
        # Score each proxy
        proxy_scores = {}
        
        for proxy in available_proxies:
            stats = self.proxy_stats.get(proxy, {})
            score = 0.0
            
            # 1. Success rate (40% weight)
            total_uses = stats.get('total_uses', 0)
            if total_uses > 0:
                success_rate = stats.get('successful_uses', 0) / total_uses
                score += success_rate * 0.4
            else:
                score += 0.2  # Bonus for untested proxies
            
            # 2. Response time (30% weight)
            avg_response_time = 0
            if total_uses > 0:
                avg_response_time = stats.get('total_response_time', 0) / total_uses
            
            # Faster proxies get higher scores
            if avg_response_time > 0:
                time_score = max(0.1, 1.0 - (avg_response_time / 10.0))  # Normalize
                score += time_score * 0.3
            
            # 3. Recency (20% weight)
            last_success = stats.get('last_success', 0)
            if last_success > 0:
                hours_since_success = (time.time() - last_success) / 3600
                recency_score = max(0.1, 1.0 - (hours_since_success / 48.0))
                score += recency_score * 0.2
            
            # 4. Usage frequency (10% weight) - less used proxies get bonus
            usage_count = stats.get('total_uses', 0)
            usage_score = max(0.1, 1.0 - (usage_count / 100.0))
            score += usage_score * 0.1
            
            proxy_scores[proxy] = score
        
        # Select proxy with highest score
        return max(proxy_scores.items(), key=lambda x: x[1])[0]
    
    def sticky_rotation(self, available_proxies: List[str]) -> str:
        """Sticky rotation - prefer current proxy if performing well"""
        if not available_proxies:
            return None
        
        # Check if we have a current sticky proxy
        if hasattr(self, 'sticky_proxy') and self.sticky_proxy in available_proxies:
            stats = self.proxy_stats.get(self.sticky_proxy, {})
            
            # Check if sticky proxy is still performing well
            total_uses = stats.get('total_uses', 0)
            if total_uses > 0:
                recent_success_rate = stats.get('successful_uses', 0) / total_uses
                consecutive_failures = stats.get('consecutive_failures', 0)
                
                # Keep using if success rate > 70% and no recent failures
                if recent_success_rate > 0.7 and consecutive_failures == 0:
                    return self.sticky_proxy
        
        # Get new proxy using smart rotation
        new_proxy = self.smart_rotation(available_proxies)
        self.sticky_proxy = new_proxy
        
        return new_proxy
    
    def update_proxy_usage(self, proxy: str, success: bool = None, response_time: float = None):
        """Update proxy usage statistics"""
        if proxy not in self.proxy_stats:
            self.proxy_stats[proxy] = {
                'total_uses': 0,
                'successful_uses': 0,
                'failed_uses': 0,
                'total_response_time': 0,
                'last_used': 0,
                'last_success': 0,
                'consecutive_failures': 0,
                'is_active': True,
                'weight': 1.0
            }
        
        stats = self.proxy_stats[proxy]
        stats['total_uses'] += 1
        stats['last_used'] = time.time()
        
        if success is not None:
            if success:
                stats['successful_uses'] += 1
                stats['last_success'] = time.time()
                stats['consecutive_failures'] = 0
            else:
                stats['failed_uses'] += 1
                stats['consecutive_failures'] += 1
                
                # Deactivate after too many failures
                if stats['consecutive_failures'] > 5:
                    stats['is_active'] = False
                    logger.warning(f"Proxy {proxy} deactivated due to consecutive failures")
        
        if response_time is not None:
            stats['total_response_time'] += response_time
        
        # Update weight based on performance
        self.update_proxy_weight(proxy)
    
    def update_proxy_weight(self, proxy: str):
        """Update proxy weight based on performance"""
        if proxy not in self.proxy_stats:
            return
        
        stats = self.proxy_stats[proxy]
        total_uses = stats['total_uses']
        
        if total_uses > 0:
            success_rate = stats['successful_uses'] / total_uses
            
            # Calculate new weight
            current_weight = stats.get('weight', 1.0)
            
            if success_rate > 0.8:
                new_weight = min(current_weight * 1.1, 5.0)  # Increase weight
            elif success_rate < 0.3:
                new_weight = max(current_weight * 0.9, 0.1)  # Decrease weight
            else:
                new_weight = current_weight  # Keep same
            
            stats['weight'] = new_weight
    
    def mark_proxy_success(self, proxy: str, response_time: float = None):
        """Mark proxy as successful"""
        self.update_proxy_usage(proxy, success=True, response_time=response_time)
        
        # Reactivate if was deactivated
        if proxy in self.proxy_stats:
            self.proxy_stats[proxy]['is_active'] = True
    
    def mark_proxy_failure(self, proxy: str, response_time: float = None):
        """Mark proxy as failed"""
        self.update_proxy_usage(proxy, success=False, response_time=response_time)
    
    def add_proxy(self, proxy: str):
        """Add a new proxy"""
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            
            # Initialize stats
            if proxy not in self.proxy_stats:
                self.proxy_stats[proxy] = {
                    'total_uses': 0,
                    'successful_uses': 0,
                    'failed_uses': 0,
                    'total_response_time': 0,
                    'last_used': 0,
                    'last_success': 0,
                    'consecutive_failures': 0,
                    'is_active': True,
                    'weight': 1.0
                }
            
            logger.info(f"Added new proxy: {proxy}")
            self.save_proxies()
    
    def remove_proxy(self, proxy: str):
        """Remove a proxy"""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            
            if proxy in self.proxy_stats:
                del self.proxy_stats[proxy]
            
            logger.info(f"Removed proxy: {proxy}")
            self.save_proxies()
    
    def get_active_proxies(self) -> List[str]:
        """Get list of active proxies"""
        return [p for p in self.proxies if self.proxy_stats.get(p, {}).get('is_active', True)]
    
    def get_inactive_proxies(self) -> List[str]:
        """Get list of inactive proxies"""
        return [p for p in self.proxies if not self.proxy_stats.get(p, {}).get('is_active', True)]
    
    def reactivate_proxies(self):
        """Reactivate inactive proxies (for retry)"""
        reactivated = 0
        for proxy in self.get_inactive_proxies():
            if proxy in self.proxy_stats:
                self.proxy_stats[proxy]['is_active'] = True
                self.proxy_stats[proxy]['consecutive_failures'] = 0
                reactivated += 1
        
        if reactivated > 0:
            logger.info(f"Reactivated {reactivated} proxies")
    
    def get_proxy_stats(self, proxy: str = None) -> Dict:
        """Get statistics for a proxy or all proxies"""
        if proxy:
            return self.proxy_stats.get(proxy, {})
        
        # Overall statistics
        total_proxies = len(self.proxies)
        active_proxies = len(self.get_active_proxies())
        
        total_uses = sum(s.get('total_uses', 0) for s in self.proxy_stats.values())
        successful_uses = sum(s.get('successful_uses', 0) for s in self.proxy_stats.values())
        
        success_rate = 0
        if total_uses > 0:
            success_rate = successful_uses / total_uses
        
        avg_response_time = 0
        response_times = [s.get('total_response_time', 0) / max(1, s.get('total_uses', 0)) 
                         for s in self.proxy_stats.values() if s.get('total_uses', 0) > 0]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
        
        return {
            'total_proxies': total_proxies,
            'active_proxies': active_proxies,
            'inactive_proxies': total_proxies - active_proxies,
            'total_uses': total_uses,
            'successful_uses': successful_uses,
            'failed_uses': total_uses - successful_uses,
            'success_rate': success_rate,
            'average_response_time': avg_response_time,
            'rotation_strategy': self.current_strategy,
            'rotation_history_count': len(self.rotation_history)
        }
    
    def get_best_proxies(self, count: int = 5) -> List[Tuple[str, float]]:
        """Get best performing proxies"""
        proxy_scores = []
        
        for proxy, stats in self.proxy_stats.items():
            if stats.get('is_active', True) and stats.get('total_uses', 0) > 0:
                success_rate = stats.get('successful_uses', 0) / stats['total_uses']
                avg_response_time = stats.get('total_response_time', 0) / stats['total_uses']
                
                # Score = success rate * response time factor
                response_factor = max(0.1, 1.0 - (avg_response_time / 10.0))
                score = success_rate * response_factor
                
                proxy_scores.append((proxy, score))
        
        # Sort by score (descending)
        proxy_scores.sort(key=lambda x: x[1], reverse=True)
        
        return proxy_scores[:count]
    
    def cleanup_old_proxies(self, max_age_days: int = 30):
        """Cleanup old/unused proxies"""
        removed_count = 0
        current_time = time.time()
        
        for proxy in self.proxies[:]:  # Copy list for iteration
            stats = self.proxy_stats.get(proxy, {})
            last_used = stats.get('last_used', 0)
            
            if last_used > 0:
                days_since_use = (current_time - last_used) / (24 * 3600)
                
                if days_since_use > max_age_days:
                    self.remove_proxy(proxy)
                    removed_count += 1
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old proxies")
    
    def set_rotation_strategy(self, strategy: str):
        """Set rotation strategy"""
        if strategy in self.strategies:
            self.current_strategy = strategy
            logger.info(f"Set rotation strategy to: {strategy}")
        else:
            logger.warning(f"Unknown strategy: {strategy}, using 'smart'")
            self.current_strategy = 'smart'