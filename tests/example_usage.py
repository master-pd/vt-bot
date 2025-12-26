"""
VT View Tester - Usage Examples
Example scripts for different use cases
"""

import asyncio
import json
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.view_sender import ViewSender
from core.account_manager import AccountManager
from core.proxy_manager import ProxyManager
from utils.logger import setup_logger
from config import Colors

logger = setup_logger(__name__)

class Examples:
    """Collection of usage examples"""
    
    @staticmethod
    async def example_single_view():
        """Example: Send a single view"""
        print(f"{Colors.CYAN}=== Example: Send Single View ==={Colors.RESET}")
        
        try:
            # Initialize managers
            account_manager = AccountManager()
            proxy_manager = ProxyManager()
            
            # Initialize view sender
            view_sender = ViewSender(account_manager, proxy_manager)
            await view_sender.initialize()
            
            # Send a single view
            video_url = "https://www.tiktok.com/@example_user/video/123456789"
            result = await view_sender.send_single_view(video_url)
            
            # Print result
            if result.success:
                print(f"{Colors.GREEN}✓ View sent successfully!{Colors.RESET}")
                print(f"  View ID: {result.view_id}")
                print(f"  Method: {result.method_used}")
                print(f"  Response Time: {result.response_time:.2f}s")
            else:
                print(f"{Colors.RED}✗ View failed{Colors.RESET}")
                print(f"  Error: {result.error_message}")
            
            # Cleanup
            await view_sender.cleanup()
            
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")
    
    @staticmethod
    async def example_batch_views():
        """Example: Send batch views"""
        print(f"\n{Colors.CYAN}=== Example: Send Batch Views ==={Colors.RESET}")
        
        try:
            # Initialize managers
            account_manager = AccountManager()
            proxy_manager = ProxyManager()
            
            # Initialize view sender
            view_sender = ViewSender(account_manager, proxy_manager)
            await view_sender.initialize()
            
            # Send batch views
            video_url = "https://www.tiktok.com/@example_user/video/987654321"
            view_count = 10  # Number of views to send
            
            print(f"Sending {view_count} views to: {video_url}")
            print("This may take a moment...")
            
            results = await view_sender.send_batch_views(
                video_url, 
                view_count,
                batch_size=3  # Process 3 views at a time
            )
            
            # Analyze results
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            
            print(f"\n{Colors.GREEN}✓ Batch completed!{Colors.RESET}")
            print(f"  Successful: {successful}")
            print(f"  Failed: {failed}")
            print(f"  Success Rate: {(successful/len(results)*100):.1f}%")
            
            # Show method statistics
            print(f"\n{Colors.YELLOW}Method Statistics:{Colors.RESET}")
            stats = view_sender.get_method_stats()
            for stat in stats:
                print(f"  {stat['name']}: {stat['success_rate']:.1f}% success")
            
            # Cleanup
            await view_sender.cleanup()
            
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")
    
    @staticmethod
    async def example_account_management():
        """Example: Account management"""
        print(f"\n{Colors.CYAN}=== Example: Account Management ==={Colors.RESET}")
        
        try:
            # Initialize account manager
            account_manager = AccountManager()
            await account_manager.initialize()
            
            # Add accounts
            accounts_to_add = [
                {
                    "username": "dummy_account_1",
                    "password": "password123",
                    "email": "dummy1@example.com",
                    "notes": "Test account 1"
                },
                {
                    "username": "dummy_account_2",
                    "password": "password456",
                    "email": "dummy2@example.com",
                    "notes": "Test account 2"
                }
            ]
            
            print("Adding accounts...")
            added = await account_manager.add_accounts_bulk(accounts_to_add)
            print(f"Added {added} accounts")
            
            # Get statistics
            stats = await account_manager.get_statistics()
            print(f"\n{Colors.YELLOW}Account Statistics:{Colors.RESET}")
            print(f"  Total Accounts: {stats['total_accounts']}")
            print(f"  Active Accounts: {stats['active_accounts']}")
            print(f"  Total Views: {stats['total_views']:,}")
            
            # Export accounts
            export_data = await account_manager.export_accounts(format="json")
            print(f"\n{Colors.GREEN}Accounts exported (first 500 chars):{Colors.RESET}")
            print(export_data[:500] + "...")
            
            # Get next account for rotation
            account = await account_manager.get_next_account()
            if account:
                print(f"\n{Colors.YELLOW}Next account for rotation:{Colors.RESET}")
                print(f"  Username: {account.username}")
                print(f"  Status: {account.status}")
                print(f"  View Count: {account.view_count}")
            
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")
    
    @staticmethod
    async def example_proxy_management():
        """Example: Proxy management"""
        print(f"\n{Colors.CYAN}=== Example: Proxy Management ==={Colors.RESET}")
        
        try:
            # Initialize proxy manager
            proxy_manager = ProxyManager()
            await proxy_manager.initialize()
            
            # Add proxies
            proxies_to_add = [
                "http://proxy1.example.com:8080",
                "http://proxy2.example.com:8080",
                "socks5://proxy3.example.com:1080"
            ]
            
            print("Adding proxies...")
            added = await proxy_manager.add_proxies_bulk(proxies_to_add)
            print(f"Added {added} proxies")
            
            # Validate proxies
            print("\nValidating proxies...")
            validation_results = await proxy_manager.validate_all_proxies(batch_size=5)
            
            print(f"\n{Colors.YELLOW}Validation Results:{Colors.RESET}")
            print(f"  Total: {validation_results['total']}")
            print(f"  Valid: {validation_results['valid']}")
            print(f"  Invalid: {validation_results['invalid']}")
            print(f"  Average Speed: {validation_results['avg_speed']:.0f}ms")
            
            # Get statistics
            stats = await proxy_manager.get_statistics()
            print(f"\n{Colors.YELLOW}Proxy Statistics:{Colors.RESET}")
            print(f"  Total Proxies: {stats['total_proxies']}")
            print(f"  Active Proxies: {stats['active_proxies']}")
            print(f"  Health Score: {stats['health_score']:.1f}/100")
            
            # Get next proxy
            proxy = await proxy_manager.get_next_proxy()
            if proxy:
                print(f"\n{Colors.YELLOW}Next proxy for rotation:{Colors.RESET}")
                print(f"  URL: {proxy.url[:50]}...")
                print(f"  Type: {proxy.proxy_type}")
                print(f"  Speed: {proxy.speed:.0f}ms")
                print(f"  Success Rate: {proxy.success_rate:.1f}%")
            
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")
    
    @staticmethod
    async def example_method_testing():
        """Example: Test all view methods"""
        print(f"\n{Colors.CYAN}=== Example: Method Testing ==={Colors.RESET}")
        
        try:
            # Initialize managers
            account_manager = AccountManager()
            proxy_manager = ProxyManager()
            
            # Initialize view sender
            view_sender = ViewSender(account_manager, proxy_manager)
            await view_sender.initialize()
            
            # Test all methods
            test_url = "https://www.tiktok.com/@test_user/video/555555555"
            print(f"Testing methods with URL: {test_url}")
            
            test_results = await view_sender.test_all_methods(test_url)
            
            print(f"\n{Colors.YELLOW}Test Results:{Colors.RESET}")
            for method_result in test_results['methods']:
                status = f"{Colors.GREEN}✓" if method_result['success'] else f"{Colors.RED}✗"
                print(f"  {status} {method_result['name']}: "
                      f"{method_result['response_time']:.2f}s "
                      f"{Colors.RESET}")
            
            if test_results['best_method']:
                print(f"\n{Colors.GREEN}Best Method: {test_results['best_method']} "
                      f"({test_results['best_response_time']:.2f}s){Colors.RESET}")
            
            # Cleanup
            await view_sender.cleanup()
            
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")
    
    @staticmethod
    async def example_custom_configuration():
        """Example: Custom configuration"""
        print(f"\n{Colors.CYAN}=== Example: Custom Configuration ==={Colors.RESET}")
        
        try:
            # Custom rate limiting
            from config import VIEWS_PER_MINUTE_LIMIT
            print(f"Current rate limit: {VIEWS_PER_MINUTE_LIMIT} views/minute")
            
            # Custom view methods
            from core.view_sender import DirectRequestMethod, BrowserMethod
            
            # Create custom method combination
            custom_methods = [
                DirectRequestMethod(),  # Priority 2
                BrowserMethod(),       # Priority 1
            ]
            
            print(f"Using {len(custom_methods)} custom methods")
            
            # You can also customize the ViewSender directly
            account_manager = AccountManager()
            proxy_manager = ProxyManager()
            
            view_sender = ViewSender(account_manager, proxy_manager)
            view_sender.methods = custom_methods  # Replace default methods
            
            await view_sender.initialize()
            
            print(f"View sender initialized with {len(view_sender.active_methods)} active methods")
            
            # Get stats
            stats = view_sender.get_overall_stats()
            print(f"\n{Colors.YELLOW}View Sender Stats:{Colors.RESET}")
            print(f"  Running: {stats['running']}")
            print(f"  Active Methods: {stats['active_methods']}")
            
            await view_sender.cleanup()
            
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")

async def run_all_examples():
    """Run all examples"""
    print(f"{Colors.BOLD}{Colors.MAGENTA}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║               VT VIEW TESTER - EXAMPLES                  ║")
    print("║             Professional Usage Examples                  ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}")
    
    examples = Examples()
    
    # Run examples one by one
    await examples.example_single_view()
    await asyncio.sleep(1)
    
    await examples.example_batch_views()
    await asyncio.sleep(1)
    
    await examples.example_account_management()
    await asyncio.sleep(1)
    
    await examples.example_proxy_management()
    await asyncio.sleep(1)
    
    await examples.example_method_testing()
    await asyncio.sleep(1)
    
    await examples.example_custom_configuration()
    
    print(f"\n{Colors.GREEN}{'='*60}{Colors.RESET}")
    print(f"{Colors.GREEN}All examples completed successfully!{Colors.RESET}")
    print(f"{Colors.GREEN}{'='*60}{Colors.RESET}")

def main():
    """Main function to run examples"""
    try:
        asyncio.run(run_all_examples())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Examples interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Error running examples: {e}{Colors.RESET}")

if __name__ == "__main__":
    main()