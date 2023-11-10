from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
import urllib3
import json
import pdb

class GenericHandler:
    def __init__(self, stage):
        self.stage = stage

    def s3_root(self):
        if self.stage == "production":
            return "s3://figgy-geo-production"
        else:
            return "s3://figgy-geo-staging"

    def handle(self, event, context):
      request = event['Records'][0]['cf']['request']
      if 'querystring' in request:
        params = {k : v[0] for k, v in parse_qs(request['querystring']).items()}
      else:
        params = {}

      if ('id' in params and 'url' not in params):
          if ('cog' in request['uri']):
            # Strategy - fetch S3 URL from
            # https://figgy.princeton.edu/tilemetadata/<id>,
            # parse JSON and get URI parameter.
            item_id = params['id']
            item_url = self.cog_s3_url(item_id)
          elif ('mosaicjson' in request['uri']):
            item_id = params['id']
            item_url = self.mosaic_s3_url(item_id)

          # Replace id param with url param
          params['url'] = item_url
          params.pop('id')

      request['querystring'] = urlencode(params)
      return request

    def resource_uri(self, resource_id):
        if self.stage == "production":
            return f"https://figgy.princeton.edu/tilemetadata/{resource_id}"
        else:
            return f"https://figgy-staging.princeton.edu/tilemetadata/{resource_id}"

    def mosaic_s3_url(self, resource_id):
        path = f"{resource_id[0:2]}/{resource_id[2:4]}/{resource_id[4:6]}/{resource_id}/mosaic.json"
        if self.stage == "production":
            return f"s3://figgy-geo-production/{path}"
        else:
            return f"s3://figgy-geo-staging/{path}"

    def cog_s3_url(self, resource_id):
        http = urllib3.PoolManager()
        resp = http.request('GET', self.resource_uri(resource_id))
        return json.loads(resp.data.decode('utf8'))["uri"]
