#!/usr/bin/env python3
import os

import aws_cdk as cdk

from geoservices.geoservices_stack import GeoservicesStack


app = cdk.App()
GeoservicesStack(
    app,
    "geodata-staging",
    stage="staging",
    env=cdk.Environment(account=os.getenv('cdk_default_account'), region=os.getenv('cdk_default_region'))
)

app.synth()
