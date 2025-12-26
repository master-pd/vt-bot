# VT View Tester - API Reference

## 📋 Overview

This document provides detailed API reference for VT View Tester Professional Edition.

## 🏗️ Core Architecture

### ViewSender Class
The main class for sending TikTok views.

```python
class ViewSender:
    """Advanced view sender with multiple methods"""
    
    def __init__(self, account_manager: AccountManager, proxy_manager: ProxyManager):
        # Initialization
    
    async def initialize(self) -> None:
        """Initialize all components"""
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
    
    async def send_single_view(self, video_url: str) -> ViewResult:
        """Send a single view"""
    
    async def send_batch_views(
        self, 
        video_url: str, 
        view_count: int,
        batch_size: int = 10
    ) -> List[ViewResult]:
        """Send multiple views in batches"""
    
    def get_method_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all methods"""
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall statistics"""
    
    async def test_all_methods(self, video_url: str) -> Dict[str, Any]:
        """Test all available view methods"""