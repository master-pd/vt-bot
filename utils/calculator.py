"""
Advanced Calculator
Professional calculations, analytics, and statistics
"""

import math
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
from collections import Counter

from utils.logger import setup_logger

logger = setup_logger(__name__)

class StatisticsCalculator:
    """Advanced statistics calculations"""
    
    @staticmethod
    def calculate_success_rate(
        successful: int, 
        total: int, 
        decimal_places: int = 2
    ) -> float:
        """
        Calculate success rate percentage
        
        Args:
            successful: Number of successful attempts
            total: Total number of attempts
            decimal_places: Number of decimal places
            
        Returns:
            Success rate percentage
        """
        if total == 0:
            return 0.0
        
        rate = (successful / total) * 100
        return round(rate, decimal_places)
    
    @staticmethod
    def calculate_growth_rate(
        current_value: float,
        previous_value: float,
        decimal_places: int = 2
    ) -> float:
        """
        Calculate growth rate percentage
        
        Args:
            current_value: Current value
            previous_value: Previous value
            decimal_places: Number of decimal places
            
        Returns:
            Growth rate percentage
        """
        if previous_value == 0:
            return 0.0
        
        growth = ((current_value - previous_value) / previous_value) * 100
        return round(growth, decimal_places)
    
    @staticmethod
    def calculate_average(values: List[float], method: str = "mean") -> float:
        """
        Calculate average using specified method
        
        Args:
            values: List of values
            method: Average method ('mean', 'median', 'mode')
            
        Returns:
            Average value
        """
        if not values:
            return 0.0
        
        if method == "mean":
            return statistics.mean(values)
        elif method == "median":
            return statistics.median(values)
        elif method == "mode":
            try:
                return statistics.mode(values)
            except statistics.StatisticsError:
                # If no unique mode, return mean
                return statistics.mean(values)
        else:
            raise ValueError(f"Unknown average method: {method}")
    
    @staticmethod
    def calculate_percentile(
        values: List[float],
        percentile: float
    ) -> float:
        """
        Calculate percentile value
        
        Args:
            values: List of values
            percentile: Percentile (0-100)
            
        Returns:
            Percentile value
        """
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = int(math.floor(index))
            upper = int(math.ceil(index))
            weight = index - lower
            
            return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight
    
    @staticmethod
    def calculate_standard_deviation(values: List[float]) -> float:
        """
        Calculate standard deviation
        
        Args:
            values: List of values
            
        Returns:
            Standard deviation
        """
        if len(values) < 2:
            return 0.0
        
        return statistics.stdev(values)
    
    @staticmethod
    def calculate_correlation(
        x_values: List[float],
        y_values: List[float]
    ) -> float:
        """
        Calculate correlation coefficient
        
        Args:
            x_values: List of x values
            y_values: List of y values
            
        Returns:
            Correlation coefficient (-1 to 1)
        """
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0.0
        
        try:
            return statistics.correlation(x_values, y_values)
        except (statistics.StatisticsError, ValueError):
            return 0.0

