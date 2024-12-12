"""AWS Lambda handler."""
import logging
import middleware
import urllib3
import json
from mangum import Mangum
from titiler.application.main import app
from titiler.application.settings import ApiSettings
from fastapi import Response
from starlette.middleware.cors import CORSMiddleware
from titiler.core.middleware import LowerCaseQueryStringMiddleware

# Reset middleware so we can apply our own settings
app.user_middleware = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LowerCaseQueryStringMiddleware)
app.add_middleware(middleware.HostMiddleware)
app.add_middleware(middleware.RewriteMiddleware)
app.add_middleware(middleware.TileJSONMiddleware)

logging.getLogger("mangum.lifespan").setLevel(logging.ERROR)
logging.getLogger("mangum.http").setLevel(logging.ERROR)

api_settings = ApiSettings()

handler = Mangum(app, api_gateway_base_path=api_settings.root_path, lifespan="auto")
