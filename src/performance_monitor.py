#!/usr/bin/env python3
"""
Performance monitoring utility for the face recognition system
Tracks FPS, GPU usage, memory consumption, and system performance
"""

import time
import psutil
import threading
from datetime import datetime
import json

class PerformanceMonitor:
    def __init__(self):
        self.stats = {
            'fps_history': [],
            'gpu_memory_history': [],
            'cpu_usage_history': [],
            'ram_usage_history': [],
            'recognition_cache_hits': 0,
            'recognition_cache_misses': 0,
            'frames_processed': 0,
            'faces_detected': 0,
            'attendance_logged': 0
        }
        self.start_time = time.time()
        self.last_frame_time = time.time()
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self, interval=5.0):
        """Start background monitoring"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print("📊 Performance monitoring started")
        
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        print("📊 Performance monitoring stopped")
        
    def _monitor_loop(self, interval):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                # System metrics
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                ram_percent = memory.percent
                
                self.stats['cpu_usage_history'].append({
                    'timestamp': time.time(),
                    'value': cpu_percent
                })
                
                self.stats['ram_usage_history'].append({
                    'timestamp': time.time(),
                    'value': ram_percent
                })
                
                # GPU metrics (if available)
                try:
                    import torch
                    if torch.cuda.is_available():
                        gpu_memory_allocated = torch.cuda.memory_allocated(0) / 1024**3
                        gpu_memory_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
                        gpu_percent = (gpu_memory_allocated / gpu_memory_total) * 100
                        
                        self.stats['gpu_memory_history'].append({
                            'timestamp': time.time(),
                            'allocated_gb': gpu_memory_allocated,
                            'total_gb': gpu_memory_total,
                            'percent': gpu_percent
                        })
                except Exception as e:
                    pass
                
                # Keep only last 100 entries to prevent memory bloat
                for key in ['fps_history', 'gpu_memory_history', 'cpu_usage_history', 'ram_usage_history']:
                    if len(self.stats[key]) > 100:
                        self.stats[key] = self.stats[key][-100:]
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"⚠️ Monitoring error: {e}")
                time.sleep(interval)
    
    def log_frame_processed(self):
        """Log that a frame was processed"""
        current_time = time.time()
        fps = 1.0 / (current_time - self.last_frame_time) if current_time > self.last_frame_time else 0
        
        self.stats['fps_history'].append({
            'timestamp': current_time,
            'fps': fps
        })
        
        self.stats['frames_processed'] += 1
        self.last_frame_time = current_time
        
    def log_faces_detected(self, count):
        """Log number of faces detected"""
        self.stats['faces_detected'] += count
        
    def log_attendance_logged(self):
        """Log that attendance was recorded"""
        self.stats['attendance_logged'] += 1
        
    def log_cache_hit(self):
        """Log cache hit"""
        self.stats['recognition_cache_hits'] += 1
        
    def log_cache_miss(self):
        """Log cache miss"""
        self.stats['recognition_cache_misses'] += 1
        
    def get_summary(self):
        """Get performance summary"""
        runtime = time.time() - self.start_time
        
        # Calculate averages
        recent_fps = [entry['fps'] for entry in self.stats['fps_history'][-10:]]
        avg_fps = sum(recent_fps) / len(recent_fps) if recent_fps else 0
        
        recent_cpu = [entry['value'] for entry in self.stats['cpu_usage_history'][-10:]]
        avg_cpu = sum(recent_cpu) / len(recent_cpu) if recent_cpu else 0
        
        recent_ram = [entry['value'] for entry in self.stats['ram_usage_history'][-10:]]
        avg_ram = sum(recent_ram) / len(recent_ram) if recent_ram else 0
        
        # Cache hit rate
        total_cache_requests = self.stats['recognition_cache_hits'] + self.stats['recognition_cache_misses']
        cache_hit_rate = (self.stats['recognition_cache_hits'] / total_cache_requests * 100) if total_cache_requests > 0 else 0
        
        summary = {
            'runtime_seconds': runtime,
            'runtime_formatted': self._format_duration(runtime),
            'frames_processed': self.stats['frames_processed'],
            'faces_detected': self.stats['faces_detected'],
            'attendance_logged': self.stats['attendance_logged'],
            'average_fps': avg_fps,
            'average_cpu_percent': avg_cpu,
            'average_ram_percent': avg_ram,
            'cache_hit_rate_percent': cache_hit_rate,
            'total_cache_requests': total_cache_requests
        }
        
        # Add GPU info if available
        if self.stats['gpu_memory_history']:
            recent_gpu = self.stats['gpu_memory_history'][-1]
            summary['gpu_memory_allocated_gb'] = recent_gpu['allocated_gb']
            summary['gpu_memory_total_gb'] = recent_gpu['total_gb']
            summary['gpu_memory_percent'] = recent_gpu['percent']
        
        return summary
    
    def _format_duration(self, seconds):
        """Format duration in human readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def print_summary(self):
        """Print performance summary to console"""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("📊 PERFORMANCE SUMMARY")
        print("="*60)
        print(f"🕐 Runtime: {summary['runtime_formatted']}")
        print(f"🎬 Frames Processed: {summary['frames_processed']}")
        print(f"👥 Faces Detected: {summary['faces_detected']}")
        print(f"✅ Attendance Logged: {summary['attendance_logged']}")
        print(f"🚀 Average FPS: {summary['average_fps']:.1f}")
        print(f"🖥️  Average CPU: {summary['average_cpu_percent']:.1f}%")
        print(f"💾 Average RAM: {summary['average_ram_percent']:.1f}%")
        
        if 'gpu_memory_percent' in summary:
            print(f"🎮 GPU Memory: {summary['gpu_memory_percent']:.1f}% ({summary['gpu_memory_allocated_gb']:.1f}/{summary['gpu_memory_total_gb']:.1f} GB)")
        
        print(f"💾 Cache Hit Rate: {summary['cache_hit_rate_percent']:.1f}% ({summary['total_cache_requests']} requests)")
        
        # Performance ratings
        if summary['average_fps'] >= 20:
            fps_rating = "🟢 Excellent"
        elif summary['average_fps'] >= 15:
            fps_rating = "🟡 Good"
        elif summary['average_fps'] >= 10:
            fps_rating = "🟠 Fair"
        else:
            fps_rating = "🔴 Poor"
        
        print(f"📈 FPS Rating: {fps_rating}")
        print("="*60)
    
    def save_to_file(self, filename=None):
        """Save performance data to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_log_{timestamp}.json"
        
        data = {
            'summary': self.get_summary(),
            'detailed_stats': self.stats
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"📁 Performance data saved to: {filename}")
        except Exception as e:
            print(f"❌ Error saving performance data: {e}")

# Global monitor instance
monitor = PerformanceMonitor()

def get_global_monitor():
    """Get the global performance monitor instance"""
    return monitor

if __name__ == "__main__":
    # Demo usage
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # Simulate some activity
    for i in range(10):
        monitor.log_frame_processed()
        monitor.log_faces_detected(2)
        if i % 3 == 0:
            monitor.log_attendance_logged()
        time.sleep(1)
    
    monitor.print_summary()
    monitor.stop_monitoring()