class PerformanceCalculator:
    """Performance metrics calculations"""
    
    @staticmethod
    def calculate_views_per_minute(
        view_count: int,
        duration_seconds: float
    ) -> float:
        """
        Calculate views per minute
        
        Args:
            view_count: Number of views
            duration_seconds: Duration in seconds
            
        Returns:
            Views per minute
        """
        if duration_seconds <= 0:
            return 0.0
        
        views_per_second = view_count / duration_seconds
        return views_per_second * 60
    
    @staticmethod
    def calculate_efficiency_score(
        success_rate: float,
        speed_per_view: float,
        resource_usage: float,
        weights: Dict[str, float] = None
    ) -> float:
        """
        Calculate efficiency score (0-100)
        
        Args:
            success_rate: Success rate percentage (0-100)
            speed_per_view: Milliseconds per view (lower is better)
            resource_usage: Resource usage percentage (0-100, lower is better)
            weights: Weight for each factor
            
        Returns:
            Efficiency score (0-100)
        """
        if weights is None:
            weights = {
                "success_rate": 0.5,
                "speed": 0.3,
                "resources": 0.2
            }
        
        # Normalize speed (convert to score where higher is better)
        # Assuming optimal speed is 100ms, adjust as needed
        speed_score = max(0, min(100, (1000 / max(1, speed_per_view)) * 10))
        
        # Resource score (inverse, lower usage is better)
        resource_score = max(0, 100 - resource_usage)
        
        # Weighted average
        total_weight = sum(weights.values())
        weighted_score = (
            success_rate * weights["success_rate"] +
            speed_score * weights["speed"] +
            resource_score * weights["resources"]
        ) / total_weight
        
        return min(100, max(0, weighted_score))
    
    @staticmethod
    def calculate_uptime_percentage(
        uptime_seconds: float,
        total_time_seconds: float
    ) -> float:
        """
        Calculate uptime percentage
        
        Args:
            uptime_seconds: Uptime in seconds
            total_time_seconds: Total time in seconds
            
        Returns:
            Uptime percentage
        """
        if total_time_seconds <= 0:
            return 0.0
        
        return (uptime_seconds / total_time_seconds) * 100
    
    @staticmethod
    def calculate_response_time_percentile(
        response_times: List[float],
        percentile: float = 95
    ) -> float:
        """
        Calculate response time percentile
        
        Args:
            response_times: List of response times in milliseconds
            percentile: Percentile to calculate
            
        Returns:
            Response time at specified percentile
        """
        return StatisticsCalculator.calculate_percentile(response_times, percentile)
    
    @staticmethod
    def calculate_throughput(
        requests_completed: int,
        time_window_seconds: float
    ) -> float:
        """
        Calculate throughput (requests per second)
        
        Args:
            requests_completed: Number of requests completed
            time_window_seconds: Time window in seconds
            
        Returns:
            Throughput (requests per second)
        """
        if time_window_seconds <= 0:
            return 0.0
        
        return requests_completed / time_window_seconds

class FinancialCalculator:
    """Financial calculations"""
    
    @staticmethod
    def calculate_roi(
        investment: float,
        return_amount: float
    ) -> float:
        """
        Calculate Return on Investment (ROI)
        
        Args:
            investment: Initial investment
            return_amount: Total return
            
        Returns:
            ROI percentage
        """
        if investment == 0:
            return 0.0
        
        roi = ((return_amount - investment) / investment) * 100
        return roi
    
    @staticmethod
    def calculate_profit_margin(
        revenue: float,
        cost: float
    ) -> float:
        """
        Calculate profit margin
        
        Args:
            revenue: Total revenue
            cost: Total cost
            
        Returns:
            Profit margin percentage
        """
        if revenue == 0:
            return 0.0
        
        profit = revenue - cost
        margin = (profit / revenue) * 100
        return margin
    
    @staticmethod
    def calculate_cpm(
        cost: float,
        views: int
    ) -> float:
        """
        Calculate Cost Per Mille (CPM) - cost per 1000 views
        
        Args:
            cost: Total cost
            views: Number of views
            
        Returns:
            CPM value
        """
        if views == 0:
            return 0.0
        
        cpm = (cost / views) * 1000
        return cpm
    
    @staticmethod
    def calculate_break_even_point(
        fixed_costs: float,
        price_per_unit: float,
        variable_cost_per_unit: float
    ) -> float:
        """
        Calculate break-even point in units
        
        Args:
            fixed_costs: Total fixed costs
            price_per_unit: Price per unit
            variable_cost_per_unit: Variable cost per unit
            
        Returns:
            Break-even point (number of units)
        """
        if price_per_unit <= variable_cost_per_unit:
            return float('inf')  # Never breaks even
        
        contribution_margin = price_per_unit - variable_cost_per_unit
        return fixed_costs / contribution_margin

