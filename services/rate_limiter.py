"""
Rate limiting middleware untuk API
"""
import time
from collections import defaultdict
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware: batasi requests per customer phone (20 msgs/menit)
    """

    def __init__(self, app):
        super().__init__(app)
        # Store: {phone_number: [timestamp1, timestamp2, ...]}
        self.requests = defaultdict(list)
        self.rate_limit = settings.rate_limit_per_minute
        self.time_window = 60  # seconds

    async def dispatch(self, request: Request, call_next):
        """Process request dan check rate limit"""

        # Only rate limit webhook dan message endpoints
        if request.url.path in ["/webhook", "/test/send-message"]:
            # Extract phone number dari request
            phone_number = None

            if request.url.path == "/webhook":
                # Untuk webhook, extract dari JSON body
                try:
                    body = await request.body()
                    import json
                    data = json.loads(body)

                    # Extract phone dari nested structure
                    if "entry" in data:
                        for entry in data.get("entry", []):
                            for change in entry.get("changes", []):
                                for message in change.get("value", {}).get("messages", []):
                                    phone_number = message.get("from")
                                    if phone_number:
                                        break
                                if phone_number:
                                    break
                            if phone_number:
                                break

                    # Re-wrap body untuk next handler
                    async def receive():
                        return {"type": "http.request", "body": body}
                    request._receive = receive

                except:
                    pass

            elif request.url.path == "/test/send-message":
                # Untuk test endpoint
                try:
                    body = await request.body()
                    import json
                    data = json.loads(body)
                    phone_number = data.get("phone_number")

                    async def receive():
                        return {"type": "http.request", "body": body}
                    request._receive = receive

                except:
                    pass

            # Check rate limit
            if phone_number:
                current_time = time.time()

                # Cleanup old requests (older than time_window)
                self.requests[phone_number] = [
                    req_time for req_time in self.requests[phone_number]
                    if current_time - req_time < self.time_window
                ]

                # Check if exceeded limit
                if len(self.requests[phone_number]) >= self.rate_limit:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "Rate limit exceeded",
                            "detail": f"Maximum {self.rate_limit} requests per minute allowed"
                        }
                    )

                # Record this request
                self.requests[phone_number].append(current_time)

        response = await call_next(request)
        return response
