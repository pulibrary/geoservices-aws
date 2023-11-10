from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
import urllib3
from starlette.datastructures import URL
from starlette.requests import Request
import json
import os

class HostMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in (
          "http"
        ):
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        headers = dict(request.scope["headers"])
        headers["host"] = os.getenv("TITILER_BASE_URL")
        request.scope["headers"] = [(k, v) for k, v in headers.items()]

        url = URL(scope=scope)
        path = url.path
        base_path = path.split('/')

        if (len(base_path) > 2 and base_path[2] == 'mosaicjson'):
            item_id = base_path[1]
            server = request.scope['server'][0]
            item_url = self.mosaic_s3_url(item_id, server)
            base_path.pop(1)
            url = url.include_query_params(url=item_url)
            request.scope["path"] = '/'.join(base_path)
            request.scope["query_string"] = url.query
        elif (len(base_path) > 2 and base_path[2] == 'cog'):
            item_id = base_path[1]
            server = request.scope['server'][0]
            item_url = self.cog_s3_url(item_id, server)
            base_path.pop(1)
            url = url.include_query_params(url=item_url)
            request.scope["path"] = '/'.join(base_path)
            request.scope["query_string"] = url.query

        await self.app(scope, receive, send)

    def resource_uri(self, resource_id, server):
        if "staging" in server:
            return f"https://figgy-staging.princeton.edu/tilemetadata/{resource_id}"
        else:
            return f"https://figgy.princeton.edu/tilemetadata/{resource_id}"

    def mosaic_s3_url(self, resource_id, server):
        path = f"{resource_id[0:2]}/{resource_id[2:4]}/{resource_id[4:6]}/{resource_id}/mosaic.json"
        if "staging" in server:
            return f"s3://figgy-geo-staging/{path}"
        else:
            return f"s3://figgy-geo-production/{path}"
        return f"s3://figgy-geo-staging/{path}"

    def cog_s3_url(self, resource_id, server):
        http = urllib3.PoolManager()
        resp = http.request('GET', self.resource_uri(resource_id, server))
        return json.loads(resp.data.decode('utf8'))["uri"]
