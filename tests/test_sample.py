"""
Test Suite for VT View Tester
Unit and integration tests
"""

import asyncio
import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Import modules to test
from utils.validator import Validator
from utils.calculator import StatisticsCalculator
from database.models import init_database, SessionLocal, User
from database.crud import create_user, get_user
from utils.file_handler import FileHandler

class TestValidator(unittest.TestCase):
    """Test input validator"""
    
    def test_validate_tiktok_url(self):
        """Test TikTok URL validation"""
        test_cases = [
            ("https://www.tiktok.com/@user/video/123456789", True),
            ("http://www.tiktok.com/@user.name/video/987654321", True),
            ("tiktok.com/@user/video/123456789", True),
            ("@user/video/123456789", True),
            ("https://vm.tiktok.com/ABC123/", True),
            ("https://invalid.com/video/123", False),
            ("", False),
        ]
        
        for url, expected_valid in test_cases:
            with self.subTest(url=url):
                is_valid, normalized = Validator.validate_tiktok_url(url)
                self.assertEqual(is_valid, expected_valid)
    
    def test_validate_view_count(self):
        """Test view count validation"""
        test_cases = [
            ("100", True, 100),
            ("1,000", True, 1000),
            ("10000", True, 10000),
            ("0", False, 0),
            ("10001", False, 10001),
            ("abc", False, 0),
            ("", False, 0),
        ]
        
        for input_val, expected_valid, expected_count in test_cases:
            with self.subTest(input=input_val):
                is_valid, count = Validator.validate_view_count(input_val, max_views=10000)
                self.assertEqual(is_valid, expected_valid)
                if expected_valid:
                    self.assertEqual(count, expected_count)
    
    def test_sanitize_input(self):
        """Test input sanitization"""
        test_cases = [
            ("<script>alert('xss')</script>", "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"),
            ("test' OR '1'='1", "test&#x27; OR &#x27;1&#x27;=&#x27;1"),
            ("normal text", "normal text"),
            ("", ""),
        ]
        
        for input_val, expected_output in test_cases:
            with self.subTest(input=input_val):
                sanitized = Validator.sanitize_input(input_val)
                self.assertEqual(sanitized, expected_output)

class TestCalculator(unittest.TestCase):
    """Test calculator functions"""
    
    def test_calculate_success_rate(self):
        """Test success rate calculation"""
        test_cases = [
            (100, 200, 50.0),  # 100/200 = 50%
            (0, 100, 0.0),     # 0/100 = 0%
            (100, 100, 100.0), # 100/100 = 100%
            (75, 300, 25.0),   # 75/300 = 25%
        ]
        
        for successful, total, expected_rate in test_cases:
            with self.subTest(successful=successful, total=total):
                rate = StatisticsCalculator.calculate_success_rate(successful, total)
                self.assertAlmostEqual(rate, expected_rate, places=2)
    
    def test_calculate_growth_rate(self):
        """Test growth rate calculation"""
        test_cases = [
            (200, 100, 100.0),   # 100% growth
            (150, 100, 50.0),    # 50% growth
            (100, 100, 0.0),     # 0% growth
            (50, 100, -50.0),    # -50% growth
        ]
        
        for current, previous, expected_growth in test_cases:
            with self.subTest(current=current, previous=previous):
                growth = StatisticsCalculator.calculate_growth_rate(current, previous)
                self.assertAlmostEqual(growth, expected_growth, places=2)
    
    def test_calculate_average(self):
        """Test average calculations"""
        values = [10, 20, 30, 40, 50]
        
        # Mean
        mean = StatisticsCalculator.calculate_average(values, "mean")
        self.assertEqual(mean, 30.0)
        
        # Median
        median = StatisticsCalculator.calculate_average(values, "median")
        self.assertEqual(median, 30.0)
        
        # Mode (with mode present)
        mode_values = [1, 2, 2, 3, 4]
        mode = StatisticsCalculator.calculate_average(mode_values, "mode")
        self.assertEqual(mode, 2.0)

class TestDatabase(unittest.TestCase):
    """Test database operations"""
    
    def setUp(self):
        """Set up test database"""
        # Use in-memory SQLite database for testing
        import os
        os.environ['TESTING'] = '1'
        
        from database.models import engine
        from database.models import Base
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        self.db = SessionLocal()
    
    def tearDown(self):
        """Clean up test database"""
        self.db.close()
        
        from database.models import engine
        from database.models import Base
        
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
    
    def test_create_user(self):
        """Test user creation"""
        from database.crud import create_user, get_user_by_telegram_id
        
        # Create user
        user = create_user(
            self.db,
            telegram_id="123456",
            username="testuser",
            email="test@example.com"
        )
        
        self.assertIsNotNone(user.id)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.telegram_id, "123456")
        
        # Retrieve user
        retrieved = get_user_by_telegram_id(self.db, "123456")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.username, "testuser")
    
    def test_user_update(self):
        """Test user update"""
        from database.crud import create_user, update_user
        
        # Create user
        user = create_user(self.db, username="original")
        
        # Update user
        updated = update_user(
            self.db,
            user.id,
            username="updated",
            is_admin=True
        )
        
        self.assertEqual(updated.username, "updated")
        self.assertTrue(updated.is_admin)

