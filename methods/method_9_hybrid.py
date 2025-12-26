"""
Method 9: Hybrid Method - Combine multiple methods for best results
"""

import time
import random
import logging
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

class HybridMethod:
    def __init__(self):
        self.name = "hybrid"
        self.success_rate = 88  # 88% success rate
        self.total_views_sent = 0
        self.successful_views = 0
        self.last_used = None
        
        # Available methods (will be loaded dynamically)
        self.methods = {}
        self.method_weights = {}
        self.method_stats = defaultdict(lambda: {
            'total_views': 0,
            'successful_views': 0,
            'failed_views': 0,
            'last_success': 0,
            'avg_time': 0
        })
        
        # Hybrid strategies
        self.strategies = {
            'sequential': self.sequential_strategy,
            'parallel': self.parallel_strategy,
            'adaptive': self.adaptive_strategy,
            'fallback': self.fallback_strategy
        }
    
    def register_method(self, method_name: str, method_instance):
        """Register a method for hybrid use"""
        self.methods[method_name] = method_instance
        self.method_weights[method_name] = 1.0  # Initial weight
        
        logger.info(f"Registered method for hybrid: {method_name}")
    
    def is_available(self) -> bool:
        """Check if hybrid method is available"""
        return len(self.methods) >= 2  # Need at least 2 methods
    
    def send_views(self, video_url: str, view_count: int, strategy: str = "adaptive") -> Dict:
        """Send views using hybrid method"""
        logger.info(f"Hybrid Method: Sending {view_count} views using {strategy} strategy")
        
        if not self.methods:
            logger.error("No methods registered for hybrid")
            return {
                'method': self.name,
                'requested_views': view_count,
                'success_count': 0,
                'failed_count': view_count,
                'error': 'No methods available'
            }
        
        # Select strategy
        strategy_func = self.strategies.get(strategy, self.adaptive_strategy)
        
        results = {
            'method': self.name,
            'strategy': strategy,
            'requested_views': view_count,
            'success_count': 0,
            'failed_count': 0,
            'method_breakdown': {}
        }
        
        # Execute strategy
        strategy_results = strategy_func(video_url, view_count)
        
        # Aggregate results
        for method_name, method_result in strategy_results.items():
            if isinstance(method_result, dict):
                results['success_count'] += method_result.get('success_count', 0)
                results['failed_count'] += method_result.get('failed_count', 0)
                results['method_breakdown'][method_name] = method_result
        
        # Update overall stats
        self.total_views_sent += view_count
        self.successful_views += results['success_count']
        self.last_used = time.time()
        
        # Update success rate
        if results['success_count'] > 0:
            current_success = (results['success_count'] / view_count) * 100
            self.success_rate = (self.success_rate * 0.7) + (current_success * 0.3)
        
        # Update method weights based on performance
        self.update_method_weights(results['method_breakdown'])
        
        logger.info(f"Hybrid Results: {results['success_count']}/{view_count} successful")
        logger.info(f"Method breakdown: {results['method_breakdown']}")
        
        return results
    
    def sequential_strategy(self, video_url: str, view_count: int) -> Dict:
        """Use methods sequentially"""
        results = {}
        remaining_views = view_count
        
        # Sort methods by success rate
        sorted_methods = sorted(
            self.methods.items(),
            key=lambda x: self.method_stats[x[0]]['success_rate'],
            reverse=True
        )
        
        for method_name, method in sorted_methods:
            if remaining_views <= 0:
                break
            
            # Allocate views to this method
            method_views = min(remaining_views, max(10, view_count // len(self.methods)))
            
            logger.info(f"Sequential: Using {method_name} for {method_views} views")
            
            try:
                method_result = method.send_views(video_url, method_views)
                results[method_name] = method_result
                
                # Update method stats
                self.update_method_stats(method_name, method_result)
                
                remaining_views -= method_views
                
                # Delay between methods
                if remaining_views > 0:
                    time.sleep(random.uniform(5, 15))
                    
            except Exception as e:
                logger.error(f"Error in {method_name}: {e}")
                results[method_name] = {
                    'success_count': 0,
                    'failed_count': method_views
                }
        
        return results
    
    def parallel_strategy(self, video_url: str, view_count: int) -> Dict:
        """Use methods in parallel"""
        import threading
        from queue import Queue
        
        results = {}
        result_queue = Queue()
        
        # Divide views among methods
        method_count = len(self.methods)
        base_views = view_count // method_count
        extra_views = view_count % method_count
        
        threads = []
        
        for i, (method_name, method) in enumerate(self.methods.items()):
            # Calculate views for this method
            method_views = base_views + (1 if i < extra_views else 0)
            
            if method_views > 0:
                thread = threading.Thread(
                    target=self.parallel_method_worker,
                    args=(method_name, method, video_url, method_views, result_queue)
                )
                threads.append(thread)
                thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Collect results
        while not result_queue.empty():
            method_name, method_result = result_queue.get()
            results[method_name] = method_result
            self.update_method_stats(method_name, method_result)
        
        return results
    
    def parallel_method_worker(self, method_name, method, video_url, view_count, result_queue):
        """Worker for parallel strategy"""
        try:
            method_result = method.send_views(video_url, view_count)
            result_queue.put((method_name, method_result))
        except Exception as e:
            logger.error(f"Parallel worker error ({method_name}): {e}")
            result_queue.put((method_name, {
                'success_count': 0,
                'failed_count': view_count
            }))
    
    def adaptive_strategy(self, video_url: str, view_count: int) -> Dict:
        """Adaptively switch methods based on performance"""
        results = {}
        remaining_views = view_count
        
        # Current batch settings
        batch_size = max(5, view_count // 10)
        current_method = self.select_best_method()
        
        while remaining_views > 0:
            # Determine batch size
            current_batch = min(batch_size, remaining_views)
            
            logger.info(f"Adaptive: Using {current_method} for {current_batch} views "
                       f"({remaining_views} remaining)")
            
            try:
                method = self.methods[current_method]
                method_result = method.send_views(video_url, current_batch)
                results.setdefault(current_method, {
                    'success_count': 0,
                    'failed_count': 0
                })
                
                results[current_method]['success_count'] += method_result.get('success_count', 0)
                results[current_method]['failed_count'] += method_result.get('failed_count', 0)
                
                # Update method stats
                self.update_method_stats(current_method, method_result)
                
                remaining_views -= current_batch
                
                # Evaluate performance and possibly switch method
                if method_result.get('success_count', 0) / current_batch < 0.5:
                    # Poor performance, switch method
                    current_method = self.select_best_method(exclude=current_method)
                    logger.warning(f"Switching to {current_method} due to poor performance")
                
                # Randomly explore other methods (10% chance)
                if random.random() < 0.1:
                    current_method = self.select_random_method(exclude=current_method)
                    logger.debug(f"Randomly exploring {current_method}")
                
                # Adjust batch size based on performance
                success_ratio = method_result.get('success_count', 0) / current_batch
                if success_ratio > 0.8:
                    batch_size = min(batch_size * 1.2, 50)  # Increase batch size
                elif success_ratio < 0.3:
                    batch_size = max(batch_size * 0.8, 5)   # Decrease batch size
                
                # Delay between batches
                if remaining_views > 0:
                    time.sleep(random.uniform(3, 8))
                    
            except Exception as e:
                logger.error(f"Error in adaptive strategy ({current_method}): {e}")
                results.setdefault(current_method, {
                    'success_count': 0,
                    'failed_count': 0
                })
                results[current_method]['failed_count'] += current_batch
                remaining_views -= current_batch
                
                # Switch method on error
                current_method = self.select_best_method(exclude=current_method)
        
        return results
    
    def fallback_strategy(self, video_url: str, view_count: int) -> Dict:
        """Use fallback chain if primary method fails"""
        results = {}
        remaining_views = view_count
        
        # Method chain in order of preference
        method_chain = self.get_method_chain()
        
        for method_name in method_chain:
            if remaining_views <= 0:
                break
            
            method = self.methods[method_name]
            logger.info(f"Fallback: Trying {method_name} for {remaining_views} views")
            
            try:
                method_result = method.send_views(video_url, remaining_views)
                results[method_name] = method_result
                
                # Update method stats
                self.update_method_stats(method_name, method_result)
                
                success_count = method_result.get('success_count', 0)
                remaining_views -= success_count
                
                # If method achieved >80% success, stop chain
                success_rate = success_count / method_result.get('requested_views', 1)
                if success_rate > 0.8:
                    logger.info(f"{method_name} successful, stopping chain")
                    break
                    
            except Exception as e:
                logger.error(f"Fallback error ({method_name}): {e}")
                results[method_name] = {
                    'success_count': 0,
                    'failed_count': remaining_views
                }
                # Continue to next method in chain
        
        return results
    
    def select_best_method(self, exclude: str = None) -> str:
        """Select the best performing method"""
        available_methods = list(self.methods.keys())
        
        if exclude:
            available_methods = [m for m in available_methods if m != exclude]
        
        if not available_methods:
            return random.choice(list(self.methods.keys()))
        
        # Calculate scores based on stats and weights
        method_scores = {}
        for method_name in available_methods:
            stats = self.method_stats[method_name]
            weight = self.method_weights[method_name]
            
            # Calculate score (weighted success rate)
            total = stats['total_views']
            if total > 0:
                success_rate = stats['successful_views'] / total
            else:
                success_rate = 0.5  # Default for untested methods
            
            # Consider recency (prefer recently successful methods)
            recency_factor = 1.0
            if stats['last_success'] > 0:
                hours_since_success = (time.time() - stats['last_success']) / 3600
                recency_factor = max(0.1, 1.0 - (hours_since_success / 24))
            
            score = success_rate * weight * recency_factor
            method_scores[method_name] = score
        
        # Select method with highest score
        best_method = max(method_scores.items(), key=lambda x: x[1])[0]
        
        return best_method
    
    def select_random_method(self, exclude: str = None) -> str:
        """Select random method with weighted probability"""
        available_methods = list(self.methods.keys())
        
        if exclude:
            available_methods = [m for m in available_methods if m != exclude]
        
        if not available_methods:
            return random.choice(list(self.methods.keys()))
        
        # Use weights for random selection
        weights = [self.method_weights.get(m, 1.0) for m in available_methods]
        
        return random.choices(available_methods, weights=weights, k=1)[0]
    
    def get_method_chain(self) -> List[str]:
        """Get ordered chain of methods for fallback strategy"""
        # Order by success rate (descending)
        method_success = []
        for method_name in self.methods.keys():
            stats = self.method_stats[method_name]
            total = stats['total_views']
            if total > 0:
                success_rate = stats['successful_views'] / total
            else:
                success_rate = 0.5
            method_success.append((method_name, success_rate))
        
        method_success.sort(key=lambda x: x[1], reverse=True)
        return [m[0] for m in method_success]
    
    def update_method_stats(self, method_name: str, result: Dict):
        """Update statistics for a method"""
        if method_name not in self.method_stats:
            self.method_stats[method_name] = {
                'total_views': 0,
                'successful_views': 0,
                'failed_views': 0,
                'last_success': 0,
                'avg_time': 0
            }
        
        stats = self.method_stats[method_name]
        stats['total_views'] += result.get('requested_views', 0)
        stats['successful_views'] += result.get('success_count', 0)
        stats['failed_views'] += result.get('failed_count', 0)
        
        if result.get('success_count', 0) > 0:
            stats['last_success'] = time.time()
    
    def update_method_weights(self, method_results: Dict):
        """Update method weights based on performance"""
        for method_name, result in method_results.items():
            if method_name not in self.method_weights:
                self.method_weights[method_name] = 1.0
            
            requested = result.get('requested_views', 1)
            successful = result.get('success_count', 0)
            
            if requested > 0:
                success_rate = successful / requested
                
                # Adjust weight
                current_weight = self.method_weights[method_name]
                
                if success_rate > 0.7:
                    # Increase weight for good performance
                    new_weight = min(current_weight * 1.2, 5.0)
                elif success_rate < 0.3:
                    # Decrease weight for poor performance
                    new_weight = max(current_weight * 0.8, 0.1)
                else:
                    # Slight adjustment
                    if success_rate > 0.5:
                        new_weight = current_weight * 1.05
                    else:
                        new_weight = current_weight * 0.95
                
                self.method_weights[method_name] = new_weight
                
                logger.debug(f"Updated weight for {method_name}: {current_weight:.2f} -> {new_weight:.2f}")
    
    def get_method_performance(self) -> Dict:
        """Get performance statistics for all methods"""
        performance = {}
        
        for method_name, stats in self.method_stats.items():
            total = stats['total_views']
            if total > 0:
                success_rate = stats['successful_views'] / total
            else:
                success_rate = 0.0
            
            performance[method_name] = {
                'success_rate': success_rate,
                'total_views': total,
                'successful_views': stats['successful_views'],
                'failed_views': stats['failed_views'],
                'weight': self.method_weights.get(method_name, 1.0),
                'last_success': stats['last_success']
            }
        
        return performance
    
    def get_success_rate(self) -> float:
        """Get current success rate"""
        return self.success_rate
    
    def reset_stats(self):
        """Reset all method statistics"""
        self.method_stats.clear()
        for method_name in self.methods.keys():
            self.method_weights[method_name] = 1.0
        
        logger.info("Reset all hybrid method statistics")
    
    def cleanup(self):
        """Cleanup method"""
        pass