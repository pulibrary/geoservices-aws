import urllib3
from starlette.datastructures import URL, QueryParams
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

        headers = dict(scope["headers"])
        headers[b"host"] = bytes(os.getenv("TITILER_BASE_URL"), 'utf-8')
        scope["headers"] = [(k, v) for k, v in headers.items()]

        await self.app(scope, receive, send)

class RewriteMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in (
          "http"
        ):
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        self.stage = request.query_params["stage"]

        url = URL(scope=scope)
        path = url.path
        base_path = path.split('/')
        item_id = base_path[1]

        if (len(base_path) > 2 and base_path[2] == 'mosaicjson'):
            item_url = self.s3_url(item_id, "mosaic.json")
            base_path.pop(1)
            url = url.include_query_params(url=item_url)
            request.scope["path"] = '/'.join(base_path)
            request.scope["query_string"] = url.query
        elif (len(base_path) > 2 and base_path[2] == 'cog'):
            item_url = self.s3_url(item_id, "display_raster.tif")
            base_path.pop(1)
            url = url.include_query_params(url=item_url)
            request.scope["path"] = '/'.join(base_path)
            request.scope["query_string"] = url.query

        await self.app(scope, receive, send)

    def s3_url(self, resource_id, file_name):
        path = f"{resource_id[0:2]}/{resource_id[2:4]}/{resource_id[4:6]}/{resource_id}/{file_name}"
        if self.stage == "production":
            return f"s3://figgy-geo-production/{path}"
        else:
            return f"s3://figgy-geo-staging/{path}"

class TileJSONMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or "tilejson" not in scope["path"]:
            await self.app(scope, receive, send)
            return
        elif "method" in scope.keys() and scope["method"] != "GET":
            await self.app(scope, receive, send)
            return

        async def update_tilejson(message):
            if message["type"] == "http.response.body":
                # convert json string to dict
                obj = json.loads(message["body"].decode())

                # get tiles url and extract the resource id
                tile_url = URL(obj["tiles"][0])
                query_params = QueryParams(tile_url.query)
                url_param = query_params["url"]
                resource_id = url_param.split("/")[-2]

                # generate a new tile url with id in path and no url parameter
                tile_url = tile_url.remove_query_params("url")
                path = f"/{resource_id}{tile_url.path}"
                tile_url = URL(scheme=tile_url.scheme, netloc=tile_url.netloc, path=path)

                # insert tile url into json object and replace message body
                obj["tiles"] = [f"{tile_url}"]
                # raise Exception(message)
                # import pdb; pdb.set_trace()
                message["body"] = json.dumps(obj).encode()

            await send(message)

        await self.app(scope, receive, update_tilejson)