class TestFileHandler(unittest.IsolatedAsyncioTestCase):
    """Test file handler with async support"""
    
    async def test_file_operations(self):
        """Test basic file operations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = FileHandler(Path(temp_dir))
            
            # Test write and read
            test_content = "Hello, World!"
            test_file = "test.txt"
            
            # Write file
            success = await handler.write_file(test_file, test_content)
            self.assertTrue(success)
            
            # Check file exists
            exists = await handler.file_exists(test_file)
            self.assertTrue(exists)
            
            # Read file
            content = await handler.read_file(test_file)
            self.assertEqual(content, test_content)
            
            # Delete file
            success = await handler.delete_file(test_file)
            self.assertTrue(success)
            
            # Check file doesn't exist
            exists = await handler.file_exists(test_file)
            self.assertFalse(exists)
    
    async def test_json_operations(self):
        """Test JSON file operations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = FileHandler(Path(temp_dir))
            
            # Test data
            test_data = {
                "name": "Test",
                "value": 123,
                "items": [1, 2, 3]
            }
            
            test_file = "data.json"
            
            # Write JSON
            success = await handler.write_json(test_file, test_data)
            self.assertTrue(success)
            
            # Read JSON
            data = await handler.read_json(test_file)
            self.assertEqual(data, test_data)
    
    async def test_directory_operations(self):
        """Test directory operations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = FileHandler(Path(temp_dir))
            
            # Create directory
            test_dir = "subdir/nested"
            success = await handler.create_directory(test_dir)
            self.assertTrue(success)
            
            # List files
            files = await handler.list_files(test_dir)
            self.assertEqual(len(files), 0)
            
            # Create file in directory
            test_file = f"{test_dir}/test.txt"
            success = await handler.write_file(test_file, "test")
            self.assertTrue(success)
            
            # List files with pattern
            files = await handler.list_files(test_dir, "*.txt")
            self.assertEqual(len(files), 1)

class TestViewMethods(unittest.IsolatedAsyncioTestCase):
    """Test view sending methods (mocked)"""
    
    @patch('aiohttp.ClientSession.get')
    async def test_direct_request_method(self, mock_get):
        """Test direct request method with mocked HTTP"""
        from core.view_sender import DirectRequestMethod
        
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        mock_get.return_value = mock_response
        
        # Create method
        method = DirectRequestMethod()
        await method.initialize()
        
        # Test send view
        result = await method.send_view(
            "https://www.tiktok.com/@test/video/123",
            proxy="http://proxy:8080"
        )
        
        # Verify
        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        
        # Cleanup
        await method.cleanup()
    
    @patch('playwright.async_api.async_playwright')
    async def test_browser_method(self, mock_playwright):
        """Test browser method with mocked Playwright"""
        from core.view_sender import BrowserMethod
        
        # Mock Playwright
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        mock_playwright.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        # Mock page methods
        mock_page.goto.return_value = None
        mock_page.wait_for_timeout.return_value = None
        mock_page.query_selector_all.return_value = []
        
        # Create method
        method = BrowserMethod()
        
        # Test send view (will fail due to no video elements)
        result = await method.send_view(
            "https://www.tiktok.com/@test/video/123"
        )
        
        # Verify
        self.assertIsNotNone(result)
        self.assertFalse(result.success)  # Should fail due to no video
        
        # Cleanup
        await method.cleanup()

class IntegrationTest(unittest.IsolatedAsyncioTestCase):
    """Integration tests"""
    
    async def test_end_to_end_workflow(self):
        """Test end-to-end workflow with mocked dependencies"""
        # Mock account and proxy managers
        mock_account_manager = AsyncMock()
        mock_account_manager.get_next_account.return_value = AsyncMock(username="test_account")
        mock_account_manager.increment_account_views.return_value = True
        
        mock_proxy_manager = AsyncMock()
        mock_proxy_info = AsyncMock()
        mock_proxy_info.url = "http://proxy:8080"
        mock_proxy_manager.get_next_proxy.return_value = mock_proxy_info
        mock_proxy_manager.validate_proxy.return_value = (True, 100.0)
        
        # Create view sender with mocked dependencies
        from core.view_sender import ViewSender, DirectRequestMethod
        
        view_sender = ViewSender(mock_account_manager, mock_proxy_manager)
        
        # Mock the direct request method
        mock_method = AsyncMock()
        mock_method.name = "direct_request"
        mock_method.priority = 2
        mock_method.success_count = 0
        mock_method.failure_count = 0
        mock_method.success_rate = 0.0
        mock_method.average_time = 0.0
        
        # Mock send_view to return success
        mock_result = AsyncMock()
        mock_result.success = True
        mock_result.view_id = "test123"
        mock_result.timestamp = "2024-01-01T00:00:00"
        mock_result.method_used = "direct_request"
        mock_result.response_time = 1.0
        mock_method.send_view.return_value = mock_result
        
        view_sender.methods = [mock_method]
        view_sender.active_methods = [mock_method]
        
        # Initialize
        await view_sender.initialize()
        
        # Test single view
        result = await view_sender.send_single_view(
            "https://www.tiktok.com/@test/video/123"
        )
        
        # Verify
        self.assertTrue(result.success)
        
        # Test batch views
        results = await view_sender.send_batch_views(
            "https://www.tiktok.com/@test/video/123",
            view_count=3,
            batch_size=2
        )
        
        self.assertEqual(len(results), 3)
        
        # Cleanup
        await view_sender.cleanup()

def run_tests():
    """Run all tests"""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTest(unittest.makeSuite(TestValidator))
    suite.addTest(unittest.makeSuite(TestCalculator))
    suite.addTest(unittest.makeSuite(TestDatabase))
    suite.addTest(unittest.makeSuite(TestFileHandler))
    suite.addTest(unittest.makeSuite(TestViewMethods))
    suite.addTest(unittest.makeSuite(IntegrationTest))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)