class TimeCalculator:
    """Time and date calculations"""
    
    @staticmethod
    def calculate_estimated_completion_time(
        items_completed: int,
        items_total: int,
        start_time: datetime
    ) -> Optional[datetime]:
        """
        Calculate estimated completion time
        
        Args:
            items_completed: Number of items completed
            items_total: Total number of items
            start_time: Start time
            
        Returns:
            Estimated completion datetime or None
        """
        if items_completed <= 0 or items_total <= 0:
            return None
        
        current_time = datetime.now()
        elapsed_seconds = (current_time - start_time).total_seconds()
        
        if elapsed_seconds <= 0:
            return None
        
        items_per_second = items_completed / elapsed_seconds
        if items_per_second <= 0:
            return None
        
        items_remaining = items_total - items_completed
        seconds_remaining = items_remaining / items_per_second
        
        return current_time + timedelta(seconds=seconds_remaining)
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        Format duration in human readable format
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        
        minutes = seconds / 60
        if minutes < 60:
            return f"{minutes:.1f}m"
        
        hours = minutes / 60
        if hours < 24:
            return f"{hours:.1f}h"
        
        days = hours / 24
        return f"{days:.1f}d"
    
    @staticmethod
    def calculate_time_saved(
        manual_time_per_item: float,
        automated_time_per_item: float,
        items_processed: int
    ) -> float:
        """
        Calculate time saved by automation
        
        Args:
            manual_time_per_item: Time per item manually (seconds)
            automated_time_per_item: Time per item automated (seconds)
            items_processed: Number of items processed
            
        Returns:
            Time saved in seconds
        """
        manual_total = manual_time_per_item * items_processed
        automated_total = automated_time_per_item * items_processed
        
        return manual_total - automated_total

class AnalyticsCalculator:
    """Advanced analytics calculations"""
    
    @staticmethod
    def calculate_trend(
        data_points: List[float],
        method: str = "linear"
    ) -> Dict[str, Any]:
        """
        Calculate trend from data points
        
        Args:
            data_points: List of data points
            method: Trend calculation method ('linear', 'exponential')
            
        Returns:
            Trend information dictionary
        """
        if len(data_points) < 2:
            return {
                "trend": "insufficient_data",
                "slope": 0.0,
                "direction": "flat",
                "strength": 0.0
            }
        
        # Simple linear trend calculation
        x_values = list(range(len(data_points)))
        y_values = data_points
        
        # Calculate linear regression
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        
        if n * sum_x2 - sum_x * sum_x == 0:
            slope = 0.0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Determine trend direction and strength
        if abs(slope) < 0.01:
            direction = "flat"
            strength = 0.0
        elif slope > 0:
            direction = "up"
            strength = min(1.0, abs(slope) / max(1, statistics.mean(y_values)))
        else:
            direction = "down"
            strength = min(1.0, abs(slope) / max(1, statistics.mean(y_values)))
        
        return {
            "trend": direction,
            "slope": slope,
            "direction": direction,
            "strength": strength,
            "prediction": data_points[-1] + slope if direction != "flat" else data_points[-1]
        }
    
    @staticmethod
    def detect_anomalies(
        data_points: List[float],
        sensitivity: float = 2.0
    ) -> List[Tuple[int, float]]:
        """
        Detect anomalies in data using z-score method
        
        Args:
            data_points: List of data points
            sensitivity: Sensitivity factor (standard deviations)
            
        Returns:
            List of (index, value) tuples for anomalies
        """
        if len(data_points) < 3:
            return []
        
        mean = statistics.mean(data_points)
        stdev = statistics.stdev(data_points) if len(data_points) > 1 else 0
        
        if stdev == 0:
            return []
        
        anomalies = []
        for i, value in enumerate(data_points):
            z_score = abs((value - mean) / stdev)
            if z_score > sensitivity:
                anomalies.append((i, value))
        
        return anomalies
    
    @staticmethod
    def calculate_seasonality(
        time_series: List[float],
        season_length: int
    ) -> List[float]:
        """
        Calculate seasonal components from time series
        
        Args:
            time_series: Time series data
            season_length: Length of season (e.g., 7 for weekly)
            
        Returns:
            Seasonal components
        """
        if len(time_series) < season_length * 2:
            return [0] * season_length
        
        # Simple seasonal decomposition
        seasonal_components = [0] * season_length
        
        for i in range(season_length):
            seasonal_values = []
            for j in range(i, len(time_series), season_length):
                seasonal_values.append(time_series[j])
            
            if seasonal_values:
                seasonal_components[i] = statistics.mean(seasonal_values)
        
        # Normalize
        avg_seasonal = statistics.mean(seasonal_components)
        if avg_seasonal != 0:
            seasonal_components = [c / avg_seasonal for c in seasonal_components]
        
        return seasonal_components

