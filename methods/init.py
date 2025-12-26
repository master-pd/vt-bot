"""
Methods package - All view sending methods
"""

from .method_1_browser import BrowserMethod
from .method_2_api import APIMethod
from .method_3_multi_account import MultiAccountMethod
from .method_4_selenium_cloud import SeleniumCloudMethod
from .method_5_puppeteer import PuppeteerMethod
from .method_6_mobile_emulate import MobileEmulationMethod
from .method_7_websocket import WebSocketMethod
from .method_8_view_replay import ViewReplayMethod
from .method_9_hybrid import HybridMethod
from .method_10_ai_optimized import AIMethod

__all__ = [
    'BrowserMethod',
    'APIMethod',
    'MultiAccountMethod',
    'SeleniumCloudMethod',
    'PuppeteerMethod',
    'MobileEmulationMethod',
    'WebSocketMethod',
    'ViewReplayMethod',
    'HybridMethod',
    'AIMethod'
]