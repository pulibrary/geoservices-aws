import pytest
import json

from fastapi import FastAPI, Request
from starlette.testclient import TestClient
from middleware import HostMiddleware, RewriteMiddleware, TileJSONMiddleware

def test_staging_middleware_for_mosaics_with_id_in_url(monkeypatch):
    monkeypatch.setenv('TITILER_BASE_URL', 'base_url')
    monkeypatch.setenv('TITILER_S3_BUCKET', 'figgy-geo-staging')
    app = FastAPI()

    @app.get("/mosaicjson")
    async def route1(req: Request):
        request_args = dict(req.query_params)
        return json.dumps(request_args)

    app.add_middleware(HostMiddleware)
    app.add_middleware(RewriteMiddleware)
    app.add_middleware(TileJSONMiddleware)

    with TestClient(app) as client:
        response = client.get('/123456/mosaicjson?stage=staging')
        assert(json.loads(response.json())['url']) == 's3://figgy-geo-staging/12/34/56/123456/mosaic.json'

def test_production_middleware_for_mosaics_with_id_in_url(monkeypatch):
    monkeypatch.setenv('TITILER_BASE_URL', 'base_url')
    monkeypatch.setenv('TITILER_S3_BUCKET', 'figgy-geo-production')
    app = FastAPI()

    @app.get("/mosaicjson")
    async def route1(req: Request):
        request_args = dict(req.query_params)
        return json.dumps(request_args)

    app.add_middleware(HostMiddleware)
    app.add_middleware(RewriteMiddleware)
    app.add_middleware(TileJSONMiddleware)

    with TestClient(app) as client:
        response = client.get('/123456/mosaicjson?stage=production')
        assert(json.loads(response.json())['url']) == 's3://figgy-geo-production/12/34/56/123456/mosaic.json'

def test_staging_middleware_for_cogs_with_id_in_url(monkeypatch):
    monkeypatch.setenv('TITILER_BASE_URL', 'base_url')
    monkeypatch.setenv('TITILER_S3_BUCKET', 'figgy-geo-staging')
    app = FastAPI()

    @app.get("/cog")
    async def route1(req: Request):
        request_args = dict(req.query_params)
        return json.dumps(request_args)

    app.add_middleware(HostMiddleware)
    app.add_middleware(RewriteMiddleware)
    app.add_middleware(TileJSONMiddleware)

    with TestClient(app) as client:
        response = client.get('/123456/cog?stage=staging')
        assert(json.loads(response.json())['url']) == 's3://figgy-geo-staging/12/34/56/123456/display_raster.tif'

def test_production_middleware_for_cogs_with_id_in_url(monkeypatch):
    monkeypatch.setenv('TITILER_BASE_URL', 'base_url')
    monkeypatch.setenv('TITILER_S3_BUCKET', 'figgy-geo-production')
    app = FastAPI()

    @app.get("/cog")
    async def route1(req: Request):
        request_args = dict(req.query_params)
        return json.dumps(request_args)

    app.add_middleware(HostMiddleware)
    app.add_middleware(RewriteMiddleware)
    app.add_middleware(TileJSONMiddleware)

    with TestClient(app) as client:
        response = client.get('/123456/cog?stage=production')
        assert(json.loads(response.json())['url']) == 's3://figgy-geo-production/12/34/56/123456/display_raster.tif'

def test_middleware_for_mosaic_tilejson(monkeypatch):
    monkeypatch.setenv('TITILER_BASE_URL', 'base_url')
    monkeypatch.setenv('TITILER_S3_BUCKET', 'figgy-geo-production')
    app = FastAPI()

    @app.get("/mosaicjson/tilejson.json")
    async def route1(req: Request):
        tilejson = {"tilejson":"2.2.0","version":"1.0.0","scheme":"xyz","tiles":["https://tiles.prod/mosaicjson/tiles/WebMercatorQuad/{z}/{x}/{y}@1x?url=s3%3A%2F%2Fgeo-production%2F24%2F43%2F18%2F2443189116dd4a28bdd7da1384deb51e%2Fmosaic.json"],"minzoom":8,"maxzoom":13,"bounds":[67.50154032366855,9.00205452967639,94.49732854268473,31.999615061786308],"center":[80.99943443317665,20.50083479573135,8]}
        return tilejson

    app.add_middleware(HostMiddleware)
    app.add_middleware(RewriteMiddleware)
    app.add_middleware(TileJSONMiddleware)

    with TestClient(app) as client:
        response = client.get('/2443189116dd4a28bdd7da1384deb51e/mosaicjson/tilejson.json?stage=production')
        assert(response.json()['tiles']) == ['https://tiles.prod/2443189116dd4a28bdd7da1384deb51e/mosaicjson/tiles/WebMercatorQuad/{z}/{x}/{y}@1x']

def test_middleware_for_cog_tilejson(monkeypatch):
    monkeypatch.setenv('TITILER_BASE_URL', 'base_url')
    monkeypatch.setenv('TITILER_S3_BUCKET', 'figgy-geo-production')
    app = FastAPI()

    @app.get("/cog/tilejson.json")
    async def route1(req: Request):
        tilejson = {"tilejson":"2.2.0","version":"1.0.0","scheme":"xyz","tiles":["https://tiles.prod/cog/tiles/WebMercatorQuad/{z}/{x}/{y}@1x?url=s3%3A%2F%2Fgeo-production%2F24%2F43%2F18%2F2443189116dd4a28bdd7da1384deb51e%2Fdisplay_raster.tif"],"minzoom":8,"maxzoom":13,"bounds":[67.50154032366855,9.00205452967639,94.49732854268473,31.999615061786308],"center":[80.99943443317665,20.50083479573135,8]}
        return tilejson

    app.add_middleware(HostMiddleware)
    app.add_middleware(RewriteMiddleware)
    app.add_middleware(TileJSONMiddleware)

    with TestClient(app) as client:
        response = client.get('/2443189116dd4a28bdd7da1384deb51e/cog/tilejson.json?stage=production')
        assert(response.json()['tiles']) == ['https://tiles.prod/2443189116dd4a28bdd7da1384deb51e/cog/tiles/WebMercatorQuad/{z}/{x}/{y}@1x']