class UnitConverter:
    """Unit conversion utilities"""
    
    @staticmethod
    def convert_bytes(
        bytes_value: int,
        to_unit: str = "auto"
    ) -> Tuple[float, str]:
        """
        Convert bytes to human readable format
        
        Args:
            bytes_value: Value in bytes
            to_unit: Target unit ('auto', 'KB', 'MB', 'GB', 'TB')
            
        Returns:
            Tuple of (value, unit)
        """
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        
        if to_unit == "auto":
            # Auto-select appropriate unit
            unit_index = 0
            value = float(bytes_value)
            
            while value >= 1024 and unit_index < len(units) - 1:
                value /= 1024
                unit_index += 1
            
            return value, units[unit_index]
        else:
            # Convert to specific unit
            unit_index = units.index(to_unit.upper())
            value = bytes_value / (1024 ** unit_index)
            return value, to_unit.upper()
    
    @staticmethod
    def convert_time(
        seconds: float,
        to_unit: str = "auto"
    ) -> Tuple[float, str]:
        """
        Convert seconds to other time units
        
        Args:
            seconds: Time in seconds
            to_unit: Target unit ('auto', 'minutes', 'hours', 'days')
            
        Returns:
            Tuple of (value, unit)
        """
        units = {
            "seconds": 1,
            "minutes": 60,
            "hours": 3600,
            "days": 86400
        }
        
        if to_unit == "auto":
            # Auto-select appropriate unit
            if seconds < 60:
                return seconds, "seconds"
            elif seconds < 3600:
                return seconds / 60, "minutes"
            elif seconds < 86400:
                return seconds / 3600, "hours"
            else:
                return seconds / 86400, "days"
        else:
            # Convert to specific unit
            if to_unit not in units:
                raise ValueError(f"Unknown time unit: {to_unit}")
            
            value = seconds / units[to_unit]
            return value, to_unit
    
    @staticmethod
    def convert_percentage(
        value: float,
        from_format: str = "decimal",
        to_format: str = "percentage"
    ) -> float:
        """
        Convert between percentage formats
        
        Args:
            value: Value to convert
            from_format: Source format ('decimal', 'percentage', 'permille')
            to_format: Target format ('decimal', 'percentage', 'permille')
            
        Returns:
            Converted value
        """
        # Convert to decimal first
        if from_format == "decimal":
            decimal_value = value
        elif from_format == "percentage":
            decimal_value = value / 100
        elif from_format == "permille":
            decimal_value = value / 1000
        else:
            raise ValueError(f"Unknown from_format: {from_format}")
        
        # Convert from decimal to target format
        if to_format == "decimal":
            return decimal_value
        elif to_format == "percentage":
            return decimal_value * 100
        elif to_format == "permille":
            return decimal_value * 1000
        else:
            raise ValueError(f"Unknown to_format: {to_format}")

# Global calculator instances for convenience
stats_calc = StatisticsCalculator()
perf_calc = PerformanceCalculator()
finance_calc = FinancialCalculator()
time_calc = TimeCalculator()
analytics_calc = AnalyticsCalculator()
unit_converter = UnitConverter()