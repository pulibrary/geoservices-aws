import pytest
import os
import sys
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest.mock as mock
from rewrite_handler_production import handler as handler_production
from rewrite_handler_staging import handler as handler_staging

def test_rewrites_mosaic_id_productioni_id_in_params():
    event = {'Records': [{'cf': {'request': {'uri': 'https://test.com/mosaicjson', 'querystring': 'id=banana'}}}]}
    output = handler_production(event, {})
    assert output['querystring'] == 'url=s3%3A%2F%2Ffiggy-geo-production%2Fba%2Fna%2Fna%2Fbanana%2Fmosaic.json'

def test_rewrites_mosaic_id_staging_id_params():
    event = {'Records': [{'cf': {'request': {'uri': 'https://test.com/mosaicjson', 'querystring': 'id=banana'}}}]}
    output = handler_staging(event, {})
    assert output['uri'] == 'https://test.com/mosaicjson'
    assert output['querystring'] == 'url=s3%3A%2F%2Ffiggy-geo-staging%2Fba%2Fna%2Fna%2Fbanana%2Fmosaic.json'

# Don't re-process URL if one is given.
def test_keeps_existing_uri_production():
    event = {'Records': [{'cf': {'request': {'uri':
      'https://test.com/mosaicjson', 'querystring': 'id=banana&url=test' }}}]}
    output = handler_production(event, {})
    assert output['querystring'] == 'id=banana&url=test'

# Don't re-process URL if one is given.
def test_keeps_existing_uri_staging():
    event = {'Records': [{'cf': {'request': {'uri':
      'https://test.com/mosaicjson', 'querystring': 'id=banana&url=test' }}}]}
    output = handler_staging(event, {})
    assert output['querystring'] == 'id=banana&url=test'

def test_rewrites_cog_production_id_in_params():
    http_mock = TestHelper().http_mock("s3://figgy-geo-production/ba/na/na/banana/display_raster.tif")
    with mock.patch('urllib3.PoolManager', return_value=http_mock):
        event = {'Records': [{'cf': {'request': {'uri': 'https://test.com/cog', 'querystring': 'id=banana'}}}]}
        output = handler_production(event, {})
        assert output['querystring'] == 'url=s3%3A%2F%2Ffiggy-geo-production%2Fba%2Fna%2Fna%2Fbanana%2Fdisplay_raster.tif'

def test_rewrites_cog_staging_id_in_params():
    http_mock = TestHelper().http_mock("s3://figgy-geo-staging/ba/na/na/banana/display_raster.tif")
    with mock.patch('urllib3.PoolManager', return_value=http_mock):
        event = {'Records': [{'cf': {'request': {'uri': 'https://test.com/cog', 'querystring': 'id=banana'}}}]}
        output = handler_production(event, {})
        assert output['querystring'] == 'url=s3%3A%2F%2Ffiggy-geo-staging%2Fba%2Fna%2Fna%2Fbanana%2Fdisplay_raster.tif'

class TestHelper:
    def http_mock(self, uri):
        json_string = json.dumps({"uri": uri})
        response_mock = mock.MagicMock()
        response_mock.status_code = 200
        response_mock.data = bytes(json_string, 'utf-8')
        http_mock = mock.MagicMock()
        http_mock.request = mock.MagicMock(return_value=response_mock)
        return http_mock
