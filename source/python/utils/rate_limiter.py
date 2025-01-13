#python/utils/rate_limiter.py

import asyncio
from datetime import datetime


class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    async def __aenter__(self):
        now = datetime.now()
        self.requests = [t for t in self.requests 
                        if (now - t).total_seconds() < self.time_window]
        
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0]).total_seconds()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        self.requests.append(now)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass