"""
Test Proxies - Test proxy management and validation
"""

import unittest
import time
import logging
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from proxies.proxy_scraper import ProxyScraper
from proxies.proxy_rotator import ProxyRotator
from proxies.proxy_checker import ProxyChecker

logger = logging.getLogger(__name__)

class TestProxyScraper(unittest.TestCase):
    """Test case for ProxyScraper"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.scraper = ProxyScraper()
        
        # Mock requests
        self.requests_patcher = patch('requests.get')
        self.mock_requests_get = self.requests_patcher.start()
        
        # Mock BeautifulSoup
        self.bs4_patcher = patch('bs4.BeautifulSoup')
        self.mock_bs4 = self.bs4_patcher.start()
        
        # Setup mock responses
        self.setup_mocks()
    
    def setup_mocks(self):
        """Setup mock responses"""
        # Mock requests response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        192.168.1.1:8080
        10.0.0.1:8888
        172.16.0.1:9999
        invalid_proxy
        255.255.255.255:10000
        """
        self.mock_requests_get.return_value = mock_response
        
        # Mock BeautifulSoup
        mock_soup = MagicMock()
        mock_soup.get_text.return_value = "192.168.1.1:8080\n10.0.0.1:8888"
        mock_soup.find_all.return_value = []
        self.mock_bs4.return_value = mock_soup
    
    def tearDown(self):
        """Tear down test fixtures"""
        self.requests_patcher.stop()
        self.bs4_patcher.stop()
    
    def test_scraper_initialization(self):
        """Test ProxyScraper initialization"""
        self.assertGreater(len(self.scraper.proxy_sources), 0)
        self.assertIn('name', self.scraper.proxy_sources[0])
        self.assertIn('url', self.scraper.proxy_sources[0])
        self.assertIn('type', self.scraper.proxy_sources[0])
        self.assertIn('format', self.scraper.proxy_sources[0])
    
    def test_is_valid_proxy(self):
        """Test proxy validation"""
        test_cases = [
            ("192.168.1.1:8080", True),
            ("10.0.0.1:8888", True),
            ("172.16.0.1:9999", True),
            ("255.255.255.255:10000", False),  # Invalid IP
            ("invalid_proxy", False),
            ("192.168.1.1", False),  # No port
            ("192.168.1.1:999999", False),  # Invalid port
            ("0.0.0.0:8080", False),  # Invalid IP
            ("127.0.0.1:8080", False),  # Loopback
            ("169.254.1.1:8080", False),  # Link-local
        ]
        
        for proxy, expected in test_cases:
            with self.subTest(proxy=proxy):
                result = self.scraper.is_valid_proxy(proxy)
                self.assertEqual(result, expected, f"Failed for {proxy}")
    
    def test_parse_api_response(self):
        """Test API response parsing"""
        mock_response = MagicMock()
        mock_response.text = "192.168.1.1:8080\n10.0.0.1:8888\ninvalid\n172.16.0.1:9999"
        
        proxies = self.scraper.parse_api_response(mock_response, "text_lines")
        
        self.assertEqual(len(proxies), 3)  # Should get 3 valid proxies
        self.assertIn("192.168.1.1:8080", proxies)
        self.assertIn("10.0.0.1:8888", proxies)
        self.assertIn("172.16.0.1:9999", proxies)
        self.assertNotIn("invalid", proxies)
    
    def test_clean_proxy_list(self):
        """Test proxy list cleaning"""
        proxy_list = [
            "192.168.1.1:8080",
            "192.168.1.1:8080",  # Duplicate
            "10.0.0.1:8888",
            "invalid",
            "172.16.0.1:9999",
            "255.255.255.255:10000",  # Invalid
        ]
        
        cleaned = self.scraper.clean_proxy_list(proxy_list)
        
        self.assertEqual(len(cleaned), 3)  # 3 unique valid proxies
        self.assertNotIn("invalid", cleaned)
        self.assertNotIn("255.255.255.255:10000", cleaned)
    
    def test_scrape_source(self):
        """Test scraping from a single source"""
        source = {
            'name': 'Test Source',
            'url': 'http://test.com/proxies',
            'type': 'api',
            'format': 'text_lines'
        }
        
        proxies = self.scraper.scrape_source(source)
        
        self.assertGreater(len(proxies), 0)
        self.assertTrue(all(self.scraper.is_valid_proxy(p) for p in proxies))


