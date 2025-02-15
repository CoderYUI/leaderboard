from api.index import app
from _middleware import CloudflareMiddleware

app.add_middleware(CloudflareMiddleware)
