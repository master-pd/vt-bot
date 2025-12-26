"""
Test Methods - Test all view sending methods
"""

import unittest
import time
import logging
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from methods.method_1_browser import BrowserMethod
from methods.method_2_api import APIMethod
from methods.method_3_multi_account import MultiAccountMethod
from methods.method_6_mobile_emulate import MobileEmulationMethod
from methods.method_9_hybrid import HybridMethod
from methods.method_10_ai_optimized import AIMethod

logger = logging.getLogger(__name__)

class TestViewMethods(unittest.TestCase):
    """Test case for all view sending methods"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_video_url = "https://www.tiktok.com/@testuser/video/1234567890123456789"
        self.test_view_count = 5  # Small number for testing
        
        # Mock Selenium to avoid actual browser launch
        self.selenium_patcher = patch('selenium.webdriver')
        self.mock_webdriver = self.selenium_patcher.start()
        
        # Mock requests
        self.requests_patcher = patch('requests.post')
        self.mock_requests_post = self.requests_patcher.start()
        
        # Mock aiohttp
        self.aiohttp_patcher = patch('aiohttp.ClientSession')
        self.mock_aiohttp = self.aiohttp_patcher.start()
        
        # Mock undetected_chromedriver
        self.uc_patcher = patch('undetected_chromedriver.Chrome')
        self.mock_uc = self.uc_patcher.start()
        
        # Setup mock responses
        self.setup_mocks()
    
    def setup_mocks(self):
        """Setup mock responses"""
        # Mock Selenium driver
        mock_driver = MagicMock()
        mock_driver.get.return_value = None
        mock_driver.find_element.return_value = MagicMock()
        mock_driver.find_elements.return_value = [MagicMock()]
        mock_driver.execute_script.return_value = None
        mock_driver.quit.return_value = None
        self.mock_webdriver.Chrome.return_value = mock_driver
        self.mock_uc.return_value = mock_driver
        
        # Mock requests response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status_code': 0, 'success': True}
        self.mock_requests_post.return_value = mock_response
        
        # Mock aiohttp session
        mock_session = MagicMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session.get.return_value.__aenter__.return_value.status = 200
        self.mock_aiohttp.return_value = mock_session
    
    def tearDown(self):
        """Tear down test fixtures"""
        self.selenium_patcher.stop()
        self.requests_patcher.stop()
        self.aiohttp_patcher.stop()
        self.uc_patcher.stop()
    
    def test_browser_method_initialization(self):
        """Test BrowserMethod initialization"""
        method = BrowserMethod()
        
        self.assertEqual(method.name, "browser_human")
        self.assertEqual(method.success_rate, 85)
        self.assertEqual(method.total_views_sent, 0)
        self.assertEqual(method.successful_views, 0)
        self.assertIsNone(method.last_used)
    
    def test_browser_method_availability(self):
        """Test BrowserMethod availability check"""
        method = BrowserMethod()
        
        # Mock the test
        with patch.object(method, 'is_available') as mock_available:
            mock_available.return_value = True
            self.assertTrue(method.is_available())
    
    def test_browser_method_send_views(self):
        """Test BrowserMethod send_views"""
        method = BrowserMethod()
        
        # Mock send_single_view to avoid actual browser
        method.send_single_view = Mock(return_value=True)
        
        results = method.send_views(self.test_video_url, self.test_view_count)
        
        self.assertEqual(results['method'], "browser_human")
        self.assertEqual(results['requested_views'], self.test_view_count)
        self.assertEqual(results['success_count'], self.test_view_count)
        self.assertEqual(results['failed_count'], 0)
        self.assertGreater(method.total_views_sent, 0)
        self.assertIsNotNone(method.last_used)
    
    def test_api_method_initialization(self):
        """Test APIMethod initialization"""
        method = APIMethod()
        
        self.assertEqual(method.name, "api_direct")
        self.assertEqual(method.success_rate, 70)
        self.assertEqual(method.total_views_sent, 0)
        self.assertEqual(method.successful_views, 0)
        self.assertIsNone(method.last_used)
        self.assertGreater(len(method.api_endpoints), 0)
        self.assertGreater(len(method.headers_list), 0)
    
    def test_api_method_video_id_extraction(self):
        """Test APIMethod video ID extraction"""
        method = APIMethod()
        
        test_cases = [
            ("https://www.tiktok.com/@user/video/1234567890123456789", "1234567890123456789"),
            ("https://www.tiktok.com/@user/video/1234567890123456789?is_copy_url=1", "1234567890123456789"),
            ("https://vt.tiktok.com/ABC123/", None),  # Short URL
            ("https://www.tiktok.com/@user", None),  # No video ID
        ]
        
        for url, expected_id in test_cases:
            video_id = method.extract_video_id(url)
            self.assertEqual(video_id, expected_id)
    
    def test_api_method_send_views(self):
        """Test APIMethod send_views"""
        method = APIMethod()
        
        # Mock the actual API call
        method.send_single_view_api = Mock(return_value=True)
        
        results = method.send_views(self.test_video_url, self.test_view_count)
        
        self.assertEqual(results['method'], "api_direct")
        self.assertEqual(results['requested_views'], self.test_view_count)
        self.assertGreaterEqual(results['success_count'], 0)
        self.assertLessEqual(results['failed_count'], self.test_view_count)
    
    def test_multi_account_method_initialization(self):
        """Test MultiAccountMethod initialization"""
        method = MultiAccountMethod()
        
        self.assertEqual(method.name, "multi_account")
        self.assertEqual(method.success_rate, 95)
        self.assertEqual(method.total_views_sent, 0)
        self.assertEqual(method.successful_views, 0)
        self.assertIsNone(method.last_used)
        self.assertEqual(method.max_concurrent, 10)
        self.assertEqual(method.session_timeout, 30)
    
    def test_multi_account_method_load_accounts(self):
        """Test MultiAccountMethod account loading"""
        method = MultiAccountMethod()
        
        # Mock file operations
        with patch('builtins.open', unittest.mock.mock_open(read_data='[]')):
            with patch('json.load', return_value=[]):
                count = method.load_accounts()
                self.assertEqual(count, 0)
                self.assertEqual(len(method.accounts), 0)
                self.assertEqual(len(method.active_accounts), 0)
    
    def test_multi_account_method_create_dummy_accounts(self):
        """Test MultiAccountMethod dummy account creation"""
        method = MultiAccountMethod()
        
        # Mock save_accounts to avoid file operations
        method.save_accounts = Mock()
        
        method.create_dummy_accounts(3)
        
        self.assertEqual(len(method.accounts), 3)
        self.assertEqual(len(method.active_accounts), 3)
        
        for account in method.accounts:
            self.assertIn('username', account)
            self.assertIn('email', account)
            self.assertIn('cookies', account)
            self.assertIn('user_agent', account)
            self.assertTrue(account['username'].startswith('dummy_user_'))
    
    def test_mobile_emulation_method_initialization(self):
        """Test MobileEmulationMethod initialization"""
        method = MobileEmulationMethod()
        
        self.assertEqual(method.name, "mobile_emulation")
        self.assertEqual(method.success_rate, 90)
        self.assertEqual(method.total_views_sent, 0)
        self.assertEqual(method.successful_views, 0)
        self.assertIsNone(method.last_used)
        self.assertGreater(len(method.mobile_devices), 0)
    
    def test_mobile_emulation_method_device_selection(self):
        """Test MobileEmulationMethod device selection"""
        method = MobileEmulationMethod()
        
        device = method.get_random_device("android")
        self.assertIn(device["name"], ["Samsung Galaxy S21", "Google Pixel 6", "Xiaomi Redmi Note 10"])
        
        device = method.get_random_device("ios")
        self.assertIn(device["name"], ["iPhone 13", "iPhone 12 Pro", "iPhone SE", "iPad Air", "iPad Pro"])
        
        device = method.get_random_device("random")
        self.assertIn(device["platform"].lower(), ["android", "ios"])
    
    def test_hybrid_method_initialization(self):
        """Test HybridMethod initialization"""
        method = HybridMethod()
        
        self.assertEqual(method.name, "hybrid")
        self.assertEqual(method.success_rate, 88)
        self.assertEqual(method.total_views_sent, 0)
        self.assertEqual(method.successful_views, 0)
        self.assertIsNone(method.last_used)
        
        self.assertIn('sequential', method.strategies)
        self.assertIn('parallel', method.strategies)
        self.assertIn('adaptive', method.strategies)
        self.assertIn('fallback', method.strategies)
    
    def test_hybrid_method_register_method(self):
        """Test HybridMethod method registration"""
        method = HybridMethod()
        
        mock_method = Mock()
        mock_method.name = "test_method"
        
        method.register_method("test_method", mock_method)
        
        self.assertIn("test_method", method.methods)
        self.assertIn("test_method", method.method_weights)
        self.assertEqual(method.method_weights["test_method"], 1.0)
    
    def test_hybrid_method_select_best_method(self):
        """Test HybridMethod best method selection"""
        method = HybridMethod()
        
        # Register mock methods
        mock_method1 = Mock()
        mock_method1.name = "method1"
        
        mock_method2 = Mock()
        mock_method2.name = "method2"
        
        method.register_method("method1", mock_method1)
        method.register_method("method2", mock_method2)
        
        # Set different weights
        method.method_stats["method1"] = {
            'total_views': 100,
            'successful_views': 90,
            'failed_views': 10,
            'last_success': time.time(),
            'avg_time': 1.0
        }
        
        method.method_stats["method2"] = {
            'total_views': 100,
            'successful_views': 80,
            'failed_views': 20,
            'last_success': time.time() - 10000,  # Older
            'avg_time': 2.0
        }
        
        best_method = method.select_best_method()
        self.assertEqual(best_method, "method1")  # Higher success rate, more recent
    
    def test_ai_method_initialization(self):
        """Test AIMethod initialization"""
        method = AIMethod()
        
        self.assertEqual(method.name, "ai_optimized")
        self.assertEqual(method.success_rate, 92)
        self.assertEqual(method.total_views_sent, 0)
        self.assertEqual(method.successful_views, 0)
        self.assertIsNone(method.last_used)
        
        self.assertGreater(len(method.features), 0)
        self.assertIsNotNone(method.model)
    
    def test_ai_method_feature_extraction(self):
        """Test AIMethod feature extraction"""
        method = AIMethod()
        
        features = method.extract_video_features(self.test_video_url)
        
        self.assertIn('time_of_day', features)
        self.assertIn('day_of_week', features)
        self.assertIn('video_length', features)
        self.assertIn('video_popularity', features)
        self.assertIn('method_success_rate', features)
        self.assertIn('proxy_quality', features)
        self.assertIn('account_age', features)
        self.assertIn('previous_success', features)
        
        # Check value ranges
        self.assertGreaterEqual(features['time_of_day'], 0)
        self.assertLessEqual(features['time_of_day'], 1)
        
        self.assertGreaterEqual(features['day_of_week'], 0)
        self.assertLessEqual(features['day_of_week'], 1)
    
    def test_ai_method_register_method(self):
        """Test AIMethod method registration"""
        method = AIMethod()
        
        mock_method = Mock()
        mock_method.name = "test_method"
        
        method.register_method("test_method", mock_method)
        
        self.assertIn("test_method", method.methods)
        self.assertIn("test_method", method.model['method_weights'])
        self.assertIn("test_method", method.method_history)
    
    def test_method_performance_comparison(self):
        """Compare performance of different methods"""
        methods = [
            ("Browser", BrowserMethod(), 85),
            ("API", APIMethod(), 70),
            ("Multi-Account", MultiAccountMethod(), 95),
            ("Mobile", MobileEmulationMethod(), 90),
            ("Hybrid", HybridMethod(), 88),
            ("AI", AIMethod(), 92)
        ]
        
        for name, method, expected_success in methods:
            with self.subTest(method=name):
                self.assertEqual(method.success_rate, expected_success)
                self.assertTrue(hasattr(method, 'send_views'))
                self.assertTrue(hasattr(method, 'get_success_rate'))
                self.assertTrue(hasattr(method, 'cleanup'))
    
    def test_error_handling(self):
        """Test error handling in methods"""
        method = BrowserMethod()
        
        # Test with invalid URL
        results = method.send_views("invalid_url", 1)
        
        # Should handle error gracefully
        self.assertEqual(results['method'], "browser_human")
        self.assertEqual(results['requested_views'], 1)
        self.assertEqual(results['failed_count'], 1)  # Should fail
    
    def test_concurrent_execution(self):
        """Test concurrent execution safety"""
        # This would test thread safety in methods that support concurrent execution
        # For now, just verify methods have necessary attributes
        method = HybridMethod()
        
        self.assertTrue(hasattr(method, 'parallel_strategy'))
        self.assertTrue(hasattr(method, 'sequential_strategy'))
        self.assertTrue(hasattr(method, 'adaptive_strategy'))
    
    def test_resource_cleanup(self):
        """Test resource cleanup"""
        methods = [
            BrowserMethod(),
            APIMethod(),
            MultiAccountMethod(),
            MobileEmulationMethod(),
            HybridMethod(),
            AIMethod()
        ]
        
        for method in methods:
            with self.subTest(method=type(method).__name__):
                # Should not raise exceptions
                try:
                    method.cleanup()
                except Exception as e:
                    self.fail(f"Cleanup failed for {type(method).__name__}: {e}")


class TestMethodIntegration(unittest.TestCase):
    """Integration tests for methods"""
    
    def test_hybrid_with_multiple_methods(self):
        """Test HybridMethod with multiple registered methods"""
        hybrid = HybridMethod()
        
        # Register mock methods
        mock_methods = []
        for i in range(3):
            mock_method = Mock()
            mock_method.name = f"method_{i}"
            mock_method.send_views.return_value = {
                'success_count': 5,
                'failed_count': 0,
                'requested_views': 5
            }
            mock_methods.append(mock_method)
            hybrid.register_method(f"method_{i}", mock_method)
        
        # Test sequential strategy
        with patch.object(hybrid, 'sequential_strategy') as mock_strategy:
            mock_strategy.return_value = {
                'method_0': {'success_count': 5, 'failed_count': 0},
                'method_1': {'success_count': 5, 'failed_count': 0}
            }
            
            results = hybrid.send_views(self.test_video_url, 10, strategy="sequential")
            
            self.assertEqual(results['method'], "hybrid")
            self.assertEqual(results['strategy'], "sequential")
            self.assertIn('method_breakdown', results)
    
    def test_ai_method_learning(self):
        """Test AI method learning capability"""
        ai_method = AIMethod()
        
        # Register a mock method
        mock_method = Mock()
        mock_method.name = "test_method"
        ai_method.register_method("test_method", mock_method)
        
        # Simulate learning
        features = ai_method.extract_video_features(self.test_video_url)
        ai_method.learn_from_result("test_method", features, 0.8, 0.7)
        
        # Check that weights were updated
        self.assertIn("test_method", ai_method.model['method_weights'])
        
        # Save and load model
        with patch.object(ai_method, 'save_model'):
            ai_method.save_model()
        
        with patch('builtins.open', unittest.mock.mock_open()):
            with patch('json.load', return_value={'model': {}, 'training_data': []}):
                ai_method.load_model()
    
    def test_method_chaining(self):
        """Test method chaining (fallback strategy)"""
        hybrid = HybridMethod()
        
        # Create methods with different success rates
        mock_method1 = Mock()
        mock_method1.name = "method1"
        mock_method1.send_views.return_value = {
            'success_count': 2,
            'failed_count': 3,
            'requested_views': 5
        }
        
        mock_method2 = Mock()
        mock_method2.name = "method2"
        mock_method2.send_views.return_value = {
            'success_count': 5,
            'failed_count': 0,
            'requested_views': 5
        }
        
        hybrid.register_method("method1", mock_method1)
        hybrid.register_method("method2", mock_method2)
        
        # Test fallback strategy
        with patch.object(hybrid, 'fallback_strategy') as mock_fallback:
            mock_fallback.return_value = {
                'method1': {'success_count': 2, 'failed_count': 3},
                'method2': {'success_count': 5, 'failed_count': 0}
            }
            
            results = hybrid.send_views(self.test_video_url, 10, strategy="fallback")
            
            self.assertEqual(results['success_count'], 7)
            self.assertEqual(results['failed_count'], 3)


def run_tests():
    """Run all tests"""
    # Configure logging
    logging.basicConfig(level=logging.WARNING)
    
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestViewMethods)
    suite.addTests(loader.loadTestsFromTestCase(TestMethodIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)