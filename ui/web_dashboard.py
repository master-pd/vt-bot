"""
Web Dashboard - Web-based control panel for TikTok View Bot
"""

import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, render_template, request, jsonify, Response, send_file
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
import asyncio

logger = logging.getLogger(__name__)

class WebDashboard:
    def __init__(self, bot_engine, host: str = '0.0.0.0', port: int = 5000):
        self.bot_engine = bot_engine
        self.host = host
        self.port = port
        self.app = Flask(__name__, 
                        template_folder='ui/templates',
                        static_folder='ui/static')
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        CORS(self.app)
        
        # Dashboard statistics
        self.dashboard_stats = {
            'start_time': datetime.now(),
            'total_visitors': 0,
            'active_connections': 0,
            'total_actions': 0
        }
        
        # Real-time updates
        self.update_interval = 5  # seconds
        self.update_thread = None
        self.is_running = False
        
        # Setup routes
        self.setup_routes()
        self.setup_socket_handlers()
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main dashboard page"""
            self.dashboard_stats['total_visitors'] += 1
            return render_template('index.html')
        
        @self.app.route('/api/status')
        def api_status():
            """API endpoint for bot status"""
            status = self.bot_engine.get_status()
            return jsonify({
                'success': True,
                'data': status,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/stats')
        def api_stats():
            """API endpoint for statistics"""
            stats = self.get_detailed_stats()
            return jsonify({
                'success': True,
                'data': stats,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/proxies')
        def api_proxies():
            """API endpoint for proxy information"""
            proxy_stats = self.bot_engine.proxy_manager.get_stats()
            return jsonify({
                'success': True,
                'data': proxy_stats,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/accounts')
        def api_accounts():
            """API endpoint for account information"""
            account_stats = self.bot_engine.account_manager.get_account_stats()
            return jsonify({
                'success': True,
                'data': account_stats,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/methods')
        def api_methods():
            """API endpoint for method information"""
            methods = self.get_methods_info()
            return jsonify({
                'success': True,
                'data': methods,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/tasks')
        def api_tasks():
            """API endpoint for task information"""
            tasks = self.get_tasks_info()
            return jsonify({
                'success': True,
                'data': tasks,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/tasks/history')
        def api_tasks_history():
            """API endpoint for task history"""
            history = self.get_tasks_history()
            return jsonify({
                'success': True,
                'data': history,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/start', methods=['POST'])
        def api_start():
            """API endpoint to start bot"""
            try:
                if self.bot_engine.start():
                    return jsonify({
                        'success': True,
                        'message': 'Bot started successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Bot is already running'
                    })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error starting bot: {str(e)}'
                })
        
        @self.app.route('/api/stop', methods=['POST'])
        def api_stop():
            """API endpoint to stop bot"""
            try:
                self.bot_engine.stop()
                return jsonify({
                    'success': True,
                    'message': 'Bot stopped successfully'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error stopping bot: {str(e)}'
                })
        
        @self.app.route('/api/task/add', methods=['POST'])
        def api_add_task():
            """API endpoint to add a new task"""
            try:
                data = request.get_json()
                
                if not data:
                    return jsonify({
                        'success': False,
                        'message': 'No data provided'
                    })
                
                video_url = data.get('video_url')
                view_count = data.get('view_count')
                method = data.get('method', 'auto')
                
                if not video_url or not view_count:
                    return jsonify({
                        'success': False,
                        'message': 'Missing required fields'
                    })
                
                # Validate URL
                if not self.is_valid_tiktok_url(video_url):
                    return jsonify({
                        'success': False,
                        'message': 'Invalid TikTok URL'
                    })
                
                # Validate view count
                try:
                    view_count = int(view_count)
                    if view_count <= 0 or view_count > 10000:
                        return jsonify({
                            'success': False,
                            'message': 'View count must be between 1 and 10000'
                        })
                except ValueError:
                    return jsonify({
                        'success': False,
                        'message': 'Invalid view count'
                    })
                
                # Add task
                task_id = self.bot_engine.add_task(video_url, view_count, method)
                
                self.dashboard_stats['total_actions'] += 1
                
                return jsonify({
                    'success': True,
                    'message': 'Task added successfully',
                    'task_id': task_id
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error adding task: {str(e)}'
                })
        
        @self.app.route('/api/task/<task_id>/cancel', methods=['POST'])
        def api_cancel_task(task_id):
            """API endpoint to cancel a task"""
            # Note: Implementation depends on task cancellation support
            return jsonify({
                'success': False,
                'message': 'Task cancellation not implemented yet'
            })
        
        @self.app.route('/api/proxies/refresh', methods=['POST'])
        def api_refresh_proxies():
            """API endpoint to refresh proxies"""
            try:
                count = self.bot_engine.proxy_manager.load_proxies()
                return jsonify({
                    'success': True,
                    'message': f'Refreshed {count} proxies'
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error refreshing proxies: {str(e)}'
                })
        
        @self.app.route('/api/logs')
        def api_logs():
            """API endpoint to get logs"""
            try:
                logs = self.get_recent_logs()
                return jsonify({
                    'success': True,
                    'data': logs
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error getting logs: {str(e)}'
                })
        
        @self.app.route('/api/export/data')
        def api_export_data():
            """API endpoint to export data"""
            try:
                data = self.export_all_data()
                return jsonify({
                    'success': True,
                    'data': data
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error exporting data: {str(e)}'
                })
        
        @self.app.route('/dashboard/metrics')
        def dashboard_metrics():
            """Prometheus metrics endpoint"""
            metrics = self.generate_metrics()
            return Response(metrics, mimetype='text/plain')
    
    def setup_socket_handlers(self):
        """Setup SocketIO event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            self.dashboard_stats['active_connections'] += 1
            logger.info(f'Client connected. Active connections: {self.dashboard_stats["active_connections"]}')
            emit('connected', {'message': 'Connected to TikTok View Bot Dashboard'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            self.dashboard_stats['active_connections'] -= 1
            logger.info(f'Client disconnected. Active connections: {self.dashboard_stats["active_connections"]}')
        
        @self.socketio.on('request_update')
        def handle_request_update(data):
            """Handle update request from client"""
            update_type = data.get('type', 'full')
            
            if update_type == 'full':
                status = self.bot_engine.get_status()
                emit('status_update', status)
            elif update_type == 'stats':
                stats = self.get_detailed_stats()
                emit('stats_update', stats)
            elif update_type == 'proxies':
                proxy_stats = self.bot_engine.proxy_manager.get_stats()
                emit('proxies_update', proxy_stats)
            elif update_type == 'accounts':
                account_stats = self.bot_engine.account_manager.get_account_stats()
                emit('accounts_update', account_stats)
        
        @self.socketio.on('send_views')
        def handle_send_views(data):
            """Handle send views request"""
            try:
                video_url = data.get('video_url')
                view_count = data.get('view_count')
                method = data.get('method', 'auto')
                
                if not video_url or not view_count:
                    emit('task_error', {'message': 'Missing required fields'})
                    return
                
                task_id = self.bot_engine.add_task(video_url, view_count, method)
                
                emit('task_added', {
                    'task_id': task_id,
                    'message': 'Task added successfully'
                })
                
            except Exception as e:
                emit('task_error', {'message': f'Error: {str(e)}'})
        
        @self.socketio.on('control_bot')
        def handle_control_bot(data):
            """Handle bot control requests"""
            action = data.get('action')
            
            if action == 'start':
                success = self.bot_engine.start()
                if success:
                    emit('bot_control', {'action': 'started', 'message': 'Bot started'})
                else:
                    emit('bot_control', {'action': 'error', 'message': 'Bot already running'})
            
            elif action == 'stop':
                self.bot_engine.stop()
                emit('bot_control', {'action': 'stopped', 'message': 'Bot stopped'})
            
            elif action == 'restart':
                self.bot_engine.stop()
                time.sleep(2)
                success = self.bot_engine.start()
                if success:
                    emit('bot_control', {'action': 'restarted', 'message': 'Bot restarted'})
                else:
                    emit('bot_control', {'action': 'error', 'message': 'Failed to restart bot'})
    
    def get_detailed_stats(self) -> Dict:
        """Get detailed statistics for dashboard"""
        bot_status = self.bot_engine.get_status()
        
        stats = {
            'bot': {
                'status': 'running' if bot_status['running'] else 'stopped',
                'uptime': self.get_uptime(bot_status['stats'].get('start_time')),
                'active_tasks': bot_status['active_tasks'],
                'queued_tasks': bot_status['tasks_in_queue']
            },
            'views': {
                'total_sent': bot_status['stats'].get('total_views_sent', 0),
                'successful': bot_status['stats'].get('successful_views', 0),
                'failed': bot_status['stats'].get('failed_views', 0),
                'success_rate': self.calculate_success_rate(bot_status['stats'])
            },
            'resources': {
                'proxies': bot_status.get('proxies_available', 0),
                'accounts': bot_status.get('accounts_available', 0),
                'active_proxies': len(self.bot_engine.proxy_manager.get_active_proxies()),
                'active_accounts': len(self.bot_engine.account_manager.get_active_accounts())
            },
            'performance': {
                'avg_response_time': 0,  # Would need tracking
                'tasks_per_hour': 0,     # Would need tracking
                'views_per_minute': 0    # Would need tracking
            },
            'dashboard': {
                'visitors': self.dashboard_stats['total_visitors'],
                'active_connections': self.dashboard_stats['active_connections'],
                'total_actions': self.dashboard_stats['total_actions'],
                'uptime': self.get_dashboard_uptime()
            }
        }
        
        return stats
    
    def get_methods_info(self) -> List[Dict]:
        """Get information about all available methods"""
        methods = []
        
        # Get from view sender if available
        if hasattr(self.bot_engine, 'view_sender'):
            method_stats = self.bot_engine.view_sender.get_method_stats()
            for method_name, stats in method_stats.items():
                methods.append({
                    'name': method_name,
                    'available': stats.get('available', False),
                    'success_rate': stats.get('success_rate', 0),
                    'views_sent': stats.get('total_views_sent', 0),
                    'last_used': stats.get('last_used')
                })
        
        # Add default methods
        default_methods = [
            {'name': 'browser', 'available': True, 'success_rate': 85, 'views_sent': 0},
            {'name': 'api', 'available': True, 'success_rate': 70, 'views_sent': 0},
            {'name': 'multi_account', 'available': True, 'success_rate': 95, 'views_sent': 0},
            {'name': 'mobile', 'available': True, 'success_rate': 90, 'views_sent': 0},
            {'name': 'hybrid', 'available': True, 'success_rate': 88, 'views_sent': 0},
            {'name': 'ai', 'available': True, 'success_rate': 92, 'views_sent': 0}
        ]
        
        return methods or default_methods
    
    def get_tasks_info(self) -> List[Dict]:
        """Get information about current tasks"""
        tasks = []
        
        # This would need task tracking implementation
        # For now, return placeholder
        tasks.append({
            'id': 'sample_task_1',
            'video_url': 'https://tiktok.com/@user/video/123',
            'requested_views': 100,
            'completed_views': 45,
            'status': 'running',
            'method': 'browser',
            'started_at': datetime.now().isoformat(),
            'progress': 45
        })
        
        return tasks
    
    def get_tasks_history(self, limit: int = 50) -> List[Dict]:
        """Get task history"""
        history = []
        
        # This would need database implementation
        # For now, return placeholder
        for i in range(min(10, limit)):
            history.append({
                'id': f'task_{i}',
                'video_url': f'https://tiktok.com/@user/video/{1000 + i}',
                'requested_views': 100,
                'completed_views': 85 + i,
                'status': 'completed',
                'method': 'browser',
                'started_at': (datetime.now().replace(hour=i)).isoformat(),
                'completed_at': (datetime.now().replace(hour=i, minute=30)).isoformat(),
                'success_rate': 0.85 + (i * 0.01)
            })
        
        return history
    
    def get_recent_logs(self, limit: int = 100) -> List[str]:
        """Get recent logs"""
        logs = []
        log_file = 'logs/bot.log'
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                logs = lines[-limit:]  # Get last N lines
        except FileNotFoundError:
            logs = ['Log file not found']
        
        return logs
    
    def export_all_data(self) -> Dict:
        """Export all dashboard data"""
        return {
            'timestamp': datetime.now().isoformat(),
            'bot_status': self.bot_engine.get_status(),
            'dashboard_stats': self.dashboard_stats,
            'detailed_stats': self.get_detailed_stats(),
            'methods': self.get_methods_info(),
            'tasks': self.get_tasks_info(),
            'tasks_history': self.get_tasks_history(100),
            'recent_logs': self.get_recent_logs(50)
        }
    
    def generate_metrics(self) -> str:
        """Generate Prometheus metrics"""
        stats = self.get_detailed_stats()
        
        metrics = []
        metrics.append('# HELP tiktok_bot_views_total Total views sent')
        metrics.append('# TYPE tiktok_bot_views_total counter')
        metrics.append(f'tiktok_bot_views_total {stats["views"]["total_sent"]}')
        
        metrics.append('# HELP tiktok_bot_views_successful_total Successful views')
        metrics.append('# TYPE tiktok_bot_views_successful_total counter')
        metrics.append(f'tiktok_bot_views_successful_total {stats["views"]["successful"]}')
        
        metrics.append('# HELP tiktok_bot_views_failed_total Failed views')
        metrics.append('# TYPE tiktok_bot_views_failed_total counter')
        metrics.append(f'tiktok_bot_views_failed_total {stats["views"]["failed"]}')
        
        metrics.append('# HELP tiktok_bot_success_rate View success rate')
        metrics.append('# TYPE tiktok_bot_success_rate gauge')
        metrics.append(f'tiktok_bot_success_rate {stats["views"]["success_rate"]}')
        
        metrics.append('# HELP tiktok_bot_proxies_available Available proxies')
        metrics.append('# TYPE tiktok_bot_proxies_available gauge')
        metrics.append(f'tiktok_bot_proxies_available {stats["resources"]["proxies"]}')
        
        metrics.append('# HELP tiktok_bot_accounts_available Available accounts')
        metrics.append('# TYPE tiktok_bot_accounts_available gauge')
        metrics.append(f'tiktok_bot_accounts_available {stats["resources"]["accounts"]}')
        
        metrics.append('# HELP tiktok_bot_active_tasks Active tasks')
        metrics.append('# TYPE tiktok_bot_active_tasks gauge')
        metrics.append(f'tiktok_bot_active_tasks {stats["bot"]["active_tasks"]}')
        
        metrics.append('# HELP tiktok_dashboard_visitors_total Total dashboard visitors')
        metrics.append('# TYPE tiktok_dashboard_visitors_total counter')
        metrics.append(f'tiktok_dashboard_visitors_total {stats["dashboard"]["visitors"]}')
        
        metrics.append('# HELP tiktok_dashboard_active_connections Active connections')
        metrics.append('# TYPE tiktok_dashboard_active_connections gauge')
        metrics.append(f'tiktok_dashboard_active_connections {stats["dashboard"]["active_connections"]}')
        
        return '\n'.join(metrics)
    
    def calculate_success_rate(self, stats: Dict) -> float:
        """Calculate success rate"""
        total = stats.get('total_views_sent', 0)
        successful = stats.get('successful_views', 0)
        
        if total > 0:
            return (successful / total) * 100
        return 0.0
    
    def get_uptime(self, start_time) -> str:
        """Format uptime"""
        if not start_time:
            return "0s"
        
        if isinstance(start_time, str):
            try:
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except:
                return "0s"
        
        delta = datetime.now() - start_time
        
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        seconds = delta.seconds % 60
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def get_dashboard_uptime(self) -> str:
        """Get dashboard uptime"""
        return self.get_uptime(self.dashboard_stats['start_time'])
    
    def is_valid_tiktok_url(self, url: str) -> bool:
        """Validate TikTok URL"""
        tiktok_domains = ['tiktok.com', 'vt.tiktok.com', 'vm.tiktok.com']
        return any(domain in url.lower() for domain in tiktok_domains)
    
    def start_update_thread(self):
        """Start background thread for real-time updates"""
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()
    
    def update_loop(self):
        """Background update loop"""
        while self.is_running:
            try:
                # Get updated data
                status = self.bot_engine.get_status()
                stats = self.get_detailed_stats()
                
                # Emit updates via SocketIO
                self.socketio.emit('status_update', status)
                self.socketio.emit('stats_update', stats)
                
                # Sleep before next update
                time.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                time.sleep(10)  # Wait longer on error
    
    def start(self):
        """Start the web dashboard"""
        try:
            self.is_running = True
            
            # Start update thread
            self.start_update_thread()
            
            # Start Flask server
            logger.info(f"Starting web dashboard on http://{self.host}:{self.port}")
            
            # In production, use: self.socketio.run(self.app, host=self.host, port=self.port)
            # For development with auto-reload:
            self.app.run(host=self.host, port=self.port, debug=False, threaded=True)
            
        except Exception as e:
            logger.error(f"Failed to start web dashboard: {e}")
            self.is_running = False
    
    def stop(self):
        """Stop the web dashboard"""
        self.is_running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        logger.info("Web dashboard stopped")


# HTML Templates would be in ui/templates/

"""
Basic index.html template:

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TikTok View Bot Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css" rel="stylesheet">
    <style>
        .stat-card { transition: transform 0.3s; }
        .stat-card:hover { transform: translateY(-5px); }
        .progress { height: 20px; }
        .method-badge { font-size: 0.8em; }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">
                <i class="bi bi-play-circle"></i> TikTok View Bot Dashboard
            </a>
            <span class="navbar-text" id="connection-status">
                <i class="bi bi-circle-fill text-danger"></i> Disconnected
            </span>
        </div>
    </nav>
    
    <div class="container-fluid mt-4">
        <div class="row" id="dashboard-content">
            <!-- Content will be loaded dynamically -->
            <div class="col-12 text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <script src="/static/js/dashboard.js"></script>
</body>
</html>
"""