class TestProxyRotator(unittest.TestCase):
    """Test case for ProxyRotator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.proxy_file = "test_proxies.txt"
        
        # Create test proxy file
        with open(self.proxy_file, 'w') as f:
            f.write("192.168.1.1:8080\n")
            f.write("10.0.0.1:8888\n")
            f.write("172.16.0.1:9999\n")
        
        self.rotator = ProxyRotator(self.proxy_file)
    
    def tearDown(self):
        """Tear down test fixtures"""
        # Clean up test file
        if os.path.exists(self.proxy_file):
            os.remove(self.proxy_file)
    
    def test_rotator_initialization(self):
        """Test ProxyRotator initialization"""
        self.assertEqual(len(self.rotator.proxies), 3)
        self.assertEqual(len(self.rotator.proxy_stats), 3)
        
        for proxy in self.rotator.proxies:
            self.assertIn(proxy, self.rotator.proxy_stats)
            
            stats = self.rotator.proxy_stats[proxy]
            self.assertEqual(stats['total_uses'], 0)
            self.assertEqual(stats['successful_uses'], 0)
            self.assertEqual(stats['failed_uses'], 0)
            self.assertEqual(stats['consecutive_failures'], 0)
            self.assertTrue(stats['is_active'])
            self.assertEqual(stats['weight'], 1.0)
    
    def test_random_rotation(self):
        """Test random rotation strategy"""
        proxy = self.rotator.get_proxy(strategy='random')
        
        self.assertIn(proxy, self.rotator.proxies)
        
        # Check stats were updated
        stats = self.rotator.proxy_stats[proxy]
        self.assertEqual(stats['total_uses'], 1)
        self.assertGreater(stats['last_used'], 0)
    
    def test_round_robin_rotation(self):
        """Test round-robin rotation strategy"""
        proxies = []
        
        # Get more proxies than we have to test rotation
        for _ in range(5):
            proxy = self.rotator.get_proxy(strategy='round_robin')
            proxies.append(proxy)
        
        # Should cycle through available proxies
        self.assertEqual(len(set(proxies[:3])), 3)  # First 3 should be different
        self.assertEqual(proxies[3], proxies[0])  # Should wrap around
    
    def test_weighted_rotation(self):
        """Test weighted rotation strategy"""
        # Set different weights
        self.rotator.proxy_stats['192.168.1.1:8080']['weight'] = 0.1
        self.rotator.proxy_stats['10.0.0.1:8888']['weight'] = 0.5
        self.rotator.proxy_stats['172.16.0.1:9999']['weight'] = 1.0
        
        # Test multiple selections
        selections = {'192.168.1.1:8080': 0, '10.0.0.1:8888': 0, '172.16.0.1:9999': 0}
        
        for _ in range(100):
            proxy = self.rotator.get_proxy(strategy='weighted')
            selections[proxy] += 1
        
        # Higher weight proxies should be selected more often
        self.assertGreater(selections['172.16.0.1:9999'], selections['192.168.1.1:8080'])
        self.assertGreater(selections['10.0.0.1:8888'], selections['192.168.1.1:8080'])
    
    def test_smart_rotation(self):
        """Test smart rotation strategy"""
        # Set different success rates
        self.rotator.proxy_stats['192.168.1.1:8080']['successful_uses'] = 90
        self.rotator.proxy_stats['192.168.1.1:8080']['total_uses'] = 100
        self.rotator.proxy_stats['192.168.1.1:8080']['last_success'] = time.time()
        
        self.rotator.proxy_stats['10.0.0.1:8888']['successful_uses'] = 50
        self.rotator.proxy_stats['10.0.0.1:8888']['total_uses'] = 100
        self.rotator.proxy_stats['10.0.0.1:8888']['last_success'] = time.time() - 10000
        
        # Smart rotation should prefer the better proxy
        proxy = self.rotator.get_proxy(strategy='smart')
        self.assertEqual(proxy, '192.168.1.1:8080')
    
    def test_mark_proxy_success(self):
        """Test marking proxy as successful"""
        proxy = '192.168.1.1:8080'
        
        self.rotator.mark_proxy_success(proxy, response_time=1.5)
        
        stats = self.rotator.proxy_stats[proxy]
        self.assertEqual(stats['total_uses'], 1)
        self.assertEqual(stats['successful_uses'], 1)
        self.assertEqual(stats['consecutive_failures'], 0)
        self.assertTrue(stats['is_active'])
        self.assertGreater(stats['last_success'], 0)
        self.assertEqual(stats['total_response_time'], 1.5)
    
    def test_mark_proxy_failure(self):
        """Test marking proxy as failed"""
        proxy = '192.168.1.1:8080'
        
        self.rotator.mark_proxy_failure(proxy, response_time=5.0)
        
        stats = self.rotator.proxy_stats[proxy]
        self.assertEqual(stats['total_uses'], 1)
        self.assertEqual(stats['failed_uses'], 1)
        self.assertEqual(stats['consecutive_failures'], 1)
        self.assertTrue(stats['is_active'])  # Not enough failures to deactivate
        self.assertEqual(stats['total_response_time'], 5.0)
        
        # Multiple failures should deactivate
        for _ in range(5):
            self.rotator.mark_proxy_failure(proxy)
        
        stats = self.rotator.proxy_stats[proxy]
        self.assertFalse(stats['is_active'])
    
    def test_get_active_proxies(self):
        """Test getting active proxies"""
        # Deactivate one proxy
        self.rotator.proxy_stats['192.168.1.1:8080']['is_active'] = False
        
        active_proxies = self.rotator.get_active_proxies()
        
        self.assertEqual(len(active_proxies), 2)
        self.assertNotIn('192.168.1.1:8080', active_proxies)
        self.assertIn('10.0.0.1:8888', active_proxies)
        self.assertIn('172.16.0.1:9999', active_proxies)
    
    def test_reactivate_proxies(self):
        """Test reactivating proxies"""
        # Deactivate all proxies
        for proxy in self.rotator.proxies:
            self.rotator.proxy_stats[proxy]['is_active'] = False
            self.rotator.proxy_stats[proxy]['consecutive_failures'] = 10
        
        self.rotator.reactivate_proxies()
        
        for proxy in self.rotator.proxies:
            stats = self.rotator.proxy_stats[proxy]
            self.assertTrue(stats['is_active'])
            self.assertEqual(stats['consecutive_failures'], 0)


class TestProxyChecker(unittest.TestCase):
    """Test case for ProxyChecker"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.checker = ProxyChecker()
        
        # Mock requests
        self.requests_patcher = patch('requests.get')
        self.mock_requests_get = self.requests_patcher.start()
        self.requests_head_patcher = patch('requests.head')
        self.mock_requests_head = self.requests_head_patcher.start()
        
        # Setup mock responses
        self.setup_mocks()
    
    def setup_mocks(self):
        """Setup mock responses"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ip': '123.456.789.012'}
        mock_response.text = '123.456.789.012'
        mock_response.headers = {'content-type': 'application/json'}
        
        self.mock_requests_get.return_value = mock_response
        self.mock_requests_head.return_value = mock_response
    
    def tearDown(self):
        """Tear down test fixtures"""
        self.requests_patcher.stop()
        self.requests_head_patcher.stop()
    
    def test_checker_initialization(self):
        """Test ProxyChecker initialization"""
        self.assertGreater(len(self.checker.test_urls), 0)
        self.assertIn('us', self.checker.regional_test_urls)
        self.assertIn('eu', self.checker.regional_test_urls)
        self.assertIn('asia', self.checker.regional_test_urls)
    
    def test_check_proxy(self):
        """Test proxy checking"""
        proxy = "123.456.789.012:8080"
        
        is_working, details = self.checker.check_proxy(proxy, timeout=5)
        
        self.assertTrue(is_working)
        self.assertEqual(details['proxy'], proxy)
        self.assertGreater(details['response_time'], 0)
        self.assertEqual(details['ip_address'], '123.456.789.012')
        self.assertFalse(details['supports_https'])  # Mock doesn't support HTTPS
    
    def test_check_proxy_with_tiktok(self):
        """Test proxy checking with TikTok"""
        proxy = "123.456.789.012:8080"
        
        # Mock TikTok response
        mock_tiktok_response = MagicMock()
        mock_tiktok_response.status_code = 200
        mock_tiktok_response.text = "tiktok content"
        self.mock_requests_get.return_value = mock_tiktok_response
        
        is_working, details = self.checker.check_proxy(
            proxy, 
            timeout=5, 
            test_tiktok=True
        )
        
        self.assertTrue(is_working)
        self.assertTrue(details.get('tiktok_accessible', False))
    
    def test_check_proxy_failure(self):
        """Test proxy checking with failure"""
        proxy = "123.456.789.012:8080"
        
        # Mock failure
        mock_response = MagicMock()
        mock_response.status_code = 403  # Forbidden
        self.mock_requests_get.return_value = mock_response
        
        is_working, details = self.checker.check_proxy(proxy, timeout=5)
        
        self.assertFalse(is_working)
        self.assertEqual(details['proxy'], proxy)
    
    def test_extract_ip_from_response(self):
        """Test IP extraction from response"""
        test_cases = [
            # (response_content, content_type, expected_ip)
            ('{"ip": "123.456.789.012"}', 'application/json', '123.456.789.012'),
            ('{"origin": "123.456.789.012"}', 'application/json', '123.456.789.012'),
            ('{"query": "123.456.789.012"}', 'application/json', '123.456.789.012'),
            ('123.456.789.012', 'text/plain', '123.456.789.012'),
            ('Your IP is 123.456.789.012', 'text/html', '123.456.789.012'),
            ('No IP here', 'text/plain', None),
        ]
        
        for content, content_type, expected_ip in test_cases:
            with self.subTest(content_type=content_type):
                mock_response = MagicMock()
                mock_response.headers = {'content-type': content_type}
                mock_response.text = content
                
                if 'application/json' in content_type:
                    mock_response.json.return_value = eval(content)
                
                ip = self.checker.extract_ip_from_response(mock_response)
                self.assertEqual(ip, expected_ip)
    
    def test_validate_proxy_format(self):
        """Test proxy format validation"""
        test_cases = [
            ("192.168.1.1:8080", True),
            ("10.0.0.1:8888", True),
            ("123.456.789.012:9999", True),
            ("192.168.1.1:8080:username:password", True),  # With auth
            ("192.168.1.1", False),  # No port
            ("192.168.1.1:999999", False),  # Invalid port
            ("256.256.256.256:8080", False),  # Invalid IP
            ("192.168.1.1:8080:username", False),  # Missing password
        ]
        
        for proxy, expected in test_cases:
            with self.subTest(proxy=proxy):
                result = self.checker.validate_proxy_format(proxy)
                self.assertEqual(result, expected)
    
    def test_check_proxy_speed(self):
        """Test proxy speed checking"""
        proxy = "123.456.789.012:8080"
        
        speed_results = self.checker.check_proxy_speed(proxy, test_count=2)
        
        self.assertEqual(speed_results['proxy'], proxy)
        self.assertEqual(len(speed_results['tests']), 2)
        self.assertGreaterEqual(speed_results['success_rate'], 0)
        
        if speed_results['tests'][0]['success']:
            self.assertGreater(speed_results['average_time'], 0)
    
    def test_batch_check_proxies(self):
        """Test batch proxy checking"""
        proxies = [
            "192.168.1.1:8080",
            "10.0.0.1:8888",
            "172.16.0.1:9999"
        ]
        
        # Mock successful checks
        self.checker.check_proxy = Mock(return_value=(True, {
            'proxy': 'test',
            'response_time': 1.0,
            'ip_address': '123.456.789.012'
        }))
        
        results = self.checker.check_proxies_batch(
            proxies, 
            max_workers=2, 
            timeout=5
        )
        
        self.assertEqual(results['total_checked'], 3)
        self.assertEqual(results['success_rate'], 1.0)  # All mocked as successful
        self.assertEqual(len(results['working']), 3)
        self.assertEqual(len(results['not_working']), 0)


class TestProxyIntegration(unittest.TestCase):
    """Integration tests for proxy system"""
    
    def test_scraper_rotator_integration(self):
        """Test integration between scraper and rotator"""
        # Create test proxies
        test_proxies = [
            "192.168.1.1:8080",
            "10.0.0.1:8888",
            "172.16.0.1:9999"
        ]
        
        # Create scraper
        scraper = ProxyScraper()
        scraper.clean_proxy_list = Mock(return_value=test_proxies)
        scraper.scrape_all_proxies = Mock(return_value=test_proxies)
        
        # Create rotator
        rotator = ProxyRotator("test_proxies.txt")
        
        # Simulate adding scraped proxies to rotator
        for proxy in test_proxies:
            rotator.add_proxy(proxy)
        
        self.assertEqual(len(rotator.proxies), 3)
        
        # Test rotation
        for _ in range(5):
            proxy = rotator.get_proxy()
            self.assertIn(proxy, test_proxies)
    
    def test_rotator_checker_integration(self):
        """Test integration between rotator and checker"""
        # Create rotator with test proxies
        rotator = ProxyRotator("test_proxies.txt")
        test_proxies = ["192.168.1.1:8080", "10.0.0.1:8888"]
        
        for proxy in test_proxies:
            rotator.add_proxy(proxy)
        
        # Create checker
        checker = ProxyChecker()
        checker.check_proxy = Mock(return_value=(True, {
            'proxy': 'test',
            'response_time': 1.0,
            'ip_address': '123.456.789.012'
        }))
        
        # Check all proxies
        results = checker.check_proxies_batch(test_proxies, max_workers=2)
        
        self.assertEqual(results['success_rate'], 1.0)
        
        # Update rotator stats based on checker results
        for result in results['working']:
            proxy = result['proxy']
            rotator.mark_proxy_success(proxy, response_time=1.0)
        
        # Verify stats were updated
        for proxy in test_proxies:
            stats = rotator.proxy_stats[proxy]
            self.assertEqual(stats['total_uses'], 1)
            self.assertEqual(stats['successful_uses'], 1)
    
    def test_full_proxy_workflow(self):
        """Test full proxy workflow: scrape -> check -> rotate"""
        # Step 1: Scrape proxies
        scraper = ProxyScraper()
        scraper.scrape_all_proxies = Mock(return_value=[
            "192.168.1.1:8080",
            "10.0.0.1:8888",
            "172.16.0.1:9999",
            "invalid_proxy"
        ])
        
        scraped_proxies = scraper.scrape_all_proxies()
        
        # Step 2: Clean proxies
        cleaned_proxies = scraper.clean_proxy_list(scraped_proxies)
        self.assertEqual(len(cleaned_proxies), 3)  # 3 valid proxies
        
        # Step 3: Check proxies
        checker = ProxyChecker()
        checker.check_proxy = Mock(side_effect=[
            (True, {'response_time': 1.0, 'ip_address': '192.168.1.1'}),
            (False, {'error': 'Timeout'}),
            (True, {'response_time': 2.0, 'ip_address': '172.16.0.1'})
        ])
        
        working_proxies = []
        for proxy in cleaned_proxies:
            is_working, details = checker.check_proxy(proxy)
            if is_working:
                working_proxies.append((proxy, details['response_time']))
        
        self.assertEqual(len(working_proxies), 2)  # 2 working proxies
        
        # Step 4: Add to rotator
        rotator = ProxyRotator("test_proxies.txt")
        
        for proxy, response_time in working_proxies:
            rotator.add_proxy(proxy)
            rotator.mark_proxy_success(proxy, response_time=response_time)
        
        self.assertEqual(len(rotator.proxies), 2)
        
        # Step 5: Use rotator
        for _ in range(3):
            proxy = rotator.get_proxy(strategy='smart')
            self.assertIn(proxy, [p for p, _ in working_proxies])


def run_proxy_tests():
    """Run all proxy tests"""
    # Configure logging
    logging.basicConfig(level=logging.WARNING)
    
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestProxyScraper)
    suite.addTests(loader.loadTestsFromTestCase(TestProxyRotator))
    suite.addTests(loader.loadTestsFromTestCase(TestProxyChecker))
    suite.addTests(loader.loadTestsFromTestCase(TestProxyIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_proxy_tests()
    sys.exit(0 if success else 1)