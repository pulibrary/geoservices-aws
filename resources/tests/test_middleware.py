import pytest
import json
import unittest.mock as mock

from fastapi import FastAPI, Request
from starlette.testclient import TestClient
from middleware import HostMiddleware

def test_staging_middleware_for_mosaics_with_id_in_url():
    app = FastAPI()

    @app.get("/mosaicjson")
    async def route1(req: Request):
        request_args = dict(req.query_params)
        return json.dumps(request_args)

    app.add_middleware(HostMiddleware)

    with TestClient(app) as client:
        response = client.get('/123456/mosaicjson?stage=staging')
        assert(json.loads(response.json())['url']) == 's3://figgy-geo-staging/12/34/56/123456/mosaic.json'

def test_production_middleware_for_mosaics_with_id_in_url():
    app = FastAPI()

    @app.get("/mosaicjson")
    async def route1(req: Request):
        request_args = dict(req.query_params)
        return json.dumps(request_args)

    app.add_middleware(HostMiddleware)

    with TestClient(app) as client:
        response = client.get('/123456/mosaicjson?stage=production')
        assert(json.loads(response.json())['url']) == 's3://figgy-geo-production/12/34/56/123456/mosaic.json'

def test_staging_middleware_for_cogs_with_id_in_url():
    app = FastAPI()

    @app.get("/cog")
    async def route1(req: Request):
        request_args = dict(req.query_params)
        return json.dumps(request_args)

    app.add_middleware(HostMiddleware)

    with TestClient(app) as client:
        response = client.get('/123456/cog?stage=staging')
        assert(json.loads(response.json())['url']) == 's3://figgy-geo-staging/12/34/56/123456/display_raster.tif'

def test_production_middleware_for_cogs_with_id_in_url():
    app = FastAPI()

    @app.get("/cog")
    async def route1(req: Request):
        request_args = dict(req.query_params)
        return json.dumps(request_args)

    app.add_middleware(HostMiddleware)

    with TestClient(app) as client:
        response = client.get('/123456/cog?stage=production')
        assert(json.loads(response.json())['url']) == 's3://figgy-geo-production/12/34/56/123456/display_raster.tif'
