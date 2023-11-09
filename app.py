#!/usr/bin/env python3
import os
import aws_cdk as cdk
from geoservices.geodata_stack import GeodataStack
from geoservices.titiler_service_stack import TitilerServiceStack

app = cdk.App()
GeodataStack(
    app,
    "geodata-staging",
    stage="staging",
    env=cdk.Environment(account=os.getenv('cdk_default_account'), region=os.getenv('cdk_default_region'))
)

GeodataStack(
    app,
    "geodata-production",
    stage="production",
    env=cdk.Environment(account=os.getenv('cdk_default_account'), region=os.getenv('cdk_default_region'))
)

TitilerServiceStack(
    app,
    "titiler-staging",
    stage="staging",
    env=cdk.Environment(account=os.getenv('cdk_default_account'), region=os.getenv('cdk_default_region'))
)

TitilerServiceStack(
    app,
    "titiler-production",
    stage="production",
    env=cdk.Environment(account=os.getenv('cdk_default_account'), region=os.getenv('cdk_default_region'))
)

app.synth()
