from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import os

class CloudflareMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-cache'
        return response
