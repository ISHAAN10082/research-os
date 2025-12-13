import psutil
import time
from loguru import logger

class ThermalGovernor:
    """
    Manages resource usage to prevent M4 Air throttling.
    Also handles rate limiting for external APIs.
    """
    
    def __init__(self):
        self.last_check = 0
        self.cached_status = "nominal"
        # Rate limits (calls per minute)
        self.rate_limits = {
            "groq": 30,
            "arxiv": 60
        }
        self.usage_history = {
            "groq": [],
            "arxiv": []
        }
        
    def check_thermal_status(self) -> str:
        """
        Check if we need to throttle back.
        Returns: 'nominal', 'throttle', 'critical'
        """
        now = time.time()
        if now - self.last_check < 5:
            return self.cached_status
            
        self.last_check = now
        
        # CPU usage check (since we can't easily get temps on macOS without root/extra libs usually)
        # High sustained CPU is a proxy for heat.
        cpu_percent = psutil.cpu_percent(interval=None)
        
        if cpu_percent > 85:
            self.cached_status = "critical"
        elif cpu_percent > 60:
            self.cached_status = "throttle"
        else:
            self.cached_status = "nominal"
            
        return self.cached_status

    def can_use_api(self, api_name: str) -> bool:
        """Check rate limits."""
        history = self.usage_history.get(api_name, [])
        now = time.time()
        
        # Filter calls in last minute
        active_window = [t for t in history if now - t < 60]
        self.usage_history[api_name] = active_window
        
        limit = self.rate_limits.get(api_name, 30)
        return len(active_window) < limit

    def log_api_usage(self, api_name: str):
        self.usage_history.setdefault(api_name, []).append(time.time())

# Singleton
governor = ThermalGovernor()
